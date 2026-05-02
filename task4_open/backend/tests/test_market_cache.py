"""TTL + refresh tests for market/cache.py — fetch is monkeypatched."""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _fake_snapshot_inputs():
    from market.schema import Headline, NiftyPoint, NiftyTrend
    trend = NiftyTrend(
        points=[NiftyPoint(date=date(2026, 1, 1), close=22000.0)],
        pct_change_period=0.0, current=22000.0, period_days=1,
    )
    headlines = [
        Headline(title="Reliance hits new high", publisher="x",
                 url="https://x/x", published_at=datetime.now(timezone.utc)),
    ]
    return trend, headlines


def _holdings_with(names):
    from parser.schema import Asset, NormalizedHoldings, PortfolioSummary
    assets = [
        Asset(name=n, asset_type="mutual_fund", units=1.0,
              invested_value_inr=1000.0, current_value_inr=1100.0,
              pnl_inr=100.0, pnl_pct=10.0)
        for n in names
    ]
    return NormalizedHoldings(
        holder_name="t", source_format="test",
        summary=PortfolioSummary(
            total_invested_inr=1000.0, total_current_inr=1100.0,
            total_pnl_inr=100.0, total_pnl_pct=10.0, asset_count=len(assets),
        ),
        assets=assets,
    )


@pytest.fixture(autouse=True)
def _reset_cache():
    from market import cache as cache_mod
    cache_mod._reset_for_tests()
    yield
    cache_mod._reset_for_tests()


def test_cold_call_fetches(monkeypatch):
    from market import cache as cache_mod
    trend, headlines = _fake_snapshot_inputs()
    calls = {"trend": 0, "rss": 0}

    def fake_trend(period_days=90):
        calls["trend"] += 1
        return trend

    def fake_rss(max_total=30):
        calls["rss"] += 1
        return headlines

    monkeypatch.setattr(cache_mod, "fetch_nifty_trend", fake_trend)
    monkeypatch.setattr(cache_mod, "fetch_rss_headlines", fake_rss)

    snap = cache_mod.get_market_snapshot(_holdings_with(["Reliance Industries"]))
    assert snap.nifty_trend.current == 22000.0
    assert calls == {"trend": 1, "rss": 1}


def test_warm_call_serves_cache(monkeypatch):
    from market import cache as cache_mod
    trend, headlines = _fake_snapshot_inputs()
    calls = {"n": 0}

    def fake_trend(period_days=90):
        calls["n"] += 1
        return trend

    monkeypatch.setattr(cache_mod, "fetch_nifty_trend", fake_trend)
    monkeypatch.setattr(cache_mod, "fetch_rss_headlines", lambda max_total=30: headlines)

    h = _holdings_with(["Reliance Industries"])
    cache_mod.get_market_snapshot(h)
    cache_mod.get_market_snapshot(h)
    assert calls["n"] == 1


def test_refresh_bypasses_cache(monkeypatch):
    from market import cache as cache_mod
    trend, headlines = _fake_snapshot_inputs()
    calls = {"n": 0}

    def fake_trend(period_days=90):
        calls["n"] += 1
        return trend

    monkeypatch.setattr(cache_mod, "fetch_nifty_trend", fake_trend)
    monkeypatch.setattr(cache_mod, "fetch_rss_headlines", lambda max_total=30: headlines)

    h = _holdings_with(["Reliance Industries"])
    cache_mod.get_market_snapshot(h)
    cache_mod.get_market_snapshot(h, refresh=True)
    assert calls["n"] == 2


def test_ttl_expired_refetches(monkeypatch):
    from market import cache as cache_mod
    trend, headlines = _fake_snapshot_inputs()
    calls = {"n": 0}

    def fake_trend(period_days=90):
        calls["n"] += 1
        return trend

    monkeypatch.setattr(cache_mod, "fetch_nifty_trend", fake_trend)
    monkeypatch.setattr(cache_mod, "fetch_rss_headlines", lambda max_total=30: headlines)

    h = _holdings_with(["Reliance Industries"])
    cache_mod.get_market_snapshot(h)

    with cache_mod._lock:
        old_at, snap = cache_mod._cached
        cache_mod._cached = (old_at - timedelta(minutes=20), snap)

    cache_mod.get_market_snapshot(h)
    assert calls["n"] == 2
