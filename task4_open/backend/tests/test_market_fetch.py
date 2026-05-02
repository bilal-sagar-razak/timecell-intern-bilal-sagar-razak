"""Unit tests for market/fetch.py — yfinance and feedparser are mocked."""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _fake_history_df():
    idx = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"])
    return pd.DataFrame({"Close": [22000.0, 22100.0, 22200.0]}, index=idx)


def test_fetch_nifty_trend_shape(monkeypatch):
    from market import fetch as fetch_mod

    fake_ticker = MagicMock()
    fake_ticker.history.return_value = _fake_history_df()
    monkeypatch.setattr(fetch_mod.yf, "Ticker", lambda symbol: fake_ticker)

    trend = fetch_mod.fetch_nifty_trend(period_days=3)

    assert trend.period_days == 3
    assert len(trend.points) == 3
    assert trend.points[0].close == 22000.0
    assert trend.points[-1].close == 22200.0
    assert trend.current == 22200.0
    assert abs(trend.pct_change_period - ((22200.0 - 22000.0) / 22000.0 * 100)) < 1e-9


def test_fetch_nifty_trend_empty_raises(monkeypatch):
    from market import fetch as fetch_mod

    empty = pd.DataFrame({"Close": []})
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = empty
    monkeypatch.setattr(fetch_mod.yf, "Ticker", lambda symbol: fake_ticker)

    with pytest.raises(RuntimeError, match="empty"):
        fetch_mod.fetch_nifty_trend(period_days=3)


def _fake_feed(entries: list[dict]):
    feed = MagicMock()
    feed.entries = entries
    feed.bozo = False
    return feed


def test_fetch_rss_headlines_aggregates_and_dedups(monkeypatch):
    from market import fetch as fetch_mod

    e1 = {"title": "Reliance hits new high", "link": "https://a.example/1",
          "published_parsed": (2026, 1, 3, 0, 0, 0, 0, 0, 0), "summary": "snippet 1"}
    e1_dup = {"title": "Reliance hits new high — analysts agree", "link": "https://b.example/1",
              "published_parsed": (2026, 1, 3, 1, 0, 0, 0, 0, 0), "summary": "snippet 2"}
    e2 = {"title": "TCS Q3 results beat estimates", "link": "https://c.example/2",
          "published_parsed": (2026, 1, 2, 0, 0, 0, 0, 0, 0), "summary": "snippet 3"}

    feeds = {
        "https://www.moneycontrol.com/rss/marketsnews.xml": _fake_feed([e1, e2]),
        "https://www.livemint.com/rss/markets": _fake_feed([e1_dup]),
        "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.xml": _fake_feed([]),
    }
    monkeypatch.setattr(fetch_mod.feedparser, "parse", lambda url: feeds[url])

    headlines = fetch_mod.fetch_rss_headlines()

    titles = [h.title for h in headlines]
    assert "Reliance hits new high" in titles
    assert sum(1 for t in titles if t.lower().startswith("reliance")) == 1
    assert headlines[0].published_at >= headlines[-1].published_at


def test_fetch_rss_headlines_one_feed_failure_does_not_break_others(monkeypatch, caplog):
    from market import fetch as fetch_mod

    good = _fake_feed([{
        "title": "Nifty closes flat",
        "link": "https://a.example/x",
        "published_parsed": (2026, 1, 3, 0, 0, 0, 0, 0, 0),
        "summary": "ok",
    }])

    def parse(url: str):
        if "livemint" in url:
            raise OSError("network down")
        return good

    monkeypatch.setattr(fetch_mod.feedparser, "parse", parse)
    caplog.set_level(logging.WARNING)
    headlines = fetch_mod.fetch_rss_headlines()
    assert len(headlines) >= 1
    assert any("livemint" in r.message for r in caplog.records)


def _holdings_with(asset_names: list[str]):
    from parser.schema import Asset, NormalizedHoldings, PortfolioSummary
    assets = [
        Asset(
            name=n, asset_type="mutual_fund", units=1.0,
            invested_value_inr=1000.0, current_value_inr=1100.0,
            pnl_inr=100.0, pnl_pct=10.0,
        )
        for n in asset_names
    ]
    summary = PortfolioSummary(
        total_invested_inr=sum(a.invested_value_inr for a in assets),
        total_current_inr=sum(a.current_value_inr for a in assets),
        total_pnl_inr=sum(a.pnl_inr for a in assets),
        total_pnl_pct=10.0,
        asset_count=len(assets),
    )
    return NormalizedHoldings(holder_name="Test", source_format="test",
                              summary=summary, assets=assets)


def _h(title: str):
    from market.schema import Headline
    return Headline(
        title=title, publisher="x", url="https://x/" + title[:5],
        published_at=datetime.now(timezone.utc),
    )


def test_filter_news_matches_holding_token():
    from market.fetch import filter_news_to_holdings
    holdings = _holdings_with(["Reliance Industries", "TCS"])
    news = [_h("Reliance hits new high"), _h("TCS results out"), _h("Random crypto news")]
    matching, fallback = filter_news_to_holdings(news, holdings)
    titles = [h.title for h in matching]
    assert "Reliance hits new high" in titles
    assert "Random crypto news" not in titles
    assert fallback is False


def test_filter_news_falls_back_when_no_match():
    from market.fetch import filter_news_to_holdings
    holdings = _holdings_with(["Quantum FlexCap Mutual"])
    news = [_h("Reliance hits new high"), _h("TCS results out")]
    matching, fallback = filter_news_to_holdings(news, holdings)
    assert fallback is True
    assert len(matching) == 2


def test_filter_news_short_token_ignored():
    """A token shorter than 4 chars (e.g., 'UTI' is 3) must NOT cause spurious matches alone."""
    from market.fetch import filter_news_to_holdings
    holdings = _holdings_with(["UTI"])
    news = [_h("Bank of UTI announces dividend")]
    matching, fallback = filter_news_to_holdings(news, holdings)
    assert fallback is True
