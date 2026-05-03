"""Tests for amfi/bundle.py loader + indexes."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURE = Path(__file__).parent / "fixtures" / "amfi" / "bundle_tiny.json"


@pytest.fixture(autouse=True)
def _reset_bundle(monkeypatch):
    """Point loader at the test fixture and clear any cached singleton."""
    monkeypatch.setattr("amfi.bundle.BUNDLE_PATH", FIXTURE)
    from amfi import bundle
    bundle._cached = None
    yield
    bundle._cached = None


def test_load_bundle_returns_4_schemes():
    from amfi.bundle import load_bundle
    b = load_bundle()
    assert len(b.schemes) == 4


def test_by_isin_index_lookup_hits():
    from amfi.bundle import load_bundle
    b = load_bundle()
    assert b.by_isin["INF879O01027"].scheme_name.startswith("Parag Parikh Flexi Cap")


def test_by_normalized_name_index_lookup_hits():
    from amfi.bundle import load_bundle
    from amfi.normalize import normalize_scheme_name
    b = load_bundle()
    key = normalize_scheme_name("HDFC Flexi Cap Fund")
    assert b.by_normalized_name[key].isin == "INF179K01YV8"


def test_load_bundle_missing_raises(monkeypatch, tmp_path):
    from amfi.bundle import BundleMissing, load_bundle
    monkeypatch.setattr("amfi.bundle.BUNDLE_PATH", tmp_path / "nope.json")
    from amfi import bundle
    bundle._cached = None
    with pytest.raises(BundleMissing):
        load_bundle()
