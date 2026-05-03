"""HDFC adapter test against a tiny xlsx fixture."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FIXTURE = Path(__file__).parent.parent / "fixtures" / "amfi" / "hdfc_sample.xlsx"


def test_hdfc_adapter_parses_one_scheme_with_3_holdings():
    from scripts.amfi_adapters import hdfc
    schemes = hdfc.parse(FIXTURE)
    assert len(schemes) == 1
    s = schemes[0]
    assert s.amc == "HDFC"
    assert s.scheme_name == "HDFC Flexi Cap Fund"
    assert len(s.holdings) == 3  # 3 stocks; cash row excluded
    h0 = next(h for h in s.holdings if h.isin == "INE040A01034")
    assert h0.name == "HDFC Bank Limited"
    assert abs(h0.weight_pct - 9.20) < 1e-6
    assert abs(s.cash_pct - 3.10) < 1e-6
