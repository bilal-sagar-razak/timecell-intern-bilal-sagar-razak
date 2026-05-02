"""Tests for main.py FastAPI app — happy path + all error branches, all LLM calls mocked."""
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app
from parser.normalize import BudgetExhausted, NormalizationError
from parser.schema import Asset, NormalizedHoldings, PortfolioSummary

client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolate_parse_cache(tmp_path_factory, monkeypatch):
    """Redirect parse-cache to a per-test tempdir so tests never touch the user's real cache."""
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path_factory.mktemp("parse-cache"))

SAMPLE_DIR = Path(__file__).parent.parent / "samples"
SAMPLE_XLSX = SAMPLE_DIR / "sample_groww.xlsx"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _fake_normalized() -> NormalizedHoldings:
    """A small but realistic 2-asset portfolio used as the mocked normalize() return."""
    assets = [
        Asset(
            name="Parag Parikh Flexi Cap",
            asset_type="mutual_fund",
            category="Equity",
            sub_category="Flexi Cap",
            units=1234.567,
            invested_value_inr=120000.00,
            current_value_inr=145000.50,
            xirr_pct=14.32,
            pnl_inr=25000.50,
            pnl_pct=20.83,
        ),
        Asset(
            name="ICICI Pru Gilt Fund",
            asset_type="mutual_fund",
            category="Debt",
            sub_category="Gilt",
            units=2000.0,
            invested_value_inr=67129.48,
            current_value_inr=70166.19,
            xirr_pct=4.10,
            pnl_inr=3036.71,
            pnl_pct=4.52,
        ),
    ]
    total_invested = sum(a.invested_value_inr for a in assets)
    total_current = sum(a.current_value_inr for a in assets)
    return NormalizedHoldings(
        holder_name="Test User A",
        source_format="groww_xlsx",
        summary=PortfolioSummary(
            total_invested_inr=round(total_invested, 2),
            total_current_inr=round(total_current, 2),
            total_pnl_inr=round(total_current - total_invested, 2),
            total_pnl_pct=round((total_current - total_invested) / total_invested * 100, 2),
            overall_xirr_pct=9.21,
            asset_count=len(assets),
        ),
        assets=assets,
    )


def test_health_returns_ok() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model"] == "claude-haiku-4-5"
    assert "anthropic_key_set" in body


def test_parse_and_compute_happy_path() -> None:
    with patch("main.normalize", return_value=_fake_normalized()):
        with SAMPLE_XLSX.open("rb") as fh:
            resp = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", fh, XLSX_MIME)},
            )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["normalized"]["holder_name"] == "Test User A"
    assert body["kpis"]["asset_count"] == 2
    assert body["kpis"]["equity_pct"] > 0
    assert len(body["allocation"]) >= 1
    assert len(body["xirr_by_fund"]) == 2
    assert len(body["category_performance"]) == 2


def test_parse_and_compute_rejects_unsupported_extension() -> None:
    fake = io.BytesIO(b"not really a docx")
    resp = client.post(
        "/api/parse-and-compute",
        files={"file": ("foo.docx", fake, "application/octet-stream")},
    )
    assert resp.status_code == 415
    body = resp.json()
    assert "unsupported" in body["detail"]["error"]


def test_parse_and_compute_rejects_oversized_file() -> None:
    big = io.BytesIO(b"\0" * (11 * 1024 * 1024))
    resp = client.post(
        "/api/parse-and-compute",
        files={"file": ("huge.xlsx", big, XLSX_MIME)},
    )
    assert resp.status_code == 413
    body = resp.json()
    assert body["detail"]["error"] == "file too large"


def test_parse_and_compute_handles_normalization_error() -> None:
    with patch(
        "main.normalize",
        side_effect=NormalizationError("bad", attempts=["x", "y"], errors=["e1", "e2"]),
    ):
        with SAMPLE_XLSX.open("rb") as fh:
            resp = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", fh, XLSX_MIME)},
            )
    assert resp.status_code == 502
    body = resp.json()
    assert "could not normalize" in body["detail"]["error"]


def test_parse_and_compute_handles_budget_exhausted() -> None:
    with patch("main.normalize", side_effect=BudgetExhausted("limit")):
        with SAMPLE_XLSX.open("rb") as fh:
            resp = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", fh, XLSX_MIME)},
            )
    assert resp.status_code == 429
    body = resp.json()
    assert "budget" in body["detail"]["error"]


def test_parse_and_compute_cache_hit_skips_normalize(tmp_path, monkeypatch) -> None:
    """Two requests with the same file body → normalize called only once."""
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    fake = _fake_normalized()
    with patch("main.normalize", return_value=fake) as mock_norm:
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r1 = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r2 = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["cached"] is False, "first call should be a miss"
    assert r2.json()["cached"] is True, "second call should be a hit"
    assert mock_norm.call_count == 1, \
        f"normalize should run once across two same-file requests, got {mock_norm.call_count}"


def test_parse_and_compute_force_bypasses_cache(tmp_path, monkeypatch) -> None:
    """?force=true skips lookup and re-runs normalize."""
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    fake = _fake_normalized()
    with patch("main.normalize", return_value=fake) as mock_norm:
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r2 = client.post(
                "/api/parse-and-compute?force=true",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r2.status_code == 200
    assert r2.json()["cached"] is False, "force=true must produce a fresh response"
    assert mock_norm.call_count == 2, \
        f"normalize must run on both calls when second uses force, got {mock_norm.call_count}"


def test_parse_and_compute_does_not_cache_on_error(tmp_path, monkeypatch) -> None:
    """NormalizationError → 502 → no file written under PARSE_CACHE_DIR."""
    from parser.normalize import NormalizationError
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    err = NormalizationError("boom", attempts=["x", "y"], errors=["e1", "e2"])
    with patch("main.normalize", side_effect=err):
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r.status_code == 502
    cache_files = list(tmp_path.iterdir())
    assert cache_files == [], f"no cache should be written on error, got {cache_files}"
