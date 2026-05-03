"""Unit tests for amfi/match.py — uses the tiny bundle fixture."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURE = Path(__file__).parent / "fixtures" / "amfi" / "bundle_tiny.json"


@pytest.fixture(autouse=True)
def _reset_bundle(monkeypatch):
    monkeypatch.setattr("amfi.bundle.BUNDLE_PATH", FIXTURE)
    from amfi import bundle
    bundle._cached = None
    yield
    bundle._cached = None


def _asset(name: str, isin: str | None = None, amc: str | None = None):
    from parser.schema import Asset
    return Asset(
        name=name, asset_type="mutual_fund", isin=isin, amc=amc,
        units=1.0, invested_value_inr=1000.0, current_value_inr=1100.0,
        pnl_inr=100.0, pnl_pct=10.0,
    )


def test_match_by_isin_exact():
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    matches = match_user_funds([_asset("Parag Parikh Flexi Cap Fund", isin="INF879O01027")], b)
    assert matches[0].matched is True
    assert matches[0].matched_by == "isin"
    assert matches[0].confidence == 1.0
    assert matches[0].scheme.isin == "INF879O01027"


def test_match_by_normalized_name_exact():
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    matches = match_user_funds([_asset("HDFC Flexi Cap Fund - Direct Growth")], b)
    assert matches[0].matched is True
    assert matches[0].matched_by == "name"
    assert matches[0].confidence >= 0.9
    assert matches[0].scheme.isin == "INF179K01YV8"


def test_match_by_fuzzy_name_above_threshold():
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    # Slightly typo'd name should still fuzzy-match HDFC Flexi Cap Fund
    matches = match_user_funds([_asset("HDFC FlexiCap Fund Direct Plan")], b)
    assert matches[0].matched is True
    assert matches[0].matched_by == "name"
    assert 0.85 <= matches[0].confidence < 1.0


def test_match_no_isin_or_name_returns_none():
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    matches = match_user_funds([_asset("Made Up Fund That Does Not Exist Anywhere")], b)
    assert matches[0].matched is False
    assert matches[0].matched_by == "none"
    assert matches[0].scheme is None


def test_match_scoped_to_amc_when_provided():
    """When asset.amc is provided, fuzzy lookup is restricted to that AMC's schemes."""
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    # "Flexi Cap Fund" alone is ambiguous (HDFC + PPFAS); scope by AMC=HDFC
    matches = match_user_funds([_asset("Flexi Cap Fund", amc="HDFC")], b)
    assert matches[0].matched is True
    assert matches[0].scheme.amc == "HDFC"
