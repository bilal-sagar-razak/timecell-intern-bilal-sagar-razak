"""Unit tests for holdings/overlap.py — pure math, no bundle/network."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _scheme(name: str, holdings: list[dict], cash_pct: float = 0.0):
    from amfi.schema import FundHolding, Scheme
    return Scheme(
        scheme_name=name, isin=None, amc="X",
        scheme_aum_inr=1e9, as_of_date=date(2026, 4, 30),
        holdings=[FundHolding(**h) for h in holdings],
        cash_pct=cash_pct,
    )


def test_identical_funds_overlap_close_to_100():
    from holdings.overlap import pairwise_overlap
    a = _scheme("A", [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 50.0, "value_inr": 5e8},
        {"name": "Reliance",  "isin": "INE002A01018", "weight_pct": 50.0, "value_inr": 5e8},
    ])
    res = pairwise_overlap(a, a)
    assert 99.0 <= res.overlap_pct <= 100.01
    assert res.shared_count == 2


def test_disjoint_funds_overlap_zero():
    from holdings.overlap import pairwise_overlap
    a = _scheme("A", [{"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 100.0, "value_inr": 1e9}])
    b = _scheme("B", [{"name": "Reliance",  "isin": "INE002A01018", "weight_pct": 100.0, "value_inr": 1e9}])
    res = pairwise_overlap(a, b)
    assert res.overlap_pct == 0.0
    assert res.shared_count == 0


def test_partial_overlap_uses_min_weight():
    from holdings.overlap import pairwise_overlap
    a = _scheme("A", [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 30.0, "value_inr": 3e8},
        {"name": "Reliance",  "isin": "INE002A01018", "weight_pct": 70.0, "value_inr": 7e8},
    ])
    b = _scheme("B", [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 50.0, "value_inr": 5e8},
        {"name": "Infosys",   "isin": "INE009A01021", "weight_pct": 50.0, "value_inr": 5e8},
    ])
    res = pairwise_overlap(a, b)
    # min(30, 50) = 30 for HDFC Bank; nothing else shared
    assert abs(res.overlap_pct - 30.0) < 1e-6
    assert res.shared_count == 1
    assert res.shared_stocks[0]["name"] == "HDFC Bank"
    assert res.shared_stocks[0]["min"] == 30.0


def test_match_by_name_when_isin_missing():
    """When ISIN is null on either side, fall back to normalized stock-name match."""
    from holdings.overlap import pairwise_overlap
    a = _scheme("A", [{"name": "HDFC Bank", "isin": None, "weight_pct": 60.0, "value_inr": 6e8}])
    b = _scheme("B", [{"name": "HDFC Bank", "isin": None, "weight_pct": 40.0, "value_inr": 4e8}])
    res = pairwise_overlap(a, b)
    assert abs(res.overlap_pct - 40.0) < 1e-6


def test_build_matrix_emits_full_n_by_n_with_shared_index():
    from holdings.overlap import build_matrix
    a = _scheme("A", [{"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 50.0, "value_inr": 5e8}])
    b = _scheme("B", [{"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 30.0, "value_inr": 3e8}])
    funds = [
        {"asset_name": "Fund A", "scheme_name": "A", "matched_by": "isin", "scheme": a},
        {"asset_name": "Fund B", "scheme_name": "B", "matched_by": "isin", "scheme": b},
    ]
    out = build_matrix(funds)
    assert len(out["matrix"]) == 2
    assert len(out["matrix"][0]) == 2
    # Symmetry
    assert out["matrix"][0][1]["overlap_pct"] == out["matrix"][1][0]["overlap_pct"]
    # shared_stocks_index keyed only for i<j
    assert "0_1" in out["shared_stocks_index"]
    assert "1_0" not in out["shared_stocks_index"]
