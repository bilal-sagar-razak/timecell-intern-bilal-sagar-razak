# Task 4a — Dashboard Shell + Holdings Parser + Overview Tab

**Status:** approved design — ready for implementation plan.
**Date:** 2026-05-02
**Branch:** `task4a/dashboard-shell` (off `main` at `8619b64`)

## Goal

Build the **shared webapp shell** for Task 4 plus its first feature: a **holdings parser** (LLM-normalized, format-agnostic) and the **Overview tab** that renders KPIs, allocation donut, XIRR-by-fund chart, and category-performance cards from any uploaded holdings statement. The other three tabs (Holdings, Market, Rebalance) ship as stubs that say "Coming in Task 4b/4c" — the shell is complete in 4a; the features fill in across 4b and 4c.

The dashboard's overall feature scope across all three sub-tasks (decided up-front so the shell can accommodate it):

| Sub-task | Tab | Feature |
|---|---|---|
| **4a** (this spec) | Overview | KPI cards, allocation donut, XIRR-by-fund bar chart, category cards |
| **4a** (this spec) | Holdings, Market, Rebalance | Stub cards saying "Coming in Task 4b/4c" |
| **4b** | Market | Nifty 50 trend, market news (NewsAPI / Anthropic web search) |
| **4b** | Rebalance | Anthropic agent loop with tool calls — gives rebalancing recommendations |
| **4c** | Holdings | Per-fund stock breakdown, drilldown |
| **4c** | Holdings (or sub-tab) | Fund-overlap matrix (heatmap from mockup image 2) |

## Architecture

### Stack

- **Backend:** FastAPI 0.115+ (Python 3.10+), Pydantic v2, scipy (XIRR), Anthropic SDK, openpyxl, BeautifulSoup4, pdfplumber, Pillow
- **Frontend:** Next.js (latest, App Router, TypeScript strict), Tailwind CSS, shadcn/ui primitives, Recharts (donut + bar chart), Lucide React (icons), Zustand (in-memory portfolio store)
- **AI model:** **Claude Haiku 4.5** (`claude-haiku-4-5`) for the parser — confirmed via `claude-api` skill at implementation time. Haiku is the right tier for structured extraction; Sonnet is overkill at $3/$15 per 1M when Haiku at $1/$5 produces equivalent JSON quality on this task.
- **Persistence:** none. Stateless — every visit, user uploads, results render, refresh = re-upload.
- **Auth:** none. Single-user demo.

### Repo layout

```
task4_open/
├── backend/
│   ├── main.py                       # FastAPI app, CORS, routes
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── extract.py                # file → raw text/tables (xlsx/html/pdf/image)
│   │   ├── normalize.py              # text/tables + canonical schema → Haiku → validated JSON
│   │   └── schema.py                 # Pydantic: Asset, PortfolioSummary, NormalizedHoldings
│   ├── metrics/
│   │   ├── __init__.py
│   │   └── compute.py                # XIRR, allocation %, category P&L — pure functions
│   ├── prompts/
│   │   └── normalize.txt             # externalized normalizer prompt (string.Template)
│   ├── tests/
│   │   ├── test_extract.py           # mocked file readers
│   │   ├── test_normalize.py         # mocked Anthropic SDK
│   │   └── test_metrics.py           # pure function tests
│   ├── samples/                      # 3 sample holdings files for tests + dev
│   │   ├── Holdings_Statement_2026-05-02.xlsx       # Groww format
│   │   ├── Portfolio_summary_report_withoutFormatting.xls   # Camsonline MHTML
│   │   └── holdings-EEM619.xlsx                     # Zerodha Console format
│   ├── requirements.txt
│   └── pyproject.toml                # ruff + pytest config
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                # root layout — theme provider, font imports
│   │   ├── page.tsx                  # "/" — landing + file upload widget
│   │   ├── dashboard/
│   │   │   ├── layout.tsx            # header (holder name, total ₹) + tab nav
│   │   │   ├── page.tsx              # "/dashboard" — Overview tab (this is what 4a ships)
│   │   │   ├── holdings/page.tsx     # stub — "Coming in Task 4c"
│   │   │   ├── market/page.tsx       # stub — "Coming in Task 4b"
│   │   │   └── rebalance/page.tsx    # stub — "Coming in Task 4b"
│   │   └── globals.css               # Tailwind directives + Ledger CSS variables
│   ├── components/
│   │   ├── KpiCard.tsx
│   │   ├── AllocationDonut.tsx       # Recharts pie chart
│   │   ├── XirrBarChart.tsx          # Recharts horizontal bar chart
│   │   ├── CategoryCard.tsx
│   │   ├── FileUpload.tsx            # dropzone with progress
│   │   ├── TabNav.tsx                # 4-tab strip
│   │   └── StubTab.tsx               # "Coming in 4b/4c" placeholder
│   ├── lib/
│   │   ├── api.ts                    # typed fetch wrapper (parses to TS types matching Pydantic schema)
│   │   ├── format.ts                 # formatINR — Indian-grouping ported from Task 3
│   │   ├── store.ts                  # Zustand portfolio store
│   │   └── theme.ts                  # color tokens object (mirrors Tailwind config, used by charts)
│   ├── __tests__/                    # Vitest + RTL component tests
│   ├── e2e/                          # Playwright smoke test
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts            # Ledger palette + Fraunces/Geist Mono
│   ├── next.config.js                # /api/* rewrite → http://localhost:8000/api/*
│   └── .eslintrc.json
├── README.md                         # task4 overview, dev workflow, AI usage
└── Makefile                          # `make dev`, `make test`, `make install`
```

### Theme — pulled directly from timecell.ai

The frontend uses the **"Ledger" design system** from `https://timecell.ai`. CSS variables, fonts, and visual treatments are baked into `frontend/app/globals.css` and `frontend/tailwind.config.ts`:

```css
/* Ledger design system — from timecell.ai */
:root {
  --bg: #13110f;          /* main background — warm dark */
  --fg: #efe8da;          /* primary text — warm cream */
  --fg-soft: #a8a08a;     /* secondary text */
  --rule: #2a2620;        /* borders / dividers */
  --rule-soft: #1f1c18;   /* softer borders */
  --muted: #8a8275;       /* muted text */
  --muted-deep: #6a6258;
  --muted-deeper: #5a5240;
  --brass: #a88b4a;       /* primary accent — for positive XIRR, active tab, buttons */
  --brass-bright: #c9a86a; /* hover / highlight accent */
  --oxblood: #c97a6f;     /* destructive — for negative XIRR, errors */
}
```

**Fonts** (loaded from Google Fonts in `app/layout.tsx`):
- `Fraunces` (300, 400, 500, opsz 9..144) — body text, headings, KPI labels
- `Geist Mono` (400, 500) — KPI numerical values, tab labels, button text (uppercase, wide letter-spacing per timecell convention)

**Visual treatments** (from timecell.ai, used as background-image on body):
- Subtle radial gradient at top (`rgba(168, 139, 74, 0.08)` brass glow)
- Faint horizontal rule lines every 48px (`rgba(42, 38, 32, 0.35)`) — gives a ledger-paper feel

**Chart palette mapping** (the mockup image 1 uses generic purple/green/red; we remap to the Ledger palette):
- **Positive XIRR / P&L:** `--brass` solid bars
- **Negative XIRR / P&L:** `--oxblood` solid bars
- **Donut segments:** rotate through `--brass-bright`, `--brass`, `--muted`, `--muted-deep`, `--muted-deeper`, `--fg-soft` — six tones is enough for typical category counts

The result: the dashboard's *structure* matches mockup image 1 exactly (KPI cards on top, donut + bar side-by-side, category cards below), but colors and fonts are timecell.ai's house style — not the generic dark-dashboard look from the screenshot.

### Logo

Use `/logo.png` from timecell.ai (download once during implementation, store at `frontend/public/timecell-logo.png`). Display in the dashboard header at 22px height, opacity 0.9, with the "TIMECELL" wordmark in Geist Mono uppercase next to it (matches their topbar treatment).

## Data model

### Pydantic schema — `backend/parser/schema.py`

```python
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field

class Asset(BaseModel):
    """One row in a holdings statement — stock or mutual fund."""
    name: str = Field(..., description="Scheme name or stock symbol")
    asset_type: Literal["mutual_fund", "stock", "etf", "bond", "commodity", "other"]
    isin: str | None = None
    amc: str | None = None
    category: str | None = None        # "Equity" | "Debt" | "Hybrid" | "Commodities" | None
    sub_category: str | None = None    # "Flexi Cap" | "Mid Cap" | "Gilt" | etc.
    folio: str | None = None
    units: float
    invested_value_inr: float
    current_value_inr: float
    xirr_pct: float | None = None
    pnl_inr: float
    pnl_pct: float

class PortfolioSummary(BaseModel):
    """Top-level numbers — extracted from the statement, or computed from assets if absent."""
    total_invested_inr: float
    total_current_inr: float
    total_pnl_inr: float
    total_pnl_pct: float
    overall_xirr_pct: float | None = None
    asset_count: int
    statement_date: date | None = None

class NormalizedHoldings(BaseModel):
    """Top-level container — what the parser returns."""
    holder_name: str | None = None
    source_format: str                 # "groww_xlsx" | "camsonline_mhtml" | "zerodha_console" | "unknown"
    summary: PortfolioSummary
    assets: list[Asset]
    parser_warnings: list[str] = []
```

### Computed metrics (added by `metrics/compute.py`)

```python
class KPIs(BaseModel):
    invested_inr: float
    current_inr: float
    equity_pct: float           # sum of category=="Equity" current_value / total
    debt_pct: float             # sum of category in {"Debt","Gilt"} current_value / total
    daily_change_inr: float | None = None   # not available from statement; None
    daily_change_pct: float | None = None
    overall_xirr_pct: float | None = None
    asset_count: int

class AllocationSlice(BaseModel):
    label: str                  # category name
    value_inr: float
    pct: float

class XirrEntry(BaseModel):
    name: str                   # truncated to 24 chars for chart readability
    xirr_pct: float
    color: Literal["positive", "negative"]   # frontend maps to brass/oxblood

class CategoryPerformance(BaseModel):
    category: str
    pnl_inr: float
    cagr_pct: float | None      # statement-provided when available

class ParseAndComputeResponse(BaseModel):
    normalized: NormalizedHoldings
    kpis: KPIs
    allocation: list[AllocationSlice]
    xirr_by_fund: list[XirrEntry]      # sorted descending by xirr_pct
    category_performance: list[CategoryPerformance]
```

## Backend API

### Endpoints

```
POST /api/parse-and-compute
  Multipart upload: file=<holdings file>
  Response 200:  ParseAndComputeResponse JSON
  Response 400:  {"error": "no file provided"}
  Response 413:  {"error": "file too large", "max_mb": 10}
  Response 415:  {"error": "unsupported file type", "supported": ["xlsx","xls","pdf","png","jpg","jpeg"]}
  Response 422:  {"error": "could not extract structured data from file", "detail": "..."}
  Response 429:  {"error": "daily LLM budget exhausted"}
  Response 502:  {"error": "LLM service unavailable" | "could not normalize statement after retry", "detail": "..."}
  Notes:
    - Streams file to disk in tempfile, max 10MB
    - Extracts structured data via extract.py
    - Calls Haiku via normalize.py (with cost guards + 1-retry-on-validation-failure)
    - Computes derived metrics via metrics/compute.py (pure functions)
    - 60s total timeout
    - Logs estimated cost + actual usage to stderr per call

GET /api/health
  Response 200: {"status": "ok", "anthropic_key_set": true|false, "model": "claude-haiku-4-5"}
```

The `/api/parse` and `/api/metrics` endpoints from earlier brainstorming are **not** built — combined into one endpoint since the metrics are pure-function-cheap and there's no benefit to splitting in the stateless model.

### CORS

Dev: backend listens on `:8000`, frontend dev server on `:3000`. The `next.config.js` rewrites `/api/*` → `http://localhost:8000/api/*`, so CORS is bypassed entirely (same-origin from the browser's perspective). Production deployment is out of scope for 4a.

### Parser flow inside `/api/parse-and-compute`

```
1. extract.py:
   - Sniff MIME / extension:
     - .xlsx           → openpyxl.load_workbook(data_only=True) → list[(sheet_name, list[list[cell]])]
                          For multi-sheet files (Zerodha format with Equity / Mutual Funds / Combined sheets):
                          prefer the "Combined" sheet if present; otherwise pass all sheets to the LLM
                          (the prompt's rules tell it to dedupe by ISIN+name)
     - .xls            → first peek bytes; if HTML markers ("<html") → BeautifulSoup → text+tables;
                          else → xlrd (pre-2007 binary xls)
     - .pdf            → pdfplumber → page-by-page text + tables
     - .png/.jpg/.jpeg → return binary; the LLM call uses Anthropic's vision input directly
   - Returns: ExtractedContent dataclass with `kind: "tables" | "text" | "image"` + payload
   - Raises ExtractError(message) on file corruption / unreadable input

2. normalize.py:
   - Build prompt from prompts/normalize.txt (string.Template, like Task 3):
     - $extracted_content (formatted as text — tables become "Sheet: X\nRow: [...]" strings)
     - $canonical_schema_json (the Pydantic schema rendered as a JSON-Schema string)
   - Pre-flight cost guard:
     - Count tokens via anthropic.Anthropic().messages.count_tokens(...)
     - If > MAX_INPUT_TOKENS (30_000): truncate input + add parser_warning("input truncated")
     - Estimate cost; log to stderr; check daily-budget cache
   - Call Anthropic:
     - For text/tables: messages.create(model="claude-haiku-4-5", max_tokens=4096,
                                         messages=[{"role":"user","content":prompt}])
     - For images: messages.create with image content blocks (base64-encoded)
   - Parse the response:
     - Strip ```json fences (defensive, like Task 3)
     - json.loads → Pydantic.NormalizedHoldings.model_validate(data)
   - On ValidationError:
     - Log the validation errors
     - Append validation errors to a fresh prompt; call Anthropic ONCE more
     - On second failure: raise NormalizationError(attempts=[raw1, raw2], errors=[err1, err2])
   - Log actual cost from response.usage; update daily-budget cache
   - Return NormalizedHoldings

3. metrics/compute.py:
   - Pure functions — no LLM, no I/O, deterministic
   - kpis(NormalizedHoldings) → KPIs
   - allocation(NormalizedHoldings) → list[AllocationSlice]
   - xirr_by_fund(NormalizedHoldings) → list[XirrEntry] (sorted desc, capped at 20 entries for chart readability)
   - category_performance(NormalizedHoldings) → list[CategoryPerformance]
   - For overall_xirr if missing: compute from cashflows using scipy.optimize.brentq
     (assume single-investment-date for MVP; multi-cashflow XIRR needs purchase history we don't have)
```

### Normalizer prompt (`backend/prompts/normalize.txt`)

```
You are a financial data extraction system. Convert the following holdings statement into the
canonical JSON schema below. Output ONLY valid JSON — no markdown, no fences, no preamble.

<extracted_content>
$extracted_content
</extracted_content>

<canonical_schema>
$canonical_schema_json
</canonical_schema>

<rules>
- Extract every asset row (mutual fund or stock).
- For asset_type: "mutual_fund" if name contains "Fund"/"Plan"/"Scheme"; "stock" if it looks
  like an NSE/BSE symbol (all-caps, no spaces); "etf" if name contains "ETF"; otherwise "other".
- For category: map to one of {"Equity","Debt","Hybrid","Commodities"} based on the row's
  category column, sub-category, or scheme name. If unclear, use null.
- For sub_category: pass through the statement's sub-category text (e.g. "Flexi Cap", "Gilt").
- For pnl_inr: if the statement provides P&L, use it; else compute (current_value - invested_value).
- For pnl_pct: if provided, use it; else compute (pnl / invested * 100).
- Do NOT compute XIRR — pass it through if the statement provides one, else null.
- If the source has multiple sheets (e.g. Zerodha's Equity + Mutual Funds + Combined), prefer
  the Combined sheet. If multiple sheets are passed, dedupe by (isin, name) — emit each unique
  asset only once.
- For source_format: classify as "groww_xlsx" if you see Groww-style columns, "camsonline_mhtml"
  if HTML table structure with category-grouped headers, "zerodha_console" if multi-sheet
  Equity/MF/Combined layout, otherwise "unknown".
- For holder_name: extract from the statement header if present.
- For statement_date: extract any "as on" date if present (ISO format).
- All currency values MUST be in INR as floats (no commas, no rupee symbols).
- If a field is genuinely absent in the source, use null — do NOT guess.
</rules>

<example_minimal_output>
{
  "holder_name": "Bhavana Jagadeesh",
  "source_format": "camsonline_mhtml",
  "summary": {
    "total_invested_inr": 4149792.26,
    "total_current_inr": 4481646.82,
    "total_pnl_inr": 331854.56,
    "total_pnl_pct": 8.00,
    "overall_xirr_pct": 4.71,
    "asset_count": 12,
    "statement_date": "2026-03-19"
  },
  "assets": [
    {
      "name": "Parag Parikh Flexi Cap Fund Direct Plan Growth",
      "asset_type": "mutual_fund",
      "isin": null,
      "amc": "PPFAS Mutual Fund",
      "category": "Equity",
      "sub_category": "Flexi Cap",
      "folio": "13959825",
      "units": 8547.228,
      "invested_value_inr": 624968.74,
      "current_value_inr": 763913.63,
      "xirr_pct": 10.22,
      "pnl_inr": 138944.89,
      "pnl_pct": 22.23
    }
  ],
  "parser_warnings": []
}
</example_minimal_output>
```

## Frontend

### Pages

- `/` — landing page. Hero with timecell-style typography ("Drop your holdings statement"), file dropzone, supported formats line. On successful upload → `router.push("/dashboard")`.
- `/dashboard` — Overview tab (default). Renders KPIs + donut + XIRR bar + category cards.
- `/dashboard/holdings`, `/dashboard/market`, `/dashboard/rebalance` — stubs.

### Layout — `app/dashboard/layout.tsx`

```
┌───────────────────────────────────────────────────────────────────┐
│ ▢ TIMECELL                            Bhavana Jagadeesh   ₹44.8L  │
│                                       Portfolio Intelligence Report│
│                                                +₹3.31L  (+8.00%)  │
├───────────────────────────────────────────────────────────────────┤
│  Overview │ Holdings │ Market │ Rebalance                          │
│  ━━━━━━━━━                                                         │
└───────────────────────────────────────────────────────────────────┘
                       (children render below)
```

Header bar uses Geist Mono uppercase for "TIMECELL" + tab labels, Fraunces serif for the holder name. Total ₹ uses Geist Mono with tabular-numerals. Active tab indicator is a 1px brass underline.

### Overview tab — `/dashboard/page.tsx`

Layout matches mockup image 1's content arrangement, restyled with the Ledger palette:

```
[ KPI grid — 4 cards, equal width, Geist Mono numerals, Fraunces labels ]
  INVESTED        CURRENT          EQUITY              DEBT
  ₹41,49,792      ₹44,81,647       64.2%               35.8%
  12 schemes      XIRR 4.71%       ₹28,75,766          ₹16,06,270

[ Two-column row (1fr 2fr on desktop, stacked on mobile) ]
  ┌──────────────────┐  ┌──────────────────────────────────────────┐
  │  ALLOCATION      │  │  XIRR BY FUND                            │
  │  (donut)         │  │  (horizontal bar chart, sorted desc)     │
  │  ₹44.8L center   │  │  positive bars: brass                    │
  │  Brass legend    │  │  negative bars: oxblood                  │
  │                  │  │  truncate fund names at 24 chars         │
  └──────────────────┘  └──────────────────────────────────────────┘

[ CATEGORY PERFORMANCE — grid of cards, one per category present ]
  Each card: category name (Fraunces) | P&L (Geist Mono) | CAGR (Geist Mono)
  Border color: brass if positive P&L, oxblood if negative
```

### Stub tab UX — `components/StubTab.tsx`

For `/dashboard/holdings`, `/dashboard/market`, `/dashboard/rebalance`:

```
        [ centered card with rule border ]
        ┌─────────────────────────────────────┐
        │  ⊘  COMING IN TASK 4{b|c}            │
        │                                      │
        │  This tab will [one-line description]│
        │                                      │
        │  Holdings:   per-fund stock breakdown│
        │  Market:     Nifty trend + news      │
        │  Rebalance:  Anthropic agent loop    │
        └─────────────────────────────────────┘
```

Uses `--rule` border, `--muted-deep` text. Lock icon from Lucide. Card sits centered in viewport with ~40vh top padding so it doesn't look broken.

### Landing page upload flow

```
1. User drops file → FileUpload.tsx triggers POST /api/parse-and-compute
2. UI shows progress phases:
   - "Reading statement..."          (extract.py phase)
   - "Analysing with Claude..."      (Haiku call)
   - "Computing metrics..."          (compute.py)
3. Backend response → Zustand store.setPortfolio({normalized, kpis, allocation, ...})
4. router.push("/dashboard") → Overview renders
5. If error → toast (sonner) with the error message + "Try again" button
6. If user navigates to /dashboard with empty store → redirect to "/"
```

Progress phases are estimates — the backend doesn't stream phase events in 4a (would need SSE; YAGNI for one upload). The frontend cycles through phases on a fixed schedule (1.5s each) and the API returns when ready.

## Cost guardrails

Three layers in `backend/parser/normalize.py`:

### 1. Hard input ceiling

```python
MAX_INPUT_TOKENS = 30_000   # ~$0.04 max per parse at Haiku rates
```

Before the Anthropic call, count tokens on the extracted content via `count_tokens`. If above ceiling: truncate to first 30K tokens, append `parser_warning("input truncated — file unusually large; some assets may be missing")`. This is a defense against pathological uploads (a corrupt 50MB file shouldn't drain budget).

### 2. Per-call cost logging

Always log to stderr around each Anthropic call:

```
[parser] estimated cost: $0.024 (input: 8200 tokens, max output: 4096 tokens, model: claude-haiku-4-5)
[parser] actual cost:    $0.018 (input: 8200 tokens, output: 1240 tokens, total: 9440)
```

Cumulative session total ticks up in a module-level counter; logged at process exit:

```
[parser] session total: $0.142 across 8 parses
```

### 3. Daily ceiling via env var

```python
MAX_DAILY_LLM_USD = float(os.environ.get("MAX_DAILY_LLM_USD", "2.00"))   # default $2/day
# Set to "disabled" to opt out (useful for dev / CI)
```

Track per-day total in `~/.cache/timecell-task4/usage-YYYY-MM-DD.json` (atomic-rename writes). If `today_total + this_call_estimate > MAX_DAILY_LLM_USD`: refuse with HTTP 429.

These guardrails apply to the parser only. The agentic rebalancer in 4b will need its own (and a higher ceiling, since Sonnet calls cost more).

## Error handling

| Failure mode | HTTP | Body | Frontend toast |
|---|---|---|---|
| No file in upload | 400 | `{"error": "no file provided"}` | "Pick a file to upload." |
| File > 10 MB | 413 | `{"error": "file too large", "max_mb": 10}` | "File too large (max 10 MB)." |
| Unsupported MIME | 415 | `{"error": "unsupported file type", "supported": [...]}` | "Can't read this file type." |
| Extract failure (corrupt) | 422 | `{"error": "could not extract structured data", "detail": "..."}` | "File seems corrupted." |
| Anthropic timeout/5xx | 502 | `{"error": "LLM service unavailable", "detail": "..."}` | "AI service is down. Try again in a minute." |
| LLM JSON invalid x2 | 502 | `{"error": "could not normalize statement after retry", "raw_attempts": [...]}` | "Couldn't understand this statement format." |
| Daily budget exhausted | 429 | `{"error": "daily LLM budget exhausted"}` | "Daily AI budget reached." |
| Per-asset Pydantic validation fails | 200 | Asset omitted from `assets[]`, `parser_warnings.append(...)` | Warning shown in a small "Parser notes" expander on Overview |

**No silent degradation.** Either it's a known failure with a clear message, or it propagates to a 500 with the stack trace logged.

**No `try/except: pass` anywhere** — same as the Task 3 discipline.

## Testing

### Backend (`backend/tests/`)

Run: `cd task4_open/backend && pytest -v`. Stdlib `assert`, no pytest fixtures beyond `tmp_path`.

- `test_extract.py` — for each of the 3 sample files in `backend/samples/`, call `extract.py` and assert it returns non-empty content and doesn't raise. **No LLM, no network.**
- `test_normalize.py` — mocks `anthropic.Anthropic.messages.create` with canned JSON responses:
  - Happy path → returns valid `NormalizedHoldings`
  - First call returns invalid JSON, second returns valid → uses retry path, returns
  - Both calls return invalid JSON → raises `NormalizationError`
  - Token-count over `MAX_INPUT_TOKENS` → input is truncated, `parser_warnings` includes the truncation message
  - Daily budget cache is over `MAX_DAILY_LLM_USD` → raises `BudgetExhausted`
- `test_metrics.py` — pure-function tests with hand-built `NormalizedHoldings` fixtures:
  - Allocation percentages sum to 100 ± 0.01
  - Equity/debt split correct for a mixed portfolio
  - XIRR fallback returns sensible value when statement-provided XIRR is None
  - Empty portfolio returns zeros without crashing

### Frontend (`frontend/__tests__/` + `frontend/e2e/`)

Run: `cd task4_open/frontend && npm test` (Vitest), `npm run test:e2e` (Playwright).

- **Vitest + RTL component tests:**
  - `KpiCard` — renders label + value with correct color class for positive/negative
  - `formatINR` — `1,00,00,000` for `10000000`, handles negatives, handles zero
  - `AllocationDonut` — renders with sample slices, total in center
  - `XirrBarChart` — bars colored brass for positive, oxblood for negative
- **Playwright smoke test (gated, not on every save):**
  - Upload `samples/holdings-EEM619.xlsx` → see Overview tab render with non-zero KPIs

### Manual acceptance (end of 4a)

1. `make -C task4_open dev` starts backend (`:8000`) + frontend (`:3000`) in parallel
2. Open `http://localhost:3000` → see upload widget styled with timecell.ai's Ledger palette
3. Drop each of the 3 sample files in turn → Overview tab renders for each. KPIs match the file's headline numbers within ±1% rounding.
4. Drop a clearly-bad file (e.g. `echo "not a holdings file" > bad.xlsx`) → see clear error toast, app does not crash
5. Click each tab (Holdings, Market, Rebalance) → see "Coming in 4b/4c" stub card
6. Refresh the page → returns to upload screen (stateless verified)
7. Inspect stderr logs → see one `[parser] estimated cost:` and one `[parser] actual cost:` line per upload
8. `cat ~/.cache/timecell-task4/usage-*.json` → see today's accumulated cost as a JSON number

## Acceptance criteria (must all pass for 4a to ship)

- All backend pytest tests pass
- All frontend Vitest tests pass
- Playwright smoke test passes against `make dev` stack
- Manual acceptance steps 1-8 above all pass
- A grader can clone the repo, run `make -C task4_open install && make -C task4_open dev`, drop any of the 3 sample files, and see the Overview tab render with correct numbers
- Total LLM spend during full acceptance run is < $0.50 (verified via stderr log)

## What's deferred to 4b / 4c

- **4b — Market tab:** Nifty 50 trend (yfinance, pattern from Task 2), market news (NewsAPI free tier, MoneyControl RSS, or Anthropic web search tool — decided in 4b's brainstorm)
- **4b — Rebalance tab:** Anthropic agent loop (Sonnet 4.6) with tools: get_portfolio_metrics, get_nifty_trend, get_news_summary. Streams the agent's reasoning + tool calls + final recommendations to the frontend.
- **4c — Holdings tab:** Per-fund drilldown showing top 10 stock holdings (data sourced from AMFI monthly disclosures, keyed on ISIN)
- **4c — Fund-overlap matrix:** Pairwise overlap heatmap from mockup image 2, plus the gilt-fund redundancy callout

## Implementation notes

- The `claude-api` skill must be invoked at implementation Task 1 to confirm `claude-haiku-4-5` is still the current Haiku model ID (parallel to Task 3's Sonnet confirmation).
- The Pydantic v2 syntax (`model_validate`, `BaseModel`, `Field`) is required — this is a fresh codebase, so no v1 baggage.
- The `samples/` directory contains the 3 sample holdings files — copy from `task4_open/` (where they currently sit) into `task4_open/backend/samples/`.
- The 3 sample holdings files in `task4_open/` are real personal financial documents (with real names, PANs, phone numbers, and client IDs from the user's family/friends). **Decision: redact before committing** (the repo is public on GitHub and git history is permanent). The implementation plan's Task 1 must perform the redaction in-place on copies moved into `backend/samples/`, replacing:
  - Holder names → `Test User A`, `Test User B`, `Test User C` (distinct per file so tests can assert which sample produced which output)
  - PAN numbers → `AAAAA1234A`, `BBBBB1234B`, `CCCCC1234C` (matches `[A-Z]{5}[0-9]{4}[A-Z]` PAN format so any validation code stays happy)
  - Phone numbers → `9999999999`
  - Zerodha Client ID `EEM619` → `TEST01`
  - All folio numbers and demat account refs → leave as-is (they're meaningless without the PAN/name pairing)
  
  Numeric values (units, invested, current, P&L, XIRR) are NOT redacted — they're the actual test data and changing them would invalidate the acceptance criteria's "KPIs match the file's headline numbers within ±1% rounding" check. The original files stay only on the user's local machine (the implementation plan must add them to `.gitignore` if they're not already covered).
