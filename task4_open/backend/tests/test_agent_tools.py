"""Pure-function tests for agent/tools.py — Anthropic SDK is NOT called here."""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _holdings():
    from parser.schema import Asset, NormalizedHoldings, PortfolioSummary
    assets = [
        Asset(name="Reliance Industries", asset_type="stock", category="Equity",
              units=10, invested_value_inr=20000.0, current_value_inr=30000.0,
              pnl_inr=10000.0, pnl_pct=50.0),
        Asset(name="ICICI Pru Gilt Fund", asset_type="mutual_fund", category="Debt",
              units=100, invested_value_inr=10000.0, current_value_inr=10500.0,
              pnl_inr=500.0, pnl_pct=5.0),
        Asset(name="HDFC Liquid Fund", asset_type="mutual_fund", category="Debt",
              units=50, invested_value_inr=5000.0, current_value_inr=5100.0,
              pnl_inr=100.0, pnl_pct=2.0),
    ]
    return NormalizedHoldings(
        holder_name="t", source_format="test",
        summary=PortfolioSummary(
            total_invested_inr=35000.0, total_current_inr=45600.0,
            total_pnl_inr=10600.0, total_pnl_pct=30.28, asset_count=3,
        ),
        assets=assets,
    )


def _snapshot():
    from market.schema import Headline, MarketSnapshot, NiftyPoint, NiftyTrend
    points = [NiftyPoint(date=date(2026, 1, i + 1), close=22000.0 + i * 10)
              for i in range(7)]
    return MarketSnapshot(
        nifty_trend=NiftyTrend(points=points, pct_change_period=0.27,
                               current=22060.0, period_days=7),
        news=[
            Headline(title="Reliance hits new high", publisher="X",
                     url="https://x/1", published_at=datetime.now(timezone.utc)),
            Headline(title="Markets close flat", publisher="X",
                     url="https://x/2", published_at=datetime.now(timezone.utc)),
        ],
        news_fallback_used=False,
        cached_at=datetime.now(timezone.utc),
    )


@pytest.fixture(autouse=True)
def _ctx():
    from agent import tools as t
    t._ctx.clear()
    t._ctx["holdings"] = _holdings()
    t._ctx["snapshot"] = _snapshot()
    yield
    t._ctx.clear()


def test_get_nifty_trend_returns_trend_dict():
    from agent.tools import get_nifty_trend
    result = get_nifty_trend.func(period_days=7)
    assert result["period_days"] == 7
    assert len(result["points"]) == 7
    assert result["current"] == 22060.0


def test_get_nifty_trend_invalid_period():
    from agent.tools import get_nifty_trend
    result = get_nifty_trend.func(period_days=42)
    assert "error" in result


def test_get_news_for_holding_filters_by_substring():
    from agent.tools import get_news_for_holding
    result = get_news_for_holding.func(name="Reliance")
    assert result["name"] == "Reliance"
    assert len(result["headlines"]) == 1
    assert "Reliance" in result["headlines"][0]["title"]


def test_compute_concentration_flags_over_threshold_and_categories():
    from agent.tools import compute_concentration
    result = compute_concentration.func(threshold_pct=15.0)
    assert any(o["name"] == "Reliance Industries" for o in result["over_threshold"])
    assert "Equity" in result["category_pct"]
    assert "Debt" in result["category_pct"]


def test_propose_drawdown_simulation_shifts_categories():
    from agent.tools import propose_drawdown_simulation
    proposal = {
        "sell": [{"name": "Reliance Industries", "pct_to_trim": 20.0}],
        "buy": [{"name": "ICICI Pru Gilt Fund", "pct_to_add": 20.0}],
    }
    result = propose_drawdown_simulation.func(rebalance_proposal=proposal)
    assert "category_pct" in result
    assert "new_equity_pct" in result
    assert "fits_risk_band_60_70" in result
    original_equity_pct = 30000.0 / 45600.0 * 100
    assert result["new_equity_pct"] < original_equity_pct


def test_propose_drawdown_clips_holding_at_zero():
    """Trimming more than a holding's full value should clip to 0, not go negative."""
    from agent.tools import propose_drawdown_simulation
    proposal = {
        "sell": [{"name": "ICICI Pru Gilt Fund", "pct_to_trim": 90.0}],
        "buy": [],
    }
    result = propose_drawdown_simulation.func(rebalance_proposal=proposal)
    assert result["category_pct"]["Debt"] >= 0
    assert result["new_equity_pct"] >= 0


def test_propose_drawdown_empty_proposal_keeps_mix_unchanged():
    """An empty proposal should leave the category mix at its original distribution."""
    from agent.tools import propose_drawdown_simulation, compute_concentration
    baseline = compute_concentration.func(threshold_pct=15.0)["category_pct"]
    result = propose_drawdown_simulation.func(rebalance_proposal={})
    assert result["category_pct"] == baseline


def test_propose_drawdown_unknown_name_silently_skipped():
    """A sell/buy on a name not in holdings should be a no-op, not an error."""
    from agent.tools import propose_drawdown_simulation, compute_concentration
    baseline = compute_concentration.func(threshold_pct=15.0)["category_pct"]
    result = propose_drawdown_simulation.func(
        rebalance_proposal={
            "sell": [{"name": "Nonexistent Fund", "pct_to_trim": 50.0}],
            "buy": [{"name": "Also Missing", "pct_to_add": 50.0}],
        },
    )
    assert result["category_pct"] == baseline


def test_compute_concentration_high_threshold_returns_no_holdings():
    """Threshold of 99% should leave nothing over (none of the test holdings are 99% of total)."""
    from agent.tools import compute_concentration
    result = compute_concentration.func(threshold_pct=99.0)
    assert result["over_threshold"] == []
