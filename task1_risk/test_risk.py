"""Tests for task1_risk.risk — plain-assert, no pytest."""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

# Sibling import: ensure task1_risk/ is on sys.path when running from repo root
sys.path.insert(0, str(Path(__file__).parent))

from risk import compute_risk_metrics  # noqa: E402


SAMPLE = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 80_000,
    "assets": [
        {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct": 0},
    ],
}


def test_post_crash_value_sample() -> None:
    result = compute_risk_metrics(SAMPLE)
    assert math.isclose(result["post_crash_value"], 5_700_000, rel_tol=1e-9), \
        f"expected 5_700_000, got {result['post_crash_value']}"


def test_runway_and_ruin_test_sample() -> None:
    result = compute_risk_metrics(SAMPLE)
    assert math.isclose(result["runway_months"], 71.25, rel_tol=1e-9), \
        f"expected 71.25, got {result['runway_months']}"
    assert result["ruin_test"] == "PASS", \
        f"expected 'PASS', got {result['ruin_test']!r}"


def test_largest_risk_asset_sample() -> None:
    result = compute_risk_metrics(SAMPLE)
    assert result["largest_risk_asset"] == "BTC", \
        f"expected 'BTC', got {result['largest_risk_asset']!r}"


def test_concentration_boundary() -> None:
    result = compute_risk_metrics(SAMPLE)
    # NIFTY50 is exactly 40 — must NOT trigger (strict > 40 only)
    assert result["concentration_warning"] is False, \
        f"expected False, got {result['concentration_warning']!r}"


def test_zero_expenses() -> None:
    portfolio = copy.deepcopy(SAMPLE)
    portfolio["monthly_expenses_inr"] = 0
    result = compute_risk_metrics(portfolio)
    assert result["runway_months"] == float("inf"), \
        f"expected inf, got {result['runway_months']}"
    assert result["ruin_test"] == "PASS", \
        f"expected 'PASS', got {result['ruin_test']!r}"


def test_empty_assets() -> None:
    portfolio = {
        "total_value_inr": 1_000_000,
        "monthly_expenses_inr": 50_000,
        "assets": [],
    }
    result = compute_risk_metrics(portfolio)
    assert result["post_crash_value"] == 0, \
        f"expected 0, got {result['post_crash_value']}"
    assert result["largest_risk_asset"] is None, \
        f"expected None, got {result['largest_risk_asset']!r}"
    assert result["concentration_warning"] is False, \
        f"expected False, got {result['concentration_warning']!r}"


def test_single_asset_50pct() -> None:
    portfolio = {
        "total_value_inr": 1_000_000,
        "monthly_expenses_inr": 10_000,
        "assets": [
            {"name": "ONLY", "allocation_pct": 50, "expected_crash_pct": -20},
        ],
    }
    result = compute_risk_metrics(portfolio)
    assert result["concentration_warning"] is True, \
        f"expected True, got {result['concentration_warning']!r}"


def test_validation_raises_on_missing_key() -> None:
    try:
        compute_risk_metrics({})
    except ValueError:
        return
    raise AssertionError("expected ValueError, none raised")


def test_input_not_mutated() -> None:
    snapshot = copy.deepcopy(SAMPLE)
    compute_risk_metrics(SAMPLE)
    assert SAMPLE == snapshot, "compute_risk_metrics mutated its input"


if __name__ == "__main__":
    test_post_crash_value_sample()
    test_runway_and_ruin_test_sample()
    test_largest_risk_asset_sample()
    test_concentration_boundary()
    test_zero_expenses()
    test_empty_assets()
    test_single_asset_50pct()
    test_validation_raises_on_missing_key()
    test_input_not_mutated()
    print("All tests passed")
