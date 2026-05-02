"""Tests for agent/loop.py — Anthropic client is fully mocked."""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _holdings():
    from parser.schema import Asset, NormalizedHoldings, PortfolioSummary
    a = Asset(name="Reliance Industries", asset_type="stock", category="Equity",
              units=10, invested_value_inr=20000.0, current_value_inr=30000.0,
              pnl_inr=10000.0, pnl_pct=50.0)
    return NormalizedHoldings(
        holder_name="t", source_format="test",
        summary=PortfolioSummary(
            total_invested_inr=20000.0, total_current_inr=30000.0,
            total_pnl_inr=10000.0, total_pnl_pct=50.0, asset_count=1,
        ),
        assets=[a],
    )


def _snapshot():
    from market.schema import MarketSnapshot, NiftyPoint, NiftyTrend
    points = [NiftyPoint(date=date(2026, 1, i + 1), close=22000.0) for i in range(3)]
    return MarketSnapshot(
        nifty_trend=NiftyTrend(points=points, pct_change_period=0.0,
                               current=22000.0, period_days=3),
        news=[],
        news_fallback_used=False,
        cached_at=datetime.now(timezone.utc),
    )


@pytest.fixture(autouse=True)
def _isolate_cache_dir(tmp_path, monkeypatch):
    """Redirect the daily-spend file to a per-test tempdir."""
    monkeypatch.setattr("parser.normalize.CACHE_DIR", tmp_path / "cache")


def _make_text_block(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _make_message(text="", input_tokens=200, output_tokens=100):
    msg = MagicMock()
    msg.content = [_make_text_block(text)] if text else []
    msg.usage.input_tokens = input_tokens
    msg.usage.output_tokens = output_tokens
    msg.stop_reason = "end_turn"
    return msg


def _fake_client_with_messages(*messages):
    """Returns a mock Anthropic client whose tool_runner yields the given messages."""
    fake_client = MagicMock()
    fake_client.messages.count_tokens.return_value = MagicMock(input_tokens=300)

    runner = MagicMock()
    runner.__iter__.return_value = iter(messages)
    fake_client.beta.messages.tool_runner.return_value = runner
    return fake_client


def test_happy_path_returns_advice_and_cost(monkeypatch):
    from agent import loop
    msg = _make_message(text="1. Trim Reliance — Evidence: compute_concentration shows 100%.")
    fake = _fake_client_with_messages(msg)
    monkeypatch.setattr(loop, "Anthropic", lambda: fake)

    result = loop.run_rebalance(_holdings(), _snapshot())

    assert "Trim Reliance" in result.advice_markdown
    assert result.iterations == 1
    assert result.truncated is False
    assert result.cost_usd > 0


def test_iteration_cap_marks_truncated(monkeypatch):
    """When the runner yields MAX_TOOL_ITERATIONS messages without a final text answer, mark truncated."""
    from agent import loop
    empty_msgs = [_make_message(text="") for _ in range(loop.MAX_TOOL_ITERATIONS)]
    fake = _fake_client_with_messages(*empty_msgs)
    monkeypatch.setattr(loop, "Anthropic", lambda: fake)

    result = loop.run_rebalance(_holdings(), _snapshot())
    assert result.truncated is True
    assert result.iterations == loop.MAX_TOOL_ITERATIONS


def test_per_call_cap_raises_budget_exhausted(monkeypatch):
    """Worst-case cost estimate over MAX_REBALANCE_USD_PER_CALL must raise BudgetExhausted before any SDK call."""
    from agent import loop
    from parser.normalize import BudgetExhausted

    fake = MagicMock()
    fake.messages.count_tokens.return_value = MagicMock(input_tokens=10_000_000)
    fake.beta.messages.tool_runner = MagicMock()
    monkeypatch.setattr(loop, "Anthropic", lambda: fake)

    with pytest.raises(BudgetExhausted):
        loop.run_rebalance(_holdings(), _snapshot())
    fake.beta.messages.tool_runner.assert_not_called()


def test_daily_cap_pre_check_raises(monkeypatch, tmp_path):
    """If the shared daily-spend file is already over the cap, raise BudgetExhausted."""
    from agent import loop
    from parser.normalize import BudgetExhausted, _today_cache_path
    monkeypatch.setattr("parser.normalize.CACHE_DIR", tmp_path / "cache")
    p = _today_cache_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('{"usd": 10.00}')
    monkeypatch.setenv("MAX_DAILY_LLM_USD", "2.00")

    fake = MagicMock()
    fake.messages.count_tokens.return_value = MagicMock(input_tokens=300)
    fake.beta.messages.tool_runner = MagicMock()
    monkeypatch.setattr(loop, "Anthropic", lambda: fake)

    with pytest.raises(BudgetExhausted):
        loop.run_rebalance(_holdings(), _snapshot())
    fake.beta.messages.tool_runner.assert_not_called()


def test_happy_path_cost_math_is_exact(monkeypatch):
    """Cost = (input_tokens × $3 + output_tokens × $15) / 1M, summed over all turns."""
    from agent import loop
    msg = _make_message(text="ok", input_tokens=200, output_tokens=100)
    fake = _fake_client_with_messages(msg)
    monkeypatch.setattr(loop, "Anthropic", lambda: fake)

    result = loop.run_rebalance(_holdings(), _snapshot())
    expected = 200 * 3.0 / 1_000_000 + 100 * 15.0 / 1_000_000
    assert abs(result.cost_usd - expected) < 1e-9


def test_multi_turn_costs_are_summed(monkeypatch):
    """Two turns of usage should sum, not overwrite."""
    from agent import loop
    msgs = [
        _make_message(text="", input_tokens=100, output_tokens=50),
        _make_message(text="final", input_tokens=300, output_tokens=80),
    ]
    fake = _fake_client_with_messages(*msgs)
    monkeypatch.setattr(loop, "Anthropic", lambda: fake)

    result = loop.run_rebalance(_holdings(), _snapshot())
    expected = (100 + 300) * 3.0 / 1_000_000 + (50 + 80) * 15.0 / 1_000_000
    assert abs(result.cost_usd - expected) < 1e-9
    assert result.iterations == 2


def test_instrument_tools_records_calls_into_trace_list():
    """Direct unit test of the trace wrapper: records name, input, output, duration_ms."""
    from agent import loop, tools

    trace: list = []
    instrumented = loop._instrument_tools(trace, tools.TOOLS)
    tools._ctx["holdings"] = _holdings()
    tools._ctx["snapshot"] = _snapshot()
    try:
        next(t for t in instrumented if t.name == "compute_concentration").func(threshold_pct=15.0)
    finally:
        tools._ctx.clear()

    assert len(trace) == 1
    entry = trace[0]
    assert entry["tool_name"] == "compute_concentration"
    assert entry["input_json"] == {"threshold_pct": 15.0}
    assert "category_pct" in entry["output_json"]
    assert isinstance(entry["duration_ms"], int) and entry["duration_ms"] >= 0
