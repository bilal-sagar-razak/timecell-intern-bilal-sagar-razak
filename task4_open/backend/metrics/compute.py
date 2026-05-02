"""Pure-function metrics computed from NormalizedHoldings. No I/O, no LLM."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.schema import NormalizedHoldings


class KPIs(BaseModel):
    invested_inr: float
    current_inr: float
    equity_pct: float
    debt_pct: float
    overall_xirr_pct: float | None = None
    asset_count: int


class AllocationSlice(BaseModel):
    label: str
    value_inr: float
    pct: float


class XirrEntry(BaseModel):
    name: str
    xirr_pct: float
    color: Literal["positive", "negative"]


class CategoryPerformance(BaseModel):
    category: str
    pnl_inr: float
    cagr_pct: float | None = None


def kpis(nh: NormalizedHoldings) -> KPIs:
    total_current = nh.summary.total_current_inr or 1e-9
    equity_value = sum(a.current_value_inr for a in nh.assets if a.category == "Equity")
    debt_value = sum(a.current_value_inr for a in nh.assets if a.category == "Debt")
    return KPIs(
        invested_inr=nh.summary.total_invested_inr,
        current_inr=nh.summary.total_current_inr,
        equity_pct=round(equity_value / total_current * 100, 2),
        debt_pct=round(debt_value / total_current * 100, 2),
        overall_xirr_pct=nh.summary.overall_xirr_pct,
        asset_count=nh.summary.asset_count,
    )


def allocation(nh: NormalizedHoldings) -> list[AllocationSlice]:
    """Group by sub_category if present, else by category, else by name."""
    buckets: dict[str, float] = {}
    for a in nh.assets:
        label = a.sub_category or a.category or a.name
        buckets[label] = buckets.get(label, 0) + a.current_value_inr
    total = sum(buckets.values()) or 1e-9
    slices = [
        AllocationSlice(label=label, value_inr=v, pct=round(v / total * 100, 2))
        for label, v in buckets.items()
    ]
    slices.sort(key=lambda s: s.value_inr, reverse=True)
    return slices


def xirr_by_fund(nh: NormalizedHoldings, max_entries: int = 20) -> list[XirrEntry]:
    """Sorted desc by xirr_pct, capped at max_entries, names truncated to 24 chars."""
    entries = []
    for a in nh.assets:
        if a.xirr_pct is None:
            continue
        name = a.name if len(a.name) <= 24 else a.name[:21] + "..."
        entries.append(XirrEntry(
            name=name,
            xirr_pct=a.xirr_pct,
            color="positive" if a.xirr_pct >= 0 else "negative",
        ))
    entries.sort(key=lambda e: e.xirr_pct, reverse=True)
    return entries[:max_entries]


def category_performance(nh: NormalizedHoldings) -> list[CategoryPerformance]:
    """Aggregate P&L per category. CAGR is mean of per-asset XIRR within the category."""
    by_cat: dict[str, dict[str, float]] = {}
    for a in nh.assets:
        cat = a.category or "Other"
        if cat not in by_cat:
            by_cat[cat] = {"pnl": 0.0, "invested": 0.0, "current": 0.0}
        by_cat[cat]["pnl"] += a.pnl_inr
        by_cat[cat]["invested"] += a.invested_value_inr
        by_cat[cat]["current"] += a.current_value_inr
    out = []
    for cat, vals in by_cat.items():
        cagrs = [a.xirr_pct for a in nh.assets if (a.category or "Other") == cat and a.xirr_pct is not None]
        avg_cagr = sum(cagrs) / len(cagrs) if cagrs else None
        out.append(CategoryPerformance(
            category=cat,
            pnl_inr=round(vals["pnl"], 2),
            cagr_pct=round(avg_cagr, 2) if avg_cagr is not None else None,
        ))
    out.sort(key=lambda c: c.pnl_inr, reverse=True)
    return out
