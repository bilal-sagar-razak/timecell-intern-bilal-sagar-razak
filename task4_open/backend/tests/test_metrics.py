"""Tests for metrics.compute — pure functions, hand-built fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from metrics.compute import allocation, category_performance, kpis, xirr_by_fund
from parser.schema import Asset, NormalizedHoldings, PortfolioSummary


def _asset(name: str, category: str | None, sub_category: str | None,
           current: float, invested: float, xirr: float | None = None) -> Asset:
    return Asset(
        name=name,
        asset_type="mutual_fund",
        category=category,
        sub_category=sub_category,
        units=1.0,
        invested_value_inr=invested,
        current_value_inr=current,
        xirr_pct=xirr,
        pnl_inr=current - invested,
        pnl_pct=((current - invested) / invested * 100) if invested else 0.0,
    )


def _portfolio(assets: list[Asset], overall_xirr: float | None = 4.71) -> NormalizedHoldings:
    total_invested = sum(a.invested_value_inr for a in assets)
    total_current = sum(a.current_value_inr for a in assets)
    return NormalizedHoldings(
        holder_name="Test",
        source_format="test",
        summary=PortfolioSummary(
            total_invested_inr=total_invested,
            total_current_inr=total_current,
            total_pnl_inr=total_current - total_invested,
            total_pnl_pct=((total_current - total_invested) / total_invested * 100) if total_invested else 0,
            overall_xirr_pct=overall_xirr,
            asset_count=len(assets),
        ),
        assets=assets,
    )


def test_kpis_equity_debt_split() -> None:
    nh = _portfolio([
        _asset("Equity Fund", "Equity", "Flexi Cap", current=600, invested=500),
        _asset("Debt Fund", "Debt", "Gilt", current=400, invested=400),
    ])
    k = kpis(nh)
    assert k.equity_pct == 60.0, f"got {k.equity_pct}"
    assert k.debt_pct == 40.0, f"got {k.debt_pct}"
    assert k.invested_inr == 900.0
    assert k.current_inr == 1000.0
    assert k.overall_xirr_pct == 4.71


def test_kpis_empty_portfolio() -> None:
    nh = _portfolio([], overall_xirr=None)
    k = kpis(nh)
    assert k.equity_pct == 0.0
    assert k.debt_pct == 0.0
    assert k.asset_count == 0


def test_allocation_groups_by_sub_category() -> None:
    nh = _portfolio([
        _asset("Fund A", "Equity", "Flexi Cap", current=500, invested=400),
        _asset("Fund B", "Equity", "Flexi Cap", current=300, invested=300),
        _asset("Fund C", "Debt", "Gilt", current=200, invested=200),
    ])
    slices = allocation(nh)
    by_label = {s.label: s for s in slices}
    assert by_label["Flexi Cap"].value_inr == 800.0
    assert by_label["Flexi Cap"].pct == 80.0
    assert by_label["Gilt"].value_inr == 200.0
    assert by_label["Gilt"].pct == 20.0


def test_allocation_falls_back_to_category_then_name() -> None:
    nh = _portfolio([
        _asset("Fund X", "Equity", None, current=500, invested=500),
        _asset("Lone", None, None, current=500, invested=500),
    ])
    slices = allocation(nh)
    labels = [s.label for s in slices]
    assert "Equity" in labels
    assert "Lone" in labels


def test_xirr_by_fund_sorted_desc_with_color() -> None:
    nh = _portfolio([
        _asset("Top Fund", "Equity", "Flexi Cap", current=110, invested=100, xirr=10.5),
        _asset("Negative Fund", "Equity", "Mid Cap", current=90, invested=100, xirr=-5.2),
        _asset("Middle Fund", "Equity", "Large Cap", current=105, invested=100, xirr=2.3),
        _asset("No XIRR Fund", "Equity", "Small Cap", current=100, invested=100, xirr=None),
    ])
    entries = xirr_by_fund(nh)
    assert len(entries) == 4, f"all assets should appear via pnl_pct fallback, got {len(entries)}"
    assert entries[0].name == "Top Fund"
    assert entries[0].color == "positive"
    assert entries[-1].name == "Negative Fund"
    assert entries[-1].color == "negative"


def test_xirr_by_fund_falls_back_to_pnl_pct() -> None:
    nh = _portfolio([
        _asset("Zerodha Fund", "Equity", "Small Cap", current=120, invested=100, xirr=None),
    ])
    entries = xirr_by_fund(nh)
    assert len(entries) == 1
    assert entries[0].xirr_pct == 20.0, f"expected pnl_pct fallback (20.0), got {entries[0].xirr_pct}"
    assert entries[0].color == "positive"


def test_xirr_by_fund_truncates_long_names() -> None:
    nh = _portfolio([
        _asset("This is an extremely long mutual fund name that exceeds 24 chars",
               "Equity", "Flexi Cap", current=110, invested=100, xirr=5.0),
    ])
    entries = xirr_by_fund(nh)
    assert len(entries[0].name) == 24, f"name not truncated: {entries[0].name}"
    assert entries[0].name.endswith("...")


def test_category_performance_aggregates() -> None:
    nh = _portfolio([
        _asset("Fund A", "Equity", "Flexi Cap", current=500, invested=400, xirr=10.0),
        _asset("Fund B", "Equity", "Mid Cap", current=300, invested=300, xirr=0.0),
        _asset("Fund C", "Debt", "Gilt", current=400, invested=350, xirr=5.0),
    ])
    perf = category_performance(nh)
    by_cat = {p.category: p for p in perf}
    assert by_cat["Equity"].pnl_inr == 100.0
    assert by_cat["Debt"].pnl_inr == 50.0
    assert by_cat["Equity"].cagr_pct == 5.0
    assert by_cat["Debt"].cagr_pct == 5.0


def test_category_performance_includes_sub_breakdowns() -> None:
    nh = _portfolio([
        _asset("Fund A", "Equity", "Flexi Cap", current=500, invested=400, xirr=10.0),
        _asset("Fund B", "Equity", "Mid Cap", current=290, invested=300, xirr=-2.0),
        _asset("Fund C", "Equity", "Flexi Cap", current=220, invested=200, xirr=8.0),
        _asset("Fund D", "Debt", "Gilt", current=400, invested=350, xirr=5.0),
    ])
    perf = category_performance(nh)
    by_cat = {p.category: p for p in perf}

    eq_subs = {b.label: b for b in by_cat["Equity"].sub_breakdowns}
    assert "Flexi Cap" in eq_subs
    assert "Mid Cap" in eq_subs
    assert eq_subs["Flexi Cap"].pnl_inr == 120.0, f"got {eq_subs['Flexi Cap'].pnl_inr}"
    assert eq_subs["Flexi Cap"].cagr_pct == 9.0
    assert eq_subs["Mid Cap"].pnl_inr == -10.0
    assert eq_subs["Mid Cap"].cagr_pct == -2.0

    debt_subs = by_cat["Debt"].sub_breakdowns
    assert len(debt_subs) == 1
    assert debt_subs[0].label == "Gilt"
    assert debt_subs[0].pnl_inr == 50.0


def test_category_performance_falls_back_to_pnl_pct_for_cagr() -> None:
    nh = _portfolio([
        _asset("ZerodhaFund", "Equity", "Small Cap", current=120, invested=100, xirr=None),
    ])
    perf = category_performance(nh)
    assert perf[0].cagr_pct == 20.0, f"expected pnl_pct fallback, got {perf[0].cagr_pct}"
    assert perf[0].sub_breakdowns[0].cagr_pct == 20.0
