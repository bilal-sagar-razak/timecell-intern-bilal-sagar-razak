"""Pure functions that source market data: Nifty 50 trend + RSS headlines + filtering."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import feedparser
import yfinance as yf

from market.schema import Headline, NiftyPoint, NiftyTrend
from parser.schema import NormalizedHoldings

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("Moneycontrol", "https://www.moneycontrol.com/rss/marketsnews.xml"),
    ("Livemint",     "https://www.livemint.com/rss/markets"),
    ("EconomicTimes","https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.xml"),
]

_TOKEN_RE = re.compile(r"[a-z0-9]{4,}")


def fetch_nifty_trend(period_days: int = 90) -> NiftyTrend:
    """Pull the last `period_days` daily closes for ^NSEI from Yahoo Finance."""
    ticker = yf.Ticker("^NSEI")
    df = ticker.history(period=f"{period_days}d")
    if df.empty:
        raise RuntimeError("yfinance returned empty Nifty history")
    df = df.sort_index()
    points = [
        NiftyPoint(date=idx.date(), close=float(row["Close"]))
        for idx, row in df.iterrows()
    ]
    first = points[0].close
    last = points[-1].close
    pct = (last - first) / first * 100 if first else 0.0
    return NiftyTrend(
        points=points,
        pct_change_period=pct,
        current=last,
        period_days=period_days,
    )


def _entry_to_headline(publisher: str, entry: dict) -> Headline | None:
    title = (entry.get("title") or "").strip()
    link = (entry.get("link") or "").strip()
    if not title or not link:
        return None
    pp = entry.get("published_parsed")
    if pp is not None:
        try:
            published_at = datetime(*pp[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            published_at = datetime.now(timezone.utc)
    else:
        published_at = datetime.now(timezone.utc)
    snippet = (entry.get("summary") or "").strip() or None
    return Headline(
        title=title,
        publisher=publisher,
        url=link,
        published_at=published_at,
        snippet=snippet,
    )


def _dedup_key(title: str) -> str:
    """First 4 lowercased word-tokens — catches near-duplicates with publisher-added suffixes."""
    words = re.findall(r"\w+", title.lower())
    return " ".join(words[:4])


def fetch_rss_headlines(max_total: int = 30) -> list[Headline]:
    """Aggregate across feeds, dedup by first 4 words of the title, sort newest first."""
    seen_keys: set[str] = set()
    out: list[Headline] = []
    for publisher, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.warning("RSS fetch failed for %s (%s): %s", publisher, url, e)
            continue
        for entry in getattr(feed, "entries", []) or []:
            h = _entry_to_headline(publisher, entry)
            if h is None:
                continue
            key = _dedup_key(h.title)
            if not key or key in seen_keys:
                continue
            seen_keys.add(key)
            out.append(h)
    out.sort(key=lambda h: h.published_at, reverse=True)
    return out[:max_total]


def _holding_tokens(holdings: NormalizedHoldings) -> set[str]:
    """Lowercased tokens of length >=4 from every asset name."""
    tokens: set[str] = set()
    for asset in holdings.assets:
        for tok in _TOKEN_RE.findall(asset.name.lower()):
            tokens.add(tok)
    return tokens


def filter_news_to_holdings(
    headlines: list[Headline], holdings: NormalizedHoldings,
) -> tuple[list[Headline], bool]:
    """Return (matching, fallback_used). If no headline contains a >=4-char holding token,
    fall back to the top 10 newest unfiltered headlines."""
    tokens = _holding_tokens(holdings)
    if not tokens:
        return headlines[:10], True
    matching: list[Headline] = []
    for h in headlines:
        title_lower = h.title.lower()
        if any(re.search(rf"\b{re.escape(t)}\b", title_lower) for t in tokens):
            matching.append(h)
    if not matching:
        return headlines[:10], True
    return matching, False
