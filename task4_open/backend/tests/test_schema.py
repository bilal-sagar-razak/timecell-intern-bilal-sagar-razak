"""Tests for parser.schema — Pydantic validation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.schema import Asset, NormalizedHoldings, PortfolioSummary


def _valid_asset_dict() -> dict:
    return {
        "name": "Parag Parikh Flexi Cap Fund Direct",
        "asset_type": "mutual_fund",
        "isin": None,
        "amc": "PPFAS",
        "category": "Equity",
        "sub_category": "Flexi Cap",
        "folio": "13959825",
        "units": 8547.228,
        "invested_value_inr": 624968.74,
        "current_value_inr": 763913.63,
        "xirr_pct": 10.22,
        "pnl_inr": 138944.89,
        "pnl_pct": 22.23,
    }


def test_asset_happy_path() -> None:
    asset = Asset.model_validate(_valid_asset_dict())
    assert asset.name == "Parag Parikh Flexi Cap Fund Direct"
    assert asset.category == "Equity"


def test_asset_rejects_invalid_category() -> None:
    bad = _valid_asset_dict() | {"category": "Crypto"}
    try:
        Asset.model_validate(bad)
    except Exception as e:
        assert "category" in str(e), f"category not in error: {e}"
        return
    raise AssertionError("expected validation error, none raised")


def test_normalized_holdings_minimal() -> None:
    payload = {
        "holder_name": "Test User",
        "source_format": "groww_xlsx",
        "summary": {
            "total_invested_inr": 100.0,
            "total_current_inr": 110.0,
            "total_pnl_inr": 10.0,
            "total_pnl_pct": 10.0,
            "asset_count": 1,
        },
        "assets": [_valid_asset_dict()],
    }
    nh = NormalizedHoldings.model_validate(payload)
    assert nh.holder_name == "Test User"
    assert len(nh.assets) == 1
    assert nh.parser_warnings == []


def test_summary_rejects_negative_count() -> None:
    bad = {
        "total_invested_inr": 0.0,
        "total_current_inr": 0.0,
        "total_pnl_inr": 0.0,
        "total_pnl_pct": 0.0,
        "asset_count": -1,
    }
    try:
        PortfolioSummary.model_validate(bad)
    except Exception as e:
        assert "asset_count" in str(e), f"asset_count not in error: {e}"
        return
    raise AssertionError("expected validation error, none raised")
