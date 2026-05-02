"""Anthropic Sonnet tool-use loop driving the rebalance agent."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from anthropic.lib.tools import beta_tool
from pydantic import BaseModel

from agent.tools import TOOLS, _ctx
from market.schema import MarketSnapshot
from parser.normalize import (
    BudgetExhausted,
    _max_daily_usd,
    _read_today_usd,
    _write_today_usd,
)
from parser.schema import NormalizedHoldings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_OUTPUT_TOKENS_PER_TURN = 2048
MAX_TOOL_ITERATIONS = 8
MAX_REBALANCE_USD_PER_CALL = 0.50
SONNET_INPUT_USD_PER_M = 3.0
SONNET_OUTPUT_USD_PER_M = 15.0

_PROMPT_PATH = Path(__file__).parent / "prompts" / "rebalance.txt"


class ToolCall(BaseModel):
    tool_name: str
    input_json: dict
    output_json: dict
    ts: datetime
    duration_ms: int


class RebalanceResult(BaseModel):
    advice_markdown: str
    trace: list[ToolCall]
    iterations: int
    truncated: bool
    cost_usd: float


def _build_user_message(holdings: NormalizedHoldings, snapshot: MarketSnapshot) -> str:
    total = holdings.summary.total_current_inr or 1e-9
    lines = ["Portfolio digest:"]
    for a in holdings.assets:
        pct = a.current_value_inr / total * 100
        lines.append(
            f"- {a.name} [{a.category or 'Other'}]: "
            f"INR {a.current_value_inr:,.0f} ({pct:.1f}%), "
            f"P&L INR {a.pnl_inr:,.0f} ({a.pnl_pct:+.2f}%)"
        )
    lines.append("")
    lines.append("Market context:")
    nt = snapshot.nifty_trend
    lines.append(
        f"- Nifty 50 current: {nt.current:.2f}, "
        f"period change ({nt.period_days}d): {nt.pct_change_period:+.2f}%"
    )
    lines.append(f"- News headlines available: {len(snapshot.news)}")
    lines.append("")
    lines.append(
        "Produce 2 or 3 numbered rebalancing suggestions per the system prompt. "
        "Use the tools to anchor every suggestion in evidence."
    )
    return "\n".join(lines)


def _instrument_tools(trace_list: list[dict], original_tools):
    """Wrap each tool's func to record into trace_list, then re-decorate as BetaFunctionTools."""
    wrapped = []
    for original in original_tools:
        original_func = original.func
        original_name = original.name

        def make_wrapper(fn, nm):
            def wrapper(**kwargs) -> dict:
                started = time.time()
                ts = datetime.now(timezone.utc)
                out: dict = {}
                try:
                    out = fn(**kwargs)
                    return out
                except Exception as e:
                    out = {"error": str(e)}
                    raise
                finally:
                    trace_list.append({
                        "tool_name": nm,
                        "input_json": kwargs,
                        "output_json": out if isinstance(out, dict) else {"value": out},
                        "ts": ts,
                        "duration_ms": int((time.time() - started) * 1000),
                    })

            wrapper.__name__ = nm
            wrapper.__doc__ = fn.__doc__
            wrapper.__annotations__ = fn.__annotations__
            return wrapper

        wrapped.append(beta_tool(make_wrapper(original_func, original_name)))
    return wrapped


def _last_text(message) -> str:
    """Return the last text block content from a message, or '' if none."""
    if not getattr(message, "content", None):
        return ""
    for block in reversed(message.content):
        if getattr(block, "type", None) == "text":
            return getattr(block, "text", "") or ""
    return ""


def run_rebalance(
    holdings: NormalizedHoldings, snapshot: MarketSnapshot
) -> RebalanceResult:
    """Drive the Sonnet tool-use loop and return advice + trace + cost."""
    system_prompt = _PROMPT_PATH.read_text()
    user_msg = _build_user_message(holdings, snapshot)

    client = Anthropic()

    count_resp = client.messages.count_tokens(
        model=DEFAULT_MODEL,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    per_turn_input_tokens = count_resp.input_tokens

    # Input prefix (system + user + tools) is re-billed every turn.
    worst_case = (
        per_turn_input_tokens * MAX_TOOL_ITERATIONS * SONNET_INPUT_USD_PER_M / 1_000_000
        + (MAX_OUTPUT_TOKENS_PER_TURN * MAX_TOOL_ITERATIONS)
        * SONNET_OUTPUT_USD_PER_M
        / 1_000_000
    )
    if worst_case > MAX_REBALANCE_USD_PER_CALL:
        raise BudgetExhausted(
            f"per-call cap ${MAX_REBALANCE_USD_PER_CALL:.2f} would be exceeded "
            f"(worst-case estimated ${worst_case:.4f})"
        )

    cap = _max_daily_usd()
    if cap is not None:
        spent = _read_today_usd()
        if spent + worst_case > cap:
            raise BudgetExhausted(
                f"daily budget ${cap:.2f} would be exceeded "
                f"(spent ${spent:.4f} so far, this call worst-case ${worst_case:.4f})"
            )

    _ctx["holdings"] = holdings
    _ctx["snapshot"] = snapshot

    trace_list: list[dict] = []
    instrumented = _instrument_tools(trace_list, TOOLS)

    total_input = 0
    total_output = 0
    iterations = 0
    last_message = None

    try:
        runner = client.beta.messages.tool_runner(
            model=DEFAULT_MODEL,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
            tools=instrumented,
            max_tokens=MAX_OUTPUT_TOKENS_PER_TURN,
            max_iterations=MAX_TOOL_ITERATIONS,
        )

        for msg in runner:
            iterations += 1
            last_message = msg
            usage = getattr(msg, "usage", None)
            if usage is not None:
                total_input += getattr(usage, "input_tokens", 0) or 0
                total_output += getattr(usage, "output_tokens", 0) or 0

        advice = _last_text(last_message) if last_message is not None else ""
        truncated = iterations >= MAX_TOOL_ITERATIONS and not advice.strip()
    finally:
        _ctx.clear()

    cost = (
        total_input * SONNET_INPUT_USD_PER_M / 1_000_000
        + total_output * SONNET_OUTPUT_USD_PER_M / 1_000_000
    )

    if cap is not None and cost > 0:
        try:
            _write_today_usd(_read_today_usd() + cost)
        except OSError as e:
            logger.warning("failed to update daily spend file: %s", e, exc_info=True)

    return RebalanceResult(
        advice_markdown=advice.strip(),
        trace=[ToolCall(**t) for t in trace_list],
        iterations=iterations,
        truncated=truncated,
        cost_usd=round(cost, 6),
    )
