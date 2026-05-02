# Task 4b — Market + Rebalance Design

Adds two functional tabs to the Task 4a dashboard: **Market** (Nifty 50 trend + portfolio-personalized news) and **Rebalance** (Anthropic Sonnet tool-use agent that produces 2–3 actionable rebalancing suggestions grounded in your portfolio + market context).

**Built on top of:** Task 4a backend (`task4_open/backend/{main,parser,metrics}/...`) + Task 4a result-caching layer + Task 4a frontend shell (`task4_open/frontend/{app,components,lib}/...`). No backend or frontend rewrite — additive only. The two pages currently render `<StubTab>` placeholders; this work replaces them.

---

## Goals

1. **Market tab** renders the Nifty 50 trend (90-day line chart) and a news list filtered to the user's holdings, with a "Refresh market" override.
2. **Rebalance tab** runs an Anthropic Sonnet tool-use agent that calls 4 typed tools, then produces 2–3 markdown-formatted suggestions plus a collapsible chronological trace of every tool call.
3. **Cost stays inside the existing $25 Anthropic budget.** The agent loop reuses the daily-budget cap from `parser/normalize.py`; per-call ceiling of $0.50.
4. **No new paid services.** RSS feeds for news (free), `yfinance` for Nifty (free), Anthropic for the agent only.
5. **Shared shell, no schema break.** Existing routes, store fields, components, and `/api/parse-and-compute` continue to work unchanged.

Non-goals: order placement (no broker integration), portfolio mutation (the dashboard remains read-only — suggestions are advisory text), historical trend backtesting, multi-index views, sector heatmaps, social sentiment, options/futures, multi-user.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Browser                                                                 │
│  ┌────────────────────────────┐   ┌────────────────────────────┐         │
│  │  /dashboard/market         │   │  /dashboard/rebalance      │         │
│  │  - Nifty 90-day chart      │   │  - "Generate plan" button  │         │
│  │  - News filtered to your   │   │  - Recommendation panel    │         │
│  │    holdings                │   │  - <details> agent trace   │         │
│  │  - ↻ Refresh market button │   │  - ↻ Re-run button         │         │
│  └─────────┬──────────────────┘   └────────┬───────────────────┘         │
│            │ POST /api/market          POST│/api/rebalance               │
└────────────┼──────────────────────────────┼─────────────────────────────┘
             ▼                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                                       │
│  ┌──────────────────────┐    ┌─────────────────────────────────────────┐ │
│  │ market/              │    │ agent/                                  │ │
│  │  fetch.py            │    │  tools.py — 4 tool functions            │ │
│  │  cache.py (15-min)   │    │  loop.py — Sonnet tool-use runner       │ │
│  │  schema.py           │    │  prompts/rebalance.txt                  │ │
│  │                      │    │                                         │ │
│  └──────────────────────┘    └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Module boundaries:**

- `task4_open/backend/market/` — pure-function market data sourcing + 15-min in-memory cache. No LLM here.
- `task4_open/backend/agent/` — Anthropic SDK tool-use loop + 4 typed tools. The tools close over a per-request context (holdings + market snapshot) so Sonnet sees them as zero-arg helpers.
- `task4_open/backend/main.py` — adds two endpoints; existing `/api/health` and `/api/parse-and-compute` unchanged.
- `task4_open/frontend/app/dashboard/{market,rebalance}/page.tsx` — replace the stubs.
- `task4_open/frontend/components/{NiftyChart,NewsList,RebalanceAdvice,AgentTrace,AgentRunningIndicator}.tsx` — new.
- `task4_open/frontend/lib/store.ts` — adds `marketSnapshot` + `rebalanceResult` (NOT in `partialize`, session-only).
- `task4_open/frontend/lib/api.ts` — adds `fetchMarketSnapshot()`, `runRebalance()` + their TS types.

---

## Backend — market data

### `market/schema.py` (new)

```python
class NiftyPoint(BaseModel):
    date: date
    close: float

class NiftyTrend(BaseModel):
    points: list[NiftyPoint]
    pct_change_period: float
    current: float
    period_days: int

class Headline(BaseModel):
    title: str
    publisher: str
    url: str
    published_at: datetime
    snippet: str | None = None

class MarketSnapshot(BaseModel):
    nifty_trend: NiftyTrend
    news: list[Headline]
    news_fallback_used: bool
    cached_at: datetime
```

### `market/fetch.py` (new)

Three pure functions, no caching:

```python
def fetch_nifty_trend(period_days: int = 90) -> NiftyTrend:
    """yfinance.Ticker('^NSEI').history(period=f'{period_days}d').
    Returns NiftyTrend with points sorted by date asc, pct_change_period
    computed as (last_close - first_close) / first_close * 100."""

def fetch_rss_headlines(max_per_feed: int = 10) -> list[Headline]:
    """Aggregate via feedparser from:
       - https://www.moneycontrol.com/rss/marketsnews.xml
       - https://www.livemint.com/rss/markets
       - https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.xml
    Each feed: best-effort, on parse failure log WARN and continue.
    Dedup across feeds by title prefix (first 50 chars, lowercased).
    Sort by published_at desc. Returns up to 30 items."""

def filter_news_to_holdings(
    headlines: list[Headline],
    holdings: NormalizedHoldings,
) -> tuple[list[Headline], bool]:
    """Match headline.title against any token (>=4 chars, lowercased,
    word-boundaried) from any asset.name. Returns (matching, fallback_used).
    If matching is empty, returns (top 10 by published_at, fallback_used=True)."""
```

`yfinance` and `feedparser` are added to `backend/requirements.txt`.

### `market/cache.py` (new)

Process-local in-memory cache, NOT disk-backed (snapshot is small + ephemeral + we don't need cross-process sharing in single-uvicorn dev):

```python
import threading
from datetime import datetime, timedelta

_lock = threading.Lock()
_cached: tuple[datetime, MarketSnapshot] | None = None
TTL = timedelta(minutes=15)


def get_market_snapshot(
    holdings: NormalizedHoldings,
    refresh: bool = False,
) -> MarketSnapshot:
    """Returns cached snapshot if <15 min old and refresh=False.
    Otherwise fetches Nifty + RSS, filters news, caches, returns.
    The filtered news is cached PER PORTFOLIO if multiple portfolios
    are queried within the TTL — for v1 we cache the unfiltered news
    list and re-filter on each request (cheap)."""
```

### `main.py` additions

```python
class MarketRequest(BaseModel):
    holdings: NormalizedHoldings
    refresh: bool = False

@app.post("/api/market", response_model=MarketSnapshot)
def market(req: MarketRequest) -> MarketSnapshot:
    """Returns market snapshot filtered to the holder's portfolio."""
    return get_market_snapshot(req.holdings, refresh=req.refresh)
```

POST (not GET) so the holdings JSON travels in the body, not the query string.

---

## Backend — agent loop

### `agent/tools.py` (new)

Four tools registered via the Anthropic Python SDK's `@beta_tool` decorator. Each tool closes over a `_request_context` global (set fresh inside `run_rebalance` before the loop starts and cleared after). This avoids passing context through tool function signatures, which the SDK's tool runner does not allow:

```python
from anthropic.lib.tools import beta_tool

_ctx: dict = {}  # populated by agent.loop.run_rebalance() before the loop

@beta_tool
def get_nifty_trend(period_days: int = 90) -> dict:
    """Latest Nifty 50 close prices and % change over the period.
    period_days must be one of: 7, 30, 90, 365.
    Returns: {points: [{date, close}], pct_change_period, current}."""
    valid = {7, 30, 90, 365}
    if period_days not in valid:
        return {"error": f"period_days must be one of {valid}"}
    snap = _ctx["snapshot"]
    if period_days == snap.nifty_trend.period_days:
        return snap.nifty_trend.model_dump(mode="json")
    sliced = snap.nifty_trend.points[-period_days:]
    return {
        "points": [p.model_dump(mode="json") for p in sliced],
        "pct_change_period": _pct_change(sliced),
        "current": snap.nifty_trend.current,
        "period_days": period_days,
    }

@beta_tool
def get_news_for_holding(name: str) -> dict:
    """Recent headlines whose title contains the holding's name (case-insensitive).
    Returns up to 5 matches with title, publisher, url, published_at, snippet."""
    snap = _ctx["snapshot"]
    matches = [h for h in snap.news if name.lower() in h.title.lower()]
    return {"name": name, "headlines": [h.model_dump(mode="json") for h in matches[:5]]}

@beta_tool
def compute_concentration(threshold_pct: float = 15.0) -> dict:
    """Returns assets exceeding threshold_pct of current portfolio value
    plus per-major-category percentages (Equity / Debt / Hybrid / Commodities)."""
    holdings = _ctx["holdings"]
    total = sum(a.current_value_inr for a in holdings.assets) or 1e-9
    over = [
        {"name": a.name, "pct": round(a.current_value_inr / total * 100, 2),
         "category": a.category, "sub_category": a.sub_category}
        for a in holdings.assets
        if a.current_value_inr / total * 100 > threshold_pct
    ]
    by_cat: dict[str, float] = {}
    for a in holdings.assets:
        by_cat[a.category or "Other"] = by_cat.get(a.category or "Other", 0) + a.current_value_inr
    return {
        "threshold_pct": threshold_pct,
        "over_threshold": over,
        "category_pct": {k: round(v / total * 100, 2) for k, v in by_cat.items()},
    }

@beta_tool
def propose_drawdown_simulation(rebalance_proposal: dict) -> dict:
    """Given {sell: [{name, pct_to_trim}], buy: [{name, pct_to_add}]}, returns
    the resulting category percentages and a flag indicating whether the new
    Equity allocation falls inside the user's pre-stated risk band.

    pct_to_trim/pct_to_add are percentages of CURRENT TOTAL portfolio value, not
    of each holding individually."""
    holdings = _ctx["holdings"]
    total = sum(a.current_value_inr for a in holdings.assets) or 1e-9
    new_values = {a.name: a.current_value_inr for a in holdings.assets}
    for sell in rebalance_proposal.get("sell", []):
        new_values[sell["name"]] = max(
            0, new_values.get(sell["name"], 0) - sell["pct_to_trim"] / 100 * total,
        )
    for buy in rebalance_proposal.get("buy", []):
        new_values[buy["name"]] = new_values.get(buy["name"], 0) + buy["pct_to_add"] / 100 * total
    new_by_cat: dict[str, float] = {}
    for a in holdings.assets:
        cat = a.category or "Other"
        new_by_cat[cat] = new_by_cat.get(cat, 0) + new_values.get(a.name, 0)
    new_total = sum(new_values.values()) or 1e-9
    new_eq_pct = (new_by_cat.get("Equity", 0) / new_total) * 100
    return {
        "category_pct": {k: round(v / new_total * 100, 2) for k, v in new_by_cat.items()},
        "new_equity_pct": round(new_eq_pct, 2),
        "fits_risk_band_60_70": 60.0 <= new_eq_pct <= 70.0,
    }
```

### `agent/loop.py` (new)

```python
DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_INPUT_TOKENS = 20_000
MAX_OUTPUT_TOKENS_PER_TURN = 2048
MAX_TOOL_ITERATIONS = 8
MAX_REBALANCE_USD_PER_CALL = 0.50
SONNET_INPUT_USD_PER_M = 3.0
SONNET_OUTPUT_USD_PER_M = 15.0


class ToolCall(BaseModel):
    tool_name: str
    input_json: dict
    output_json: dict
    ts: datetime
    duration_ms: int


class RebalanceResult(BaseModel):
    advice_markdown: str
    trace: list[ToolCall]
    iterations: int
    truncated: bool
    cost_usd: float


def run_rebalance(holdings: NormalizedHoldings, snapshot: MarketSnapshot) -> RebalanceResult:
    """Runs the Sonnet tool-use loop with the 4 tools registered.
    Captures every tool call into a trace list. Returns a RebalanceResult.

    Cost guardrails:
      - Pre-flight: count_tokens on the first user message; estimate worst-case
        cost as input + (MAX_TOOL_ITERATIONS × MAX_OUTPUT_TOKENS_PER_TURN). If
        > MAX_REBALANCE_USD_PER_CALL, raise BudgetExhausted.
      - Pre-flight: read today's spend from the parse-cache CACHE_DIR file used
        by parser/normalize.py. If cap would be exceeded, raise BudgetExhausted.
      - Post-flight: sum all turn usages, write actual cost to the same daily
        spend file (atomic .tmp + replace).
      - Iteration cap: stop after MAX_TOOL_ITERATIONS round-trips. Set
        truncated=True if Sonnet hadn't returned a final text-only message."""
```

### `agent/prompts/rebalance.txt` (new)

A system prompt that:

- Identifies the agent as "a portfolio analyst, not a financial advisor"
- Lists each of the 4 tools and when to use them
- Tells Sonnet to call `compute_concentration(15)` at minimum, and at least one of `get_nifty_trend` / `get_news_for_holding` before proposing
- Constrains the final output to 2–3 numbered markdown items, each ≤ 80 words, each ending with an "Evidence: …" line citing which tool's result drove the suggestion
- Bans inventing prices, news headlines, or returns
- Includes one example of well-formed output

### `main.py` rebalance endpoint

```python
class RebalanceRequest(BaseModel):
    holdings: NormalizedHoldings

@app.post("/api/rebalance", response_model=RebalanceResult)
def rebalance(req: RebalanceRequest) -> RebalanceResult:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(503, detail={"error": "rebalance unavailable",
                                          "detail": "ANTHROPIC_API_KEY not set"})
    snapshot = get_market_snapshot(req.holdings, refresh=False)
    try:
        return run_rebalance(req.holdings, snapshot)
    except BudgetExhausted as e:
        raise HTTPException(429, detail={"error": "budget exhausted", "detail": str(e)})
    except Exception as e:
        logger.exception("rebalance failed")
        raise HTTPException(502, detail={"error": "rebalance failed", "detail": str(e)})
```

---

## Frontend — Market tab

### `lib/store.ts` additions

```typescript
interface PortfolioState {
  // existing fields unchanged
  marketSnapshot: MarketSnapshot | null
  rebalanceResult: RebalanceResult | null
  setMarketSnapshot: (s: MarketSnapshot | null) => void
  setRebalanceResult: (r: RebalanceResult | null) => void
}
```

`partialize` continues to persist only `data` — the new fields are session-only.

### `lib/api.ts` additions

```typescript
export interface NiftyPoint { date: string; close: number }
export interface NiftyTrend { points: NiftyPoint[]; pct_change_period: number; current: number; period_days: number }
export interface Headline { title: string; publisher: string; url: string; published_at: string; snippet: string | null }
export interface MarketSnapshot { nifty_trend: NiftyTrend; news: Headline[]; news_fallback_used: boolean; cached_at: string }
export interface ToolCall { tool_name: string; input_json: unknown; output_json: unknown; ts: string; duration_ms: number }
export interface RebalanceResult { advice_markdown: string; trace: ToolCall[]; iterations: number; truncated: boolean; cost_usd: number }

export async function fetchMarketSnapshot(holdings: NormalizedHoldings, opts?: { refresh?: boolean }): Promise<MarketSnapshot>
export async function runRebalance(holdings: NormalizedHoldings): Promise<RebalanceResult>
```

### `app/dashboard/market/page.tsx` (replaces stub)

Reads `data` from the store; on first mount, calls `fetchMarketSnapshot(data.normalized)` and stores it. Renders header (with `Refresh market` button), `<NiftyChart>`, `<NewsList>`. Loading state via `<Loading label="…">` while `snapshot` is null and a fetch is in flight.

### `components/NiftyChart.tsx` (new)

Recharts `LineChart` (90 days, `points`), brass stroke + 8% area fill. Header shows "NIFTY 50" mono, current value (large mono-tabular), period change (brass-bright if ≥0 else oxblood). Inherits the dashboard's existing chart styling pattern from `AllocationDonut`.

### `components/NewsList.tsx` (new)

Vertical list. Each item: title (serif, brass on hover, opens new tab via `target="_blank" rel="noreferrer"`), publisher + relative-time (mono muted-deep), optional snippet (serif fg-soft, 2-line clamp via Tailwind `line-clamp-2`). When `news_fallback_used`, shows a small one-line "no headlines matched your holdings — showing top general market news" notice above the list. Empty list: "Couldn't load news right now" empty state.

---

## Frontend — Rebalance tab

### `app/dashboard/rebalance/page.tsx` (replaces stub)

Three states:

1. **No result, not busy:** centered intro paragraph + "Generate rebalance plan" button (brass border, brass-bright text, ~$0.05 hint underneath).
2. **Busy:** `<AgentRunningIndicator>` — three pulsing dots + rotating mono caption ("Reading portfolio…" → "Checking Nifty trend…" → "Pulling news for your holdings…" → "Stress-testing scenarios…"), advances every 3s.
3. **Result present:** header with cost + iteration count + "↻ Re-run" button; `<RebalanceAdvice markdown={...}>`; `<AgentTrace trace={...}>` collapsible.

### `components/RebalanceAdvice.tsx` (new)

Renders the agent's markdown via a tiny inline parser handling only `**bold**`, numbered lists, plain paragraphs, and line breaks. Each numbered suggestion in its own bordered card with brass left accent. (Pulling in a full markdown library is overkill; ~30 lines of inline parsing is enough for the constrained output we ask Sonnet for.)

### `components/AgentTrace.tsx` (new)

`<details>` collapsed by default. Header: "Agent thought process — N tool calls". Inside: ordered timeline. Each row: `[+0.5s] tool_name(input_summary)` in mono small text, then a 2-line excerpt of the output JSON. Click any row to expand the full input/output JSON in a `<pre>` block.

### `components/AgentRunningIndicator.tsx` (new)

Pure cosmetic. Three-dot pulse animation + caption that cycles via `useEffect(() => setInterval(...))`. Stops when component unmounts.

---

## Cost guardrails

The 4b agent loop **shares the existing daily-budget cap** from `parser/normalize.py`. The `~/.cache/timecell-task4/usage-YYYY-MM-DD.json` file is read + atomically updated by both the parser and the rebalance agent.

| Layer | Mechanism | Default |
|---|---|---|
| Per-call ceiling | `count_tokens` pre-flight × worst-case iteration count vs `MAX_REBALANCE_USD_PER_CALL` | $0.50 |
| Daily ceiling | shared `MAX_DAILY_LLM_USD` | $2.00 |
| Iteration cap | `MAX_TOOL_ITERATIONS` | 8 |
| Per-tool execution | tools are pure functions over already-cached data | <2 ms each |
| Market data refresh | 15-min in-memory TTL + manual `?refresh=true` | implicit |

Expected cost per rebalance run: **$0.04–$0.10** depending on portfolio size and how many tools Sonnet calls.

Expected total 4b spend (development + manual smoke + ~10 demo runs): **<$1.00**.

---

## Error handling

| Failure | HTTP | Frontend behavior |
|---|---|---|
| `data` is null on Market or Rebalance page | n/a | `useHasHydrated` gate in dashboard layout already redirects to `/` |
| yfinance Nifty fetch fails | 502 | Market page shows retry banner; rebalance still works (agent has concentration tool + portfolio data) |
| All 3 RSS feeds fail | 200 with `news: []`, `news_fallback_used: false` | NewsList shows "Couldn't load news right now" empty state |
| One or two RSS feeds fail | 200 with the rest | Silent (logged WARN) |
| `BudgetExhausted` during rebalance | 429 | Toast: "Daily LLM budget exhausted. Set `MAX_DAILY_LLM_USD=disabled` or wait until tomorrow." |
| Per-call `> $0.50` cap | 429 | Toast: "Portfolio too large for rebalance — expected $X.XX, cap $0.50." |
| `MAX_TOOL_ITERATIONS` reached without final answer | 200 with `truncated: true` | `<RebalanceAdvice>` shows partial output + amber "Agent didn't finalise within 8 iterations — partial advice below." |
| Sonnet returns malformed markdown | 200, raw text rendered | Acceptable. No retry. |
| Generic Anthropic error | 502 | Toast with error; user can Re-run |
| Tool function raises | n/a | Tool runner returns error to Sonnet; Sonnet recovers or proceeds |
| `ANTHROPIC_API_KEY` unset | 503 | Rebalance page shows permanent "Set `ANTHROPIC_API_KEY` in `.env`" notice instead of Generate button |

`/api/market` works without an API key (no LLM involved).

---

## Testing

### Backend (pytest) — 18 new tests

| File | Tests | Notes |
|---|---|---|
| `tests/test_market_fetch.py` | 3: `fetch_nifty_trend` shape (mocked yfinance), `fetch_rss_headlines` parses + dedups (3 fixture XML strings), `filter_news_to_holdings` matches + falls back | yfinance mocked via `monkeypatch.setattr` on `yfinance.Ticker` |
| `tests/test_market_cache.py` | 3: cold call fetches; warm call within TTL serves cache; `refresh=True` bypasses | Time travel via monkeypatching the cache's clock |
| `tests/test_agent_tools.py` | 4: each tool returns the right shape against hand-built portfolio + market snapshot | Pure-function tests, no LLM |
| `tests/test_agent_loop.py` | 4: happy-path (mocked Sonnet returns advice + trace); iteration cap returns `truncated=True`; budget guard raises before SDK call; per-call $0.50 cap raises | All `anthropic.Anthropic` patched |
| `tests/test_main.py` | +4 added: `POST /api/market` happy + 502 on yfinance failure; `POST /api/rebalance` happy (mocked agent) + 429 on budget | `monkeypatch.setattr("agent.loop.run_rebalance", ...)` |

**Total backend tests: 43 → 61.**

### Frontend (Vitest + RTL) — 11 new tests

| File | Tests |
|---|---|
| `__tests__/NiftyChart.test.tsx` | 2: renders header + current value; renders correct number of points |
| `__tests__/NewsList.test.tsx` | 3: renders headlines; shows fallback banner when `fallbackUsed`; empty state when no news |
| `__tests__/RebalanceAdvice.test.tsx` | 2: renders numbered suggestions; bold + list parsing |
| `__tests__/AgentTrace.test.tsx` | 2: `<details>` collapsed by default; expands to show tool calls in chronological order |
| `__tests__/store.test.ts` | +2: `marketSnapshot` + `rebalanceResult` are excluded from `partialize` |

**Total frontend tests: 23 → 34.**

### Live verification (manual)

1. `POST /api/market` returns Nifty + news; second call within 15 min serves cache (assert `cached_at` unchanged); `?refresh=true` updates `cached_at`.
2. `POST /api/rebalance` against `sample_groww.xlsx`: assert advice contains a numbered list, trace has ≥2 tool calls, cost reported.
3. Browser walkthrough: Market tab → Nifty chart renders + news loads + Refresh button works; Rebalance tab → Generate button visible → click → ~15s spinner → advice + trace appear; click trace `<details>` → expands; click Re-run → spinner reappears.

---

## Performance

- `/api/market` first call: ~1.5–2 s (yfinance + 3 RSS feeds in parallel via `concurrent.futures.ThreadPoolExecutor`).
- `/api/market` cached call: ~10 ms.
- `/api/rebalance`: ~10–20 s (Sonnet + 3–6 tool round-trips).
- Frontend payload sizes: market snapshot ~5–15 KB; rebalance result ~2–8 KB.
- No persistence cost (both stored in-memory client-side, in-memory server-side).

---

## Migration / rollout

No DB, no auth, no schema migrations. The two new endpoints are additive — old clients see no behavior change. The frontend store gains two new fields with default `null`; existing persisted state under `timecell-portfolio-v1` continues to work unchanged because the new fields are not in `partialize`. Deploying mid-session: Market and Rebalance tabs go from "Coming in Task 4b" stubs to live.
