"""Portfolio risk calculator — stdlib only."""
from __future__ import annotations

import json
import sys
from typing import Any


RUIN_THRESHOLD_MONTHS = 12
CONCENTRATION_THRESHOLD_PCT = 40
_VALID_ASSET_KEYS = ("name", "allocation_pct", "expected_crash_pct")


def _validate_portfolio(portfolio: dict) -> None:
    """Raise ValueError on bad input. Allocation-sum mismatch only warns."""
    if not isinstance(portfolio, dict):
        raise ValueError("portfolio must be a dict")

    for key in ("total_value_inr", "monthly_expenses_inr", "assets"):
        if key not in portfolio:
            raise ValueError(f"missing required key: {key}")

    for field in ("total_value_inr", "monthly_expenses_inr"):
        value = portfolio[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be a number, got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"{field} must be >= 0, got {value}")

    assets = portfolio["assets"]
    if not isinstance(assets, list):
        raise ValueError("assets must be a list")

    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise ValueError(f"asset[{i}] must be a dict")
        for key in _VALID_ASSET_KEYS:
            if key not in asset:
                raise ValueError(f"asset[{i}].{key}: missing")

        name = asset["name"]
        if not isinstance(name, str) or not name:
            raise ValueError(f"asset[{i}].name: must be a non-empty string")

        alloc = asset["allocation_pct"]
        if isinstance(alloc, bool) or not isinstance(alloc, (int, float)):
            raise ValueError(f"asset[{i}].allocation_pct: must be a number")
        if not (0 <= alloc <= 100):
            raise ValueError(f"asset[{i}].allocation_pct: must be in [0, 100], got {alloc}")

        crash = asset["expected_crash_pct"]
        if isinstance(crash, bool) or not isinstance(crash, (int, float)):
            raise ValueError(f"asset[{i}].expected_crash_pct: must be a number")
        if crash > 0:
            raise ValueError(f"asset[{i}].expected_crash_pct: must be <= 0, got {crash}")

    if assets:
        total_alloc = sum(a["allocation_pct"] for a in assets)
        if not (99.99 <= total_alloc <= 100.01):
            print(
                f"warning: allocations sum to {total_alloc:.2f}, not 100",
                file=sys.stderr,
            )


def _asset_post_crash_value(asset: dict, total_value_inr: float) -> float:
    asset_value = total_value_inr * (asset["allocation_pct"] / 100)
    return asset_value * (1 + asset["expected_crash_pct"] / 100)


def compute_risk_metrics(portfolio: dict) -> dict[str, Any]:
    """Compute five risk metrics for a portfolio under a crash scenario.

    Args:
        portfolio: dict with keys total_value_inr (>= 0), monthly_expenses_inr
            (>= 0), and assets (list of dicts with name/allocation_pct/
            expected_crash_pct).

    Returns:
        dict with keys post_crash_value (float), runway_months (float; inf
        when expenses == 0), ruin_test ('PASS' if runway > 12 months else
        'FAIL'), largest_risk_asset (asset name with max allocation_pct *
        |expected_crash_pct|, None if no assets, ties broken by first
        appearance), concentration_warning (True if any asset's
        allocation_pct > 40).

    Raises:
        ValueError: on missing keys, wrong types, or negative numeric fields.
            Allocations not summing to 100 only emit a stderr warning.
    """
    _validate_portfolio(portfolio)
    assets = portfolio["assets"]
    total_value = portfolio["total_value_inr"]
    monthly_expenses = portfolio["monthly_expenses_inr"]

    post_crash_value = sum(_asset_post_crash_value(a, total_value) for a in assets)

    if monthly_expenses == 0:
        runway_months = float("inf")
    else:
        runway_months = post_crash_value / monthly_expenses

    ruin_test = "PASS" if runway_months > RUIN_THRESHOLD_MONTHS else "FAIL"

    if assets:
        largest_risk_asset = max(
            assets,
            key=lambda a: a["allocation_pct"] * abs(a["expected_crash_pct"]),
        )["name"]
    else:
        largest_risk_asset = None

    concentration_warning = any(
        a["allocation_pct"] > CONCENTRATION_THRESHOLD_PCT for a in assets
    )

    return {
        "post_crash_value": post_crash_value,
        "runway_months": runway_months,
        "ruin_test": ruin_test,
        "largest_risk_asset": largest_risk_asset,
        "concentration_warning": concentration_warning,
    }


if __name__ == "__main__":
    sample = {
        "total_value_inr": 10_000_000,
        "monthly_expenses_inr": 80_000,
        "assets": [
            {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
            {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
            {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
            {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct": 0},
        ],
    }
    print(json.dumps(compute_risk_metrics(sample), indent=2))
