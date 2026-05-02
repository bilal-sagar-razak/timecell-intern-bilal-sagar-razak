"""Process-local 15-minute TTL cache for the unfiltered Nifty + RSS snapshot.

Filtering is cheap and per-portfolio, so we cache the unfiltered (trend, headlines)
pair and refilter on every request rather than caching per-portfolio.
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from market.fetch import fetch_nifty_trend, fetch_rss_headlines, filter_news_to_holdings
from market.schema import Headline, MarketSnapshot, NiftyTrend
from parser.schema import NormalizedHoldings

TTL = timedelta(minutes=15)

_lock = threading.Lock()
_cached: tuple[datetime, "MarketCacheValue"] | None = None


class MarketCacheValue:
    __slots__ = ("nifty_trend", "headlines")

    def __init__(self, nifty_trend: NiftyTrend, headlines: list[Headline]):
        self.nifty_trend = nifty_trend
        self.headlines = headlines


def _reset_for_tests() -> None:
    """Test-only hook: clear the module-level cache."""
    global _cached
    with _lock:
        _cached = None


def get_market_snapshot(
    holdings: NormalizedHoldings, refresh: bool = False,
) -> MarketSnapshot:
    """Return a MarketSnapshot for `holdings`, served from cache if <15 min old."""
    global _cached
    now = datetime.now(timezone.utc)
    with _lock:
        cached = _cached
    use_cached = (
        cached is not None
        and not refresh
        and (now - cached[0]) < TTL
    )
    if use_cached:
        cached_at, value = cached
    else:
        trend = fetch_nifty_trend(period_days=90)
        headlines = fetch_rss_headlines()
        value = MarketCacheValue(trend, headlines)
        cached_at = now
        with _lock:
            _cached = (cached_at, value)

    filtered, fallback = filter_news_to_holdings(value.headlines, holdings)
    return MarketSnapshot(
        nifty_trend=value.nifty_trend,
        news=filtered,
        news_fallback_used=fallback,
        cached_at=cached_at,
    )
