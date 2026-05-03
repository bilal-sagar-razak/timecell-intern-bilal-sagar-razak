"""Integration test for refresh_amfi.py — stubbed network + fake adapters."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_refresh_emits_merged_bundle_and_coverage(monkeypatch, tmp_path):
    """End-to-end stubbed: fake fetch + 2 fake adapters → merged JSON + coverage.md."""
    from amfi.schema import FundHolding, Scheme
    from scripts import refresh_amfi as r

    fake_amc_dir = tmp_path / "fake_amc_inputs"
    fake_amc_dir.mkdir()
    (fake_amc_dir / "HDFC_Apr2026.xlsx").write_bytes(b"fake-hdfc")
    (fake_amc_dir / "ICICIPru_Apr2026.xlsx").write_bytes(b"fake-icici")
    monkeypatch.setattr(r, "discover_and_fetch", lambda cache_dir: fake_amc_dir)

    fake_hdfc_scheme = Scheme(
        scheme_name="HDFC Flexi Cap Fund", isin="INF179K01YV8", amc="HDFC",
        scheme_aum_inr=1e10, as_of_date=date(2026, 4, 30),
        holdings=[FundHolding(name="HDFC Bank", isin="INE040A01034",
                              weight_pct=9.0, value_inr=9e8, kind="equity")],
        cash_pct=2.0,
    )
    fake_icici_scheme = Scheme(
        scheme_name="ICICI Pru Gilt Fund", isin="INF109K01ZF6", amc="ICICI Pru",
        scheme_aum_inr=2e9, as_of_date=date(2026, 4, 30),
        holdings=[FundHolding(name="GOI 7.18% 2033", isin=None,
                              weight_pct=45.0, value_inr=9e8, kind="debt")],
        cash_pct=8.5,
    )
    fake_adapters = {
        "HDFC": MagicMock(return_value=[fake_hdfc_scheme]),
        "ICICI Pru": MagicMock(return_value=[fake_icici_scheme]),
    }
    monkeypatch.setattr(r, "ADAPTERS", fake_adapters)
    monkeypatch.setattr(r, "detect_amc_from_filename", lambda fn: "HDFC" if "hdfc" in fn.lower() else "ICICI Pru")

    bundle_path = tmp_path / "amfi_holdings.json"
    coverage_path = tmp_path / "amfi_coverage.md"
    summary = r.run(bundle_path=bundle_path, coverage_path=coverage_path)

    data = json.loads(bundle_path.read_text())
    assert data["version"] == 1
    assert len(data["schemes"]) == 2
    assert any(s["amc"] == "HDFC" for s in data["schemes"])
    coverage_text = coverage_path.read_text()
    assert "amfi_coverage" in coverage_text.lower() or "## " in coverage_text
    assert summary["scheme_count"] == 2
    assert summary["amc_count"] == 2
