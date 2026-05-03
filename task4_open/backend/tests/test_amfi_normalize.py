"""Unit tests for amfi/normalize.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_normalize_strips_direct_growth_suffix():
    from amfi.normalize import normalize_scheme_name
    assert (
        normalize_scheme_name("Parag Parikh Flexi Cap Fund - Direct Growth")
        == normalize_scheme_name("Parag Parikh Flexi Cap Fund")
    )


def test_normalize_strips_idcw_and_dividend_qualifiers():
    from amfi.normalize import normalize_scheme_name
    out = normalize_scheme_name("HDFC Flexi Cap Fund (IDCW)")
    assert "idcw" not in out
    assert normalize_scheme_name("HDFC Flexi Cap Fund - Dividend") == out


def test_normalize_collapses_whitespace_and_lowercases():
    from amfi.normalize import normalize_scheme_name
    assert normalize_scheme_name("  Quant   Active   Fund  ") == "quant active fund"


def test_normalize_strips_punctuation_except_ampersand_and_digits():
    from amfi.normalize import normalize_scheme_name
    assert normalize_scheme_name("S&P BSE 500 Fund - Direct, Plan A") == "s&p bse 500 fund"
