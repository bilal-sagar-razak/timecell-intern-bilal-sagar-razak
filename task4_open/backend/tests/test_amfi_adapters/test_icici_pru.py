"""ICICI Pru adapter test."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FIXTURE = Path(__file__).parent.parent / "fixtures" / "amfi" / "icici_pru_sample.xlsx"


def test_icici_pru_adapter_parses_gilt_fund():
    from scripts.amfi_adapters import icici_pru
    schemes = icici_pru.parse(FIXTURE)
    assert len(schemes) == 1
    s = schemes[0]
    assert s.amc == "ICICI Pru"
    assert s.scheme_name == "ICICI Pru Gilt Fund"
    assert len(s.holdings) == 2  # 2 GOI bonds; cash excluded
    assert all(h.kind == "debt" for h in s.holdings)
    assert abs(s.cash_pct - 8.50) < 1e-6
