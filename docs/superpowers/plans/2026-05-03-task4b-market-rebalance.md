# Task 4b — Market + Rebalance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Market and Rebalance stub pages on the Task 4a dashboard with a Nifty 50 trend + portfolio-personalized news tab and an Anthropic Sonnet tool-use agent that produces rebalancing suggestions.

**Architecture:** Additive only — two new backend modules (`market/`, `agent/`) and two new endpoints (`/api/market`, `/api/rebalance`). The frontend gains five new components (NiftyChart, NewsList, RebalanceAdvice, AgentTrace, AgentRunningIndicator), and the existing `lib/store.ts` gains two session-only fields (`marketSnapshot`, `rebalanceResult`) that are NOT in `partialize`. Sonnet calls 4 typed tools (Nifty trend, news for a holding, concentration, drawdown simulation) that close over a per-request `_ctx` global so signatures stay zero-arg-friendly for the SDK runner.

**Tech Stack:** FastAPI, Pydantic v2, `yfinance`, `feedparser`, Anthropic Python SDK (`@beta_tool` decorator, `claude-sonnet-4-6`), Next.js 16 + React 19, Recharts, Zustand v5 with `persist` middleware.

**Reference spec:** `docs/superpowers/specs/2026-05-02-task4b-market-rebalance-design.md`

**Branch:** `task4b/market-rebalance` (already created off `task4a/result-caching` HEAD `a4e2d0e`, spec committed at `f03d6a9`).

**Commit grouping:**
1. Tasks 1–7 → backend `market/` module + `/api/market` endpoint + tests
2. Tasks 8–11 → backend `agent/` module + `/api/rebalance` endpoint + tests
3. Task 12 → frontend store + API types/client
4. Tasks 13–15 → Market tab page + components + tests
5. Tasks 16–19 → Rebalance tab page + components + tests
6. Task 20 → final user gate (no push, no PR)

**Critical safety:** Daily LLM budget is shared with the existing parser via `~/.cache/timecell-task4/usage-YYYY-MM-DD.json`. The agent loop pre-checks the cap (raises `BudgetExhausted`) and post-writes actual cost. Per-call cap is `$0.50`; iteration cap is 8 round-trips.

**Test isolation rule:** Every backend test file that touches the daily-spend file or any other state under `~/.cache/timecell-task4/` MUST use the autouse fixture pattern from `tests/test_main.py` (monkeypatching `CACHE_DIR` to a `tmp_path_factory` mktemp dir). Never write to the user's real cache.

---

## File Structure

**Backend (new):**
- `task4_open/backend/market/__init__.py` — package marker.
- `task4_open/backend/market/schema.py` — Pydantic models for `NiftyPoint`, `NiftyTrend`, `Headline`, `MarketSnapshot`.
- `task4_open/backend/market/fetch.py` — three pure functions: `fetch_nifty_trend`, `fetch_rss_headlines`, `filter_news_to_holdings`.
- `task4_open/backend/market/cache.py` — process-local 15-min TTL cache for the unfiltered snapshot.
- `task4_open/backend/agent/__init__.py` — package marker.
- `task4_open/backend/agent/tools.py` — four `@beta_tool`-decorated functions closing over a `_ctx` global.
- `task4_open/backend/agent/loop.py` — `run_rebalance(holdings, snapshot)` orchestrator with budget guards.
- `task4_open/backend/agent/prompts/rebalance.txt` — Sonnet system prompt.
- `task4_open/backend/tests/test_market_fetch.py` — unit tests for fetch functions.
- `task4_open/backend/tests/test_market_cache.py` — TTL + refresh tests.
- `task4_open/backend/tests/test_agent_tools.py` — tool function tests.
- `task4_open/backend/tests/test_agent_loop.py` — loop tests with mocked Sonnet.

**Backend (modified):**
- `task4_open/backend/main.py` — add `MarketRequest`, `RebalanceRequest`, `/api/market`, `/api/rebalance` endpoints.
- `task4_open/backend/tests/test_main.py` — add 4 new tests for the new endpoints.
- `task4_open/backend/requirements.txt` — add `yfinance>=0.2.40`, `feedparser>=6.0.10`.

**Frontend (new):**
- `task4_open/frontend/components/NiftyChart.tsx` — Recharts line chart.
- `task4_open/frontend/components/NewsList.tsx` — vertical list of headlines.
- `task4_open/frontend/components/RebalanceAdvice.tsx` — markdown-lite renderer.
- `task4_open/frontend/components/AgentTrace.tsx` — collapsible `<details>` of tool calls.
- `task4_open/frontend/components/AgentRunningIndicator.tsx` — pulsing-dot progress affordance.
- `task4_open/frontend/__tests__/NiftyChart.test.tsx` — 2 tests.
- `task4_open/frontend/__tests__/NewsList.test.tsx` — 3 tests.
- `task4_open/frontend/__tests__/RebalanceAdvice.test.tsx` — 2 tests.
- `task4_open/frontend/__tests__/AgentTrace.test.tsx` — 2 tests.

**Frontend (modified):**
- `task4_open/frontend/lib/api.ts` — add `NiftyPoint`, `NiftyTrend`, `Headline`, `MarketSnapshot`, `ToolCall`, `RebalanceResult` types and `fetchMarketSnapshot()`, `runRebalance()` functions.
- `task4_open/frontend/lib/store.ts` — add `marketSnapshot`, `rebalanceResult` fields and setters (NOT in `partialize`).
- `task4_open/frontend/__tests__/store.test.ts` — add 2 tests for the new session-only fields.
- `task4_open/frontend/app/dashboard/market/page.tsx` — replace the stub.
- `task4_open/frontend/app/dashboard/rebalance/page.tsx` — replace the stub.

---

### Task 1: Add Python deps and ensure agent/ + market/ packages exist

**Files:**
- Modify: `task4_open/backend/requirements.txt`
- Create: `task4_open/backend/market/__init__.py`
- Create: `task4_open/backend/agent/__init__.py`
- Create: `task4_open/backend/agent/prompts/.gitkeep`

- [ ] **Step 1: Add dependencies**

Append to `task4_open/backend/requirements.txt`:

```
yfinance>=0.2.40
feedparser>=6.0.10
```

- [ ] **Step 2: Create empty package markers**

```bash
mkdir -p task4_open/backend/market task4_open/backend/agent task4_open/backend/agent/prompts
touch task4_open/backend/market/__init__.py
touch task4_open/backend/agent/__init__.py
touch task4_open/backend/agent/prompts/.gitkeep
```

- [ ] **Step 3: Install the new deps locally**

Run: `pip install -r task4_open/backend/requirements.txt`
Expected: `Successfully installed feedparser-6.x.x yfinance-0.2.x` (or "Requirement already satisfied" if cached).

- [ ] **Step 4: Smoke-import**

Run: `python -c "import yfinance, feedparser; print(yfinance.__version__, feedparser.__version__)"`
Expected: prints two version strings, no traceback.

- [ ] **Step 5: Do NOT commit yet**

Held until Task 7 (single commit for all market-backend work).

---

### Task 2: market/schema.py — Pydantic models

**Files:**
- Create: `task4_open/backend/market/schema.py`
- Test: (covered transitively via test_market_fetch.py in Task 3)

- [ ] **Step 1: Write the schema file**

Create `task4_open/backend/market/schema.py`:

```python
"""Pydantic models for market data (Nifty trend + news headlines)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class NiftyPoint(BaseModel):
    """One day's Nifty 50 close price."""
    date: date
    close: float


class NiftyTrend(BaseModel):
    """Sequence of Nifty close prices + period summary."""
    points: list[NiftyPoint]
    pct_change_period: float
    current: float
    period_days: int = Field(..., ge=1)


class Headline(BaseModel):
    """One news headline pulled from an RSS feed."""
    title: str = Field(..., min_length=1)
    publisher: str
    url: str
    published_at: datetime
    snippet: str | None = None


class MarketSnapshot(BaseModel):
    """The full payload of /api/market — Nifty trend + portfolio-filtered news."""
    nifty_trend: NiftyTrend
    news: list[Headline]
    news_fallback_used: bool = False
    cached_at: datetime
```

- [ ] **Step 2: Quick round-trip sanity check**

Run:
```bash
python -c "
from task4_open.backend.market.schema import MarketSnapshot, NiftyTrend, NiftyPoint, Headline
from datetime import date, datetime, timezone
m = MarketSnapshot(
  nifty_trend=NiftyTrend(points=[NiftyPoint(date=date(2026,1,1), close=22000.0)], pct_change_period=0.0, current=22000.0, period_days=1),
  news=[],
  news_fallback_used=False,
  cached_at=datetime.now(timezone.utc),
)
print(m.model_dump_json()[:80])
"
```
Expected: prints a JSON prefix `{"nifty_trend":{"points":[{"date":"2026-01-01","close":22000.0}]...`, no error.

- [ ] **Step 3: Do NOT commit yet** (held until Task 7).

---

### Task 3: market/fetch.py — fetch_nifty_trend

**Files:**
- Create: `task4_open/backend/market/fetch.py` (this task creates the file; Tasks 4 and 5 add to it)
- Create: `task4_open/backend/tests/test_market_fetch.py`

- [ ] **Step 1: Write the failing test**

Create `task4_open/backend/tests/test_market_fetch.py`:

```python
"""Unit tests for market/fetch.py — yfinance and feedparser are mocked."""
from __future__ import annotations

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest task4_open/backend/tests/test_market_fetch.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'market.fetch'` or `ImportError`.

- [ ] **Step 3: Write minimal implementation**

Create `task4_open/backend/market/fetch.py`:

```python
"""Pure functions that source market data: Nifty 50 trend + RSS headlines + filtering."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import yfinance as yf

from market.schema import NiftyPoint, NiftyTrend

logger = logging.getLogger(__name__)


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
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest task4_open/backend/tests/test_market_fetch.py::test_fetch_nifty_trend_shape task4_open/backend/tests/test_market_fetch.py::test_fetch_nifty_trend_empty_raises -v`
Expected: 2 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 7).

---

### Task 4: market/fetch.py — fetch_rss_headlines

**Files:**
- Modify: `task4_open/backend/market/fetch.py`
- Modify: `task4_open/backend/tests/test_market_fetch.py`

- [ ] **Step 1: Add the failing test**

Append to `task4_open/backend/tests/test_market_fetch.py`:

```python
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
    # dedup: the first 50 chars of e1 and e1_dup match — only one should survive
    assert sum(1 for t in titles if t.lower().startswith("reliance")) == 1
    # sorted newest first
    assert headlines[0].published_at >= headlines[-1].published_at


def test_fetch_rss_headlines_one_feed_failure_does_not_break_others(monkeypatch, caplog):
    from market import fetch as fetch_mod
    import logging

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
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest task4_open/backend/tests/test_market_fetch.py::test_fetch_rss_headlines_aggregates_and_dedups -v`
Expected: FAIL (function not defined).

- [ ] **Step 3: Implement fetch_rss_headlines**

Append to `task4_open/backend/market/fetch.py`:

```python
import feedparser

from market.schema import Headline

RSS_FEEDS = [
    ("Moneycontrol", "https://www.moneycontrol.com/rss/marketsnews.xml"),
    ("Livemint",     "https://www.livemint.com/rss/markets"),
    ("EconomicTimes","https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.xml"),
]


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


def fetch_rss_headlines(max_total: int = 30) -> list[Headline]:
    """Aggregate, dedup (by lowercased first 50 chars of title), and sort RSS items newest first."""
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
            key = h.title[:50].lower()
            if key in seen_keys:
                continue
            seen_keys.add(key)
            out.append(h)
    out.sort(key=lambda h: h.published_at, reverse=True)
    return out[:max_total]
```

- [ ] **Step 4: Run all market_fetch tests**

Run: `pytest task4_open/backend/tests/test_market_fetch.py -v`
Expected: 4 passed (Nifty x2 + RSS x2).

- [ ] **Step 5: Do NOT commit yet** (held until Task 7).

---

### Task 5: market/fetch.py — filter_news_to_holdings

**Files:**
- Modify: `task4_open/backend/market/fetch.py`
- Modify: `task4_open/backend/tests/test_market_fetch.py`

- [ ] **Step 1: Add the failing test**

Append to `task4_open/backend/tests/test_market_fetch.py`:

```python
from datetime import date as _date


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


def _h(title: str) -> "Headline":
    from market.schema import Headline
    return Headline(
        title=title, publisher="x", url="https://x/x",
        published_at=datetime.now(timezone.utc),
    )


def test_filter_news_matches_holding_token():
    from market.fetch import filter_news_to_holdings
    holdings = _holdings_with(["Reliance Industries", "TCS"])
    news = [_h("Reliance hits new high"), _h("TCS results out"), _h("Random crypto news")]
    matching, fallback = filter_news_to_holdings(news, holdings)
    titles = [h.title for h in matching]
    assert "Reliance hits new high" in titles
    assert "TCS results out" in titles
    assert "Random crypto news" not in titles
    assert fallback is False


def test_filter_news_falls_back_when_no_match():
    from market.fetch import filter_news_to_holdings
    holdings = _holdings_with(["Quantum FlexCap Mutual"])
    news = [_h("Reliance hits new high"), _h("TCS results out")]
    matching, fallback = filter_news_to_holdings(news, holdings)
    assert fallback is True
    assert len(matching) == 2  # all returned since none matched


def test_filter_news_short_token_ignored():
    """A token shorter than 4 chars (e.g., 'TCS' is 3) must NOT cause spurious matches alone."""
    from market.fetch import filter_news_to_holdings
    holdings = _holdings_with(["UTI"])  # 3-char token only — should not match
    news = [_h("Bank of UTI announces dividend")]
    matching, fallback = filter_news_to_holdings(news, holdings)
    assert fallback is True
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest task4_open/backend/tests/test_market_fetch.py::test_filter_news_matches_holding_token -v`
Expected: FAIL (function not defined).

- [ ] **Step 3: Implement filter_news_to_holdings**

Append to `task4_open/backend/market/fetch.py`:

```python
import re

from parser.schema import NormalizedHoldings


_TOKEN_RE = re.compile(r"[a-z0-9]{4,}")


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
    falls back to the top 10 newest unfiltered headlines."""
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
```

- [ ] **Step 4: Run the full file**

Run: `pytest task4_open/backend/tests/test_market_fetch.py -v`
Expected: 7 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 7).

---

### Task 6: market/cache.py — process-local 15-min TTL

**Files:**
- Create: `task4_open/backend/market/cache.py`
- Create: `task4_open/backend/tests/test_market_cache.py`

- [ ] **Step 1: Write the failing test**

Create `task4_open/backend/tests/test_market_cache.py`:

```python
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

    # Force the cache entry to look ancient
    with cache_mod._lock:
        old_at, snap = cache_mod._cached
        cache_mod._cached = (old_at - timedelta(minutes=20), snap)

    cache_mod.get_market_snapshot(h)
    assert calls["n"] == 2
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest task4_open/backend/tests/test_market_cache.py -v`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implement cache.py**

Create `task4_open/backend/market/cache.py`:

```python
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
    """Return a MarketSnapshot for the given holdings, served from cache if <15 min old."""
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
```

- [ ] **Step 4: Run cache tests**

Run: `pytest task4_open/backend/tests/test_market_cache.py -v`
Expected: 4 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 7).

---

### Task 7: main.py /api/market endpoint + tests + COMMIT 1

**Files:**
- Modify: `task4_open/backend/main.py`
- Modify: `task4_open/backend/tests/test_main.py`

- [ ] **Step 1: Add the failing test**

Append to `task4_open/backend/tests/test_main.py`:

```python
from datetime import date, datetime, timezone


def _fake_market_snapshot():
    from market.schema import Headline, MarketSnapshot, NiftyPoint, NiftyTrend
    return MarketSnapshot(
        nifty_trend=NiftyTrend(
            points=[NiftyPoint(date=date(2026, 1, 1), close=22000.0),
                    NiftyPoint(date=date(2026, 1, 2), close=22100.0)],
            pct_change_period=0.45, current=22100.0, period_days=2,
        ),
        news=[Headline(
            title="Reliance up", publisher="X", url="https://x/x",
            published_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )],
        news_fallback_used=False,
        cached_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )


def test_market_endpoint_happy_path(monkeypatch):
    holdings = _fake_normalized()
    snap = _fake_market_snapshot()
    monkeypatch.setattr("main.get_market_snapshot", lambda h, refresh=False: snap)
    r = client.post("/api/market", json={"holdings": holdings.model_dump(mode="json")})
    assert r.status_code == 200
    body = r.json()
    assert body["nifty_trend"]["current"] == 22100.0
    assert body["news"][0]["title"] == "Reliance up"


def test_market_endpoint_yfinance_failure_returns_502(monkeypatch):
    holdings = _fake_normalized()

    def boom(h, refresh=False):
        raise RuntimeError("yfinance returned empty Nifty history")

    monkeypatch.setattr("main.get_market_snapshot", boom)
    r = client.post("/api/market", json={"holdings": holdings.model_dump(mode="json")})
    assert r.status_code == 502
    assert "market data unavailable" in r.json()["detail"]["error"]
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest task4_open/backend/tests/test_main.py::test_market_endpoint_happy_path task4_open/backend/tests/test_main.py::test_market_endpoint_yfinance_failure_returns_502 -v`
Expected: FAIL (404 Not Found, route doesn't exist).

- [ ] **Step 3: Add the endpoint**

Modify `task4_open/backend/main.py`. Add the import block under the existing parser imports:

```python
from market.cache import get_market_snapshot
from market.schema import MarketSnapshot
```

Add this request model under `ParseAndComputeResponse`:

```python
class MarketRequest(BaseModel):
    """Request body for /api/market — holdings JSON + optional refresh."""
    holdings: NormalizedHoldings
    refresh: bool = False
```

Add the endpoint above the file's end:

```python
@app.post("/api/market", response_model=MarketSnapshot)
def market(req: MarketRequest) -> MarketSnapshot:
    """Returns Nifty 50 trend + headlines filtered to the user's portfolio."""
    try:
        return get_market_snapshot(req.holdings, refresh=req.refresh)
    except Exception as e:
        logger.exception("market fetch failed")
        raise HTTPException(
            status_code=502,
            detail={"error": "market data unavailable", "detail": str(e)},
        )
```

- [ ] **Step 4: Run all backend tests**

Run: `pytest task4_open/backend/tests/ -v`
Expected: all market tests pass + previously passing tests still pass (43 pre-existing + 11 new = 54 total minimum).

- [ ] **Step 5: Commit (commit 1)**

```bash
git add task4_open/backend/requirements.txt \
        task4_open/backend/market/__init__.py \
        task4_open/backend/market/schema.py \
        task4_open/backend/market/fetch.py \
        task4_open/backend/market/cache.py \
        task4_open/backend/agent/__init__.py \
        task4_open/backend/agent/prompts/.gitkeep \
        task4_open/backend/main.py \
        task4_open/backend/tests/test_market_fetch.py \
        task4_open/backend/tests/test_market_cache.py \
        task4_open/backend/tests/test_main.py
git commit -m "task4b: market backend — Nifty trend + portfolio-filtered news with 15-min cache"
```

---

### Task 8: agent/tools.py — four tools closing over _ctx

**Files:**
- Create: `task4_open/backend/agent/tools.py`
- Create: `task4_open/backend/tests/test_agent_tools.py`

- [ ] **Step 1: Write the failing test**

Create `task4_open/backend/tests/test_agent_tools.py`:

```python
"""Pure-function tests for agent/tools.py — Anthropic SDK is NOT called here."""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _holdings():
    from parser.schema import Asset, NormalizedHoldings, PortfolioSummary
    assets = [
        Asset(name="Reliance Industries", asset_type="stock", category="Equity",
              units=10, invested_value_inr=20000.0, current_value_inr=30000.0,
              pnl_inr=10000.0, pnl_pct=50.0),
        Asset(name="ICICI Pru Gilt Fund", asset_type="mutual_fund", category="Debt",
              units=100, invested_value_inr=10000.0, current_value_inr=10500.0,
              pnl_inr=500.0, pnl_pct=5.0),
        Asset(name="HDFC Liquid Fund", asset_type="mutual_fund", category="Debt",
              units=50, invested_value_inr=5000.0, current_value_inr=5100.0,
              pnl_inr=100.0, pnl_pct=2.0),
    ]
    return NormalizedHoldings(
        holder_name="t", source_format="test",
        summary=PortfolioSummary(
            total_invested_inr=35000.0, total_current_inr=45600.0,
            total_pnl_inr=10600.0, total_pnl_pct=30.28, asset_count=3,
        ),
        assets=assets,
    )


def _snapshot():
    from market.schema import Headline, MarketSnapshot, NiftyPoint, NiftyTrend
    points = [NiftyPoint(date=date(2026, 1, i + 1), close=22000.0 + i * 10)
              for i in range(7)]
    return MarketSnapshot(
        nifty_trend=NiftyTrend(points=points, pct_change_period=0.27,
                               current=22060.0, period_days=7),
        news=[
            Headline(title="Reliance hits new high", publisher="X",
                     url="https://x/1", published_at=datetime.now(timezone.utc)),
            Headline(title="Markets close flat", publisher="X",
                     url="https://x/2", published_at=datetime.now(timezone.utc)),
        ],
        news_fallback_used=False,
        cached_at=datetime.now(timezone.utc),
    )


@pytest.fixture(autouse=True)
def _ctx():
    from agent import tools as t
    t._ctx.clear()
    t._ctx["holdings"] = _holdings()
    t._ctx["snapshot"] = _snapshot()
    yield
    t._ctx.clear()


def test_get_nifty_trend_returns_trend_dict():
    from agent.tools import get_nifty_trend
    result = get_nifty_trend.__wrapped__(period_days=7)
    assert result["period_days"] == 7
    assert len(result["points"]) == 7
    assert result["current"] == 22060.0


def test_get_nifty_trend_invalid_period():
    from agent.tools import get_nifty_trend
    result = get_nifty_trend.__wrapped__(period_days=42)
    assert "error" in result


def test_get_news_for_holding_filters_by_substring():
    from agent.tools import get_news_for_holding
    result = get_news_for_holding.__wrapped__(name="Reliance")
    assert result["name"] == "Reliance"
    assert len(result["headlines"]) == 1
    assert "Reliance" in result["headlines"][0]["title"]


def test_compute_concentration_flags_over_threshold_and_categories():
    from agent.tools import compute_concentration
    result = compute_concentration.__wrapped__(threshold_pct=15.0)
    # Reliance is 30000 / 45600 = 65.79%, well over 15%
    assert any(o["name"] == "Reliance Industries" for o in result["over_threshold"])
    assert "Equity" in result["category_pct"]
    assert "Debt" in result["category_pct"]


def test_propose_drawdown_simulation_shifts_categories():
    from agent.tools import propose_drawdown_simulation
    proposal = {
        "sell": [{"name": "Reliance Industries", "pct_to_trim": 20.0}],
        "buy": [{"name": "ICICI Pru Gilt Fund", "pct_to_add": 20.0}],
    }
    result = propose_drawdown_simulation.__wrapped__(rebalance_proposal=proposal)
    assert "category_pct" in result
    assert "new_equity_pct" in result
    assert "fits_risk_band_60_70" in result
    # After trimming Reliance by 20% of total and adding 20% of total to debt,
    # equity allocation should fall — verify it's lower than the original.
    original_equity_pct = 30000.0 / 45600.0 * 100  # ~65.79
    assert result["new_equity_pct"] < original_equity_pct
```

> Note: test calls `get_nifty_trend.__wrapped__(...)` because `@beta_tool` wraps the function in an SDK BetaTool object — `__wrapped__` accesses the underlying callable. If the SDK exposes a different attribute, use that; if no wrapper attribute exists, the fallback is to register the tools in a way that returns the underlying callable (see implementation note below).

- [ ] **Step 2: Run to verify failure**

Run: `pytest task4_open/backend/tests/test_agent_tools.py -v`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implement tools.py**

Create `task4_open/backend/agent/tools.py`:

```python
"""Agent tools: pure functions over a per-request context (holdings + market snapshot).

The SDK's tool runner doesn't allow extra arguments to be threaded through tool calls,
so each tool reads from a module-level `_ctx` dict that `agent.loop.run_rebalance()`
populates fresh on every request and clears in a `finally` block. Tools assume `_ctx`
contains valid `holdings` and `snapshot` keys — they're not exposed to user input.
"""
from __future__ import annotations

import logging
from datetime import date as _date

from anthropic.lib.tools import beta_tool

from market.schema import NiftyPoint, NiftyTrend
from parser.schema import NormalizedHoldings

logger = logging.getLogger(__name__)

_ctx: dict = {}


def _pct_change(points: list[NiftyPoint]) -> float:
    if len(points) < 2 or points[0].close == 0:
        return 0.0
    return (points[-1].close - points[0].close) / points[0].close * 100


@beta_tool
def get_nifty_trend(period_days: int = 90) -> dict:
    """Return the Nifty 50 close-price series and overall % change for the requested window.

    Args:
        period_days: Length of the window in calendar days. Must be one of 7, 30, 90, 365.
    """
    valid = {7, 30, 90, 365}
    if period_days not in valid:
        return {"error": f"period_days must be one of {sorted(valid)}"}
    snap = _ctx["snapshot"]
    if period_days >= snap.nifty_trend.period_days:
        sliced = snap.nifty_trend.points
    else:
        sliced = snap.nifty_trend.points[-period_days:]
    return {
        "points": [{"date": p.date.isoformat(), "close": p.close} for p in sliced],
        "pct_change_period": round(_pct_change(sliced), 4),
        "current": snap.nifty_trend.current,
        "period_days": period_days,
    }


@beta_tool
def get_news_for_holding(name: str) -> dict:
    """Return up to 5 recent headlines whose title contains `name` (case-insensitive)."""
    snap = _ctx["snapshot"]
    needle = name.lower()
    matches = [h for h in snap.news if needle in h.title.lower()]
    return {
        "name": name,
        "headlines": [
            {
                "title": h.title,
                "publisher": h.publisher,
                "url": h.url,
                "published_at": h.published_at.isoformat(),
                "snippet": h.snippet,
            }
            for h in matches[:5]
        ],
    }


@beta_tool
def compute_concentration(threshold_pct: float = 15.0) -> dict:
    """List assets whose value exceeds `threshold_pct` of total portfolio value.

    Also returns per-major-category percentages (Equity / Debt / Hybrid / Commodities).
    """
    holdings: NormalizedHoldings = _ctx["holdings"]
    total = sum(a.current_value_inr for a in holdings.assets) or 1e-9
    over = [
        {
            "name": a.name,
            "pct": round(a.current_value_inr / total * 100, 2),
            "category": a.category,
            "sub_category": a.sub_category,
        }
        for a in holdings.assets
        if a.current_value_inr / total * 100 > threshold_pct
    ]
    by_cat: dict[str, float] = {}
    for a in holdings.assets:
        cat = a.category or "Other"
        by_cat[cat] = by_cat.get(cat, 0.0) + a.current_value_inr
    return {
        "threshold_pct": threshold_pct,
        "over_threshold": over,
        "category_pct": {k: round(v / total * 100, 2) for k, v in by_cat.items()},
    }


@beta_tool
def propose_drawdown_simulation(rebalance_proposal: dict) -> dict:
    """Simulate the post-rebalance category mix.

    Args:
        rebalance_proposal: {"sell": [{"name": str, "pct_to_trim": float}],
                             "buy":  [{"name": str, "pct_to_add":  float}]}
            All percentages are of CURRENT TOTAL portfolio value (not per holding).
    """
    holdings: NormalizedHoldings = _ctx["holdings"]
    total = sum(a.current_value_inr for a in holdings.assets) or 1e-9
    new_values = {a.name: a.current_value_inr for a in holdings.assets}
    for sell in rebalance_proposal.get("sell", []):
        name = sell.get("name")
        pct = float(sell.get("pct_to_trim", 0))
        new_values[name] = max(0.0, new_values.get(name, 0.0) - pct / 100.0 * total)
    for buy in rebalance_proposal.get("buy", []):
        name = buy.get("name")
        pct = float(buy.get("pct_to_add", 0))
        new_values[name] = new_values.get(name, 0.0) + pct / 100.0 * total
    new_by_cat: dict[str, float] = {}
    for a in holdings.assets:
        cat = a.category or "Other"
        new_by_cat[cat] = new_by_cat.get(cat, 0.0) + new_values.get(a.name, 0.0)
    new_total = sum(new_values.values()) or 1e-9
    new_eq_pct = (new_by_cat.get("Equity", 0.0) / new_total) * 100
    return {
        "category_pct": {k: round(v / new_total * 100, 2) for k, v in new_by_cat.items()},
        "new_equity_pct": round(new_eq_pct, 2),
        "fits_risk_band_60_70": 60.0 <= new_eq_pct <= 70.0,
    }


TOOLS = [get_nifty_trend, get_news_for_holding, compute_concentration, propose_drawdown_simulation]
```

> **Implementation note:** `@beta_tool` wraps each function. If `tool.__wrapped__` is not the right access path on the installed SDK version, replace `__wrapped__` in the test with the SDK's exposed attribute (e.g., `tool.func` or `tool.callable`). If the SDK exposes neither, refactor the tools so the underlying logic lives in plain functions (`_get_nifty_trend_impl`, etc.) that the decorated functions delegate to, then test the impl functions directly. Run `python -c "from anthropic.lib.tools import beta_tool; help(beta_tool)"` to confirm.

- [ ] **Step 4: Verify SDK wrapper attribute**

Run: `python -c "from anthropic.lib.tools import beta_tool; @beta_tool
def x(): pass
print(dir(x))"`
Expected: prints attribute list. If `__wrapped__` is absent but a similar attribute exists, update both `tools.py` (no change needed) and the test file's accessor accordingly.

- [ ] **Step 5: Run agent_tools tests**

Run: `pytest task4_open/backend/tests/test_agent_tools.py -v`
Expected: 5 passed. If the SDK wrapper attribute is different, update the test access pattern and rerun.

- [ ] **Step 6: Do NOT commit yet** (held until Task 11).

---

### Task 9: agent/prompts/rebalance.txt

**Files:**
- Create: `task4_open/backend/agent/prompts/rebalance.txt`
- Delete: `task4_open/backend/agent/prompts/.gitkeep` (no longer needed)

- [ ] **Step 1: Write the prompt**

Create `task4_open/backend/agent/prompts/rebalance.txt`:

```text
You are a portfolio analyst, not a financial advisor. You produce 2–3 concrete, evidence-backed rebalancing suggestions for a single Indian retail portfolio. You never give legally binding advice and never claim certainty about future returns.

You have these tools:

- compute_concentration(threshold_pct: float = 15.0) → returns assets exceeding threshold_pct of total portfolio value AND per-major-category percentages (Equity/Debt/Hybrid/Commodities). Call this with threshold_pct=15 at minimum to anchor your reasoning.
- get_nifty_trend(period_days: int) → Nifty 50 closes for the period. Valid: 7, 30, 90, 365. Use 30 or 90 for context.
- get_news_for_holding(name: str) → up to 5 recent headlines whose title contains the holding's name. Use this for any holding you are considering trimming or doubling down on.
- propose_drawdown_simulation(rebalance_proposal: dict) → simulates the post-rebalance category mix. Pass {"sell": [{"name", "pct_to_trim"}], "buy": [{"name", "pct_to_add"}]} where percentages are of CURRENT TOTAL portfolio value.

Workflow:
1. Always call compute_concentration(15) first.
2. Call get_nifty_trend(90) and at least one get_news_for_holding(...) before proposing.
3. If you propose a rebalance, validate it via propose_drawdown_simulation BEFORE finalising.
4. Output your final answer as exactly 2 or 3 numbered markdown items. Each item is ≤80 words and ends with an "Evidence: ..." line citing which tool result drove it.

Never invent prices, returns, or news headlines. Only cite data the tools returned. If a tool returns no relevant data, say so explicitly.

Example final output:

1. **Trim Reliance Industries by ~10% of portfolio value.** It accounts for 32% of your portfolio (compute_concentration), well above the 15% concentration threshold. Allocate the proceeds to ICICI Pru Gilt Fund to lift Debt to ~30% and pull Equity into the 60–70% target band. Evidence: compute_concentration shows Reliance at 32%; propose_drawdown_simulation confirms the new Equity = 64.5% (fits_risk_band_60_70 = true).

2. **Hold ICICI Pru Gilt Fund.** It anchors your Debt sleeve and the 90-day Nifty has moved +4% with no negative news on this fund. Evidence: get_nifty_trend(90) returned +4.1%; get_news_for_holding("ICICI Pru Gilt") returned 0 negative items.

3. **Pause new equity SIPs for 30 days.** With your equity already concentrated above target, deploy fresh capital into Debt instead. Evidence: compute_concentration's category_pct shows Equity at 71%, above the 60–70% band.
```

- [ ] **Step 2: Remove the placeholder**

```bash
rm -f task4_open/backend/agent/prompts/.gitkeep
```

- [ ] **Step 3: Sanity-check it loads**

Run:
```bash
python -c "
from pathlib import Path
p = Path('task4_open/backend/agent/prompts/rebalance.txt')
print('len=', len(p.read_text()))
"
```
Expected: prints `len= ` followed by an integer (≥1500, ≤4000).

- [ ] **Step 4: Do NOT commit yet** (held until Task 11).

---

### Task 10: agent/loop.py — run_rebalance with budget guards

**Files:**
- Create: `task4_open/backend/agent/loop.py`
- Create: `task4_open/backend/tests/test_agent_loop.py`

- [ ] **Step 1: Write the failing tests**

Create `task4_open/backend/tests/test_agent_loop.py`:

```python
"""Tests for agent/loop.py — Anthropic client is fully mocked."""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _holdings():
    from parser.schema import Asset, NormalizedHoldings, PortfolioSummary
    a = Asset(name="Reliance Industries", asset_type="stock", category="Equity",
              units=10, invested_value_inr=20000.0, current_value_inr=30000.0,
              pnl_inr=10000.0, pnl_pct=50.0)
    return NormalizedHoldings(
        holder_name="t", source_format="test",
        summary=PortfolioSummary(
            total_invested_inr=20000.0, total_current_inr=30000.0,
            total_pnl_inr=10000.0, total_pnl_pct=50.0, asset_count=1,
        ),
        assets=[a],
    )


def _snapshot():
    from market.schema import MarketSnapshot, NiftyPoint, NiftyTrend
    points = [NiftyPoint(date=date(2026, 1, i + 1), close=22000.0) for i in range(3)]
    return MarketSnapshot(
        nifty_trend=NiftyTrend(points=points, pct_change_period=0.0,
                               current=22000.0, period_days=3),
        news=[],
        news_fallback_used=False,
        cached_at=datetime.now(timezone.utc),
    )


@pytest.fixture(autouse=True)
def _isolate_cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("parser.normalize.CACHE_DIR", tmp_path / "cache")


def _mock_anthropic_class_with_runner(advice_text: str, tool_calls: list[dict]):
    """Return (FakeAnthropic, runner_mock) where the runner returns a TurnsResult-like object.

    tool_calls: list of {"name": str, "input": dict, "output": dict}
    """
    from agent.loop import RebalanceResult  # noqa: F401  (registers schema)

    runner = MagicMock()
    final = MagicMock()
    final.content = [MagicMock(type="text", text=advice_text)]
    runner.run.return_value = MagicMock(
        final_message=final,
        turns=[
            MagicMock(usage=MagicMock(input_tokens=200, output_tokens=100))
            for _ in range(max(1, len(tool_calls)))
        ],
        tool_calls=[
            MagicMock(
                tool_name=tc["name"], input=tc["input"], output=tc["output"],
                ts=datetime.now(timezone.utc), duration_ms=5,
            )
            for tc in tool_calls
        ],
    )

    fake_messages = MagicMock()
    fake_messages.beta = MagicMock()
    fake_messages.beta.tool_runner = MagicMock(return_value=runner)
    fake_messages.count_tokens = MagicMock(return_value=MagicMock(input_tokens=300))

    fake_client = MagicMock()
    fake_client.messages = fake_messages

    return fake_client, runner


def test_happy_path_returns_advice_and_trace(monkeypatch):
    from agent import loop

    fake_client, runner = _mock_anthropic_class_with_runner(
        advice_text="1. Trim Reliance — Evidence: compute_concentration shows 100%.",
        tool_calls=[
            {"name": "compute_concentration", "input": {"threshold_pct": 15},
             "output": {"over_threshold": [{"name": "Reliance"}]}},
            {"name": "get_nifty_trend", "input": {"period_days": 90},
             "output": {"current": 22000}},
        ],
    )
    monkeypatch.setattr(loop, "Anthropic", lambda: fake_client)

    result = loop.run_rebalance(_holdings(), _snapshot())
    assert "Trim Reliance" in result.advice_markdown
    assert len(result.trace) == 2
    assert result.iterations == 2
    assert result.truncated is False
    assert result.cost_usd > 0


def test_iteration_cap_marks_truncated(monkeypatch):
    from agent import loop

    fake_client, runner = _mock_anthropic_class_with_runner(
        advice_text="",  # empty: indicates no final answer was reached
        tool_calls=[{"name": "get_nifty_trend", "input": {"period_days": 90},
                     "output": {"current": 22000}}] * (loop.MAX_TOOL_ITERATIONS + 1),
    )
    monkeypatch.setattr(loop, "Anthropic", lambda: fake_client)

    result = loop.run_rebalance(_holdings(), _snapshot())
    assert result.truncated is True
    assert result.iterations <= loop.MAX_TOOL_ITERATIONS


def test_per_call_cap_raises_budget_exhausted(monkeypatch):
    from agent import loop
    from parser.normalize import BudgetExhausted

    # Force the count_tokens result to make worst-case cost exceed the per-call cap.
    fake_messages = MagicMock()
    fake_messages.count_tokens = MagicMock(return_value=MagicMock(input_tokens=10_000_000))
    fake_messages.beta = MagicMock()
    fake_messages.beta.tool_runner = MagicMock()
    fake_client = MagicMock()
    fake_client.messages = fake_messages
    monkeypatch.setattr(loop, "Anthropic", lambda: fake_client)

    with pytest.raises(BudgetExhausted):
        loop.run_rebalance(_holdings(), _snapshot())


def test_daily_cap_pre_check_raises(monkeypatch, tmp_path):
    from agent import loop
    from parser.normalize import BudgetExhausted, _today_cache_path
    monkeypatch.setattr("parser.normalize.CACHE_DIR", tmp_path / "cache")
    p = _today_cache_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('{"usd": 10.00}')  # already over $2 default cap
    monkeypatch.setenv("MAX_DAILY_LLM_USD", "2.00")

    fake_messages = MagicMock()
    fake_messages.count_tokens = MagicMock(return_value=MagicMock(input_tokens=300))
    fake_messages.beta = MagicMock()
    fake_messages.beta.tool_runner = MagicMock()
    fake_client = MagicMock()
    fake_client.messages = fake_messages
    monkeypatch.setattr(loop, "Anthropic", lambda: fake_client)

    with pytest.raises(BudgetExhausted):
        loop.run_rebalance(_holdings(), _snapshot())
```

> **Implementation note:** the exact attribute names on the SDK runner result (`runner.run().final_message`, `.turns`, `.tool_calls`) depend on the installed Anthropic SDK version. Before writing `loop.py`, run `python -c "import anthropic; print(anthropic.__version__)"` and check `dir(anthropic.lib.tools)` and `dir(anthropic.beta)` to confirm the actual surface. If the runner exposes a different shape, rewrite the loop in terms of the manual `messages.create` + tool_use loop pattern used elsewhere in `parser/normalize.py`. The plan's intent is: capture every tool round-trip into a `trace` list, sum `usage.input_tokens` and `usage.output_tokens` across all turns, stop after `MAX_TOOL_ITERATIONS`. The mocked tests above should be adapted to whatever loop shape you implement — the *behaviors* (advice + trace + truncated + cost) must hold.

- [ ] **Step 2: Run to verify failure**

Run: `pytest task4_open/backend/tests/test_agent_loop.py -v`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implement the loop**

Create `task4_open/backend/agent/loop.py`:

```python
"""Anthropic Sonnet tool-use loop that produces 2–3 rebalancing suggestions.

Iteration cap: 8 round-trips. Per-call cap: $0.50. Daily cap: shared with parser
via ~/.cache/timecell-task4/usage-YYYY-MM-DD.json (read + atomically updated).

If the SDK's beta tool runner doesn't expose `final_message`, `turns`, and
`tool_calls` cleanly, fall back to a manual loop using `client.messages.create`
+ `tool_use` content blocks (the same pattern used in `parser/normalize.py`).
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from pydantic import BaseModel

from agent.tools import TOOLS, _ctx
from market.schema import MarketSnapshot
from parser.normalize import (
    BudgetExhausted,
    _max_daily_usd,
    _read_today_usd,
    _write_today_usd,
)
from parser.schema import NormalizedHoldings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_INPUT_TOKENS = 20_000
MAX_OUTPUT_TOKENS_PER_TURN = 2048
MAX_TOOL_ITERATIONS = 8
MAX_REBALANCE_USD_PER_CALL = 0.50
SONNET_INPUT_USD_PER_M = 3.0
SONNET_OUTPUT_USD_PER_M = 15.0

_PROMPT_PATH = Path(__file__).parent / "prompts" / "rebalance.txt"


class ToolCall(BaseModel):
    """One round-trip in the agent's trace: name, input, output, timing."""
    tool_name: str
    input_json: dict
    output_json: dict
    ts: datetime
    duration_ms: int


class RebalanceResult(BaseModel):
    """Final payload returned to the frontend."""
    advice_markdown: str
    trace: list[ToolCall]
    iterations: int
    truncated: bool
    cost_usd: float


def _user_message(holdings: NormalizedHoldings, snapshot: MarketSnapshot) -> str:
    """Build the user-side message: portfolio digest + ~3-line market context."""
    total = sum(a.current_value_inr for a in holdings.assets) or 1e-9
    lines = [
        "Portfolio:",
        *[f"- {a.name} ({a.category or 'Other'}): "
          f"₹{a.current_value_inr:,.0f} ({a.current_value_inr/total*100:.1f}%) "
          f"PnL {a.pnl_pct:.1f}%"
          for a in holdings.assets],
        "",
        f"Market context: Nifty 50 last close {snapshot.nifty_trend.current:,.0f}, "
        f"period change {snapshot.nifty_trend.pct_change_period:+.2f}% over "
        f"{snapshot.nifty_trend.period_days}d.",
        f"News: {len(snapshot.news)} headlines available "
        f"({'fallback' if snapshot.news_fallback_used else 'portfolio-filtered'}).",
        "",
        "Produce 2–3 numbered rebalancing suggestions per the system prompt.",
    ]
    return "\n".join(lines)


def _estimate_worst_case_usd(input_tokens: int) -> float:
    output = MAX_OUTPUT_TOKENS_PER_TURN * MAX_TOOL_ITERATIONS
    return (
        input_tokens * SONNET_INPUT_USD_PER_M / 1_000_000
        + output * SONNET_OUTPUT_USD_PER_M / 1_000_000
    )


def _estimate_actual_usd(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * SONNET_INPUT_USD_PER_M / 1_000_000
        + output_tokens * SONNET_OUTPUT_USD_PER_M / 1_000_000
    )


def run_rebalance(
    holdings: NormalizedHoldings, snapshot: MarketSnapshot,
) -> RebalanceResult:
    """Run the Sonnet tool-use loop with budget guardrails. Caller must have set ANTHROPIC_API_KEY."""
    system_prompt = _PROMPT_PATH.read_text()
    user_msg = _user_message(holdings, snapshot)
    client = Anthropic()

    # Pre-flight 1: per-call cost cap
    count_resp = client.messages.count_tokens(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": user_msg}],
    )
    estimated_input = count_resp.input_tokens
    worst_case = _estimate_worst_case_usd(estimated_input)
    if worst_case > MAX_REBALANCE_USD_PER_CALL:
        raise BudgetExhausted(
            f"Portfolio too large for rebalance — estimated ${worst_case:.2f} > "
            f"per-call cap ${MAX_REBALANCE_USD_PER_CALL:.2f}"
        )

    # Pre-flight 2: shared daily cap
    cap = _max_daily_usd()
    if cap is not None:
        spent = _read_today_usd()
        if spent + worst_case > cap:
            raise BudgetExhausted(
                f"Daily LLM budget ${cap:.2f} would be exceeded "
                f"(spent ${spent:.4f} so far, this call worst-case ${worst_case:.4f})"
            )

    # Set up per-request context for the tools
    _ctx.clear()
    _ctx["holdings"] = holdings
    _ctx["snapshot"] = snapshot

    start = time.time()
    trace: list[ToolCall] = []
    total_input_tokens = 0
    total_output_tokens = 0
    iterations = 0
    advice_markdown = ""
    truncated = False

    try:
        runner = client.messages.beta.tool_runner(
            model=DEFAULT_MODEL,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
            tools=TOOLS,
            max_tokens=MAX_OUTPUT_TOKENS_PER_TURN,
        )
        result = runner.run(max_iterations=MAX_TOOL_ITERATIONS)

        for tc in getattr(result, "tool_calls", []) or []:
            iterations += 1
            try:
                input_json = tc.input if isinstance(tc.input, dict) else dict(tc.input)
            except Exception:
                input_json = {}
            try:
                output_json = tc.output if isinstance(tc.output, dict) else {"value": tc.output}
            except Exception:
                output_json = {}
            trace.append(ToolCall(
                tool_name=tc.tool_name,
                input_json=input_json,
                output_json=output_json,
                ts=getattr(tc, "ts", datetime.now(timezone.utc)),
                duration_ms=getattr(tc, "duration_ms", 0),
            ))

        for turn in getattr(result, "turns", []) or []:
            usage = getattr(turn, "usage", None)
            if usage is not None:
                total_input_tokens += getattr(usage, "input_tokens", 0)
                total_output_tokens += getattr(usage, "output_tokens", 0)

        final = getattr(result, "final_message", None)
        if final is not None:
            for block in getattr(final, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    advice_markdown += getattr(block, "text", "")

        if iterations > MAX_TOOL_ITERATIONS or not advice_markdown.strip():
            truncated = True
            iterations = min(iterations, MAX_TOOL_ITERATIONS)

    finally:
        _ctx.clear()
        elapsed = time.time() - start
        logger.info(
            "[agent] rebalance run finished in %.1fs (iterations=%d truncated=%s)",
            elapsed, iterations, truncated,
        )

    cost_usd = _estimate_actual_usd(total_input_tokens, total_output_tokens) or 0.0
    if cap is not None and cost_usd > 0:
        try:
            _write_today_usd(_read_today_usd() + cost_usd)
        except OSError as e:
            logger.warning("[agent] daily-spend write failed: %s", e)

    return RebalanceResult(
        advice_markdown=advice_markdown.strip(),
        trace=trace,
        iterations=iterations,
        truncated=truncated,
        cost_usd=round(cost_usd, 6),
    )
```

- [ ] **Step 4: Run agent_loop tests**

Run: `pytest task4_open/backend/tests/test_agent_loop.py -v`
Expected: 4 passed.

> **If tests fail because the mocked SDK shape doesn't match the loop's access pattern:** rewrite the loop using `client.messages.create(...)` + a manual `tool_use` content-block loop (the same pattern as `parser/normalize.py:_call_haiku`). The behavioral contract (`RebalanceResult` fields, budget guards, iteration cap, trace capture, truncated flag) must remain identical. Update the tests to mock the equivalent shape.

- [ ] **Step 5: Do NOT commit yet** (held until Task 11).

---

### Task 11: main.py /api/rebalance + tests + COMMIT 2

**Files:**
- Modify: `task4_open/backend/main.py`
- Modify: `task4_open/backend/tests/test_main.py`

- [ ] **Step 1: Add the failing tests**

Append to `task4_open/backend/tests/test_main.py`:

```python
def test_rebalance_endpoint_happy_path(monkeypatch):
    from agent.loop import RebalanceResult
    holdings = _fake_normalized()
    fake_result = RebalanceResult(
        advice_markdown="1. Test advice — Evidence: foo.",
        trace=[], iterations=2, truncated=False, cost_usd=0.05,
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("main.get_market_snapshot", lambda h, refresh=False: _fake_market_snapshot())
    monkeypatch.setattr("main.run_rebalance", lambda h, s: fake_result)
    r = client.post("/api/rebalance", json={"holdings": holdings.model_dump(mode="json")})
    assert r.status_code == 200
    body = r.json()
    assert "Test advice" in body["advice_markdown"]
    assert body["iterations"] == 2
    assert body["cost_usd"] == 0.05


def test_rebalance_endpoint_no_api_key_returns_503(monkeypatch):
    holdings = _fake_normalized()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/api/rebalance", json={"holdings": holdings.model_dump(mode="json")})
    assert r.status_code == 503
    assert "rebalance unavailable" in r.json()["detail"]["error"]


def test_rebalance_endpoint_budget_exhausted_returns_429(monkeypatch):
    from parser.normalize import BudgetExhausted
    holdings = _fake_normalized()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("main.get_market_snapshot", lambda h, refresh=False: _fake_market_snapshot())

    def raise_budget(h, s):
        raise BudgetExhausted("daily budget $2.00 would be exceeded")

    monkeypatch.setattr("main.run_rebalance", raise_budget)
    r = client.post("/api/rebalance", json={"holdings": holdings.model_dump(mode="json")})
    assert r.status_code == 429
    assert "budget" in r.json()["detail"]["error"].lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest task4_open/backend/tests/test_main.py::test_rebalance_endpoint_happy_path task4_open/backend/tests/test_main.py::test_rebalance_endpoint_no_api_key_returns_503 task4_open/backend/tests/test_main.py::test_rebalance_endpoint_budget_exhausted_returns_429 -v`
Expected: FAIL (404 — route doesn't exist).

- [ ] **Step 3: Add the endpoint**

In `task4_open/backend/main.py`, append to the imports block:

```python
from agent.loop import RebalanceResult, run_rebalance
```

Add the request model under `MarketRequest`:

```python
class RebalanceRequest(BaseModel):
    """Request body for /api/rebalance — just the holdings (market snapshot is fetched server-side)."""
    holdings: NormalizedHoldings
```

Add the endpoint at end of file:

```python
@app.post("/api/rebalance", response_model=RebalanceResult)
def rebalance(req: RebalanceRequest) -> RebalanceResult:
    """Run the Sonnet rebalance agent and return advice + trace + cost."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail={"error": "rebalance unavailable", "detail": "ANTHROPIC_API_KEY not set"},
        )
    snapshot = get_market_snapshot(req.holdings, refresh=False)
    try:
        return run_rebalance(req.holdings, snapshot)
    except BudgetExhausted as e:
        raise HTTPException(
            status_code=429,
            detail={"error": "daily LLM budget exhausted", "detail": str(e)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("rebalance failed")
        raise HTTPException(
            status_code=502,
            detail={"error": "rebalance failed", "detail": str(e)},
        )
```

- [ ] **Step 4: Run all backend tests**

Run: `pytest task4_open/backend/tests/ -v`
Expected: all market + agent + previously passing tests pass (43 + 11 + 13 = 67+ total minimum).

- [ ] **Step 5: Commit (commit 2)**

```bash
git add task4_open/backend/agent/__init__.py \
        task4_open/backend/agent/tools.py \
        task4_open/backend/agent/loop.py \
        task4_open/backend/agent/prompts/rebalance.txt \
        task4_open/backend/main.py \
        task4_open/backend/tests/test_agent_tools.py \
        task4_open/backend/tests/test_agent_loop.py \
        task4_open/backend/tests/test_main.py
git rm --cached task4_open/backend/agent/prompts/.gitkeep 2>/dev/null || true
git commit -m "task4b: rebalance agent — Sonnet tool-use loop with 4 typed tools + budget guards"
```

---

### Task 12: Frontend store + API types/client + COMMIT 3

**Files:**
- Modify: `task4_open/frontend/lib/api.ts`
- Modify: `task4_open/frontend/lib/store.ts`
- Modify: `task4_open/frontend/__tests__/store.test.ts`

- [ ] **Step 1: Add the failing test**

Append to `task4_open/frontend/__tests__/store.test.ts`:

```typescript
test("marketSnapshot is session-only and not in partialize", () => {
  const { setMarketSnapshot } = usePortfolio.getState()
  const snap = {
    nifty_trend: { points: [], pct_change_period: 0, current: 22000, period_days: 90 },
    news: [],
    news_fallback_used: false,
    cached_at: new Date().toISOString(),
  }
  setMarketSnapshot(snap as unknown as MarketSnapshot)
  expect(usePortfolio.getState().marketSnapshot).toEqual(snap)
  const persisted = JSON.parse(localStorage.getItem("timecell-portfolio-v1") || "{}")
  expect(persisted.state.marketSnapshot).toBeUndefined()
})

test("rebalanceResult is session-only and not in partialize", () => {
  const { setRebalanceResult } = usePortfolio.getState()
  const r = {
    advice_markdown: "1. Test", trace: [], iterations: 1, truncated: false, cost_usd: 0.01,
  }
  setRebalanceResult(r as unknown as RebalanceResult)
  expect(usePortfolio.getState().rebalanceResult).toEqual(r)
  const persisted = JSON.parse(localStorage.getItem("timecell-portfolio-v1") || "{}")
  expect(persisted.state.rebalanceResult).toBeUndefined()
})
```

Also add the imports at the top of `__tests__/store.test.ts` (next to the existing imports):

```typescript
import type { MarketSnapshot, RebalanceResult } from "@/lib/api"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd task4_open/frontend && npx vitest run __tests__/store.test.ts`
Expected: FAIL — `setMarketSnapshot` does not exist on store.

- [ ] **Step 3: Extend api.ts with new types and functions**

Append to `task4_open/frontend/lib/api.ts` (just before `export class ApiError`):

```typescript
export interface NiftyPoint { date: string; close: number }
export interface NiftyTrend {
  points: NiftyPoint[]
  pct_change_period: number
  current: number
  period_days: number
}
export interface Headline {
  title: string
  publisher: string
  url: string
  published_at: string
  snippet: string | null
}
export interface MarketSnapshot {
  nifty_trend: NiftyTrend
  news: Headline[]
  news_fallback_used: boolean
  cached_at: string
}
export interface ToolCall {
  tool_name: string
  input_json: Record<string, unknown>
  output_json: Record<string, unknown>
  ts: string
  duration_ms: number
}
export interface RebalanceResult {
  advice_markdown: string
  trace: ToolCall[]
  iterations: number
  truncated: boolean
  cost_usd: number
}
```

Append at end of file:

```typescript
export async function fetchMarketSnapshot(
  holdings: NormalizedHoldings,
  opts: { refresh?: boolean } = {},
): Promise<MarketSnapshot> {
  const r = await fetch("/api/market", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ holdings, refresh: opts.refresh ?? false }),
  })
  if (!r.ok) {
    let detail: unknown = null
    try {
      const body = await r.json()
      detail = body.detail
      throw new ApiError(r.status, body.detail?.error || `HTTP ${r.status}`, detail)
    } catch (e) {
      if (e instanceof ApiError) throw e
      throw new ApiError(r.status, `HTTP ${r.status}`)
    }
  }
  return r.json()
}

export async function runRebalance(
  holdings: NormalizedHoldings,
): Promise<RebalanceResult> {
  const r = await fetch("/api/rebalance", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ holdings }),
  })
  if (!r.ok) {
    let detail: unknown = null
    try {
      const body = await r.json()
      detail = body.detail
      throw new ApiError(r.status, body.detail?.error || `HTTP ${r.status}`, detail)
    } catch (e) {
      if (e instanceof ApiError) throw e
      throw new ApiError(r.status, `HTTP ${r.status}`)
    }
  }
  return r.json()
}
```

- [ ] **Step 4: Extend store.ts**

Replace the contents of `task4_open/frontend/lib/store.ts` with:

```typescript
import { useEffect, useState } from "react"
import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"
import type { ParseAndComputeResponse, MarketSnapshot, RebalanceResult } from "./api"

interface PortfolioState {
  data: ParseAndComputeResponse | null
  lastFile: File | null
  marketSnapshot: MarketSnapshot | null
  rebalanceResult: RebalanceResult | null
  setData: (d: ParseAndComputeResponse | null) => void
  setLastFile: (f: File | null) => void
  setMarketSnapshot: (s: MarketSnapshot | null) => void
  setRebalanceResult: (r: RebalanceResult | null) => void
  clear: () => void
}

export const usePortfolio = create<PortfolioState>()(
  persist(
    (set) => ({
      data: null,
      lastFile: null,
      marketSnapshot: null,
      rebalanceResult: null,
      setData: (d) => set({ data: d }),
      setLastFile: (f) => set({ lastFile: f }),
      setMarketSnapshot: (s) => set({ marketSnapshot: s }),
      setRebalanceResult: (r) => set({ rebalanceResult: r }),
      clear: () => {
        set({
          data: null,
          lastFile: null,
          marketSnapshot: null,
          rebalanceResult: null,
        })
        if (typeof window !== "undefined") {
          localStorage.removeItem("timecell-portfolio-v1")
        }
      },
    }),
    {
      name: "timecell-portfolio-v1",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ data: s.data }),
    },
  ),
)

/** True once Zustand finishes reading localStorage. Component-safe. */
export function useHasHydrated(): boolean {
  const [hydrated, setHydrated] = useState(false)
  useEffect(() => {
    setHydrated(usePortfolio.persist.hasHydrated())
    const unsub = usePortfolio.persist.onFinishHydration(() => setHydrated(true))
    return unsub
  }, [])
  return hydrated
}
```

- [ ] **Step 5: Run all frontend tests**

Run: `cd task4_open/frontend && npx vitest run`
Expected: store.test.ts now has all tests passing including the 2 new ones.

- [ ] **Step 6: Commit (commit 3)**

```bash
git add task4_open/frontend/lib/api.ts \
        task4_open/frontend/lib/store.ts \
        task4_open/frontend/__tests__/store.test.ts
git commit -m "task4b: frontend store + API types for market snapshot + rebalance result"
```

---

### Task 13: NiftyChart component + test

**Files:**
- Create: `task4_open/frontend/components/NiftyChart.tsx`
- Create: `task4_open/frontend/__tests__/NiftyChart.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `task4_open/frontend/__tests__/NiftyChart.test.tsx`:

```typescript
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { NiftyChart } from "@/components/NiftyChart"

const sample = {
  points: [
    { date: "2026-01-01", close: 22000 },
    { date: "2026-01-02", close: 22100 },
    { date: "2026-01-03", close: 22200 },
  ],
  pct_change_period: 0.91,
  current: 22200,
  period_days: 3,
}

describe("NiftyChart", () => {
  test("renders header label, current value, and period change", () => {
    render(<NiftyChart trend={sample} />)
    expect(screen.getByText("NIFTY 50")).toBeInTheDocument()
    expect(screen.getByText("22,200")).toBeInTheDocument()
    expect(screen.getByText(/\+0\.91%/)).toBeInTheDocument()
  })

  test("renders one path/line element per point series in the SVG", () => {
    const { container } = render(<NiftyChart trend={sample} />)
    // Recharts renders an SVG <path> for the line; mocked ResponsiveContainer
    // means the chart actually renders in jsdom.
    expect(container.querySelector("svg")).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd task4_open/frontend && npx vitest run __tests__/NiftyChart.test.tsx`
Expected: FAIL (component does not exist).

- [ ] **Step 3: Implement NiftyChart**

Create `task4_open/frontend/components/NiftyChart.tsx`:

```typescript
"use client"
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Area } from "recharts"
import type { NiftyTrend } from "@/lib/api"

interface NiftyChartProps {
  trend: NiftyTrend
}

export function NiftyChart({ trend }: NiftyChartProps) {
  const positive = trend.pct_change_period >= 0
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
          NIFTY 50
        </span>
        <span className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
          {trend.period_days}d
        </span>
      </div>
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-2xl tabular-nums text-fg">
          {trend.current.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
        </span>
        <span
          className={`font-mono text-sm tabular-nums ${
            positive ? "text-brass-bright" : "text-oxblood"
          }`}
        >
          {positive ? "+" : ""}
          {trend.pct_change_period.toFixed(2)}%
        </span>
      </div>
      <div className="mt-4 h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trend.points} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
            <XAxis dataKey="date" hide />
            <YAxis domain={["auto", "auto"]} hide />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(20,16,10,0.92)",
                border: "1px solid var(--color-rule)",
                borderRadius: 0,
                fontFamily: "var(--font-mono)",
                fontSize: "0.7rem",
              }}
              formatter={(v: number) => v.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
            />
            <Line
              type="monotone"
              dataKey="close"
              stroke={positive ? "var(--color-brass-bright)" : "var(--color-oxblood)"}
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run NiftyChart test**

Run: `cd task4_open/frontend && npx vitest run __tests__/NiftyChart.test.tsx`
Expected: 2 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 15).

---

### Task 14: NewsList component + test

**Files:**
- Create: `task4_open/frontend/components/NewsList.tsx`
- Create: `task4_open/frontend/__tests__/NewsList.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `task4_open/frontend/__tests__/NewsList.test.tsx`:

```typescript
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { NewsList } from "@/components/NewsList"

const sampleHeadlines = [
  {
    title: "Reliance hits new high",
    publisher: "Moneycontrol",
    url: "https://example.com/1",
    published_at: "2026-01-02T10:00:00Z",
    snippet: "Stock rallies on Q3 outlook.",
  },
  {
    title: "Nifty closes flat",
    publisher: "ET",
    url: "https://example.com/2",
    published_at: "2026-01-02T09:00:00Z",
    snippet: null,
  },
]

describe("NewsList", () => {
  test("renders each headline with title and publisher", () => {
    render(<NewsList headlines={sampleHeadlines} fallbackUsed={false} />)
    expect(screen.getByText("Reliance hits new high")).toBeInTheDocument()
    expect(screen.getByText("Nifty closes flat")).toBeInTheDocument()
    expect(screen.getByText("Moneycontrol")).toBeInTheDocument()
  })

  test("shows fallback banner when fallbackUsed is true", () => {
    render(<NewsList headlines={sampleHeadlines} fallbackUsed={true} />)
    expect(
      screen.getByText(/no headlines matched your holdings/i),
    ).toBeInTheDocument()
  })

  test("shows empty state when headlines is empty", () => {
    render(<NewsList headlines={[]} fallbackUsed={false} />)
    expect(screen.getByText(/couldn't load news right now/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd task4_open/frontend && npx vitest run __tests__/NewsList.test.tsx`
Expected: FAIL (component does not exist).

- [ ] **Step 3: Implement NewsList**

Create `task4_open/frontend/components/NewsList.tsx`:

```typescript
import type { Headline } from "@/lib/api"

interface NewsListProps {
  headlines: Headline[]
  fallbackUsed: boolean
}

function relativeTime(iso: string): string {
  const t = new Date(iso).getTime()
  const diff = Date.now() - t
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

export function NewsList({ headlines, fallbackUsed }: NewsListProps) {
  if (headlines.length === 0) {
    return (
      <div className="border border-rule bg-rule-soft/30 px-5 py-8 text-center font-mono text-xs text-muted-deep">
        Couldn't load news right now
      </div>
    )
  }
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
          Headlines
        </span>
        <span className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
          {headlines.length}
        </span>
      </div>
      {fallbackUsed && (
        <div className="mb-3 border-l-2 border-brass bg-brass/5 px-3 py-2 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-brass-bright">
          No headlines matched your holdings — showing top general market news
        </div>
      )}
      <ul className="divide-y divide-rule">
        {headlines.map((h) => (
          <li key={h.url} className="py-3">
            <a
              href={h.url}
              target="_blank"
              rel="noreferrer"
              className="block font-serif text-sm text-fg hover:text-brass"
            >
              {h.title}
            </a>
            <div className="mt-1 flex gap-2 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-muted-deep">
              <span>{h.publisher}</span>
              <span>·</span>
              <span>{relativeTime(h.published_at)}</span>
            </div>
            {h.snippet && (
              <p className="mt-1 line-clamp-2 font-serif text-xs text-fg-soft">
                {h.snippet}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

- [ ] **Step 4: Run NewsList test**

Run: `cd task4_open/frontend && npx vitest run __tests__/NewsList.test.tsx`
Expected: 3 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 15).

---

### Task 15: Market tab page + COMMIT 4

**Files:**
- Modify: `task4_open/frontend/app/dashboard/market/page.tsx`

- [ ] **Step 1: Replace the stub**

Overwrite `task4_open/frontend/app/dashboard/market/page.tsx`:

```typescript
"use client"
import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"
import { ApiError, fetchMarketSnapshot } from "@/lib/api"
import { usePortfolio } from "@/lib/store"
import { NiftyChart } from "@/components/NiftyChart"
import { NewsList } from "@/components/NewsList"

export default function MarketPage() {
  const data = usePortfolio((s) => s.data)
  const snapshot = usePortfolio((s) => s.marketSnapshot)
  const setSnapshot = usePortfolio((s) => s.setMarketSnapshot)
  const [loading, setLoading] = useState(false)

  const load = useCallback(
    async (refresh: boolean) => {
      if (!data) return
      setLoading(true)
      try {
        const fresh = await fetchMarketSnapshot(data.normalized, { refresh })
        setSnapshot(fresh)
      } catch (e) {
        const msg = e instanceof ApiError
          ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
          : (e as Error).message
        toast.error(msg)
      } finally {
        setLoading(false)
      }
    },
    [data, setSnapshot],
  )

  useEffect(() => {
    if (data && !snapshot) {
      void load(false)
    }
  }, [data, snapshot, load])

  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-xl text-fg">Market</h2>
        <button
          onClick={() => void load(true)}
          disabled={loading}
          className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass disabled:opacity-50"
        >
          {loading ? "Refreshing…" : "↻ Refresh market"}
        </button>
      </div>
      {snapshot ? (
        <>
          <NiftyChart trend={snapshot.nifty_trend} />
          <NewsList headlines={snapshot.news} fallbackUsed={snapshot.news_fallback_used} />
        </>
      ) : (
        <div className="flex min-h-[40vh] items-center justify-center">
          <span className="font-mono text-sm text-muted-deep">Loading market data…</span>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Type-check the frontend**

Run: `cd task4_open/frontend && npx tsc --noEmit`
Expected: no errors. (If errors mention any field name, re-check the `MarketSnapshot` interface in `lib/api.ts`.)

- [ ] **Step 3: Run all frontend tests**

Run: `cd task4_open/frontend && npx vitest run`
Expected: all green (existing + 5 new from NiftyChart + NewsList).

- [ ] **Step 4: Commit (commit 4)**

```bash
git add task4_open/frontend/components/NiftyChart.tsx \
        task4_open/frontend/components/NewsList.tsx \
        task4_open/frontend/app/dashboard/market/page.tsx \
        task4_open/frontend/__tests__/NiftyChart.test.tsx \
        task4_open/frontend/__tests__/NewsList.test.tsx
git commit -m "task4b: market tab — NiftyChart + NewsList + page wiring"
```

---

### Task 16: AgentRunningIndicator component (no tests — purely cosmetic)

**Files:**
- Create: `task4_open/frontend/components/AgentRunningIndicator.tsx`

- [ ] **Step 1: Implement**

Create `task4_open/frontend/components/AgentRunningIndicator.tsx`:

```typescript
"use client"
import { useEffect, useState } from "react"

const PHASES = [
  "Reading portfolio…",
  "Checking Nifty trend…",
  "Pulling news for your holdings…",
  "Stress-testing scenarios…",
]

export function AgentRunningIndicator() {
  const [phaseIdx, setPhaseIdx] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setPhaseIdx((i) => (i + 1) % PHASES.length)
    }, 3000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-6">
      <div className="flex gap-1.5">
        <span className="h-2 w-2 animate-pulse rounded-full bg-brass [animation-delay:0ms]" />
        <span className="h-2 w-2 animate-pulse rounded-full bg-brass [animation-delay:200ms]" />
        <span className="h-2 w-2 animate-pulse rounded-full bg-brass [animation-delay:400ms]" />
      </div>
      <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted-deep">
        {PHASES[phaseIdx]}
      </p>
    </div>
  )
}
```

- [ ] **Step 2: Type-check**

Run: `cd task4_open/frontend && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Do NOT commit yet** (held until Task 19).

---

### Task 17: RebalanceAdvice component + test

**Files:**
- Create: `task4_open/frontend/components/RebalanceAdvice.tsx`
- Create: `task4_open/frontend/__tests__/RebalanceAdvice.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `task4_open/frontend/__tests__/RebalanceAdvice.test.tsx`:

```typescript
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { RebalanceAdvice } from "@/components/RebalanceAdvice"

describe("RebalanceAdvice", () => {
  test("renders numbered items", () => {
    const md = "1. Trim Reliance — Evidence: foo.\n2. Hold Gilt Fund — Evidence: bar."
    render(<RebalanceAdvice markdown={md} />)
    expect(screen.getByText(/Trim Reliance/)).toBeInTheDocument()
    expect(screen.getByText(/Hold Gilt Fund/)).toBeInTheDocument()
  })

  test("parses bold markdown into <strong>", () => {
    const md = "1. **Trim Reliance** by 10%."
    const { container } = render(<RebalanceAdvice markdown={md} />)
    const strong = container.querySelector("strong")
    expect(strong).not.toBeNull()
    expect(strong?.textContent).toBe("Trim Reliance")
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd task4_open/frontend && npx vitest run __tests__/RebalanceAdvice.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement RebalanceAdvice**

Create `task4_open/frontend/components/RebalanceAdvice.tsx`:

```typescript
import { Fragment } from "react"

interface RebalanceAdviceProps {
  markdown: string
}

const NUM_ITEM_RE = /^\s*(\d+)\.\s+(.*)$/
const BOLD_RE = /\*\*([^*]+)\*\*/g

function renderInline(text: string): React.ReactNode[] {
  const out: React.ReactNode[] = []
  let last = 0
  let key = 0
  for (const m of text.matchAll(BOLD_RE)) {
    if (m.index !== undefined && m.index > last) {
      out.push(<Fragment key={key++}>{text.slice(last, m.index)}</Fragment>)
    }
    out.push(<strong key={key++}>{m[1]}</strong>)
    last = (m.index ?? 0) + m[0].length
  }
  if (last < text.length) {
    out.push(<Fragment key={key++}>{text.slice(last)}</Fragment>)
  }
  return out
}

interface Item {
  number: string
  body: string
}

function parse(markdown: string): Item[] {
  const lines = markdown.split("\n")
  const items: Item[] = []
  let current: Item | null = null
  for (const line of lines) {
    const m = NUM_ITEM_RE.exec(line)
    if (m) {
      if (current) items.push(current)
      current = { number: m[1], body: m[2] }
    } else if (current && line.trim()) {
      current.body += " " + line.trim()
    }
  }
  if (current) items.push(current)
  return items
}

export function RebalanceAdvice({ markdown }: RebalanceAdviceProps) {
  const items = parse(markdown)
  if (items.length === 0) {
    return (
      <div className="border border-rule bg-rule-soft/30 p-5 font-serif text-sm text-fg">
        {renderInline(markdown)}
      </div>
    )
  }
  return (
    <div className="space-y-3">
      {items.map((it) => (
        <div
          key={it.number}
          className="border border-rule border-l-2 border-l-brass bg-rule-soft/30 p-5"
        >
          <div className="mb-2 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-brass">
            Suggestion {it.number}
          </div>
          <p className="font-serif text-sm leading-relaxed text-fg">
            {renderInline(it.body)}
          </p>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 4: Run test**

Run: `cd task4_open/frontend && npx vitest run __tests__/RebalanceAdvice.test.tsx`
Expected: 2 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 19).

---

### Task 18: AgentTrace component + test

**Files:**
- Create: `task4_open/frontend/components/AgentTrace.tsx`
- Create: `task4_open/frontend/__tests__/AgentTrace.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `task4_open/frontend/__tests__/AgentTrace.test.tsx`:

```typescript
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { AgentTrace } from "@/components/AgentTrace"

const sampleTrace = [
  {
    tool_name: "compute_concentration",
    input_json: { threshold_pct: 15 },
    output_json: { over_threshold: [{ name: "Reliance", pct: 65 }] },
    ts: "2026-01-02T10:00:00Z",
    duration_ms: 5,
  },
  {
    tool_name: "get_nifty_trend",
    input_json: { period_days: 90 },
    output_json: { current: 22000, period_days: 90 },
    ts: "2026-01-02T10:00:01Z",
    duration_ms: 3,
  },
]

describe("AgentTrace", () => {
  test("renders collapsed details summary with count", () => {
    render(<AgentTrace trace={sampleTrace} />)
    expect(
      screen.getByText(/Agent thought process — 2 tool calls/i),
    ).toBeInTheDocument()
  })

  test("lists each tool call name in chronological order", () => {
    render(<AgentTrace trace={sampleTrace} />)
    const items = screen.getAllByText(/compute_concentration|get_nifty_trend/)
    expect(items[0].textContent).toContain("compute_concentration")
    expect(items[1].textContent).toContain("get_nifty_trend")
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd task4_open/frontend && npx vitest run __tests__/AgentTrace.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement AgentTrace**

Create `task4_open/frontend/components/AgentTrace.tsx`:

```typescript
"use client"
import { useState } from "react"
import type { ToolCall } from "@/lib/api"

interface AgentTraceProps {
  trace: ToolCall[]
}

function summarize(input: Record<string, unknown>): string {
  const parts = Object.entries(input).map(([k, v]) => `${k}=${JSON.stringify(v)}`)
  const joined = parts.join(", ")
  return joined.length > 60 ? joined.slice(0, 60) + "…" : joined
}

function relativeStart(trace: ToolCall[], idx: number): string {
  if (idx === 0 || trace.length === 0) return "+0.0s"
  const t0 = new Date(trace[0].ts).getTime()
  const ti = new Date(trace[idx].ts).getTime()
  return `+${((ti - t0) / 1000).toFixed(1)}s`
}

export function AgentTrace({ trace }: AgentTraceProps) {
  const [openIdx, setOpenIdx] = useState<number | null>(null)
  return (
    <details className="border border-rule bg-rule-soft/30 p-5">
      <summary className="cursor-pointer font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">
        Agent thought process — {trace.length} tool call{trace.length === 1 ? "" : "s"}
      </summary>
      {trace.length === 0 ? (
        <p className="mt-3 font-mono text-xs text-muted-deep">
          (No tool calls were made.)
        </p>
      ) : (
        <ol className="mt-3 space-y-2">
          {trace.map((call, idx) => (
            <li key={idx} className="border-l border-rule pl-3">
              <button
                type="button"
                onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                className="block w-full text-left font-mono text-xs text-fg hover:text-brass"
              >
                <span className="text-muted-deep">{relativeStart(trace, idx)}</span>{" "}
                <span>
                  {call.tool_name}({summarize(call.input_json)})
                </span>
              </button>
              {openIdx === idx && (
                <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-all border border-rule bg-bg-deep p-2 font-mono text-[0.65rem] text-fg-soft">
                  {JSON.stringify({ input: call.input_json, output: call.output_json }, null, 2)}
                </pre>
              )}
            </li>
          ))}
        </ol>
      )}
    </details>
  )
}
```

- [ ] **Step 4: Run test**

Run: `cd task4_open/frontend && npx vitest run __tests__/AgentTrace.test.tsx`
Expected: 2 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 19).

---

### Task 19: Rebalance tab page + COMMIT 5

**Files:**
- Modify: `task4_open/frontend/app/dashboard/rebalance/page.tsx`

- [ ] **Step 1: Replace the stub**

Overwrite `task4_open/frontend/app/dashboard/rebalance/page.tsx`:

```typescript
"use client"
import { useCallback, useState } from "react"
import { toast } from "sonner"
import { ApiError, runRebalance } from "@/lib/api"
import { usePortfolio } from "@/lib/store"
import { RebalanceAdvice } from "@/components/RebalanceAdvice"
import { AgentTrace } from "@/components/AgentTrace"
import { AgentRunningIndicator } from "@/components/AgentRunningIndicator"

export default function RebalancePage() {
  const data = usePortfolio((s) => s.data)
  const result = usePortfolio((s) => s.rebalanceResult)
  const setResult = usePortfolio((s) => s.setRebalanceResult)
  const [busy, setBusy] = useState(false)

  const run = useCallback(async () => {
    if (!data) return
    setBusy(true)
    try {
      const r = await runRebalance(data.normalized)
      setResult(r)
    } catch (e) {
      const msg = e instanceof ApiError
        ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
        : (e as Error).message
      toast.error(msg)
    } finally {
      setBusy(false)
    }
  }, [data, setResult])

  if (!data) return null

  if (busy) return <AgentRunningIndicator />

  if (!result) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-6">
        <p className="max-w-md text-center font-serif text-base text-fg-soft">
          Generate a rebalance plan tailored to your holdings, market conditions, and risk band.
          The Anthropic Sonnet agent runs 4 tools and produces 2–3 actionable suggestions.
        </p>
        <button
          onClick={run}
          className="border border-brass px-6 py-2 font-mono text-xs uppercase tracking-[0.22em] text-brass-bright hover:bg-brass/10"
        >
          Generate rebalance plan
        </button>
        <p className="font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep">
          ~$0.05 per run
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-xl text-fg">Rebalance plan</h2>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
            ${result.cost_usd.toFixed(4)} · {result.iterations} iter
          </span>
          <button
            onClick={run}
            className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass"
          >
            ↻ Re-run
          </button>
        </div>
      </div>
      {result.truncated && (
        <div className="border-l-2 border-amber-500 bg-amber-500/5 px-4 py-2 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-amber-400">
          Agent didn't finalise within 8 iterations — partial advice below.
        </div>
      )}
      <RebalanceAdvice markdown={result.advice_markdown} />
      <AgentTrace trace={result.trace} />
    </div>
  )
}
```

- [ ] **Step 2: Type-check**

Run: `cd task4_open/frontend && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Run all frontend tests**

Run: `cd task4_open/frontend && npx vitest run`
Expected: all green (existing + new).

- [ ] **Step 4: Smoke-test the dev server**

Run (background, manual): `cd task4_open/frontend && npm run dev` and `cd task4_open/backend && uvicorn main:app --port 8001 --reload`. Visit `/dashboard/rebalance` after uploading a sample file. Confirm "Generate rebalance plan" button renders. (Don't wait for the full agent run if `ANTHROPIC_API_KEY` is unset — the toast error is acceptable.)

- [ ] **Step 5: Commit (commit 5)**

```bash
git add task4_open/frontend/components/AgentRunningIndicator.tsx \
        task4_open/frontend/components/RebalanceAdvice.tsx \
        task4_open/frontend/components/AgentTrace.tsx \
        task4_open/frontend/app/dashboard/rebalance/page.tsx \
        task4_open/frontend/__tests__/RebalanceAdvice.test.tsx \
        task4_open/frontend/__tests__/AgentTrace.test.tsx
git commit -m "task4b: rebalance tab — RebalanceAdvice + AgentTrace + RunningIndicator"
```

---

### Task 20: Final user gate

**Files:** none.

- [ ] **Step 1: Show the user the branch state**

Run:
```bash
git log task4a/dashboard-shell..HEAD --oneline
git status
```
Expected: 5 new commits on top of the spec commit (`f03d6a9`), clean working tree (or only `task4_open/frontend/next.config.ts` if the dev port was tweaked — that should be reverted before Step 2).

- [ ] **Step 2: Stop. Do not push. Do not open a PR.**

CLAUDE.md workflow rule:
> Branch before any change → commit → request PR review approval. Do not merge unilaterally.

Tell the user:

> Task 4b implementation complete on `task4b/market-rebalance` (5 commits on top of spec). Backend and frontend tests are green. ANTHROPIC_API_KEY is required for `/api/rebalance` to work end-to-end; without it the endpoint returns 503 and the Rebalance tab will surface a toast. Ready for your review — I haven't pushed and I haven't opened a PR. When you're ready, tell me to `git push -u origin task4b/market-rebalance` and `gh pr create`.

- [ ] **Step 3: Wait for user instruction**

Do not run `git push` or `gh pr create` until the user confirms.

---

## Self-Review Notes

**Spec coverage:** Every section of the spec maps to a task — schema (T2), fetch (T3-5), cache (T6), market endpoint (T7), tools (T8), prompt (T9), loop (T10), rebalance endpoint (T11), frontend types/store (T12), Market tab (T13-15), Rebalance tab (T16-19). Cost guardrails are inside the loop (T10). Error-handling table is implemented in main.py (T7, T11) + the Market/Rebalance pages (T15, T19).

**Type consistency:** `MarketSnapshot`, `NiftyTrend`, `Headline`, `RebalanceResult`, `ToolCall` — all defined in T2 (Pydantic) / T12 (TS) and reused identically in every later task. `_ctx` global is initialized in T8, populated by T10's `run_rebalance`, and cleared in `finally`.

**Anthropic SDK fragility:** The `@beta_tool` decorator and `client.messages.beta.tool_runner` usage may not match the installed SDK exactly. T8 step 4 and T10 step 4 explicitly call out the verification + fallback path (manual loop + tool_use blocks à la `parser/normalize.py`). Subagents are instructed to confirm before writing code.

**Test isolation:** Every backend test file that touches `~/.cache/timecell-task4/` uses `monkeypatch.setattr("parser.normalize.CACHE_DIR", tmp_path / ...)`. The new `tests/test_main.py` already has the autouse fixture from Task 4a — it covers the new tests too because they live in the same module.

**Workflow rule:** Final task (T20) is an explicit "do not push, do not PR" stop, matching CLAUDE.md.
