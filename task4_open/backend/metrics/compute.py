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


class SubCategoryBreakdown(BaseModel):
    label: str
    pnl_inr: float
    cagr_pct: float | None = None


class CategoryPerformance(BaseModel):
    category: str
    pnl_inr: float
    cagr_pct: float | None = None
    sub_breakdowns: list[SubCategoryBreakdown] = []


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
    """Sorted desc, capped at max_entries, names truncated to 24 chars.
    Uses xirr_pct when available; falls back to pnl_pct so every asset appears
    even on broker exports (Zerodha/Groww) that don't ship per-asset XIRR.
    """
    entries = []
    for a in nh.assets:
        value = a.xirr_pct if a.xirr_pct is not None else a.pnl_pct
        name = a.name if len(a.name) <= 24 else a.name[:21] + "..."
        entries.append(XirrEntry(
            name=name,
            xirr_pct=value,
            color="positive" if value >= 0 else "negative",
        ))
    entries.sort(key=lambda e: e.xirr_pct, reverse=True)
    return entries[:max_entries]


def category_performance(nh: NormalizedHoldings) -> list[CategoryPerformance]:
    """Aggregate P&L per major category, with sub_category breakdowns inside.
    Each sub_breakdown uses the same label as the allocation donut (sub_category
    if present, else asset name). Per-bucket CAGR is the mean of per-asset
    xirr_pct in that bucket; falls back to mean pnl_pct so every bucket shows
    a return number even on broker exports without XIRR.
    """
    cat_totals: dict[str, dict[str, float]] = {}
    sub_totals: dict[tuple[str, str], dict[str, float]] = {}
    sub_returns: dict[tuple[str, str], list[float]] = {}
    cat_returns: dict[str, list[float]] = {}

    for a in nh.assets:
        cat = a.category or "Other"
        sub_label = a.sub_category or a.name
        ret = a.xirr_pct if a.xirr_pct is not None else a.pnl_pct

        cat_totals.setdefault(cat, {"pnl": 0.0})["pnl"] += a.pnl_inr
        cat_returns.setdefault(cat, []).append(ret)

        key = (cat, sub_label)
        sub_totals.setdefault(key, {"pnl": 0.0})["pnl"] += a.pnl_inr
        sub_returns.setdefault(key, []).append(ret)

    out = []
    for cat, totals in cat_totals.items():
        rets = cat_returns[cat]
        avg_cagr = sum(rets) / len(rets) if rets else None

        breakdowns = []
        for (c, label), sub in sub_totals.items():
            if c != cat:
                continue
            srets = sub_returns[(c, label)]
            sub_cagr = sum(srets) / len(srets) if srets else None
            breakdowns.append(SubCategoryBreakdown(
                label=label,
                pnl_inr=round(sub["pnl"], 2),
                cagr_pct=round(sub_cagr, 2) if sub_cagr is not None else None,
            ))
        breakdowns.sort(key=lambda b: b.pnl_inr, reverse=True)

        out.append(CategoryPerformance(
            category=cat,
            pnl_inr=round(totals["pnl"], 2),
            cagr_pct=round(avg_cagr, 2) if avg_cagr is not None else None,
            sub_breakdowns=breakdowns,
        ))
    out.sort(key=lambda c: c.pnl_inr, reverse=True)
    return out
