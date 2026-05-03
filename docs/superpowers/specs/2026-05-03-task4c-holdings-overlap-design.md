# Task 4c — Holdings + Fund-Overlap Design

Adds the Holdings tab to the Task 4a dashboard. Two stacked sections: a per-fund detail table (sortable, expandable to show each fund's underlying stocks) and a fund-overlap matrix heatmap with drill-down into shared stocks. Both sourced from a committed snapshot of AMFI's monthly portfolio disclosures.

**Built on top of:** Task 4a backend (`task4_open/backend/{main,parser,metrics}/...`) + Task 4b agent loop infrastructure + Task 4a frontend shell. Replaces the existing `<StubTab task="4c">`. No backend rewrite — additive only.

---

## Goals

1. Holdings tab renders a sortable per-fund table; each row expands inline to show that fund's top-10 underlying stocks plus cash %.
2. Fund-overlap matrix renders as a triangular heatmap; clicking any cell populates a right-hand drill-down panel showing the shared stocks with weights in each fund.
3. Underlying data sourced from a committed JSON bundle (`data/amfi_holdings.json`) built by a one-shot refresh script. No hot-path network. No LLM calls.
4. Top 20 AMC adapters cover ~95% of MF AUM; uncovered funds degrade gracefully (`match=none` badge, excluded from matrix).
5. ISIN-first matching with a fuzzy-name fallback so portfolios without ISINs still produce useful output.

Non-goals: background scheduler, write-back, historical overlap, sector/market-cap drill-down, fund-replacement suggestions, international ETF / REIT / gold ETF coverage.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser  /dashboard/holdings                                    │
│  ┌──────────────────────────────┐  ┌─────────────────────────┐   │
│  │ Holdings table               │  │ Overlap heatmap         │   │
│  │  - sortable rows             │  │  - upper triangle       │   │
│  │  - click row → expands to    │  │  - click cell → right   │   │
│  │    show underlying stocks    │  │    panel: shared stocks │   │
│  └──────────────┬───────────────┘  └─────────┬───────────────┘   │
│                 │ POST /api/holdings/per-fund │ POST /api/holdings/overlap │
└─────────────────┼────────────────────────────┼───────────────────┘
                  ▼                            ▼
┌──────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                               │
│  ┌────────────────────────────┐  ┌──────────────────────────┐    │
│  │ amfi/                      │  │ holdings/                │    │
│  │  bundle.py — JSON loader   │  │  match.py — ISIN +       │    │
│  │  schema.py — Scheme types  │  │   fuzzy name lookup      │    │
│  │                            │  │  overlap.py — symmetric  │    │
│  │ data/amfi_holdings.json    │  │    weighted overlap math │    │
│  │  (committed, ~5–15 MB)     │  │                          │    │
│  └────────────────────────────┘  └──────────────────────────┘    │
│                                                                  │
│  scripts/refresh_amfi.py — one-shot run by maintainer            │
│   1. fetch ZIP from amfiindia.com                                │
│   2. unzip per-AMC files                                         │
│   3. dispatch to top-20 per-AMC adapters                         │
│   4. emit normalized data/amfi_holdings.json                     │
│   5. emit data/amfi_coverage.md (which schemes parsed/failed)    │
└──────────────────────────────────────────────────────────────────┘
```

**Module boundaries:**

- `task4_open/backend/amfi/` — owns the bundle: load on startup, look up by ISIN, attempt fuzzy fallback. Pure data layer.
- `task4_open/backend/holdings/` — owns the analytic layer: compute overlap math, build per-fund payloads. Pure functions over the AMFI bundle + user holdings.
- `task4_open/backend/scripts/refresh_amfi.py` — standalone CLI run by maintainer/cron, NOT imported by the FastAPI app. Per-AMC parser modules under `scripts/amfi_adapters/{hdfc,icici,nippon,…}.py`. Each adapter is independent and testable in isolation.
- `task4_open/backend/main.py` — adds two endpoints; existing routes unchanged.
- `task4_open/frontend/app/dashboard/holdings/page.tsx` — replaces the stub.
- `task4_open/frontend/components/{HoldingsTable,HoldingExpandedRow,OverlapHeatmap,OverlapDrilldown,MatchBadge}.tsx` — new.
- `task4_open/frontend/lib/store.ts` — adds `holdingsData` + `overlapData` (NOT in `partialize` — reproducible from the user's holdings).
- `task4_open/frontend/lib/api.ts` — adds `fetchHoldingsPerFund()` and `fetchOverlap()` plus types.

**No LLM calls.** Pure parsing + math + UI. The committed bundle means reviewers see the matrix work without any external network access.

---

## Backend — AMFI bundle + parser pipeline

### Bundle file format

`task4_open/backend/data/amfi_holdings.json` (committed, ~5–15 MB):

```json
{
  "version": 1,
  "as_of_month": "2026-04",
  "fetched_at": "2026-05-03T12:00:00Z",
  "schemes": [
    {
      "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Growth",
      "isin": "INF879O01027",
      "amc": "PPFAS",
      "scheme_aum_inr": 87543210000,
      "as_of_date": "2026-04-30",
      "holdings": [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 8.42, "value_inr": 7372000000, "kind": "equity"},
        {"name": "Bajaj Holdings", "isin": "INE118A01012", "weight_pct": 7.10, "value_inr": 6215000000, "kind": "equity"}
      ],
      "cash_pct": 4.20
    }
  ]
}
```

Two indexes built on backend startup (in-memory, never serialized):
- `by_isin: dict[str, Scheme]` — keyed by `scheme.isin`
- `by_normalized_name: dict[str, Scheme]` — keyed by normalized `scheme.scheme_name` (see normalization rules in the matching section)

### Refresh script

`task4_open/backend/scripts/refresh_amfi.py`:

```
1. Discover the latest disclosure URL from
   https://www.amfiindia.com/research-information/other-data/monthly-portfolio-disclosure
   (scrape the page once, find the most recent ZIP/landing link).
2. Download the ZIP (or per-AMC files); cache raw inputs to scripts/cache/<month>/
   so re-runs don't re-fetch.
3. For each per-AMC file: detect AMC from filename, dispatch to
   scripts/amfi_adapters/<amc>.py (see contract below).
4. Aggregate, dedup by ISIN (last write wins), sort by AMC then scheme_name.
5. Emit data/amfi_holdings.json + data/amfi_coverage.md (which AMCs/schemes
   parsed, which failed, why).
6. Print a summary: "23 AMCs parsed, 1842 schemes, 18.3 MB JSON, 4 AMCs failed"
```

The script is invoked via `make refresh-amfi`. It is NOT imported by the FastAPI app, NOT in the test suite's hot path (one integration test stubs the network), and NOT auto-run on dev startup.

### Per-AMC adapter contract

Each `scripts/amfi_adapters/<name>.py` exports one function:

```python
def parse(file_path: Path) -> list[Scheme]:
    """Read a single AMC's monthly disclosure file and return its schemes.

    Adapters are independent. Failures are logged + skipped, not fatal.
    """
```

V1 covers 20 adapters: HDFC, ICICI Pru, Nippon, SBI, Aditya Birla, Kotak, Axis, UTI, DSP, Mirae, Tata, Edelweiss, PPFAS, Quant, Motilal Oswal, Invesco, Bandhan, Franklin Templeton, HSBC, Sundaram. AMCs outside this list are skipped during refresh; their funds will appear in user portfolios with `match=none`.

### Bundle loader

`task4_open/backend/amfi/bundle.py`:

```python
def load_bundle() -> AmfiBundle:
    """Read data/amfi_holdings.json, build by_isin + by_normalized_name indexes.

    Raises BundleMissing if the file does not exist.
    Raises BundleMalformed if JSON is invalid or schema version is unknown.
    """

def normalize_scheme_name(name: str) -> str:
    """Lowercase, strip plan/idcw/growth qualifiers, collapse whitespace."""
```

Bundle is loaded once on FastAPI startup (lazy: first request triggers load) and held in a module-level singleton. A `reload_bundle()` helper exists for tests + a future `/api/admin/reload-bundle` if needed (out of scope for v1).

---

## Backend — matching + overlap math

### Matching (`task4_open/backend/holdings/match.py`)

```python
def match_user_funds(
    user_assets: list[Asset], bundle: AmfiBundle,
) -> list[FundMatch]:
    """For each user asset, return one FundMatch:
    (asset_name, asset_isin, matched: bool, scheme: Scheme | None,
     matched_by: 'isin' | 'name' | 'none', confidence: float [0..1])."""
```

Algorithm per asset:

1. **ISIN lookup.** If `asset.isin` is non-null and in `by_isin`, return `(matched=True, scheme=…, matched_by="isin", confidence=1.0)`.
2. **Normalized name exact lookup.** Normalize `asset.name` (rules below); look up in `by_normalized_name`. Exact match → `(matched=True, scheme=…, matched_by="name", confidence=0.95)`.
3. **Fuzzy name match.** `rapidfuzz.fuzz.token_set_ratio(normalized_user_name, normalized_scheme_name) / 100` against every scheme in the same AMC (if `asset.amc` is non-null) or all schemes otherwise. Best score ≥ 0.85 wins → `(matched=True, scheme=…, matched_by="name", confidence=score)`. Below 0.85 → `(matched=False, scheme=None, matched_by="none", confidence=0.0)`.

**Normalization rules** (`normalize_scheme_name`):
- Lowercase
- Strip parenthesized qualifiers: `(direct)`, `(growth)`, `(g)`, `(idcw)`
- Strip suffixes: `- direct plan`, `- direct growth`, `- growth`, `- regular`, `- dividend`, `- idcw`, `- d`
- Strip plan codes (e.g., `(plan a)`)
- Collapse whitespace
- Remove punctuation except `&` and digits

### Overlap math (`task4_open/backend/holdings/overlap.py`)

Industry-standard symmetric weighted overlap:

```python
def pairwise_overlap(scheme_a: Scheme, scheme_b: Scheme) -> OverlapPair:
    """overlap_pct = sum_over_shared_stocks(min(weight_in_a, weight_in_b))

    Stocks are matched by ISIN; if either side's ISIN is null, fall back to
    normalized stock name comparison. Returns:
      - overlap_pct: float in [0, 100]
      - shared_stocks: list of {name, isin, weight_a, weight_b, min_weight}
        sorted by min_weight descending
    """
```

Properties:
- Symmetric: `overlap(A,B) == overlap(B,A)` ✓
- Range: 0% (disjoint) to ~100% (identical)
- Self-overlap: `overlap(A,A) ≈ 95–100%` (rest is cash) — heatmap renders the diagonal muted

### Per-fund payload (`POST /api/holdings/per-fund`)

Request body: `{"holdings": NormalizedHoldings}`

Response:
```json
{
  "matches": [
    {
      "asset_name": "Parag Parikh Flexi Cap Fund",
      "asset_isin": "INF879O01027",
      "matched": true,
      "matched_by": "isin",
      "confidence": 1.0,
      "scheme": {
        "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Growth",
        "as_of_date": "2026-04-30",
        "holdings": [{"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 8.42, "value_inr": 7372000000, "kind": "equity"}],
        "cash_pct": 4.20
      }
    }
  ]
}
```

### Overlap payload (`POST /api/holdings/overlap`)

Request body: `{"holdings": NormalizedHoldings}`

Response:
```json
{
  "funds": [
    {"asset_name": "Parag Parikh Flexi Cap", "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Growth", "matched_by": "isin"},
    {"asset_name": "ICICI Pru Gilt Fund", "scheme_name": null, "matched_by": "none"}
  ],
  "matrix": [
    [
      {"i": 0, "j": 0, "overlap_pct": 95.8, "shared_count": 92},
      {"i": 0, "j": 1, "overlap_pct": 0.0, "shared_count": 0}
    ]
  ],
  "shared_stocks_index": {
    "0_2": [
      {"name": "HDFC Bank", "isin": "INE040A01034", "weight_a": 8.42, "weight_b": 6.10, "min": 6.10}
    ]
  }
}
```

The shared-stocks per pair is emitted upfront in `shared_stocks_index` (keyed by `"i_j"`, `i < j`) so the drill-down renders without another round-trip. Unmatched funds (`matched_by: "none"`) are EXCLUDED from the matrix and the index — the frontend lists them separately.

`matrix` is the full N×N (`matrix[i][j]` cell exists for every `i, j ∈ [0, N)`); since `pairwise_overlap` is symmetric, `matrix[i][j].overlap_pct == matrix[j][i].overlap_pct` and the diagonal cells equal `~95–100%` (cash subtracted). The frontend renders only the upper triangle (`j > i`) from this. The `shared_stocks_index` is emitted only for `i < j` (one entry per unordered pair).

Both endpoints take the user's `NormalizedHoldings` in the POST body — no statement re-upload, no parse re-run.

---

## Frontend — Holdings tab

### Page layout

`task4_open/frontend/app/dashboard/holdings/page.tsx`:

Two stacked sections, separated by the dashboard's existing mono section divider.

```
┌──────────────────────────────────────────────────────────────────┐
│  Your funds                                       ↻ Reload data  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Fund                  Cat   Value      %      Return  Match │ │
│  │ ▼ Parag Parikh Flexi  Eq  ₹14,50,000  35%  +14.32%   ISIN  │ │
│  │   ┌─────────────────────────────────────────────────────┐   │ │
│  │   │ Top holdings (snapshot 2026-04-30):                 │   │ │
│  │   │   HDFC Bank          8.42%   ₹1,22,090            │   │ │
│  │   │   Bajaj Holdings     7.10%   ₹1,02,950            │   │ │
│  │   │   ITC                5.81%     ₹84,225            │   │ │
│  │   │   ... (top 10)              [show all 92]           │   │ │
│  │   │   Cash & equiv:      4.20%                          │   │ │
│  │   └─────────────────────────────────────────────────────┘   │ │
│  │ ▶ ICICI Pru Gilt Fund Debt ₹70,166    17%   +4.10%   none  │ │
│  │ ▶ Quant Active Fund   Eq  ₹2,15,000   5%   +18.50%   name  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ─────────────────────────────────────────                       │
│                                                                  │
│  Fund overlap                                                    │
│  ┌────────────────────────────────┐  ┌─────────────────────────┐ │
│  │       PPFAS  Gilt  Quant  ...  │  │ Shared stocks           │ │
│  │ PPFAS  ███   ░░░   ▓▓▓         │  │ (PPFAS ↔ Quant)         │ │
│  │ Gilt   ░     ███   ░           │  │                         │ │
│  │ Quant  ▓     ░     ███         │  │ HDFC Bank               │ │
│  │ ...                            │  │   PPFAS: 8.4%           │ │
│  │                                │  │   Quant: 5.1% (min 5.1) │ │
│  │ click any cell to drill down → │  │ Reliance Industries     │ │
│  │                                │  │   PPFAS: 6.0%           │ │
│  │ Match legend:                  │  │   Quant: 4.2% (min 4.2) │ │
│  │ ░ <10%  ▓ 10-30%  █ 30%+       │  │                         │ │
│  └────────────────────────────────┘  └─────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Components (5 new)

- **`HoldingsTable.tsx`** — renders the per-fund rows. Each row clickable to expand. Sortable on click (Value, %, Return, Match). Match column shows a small mono badge: `ISIN` (brass), `name` (brass-soft), `none` (oxblood).
- **`HoldingExpandedRow.tsx`** — expanded inline panel showing top-10 holdings + "show all" toggle + cash %.
- **`OverlapHeatmap.tsx`** — CSS grid of cells (one `<button>` per upper-triangle pair). Background opacity scaled to `overlap_pct`. Click → updates parent state.
- **`OverlapDrilldown.tsx`** — right-hand panel; shows shared-stock list for the selected pair. Empty state: "Click a cell to see shared stocks." Each row: stock name, weight in A, weight in B, min weight. Sorted by min weight descending.
- **`MatchBadge.tsx`** — tiny shared component for the `ISIN`/`name`/`none` chip used in both the table and the heatmap legend.

### Frontend store additions

`task4_open/frontend/lib/store.ts`:

```typescript
interface PortfolioState {
  // existing fields unchanged
  holdingsData: HoldingsResponse | null
  overlapData: OverlapResponse | null
  setHoldingsData: (h: HoldingsResponse | null) => void
  setOverlapData: (o: OverlapResponse | null) => void
}
```

Both NOT in `partialize` — reproducible from the user's holdings by hitting the deterministic backend endpoints, no need to bloat localStorage. Auto-fetched on page mount; manual `↻ Reload data` if the user wants a fresh response.

### API client

`task4_open/frontend/lib/api.ts`:

```typescript
export interface FundHolding { name: string; isin: string | null; weight_pct: number; value_inr: number; kind: string }
export interface AmfiScheme { scheme_name: string; as_of_date: string; holdings: FundHolding[]; cash_pct: number }
export interface FundMatch { asset_name: string; asset_isin: string | null; matched: boolean; matched_by: 'isin' | 'name' | 'none'; confidence: number; scheme: AmfiScheme | null }
export interface HoldingsResponse { matches: FundMatch[] }

export interface OverlapCell { i: number; j: number; overlap_pct: number; shared_count: number }
export interface OverlapFund { asset_name: string; scheme_name: string | null; matched_by: 'isin' | 'name' | 'none' }
export interface SharedStock { name: string; isin: string | null; weight_a: number; weight_b: number; min: number }
export interface OverlapResponse { funds: OverlapFund[]; matrix: OverlapCell[][]; shared_stocks_index: Record<string, SharedStock[]> }

export function fetchHoldingsPerFund(holdings: NormalizedHoldings): Promise<HoldingsResponse>
export function fetchOverlap(holdings: NormalizedHoldings): Promise<OverlapResponse>
```

Both POST through the `/api/*` Next.js proxy (these endpoints return small JSON in <1s; no need for the direct-backend bypass that `/api/rebalance` uses).

### Empty / error states

- **No funds matched at all**: render the table with all `match=none` rows + a one-line notice "Couldn't match any funds to AMFI bundle. Refresh script may need to run, or your holdings file may have unusual fund names."
- **Some matched, some didn't**: matrix only shows matched funds; unmatched funds listed separately in a collapsed `<details>` block below the heatmap with "(N funds excluded)".
- **Backend 503 (bundle missing)**: page-level notice with the `make refresh-amfi` command + toast.
- **Backend 500/network**: existing toast pattern.

---

## Cost guardrails

None — Task 4c is pure code with zero LLM calls. The only "cost" is the one-time AMFI fetch (free, ~80 MB raw → 5–15 MB JSON) when the maintainer runs `make refresh-amfi`. The refresh script is gated behind a make target so a casual reviewer running tests doesn't hit AMFI.

The existing daily-LLM-budget cap (shared with the parser + rebalance agent) is unaffected.

---

## Error handling

| Failure | HTTP | Frontend behavior |
|---|---|---|
| `data/amfi_holdings.json` missing | `503` "bundle missing — run `make refresh-amfi`" | Toast + page-level notice with the command |
| Bundle malformed JSON | `503` "bundle malformed — re-run `make refresh-amfi`" (logged + bundle cleared on next read) | Same page-level notice |
| User has 0 funds matched | `200` with `funds: []` matrix | Page shows "no funds matched" notice |
| Heatmap pair has 0 shared stocks | `200`, drill-down shows "no overlap" | Drilldown empty state |
| Single AMC adapter fails during refresh | logged + skipped + recorded in `coverage.md` | n/a (refresh-time only) |
| AMFI ZIP fetch fails during refresh | refresh script exits non-zero with error | n/a (refresh-time only) |

---

## Testing

### Backend (pytest) — 29 new tests

| File | Tests | Notes |
|---|---|---|
| `tests/test_amfi_match.py` | 5: ISIN exact hit, normalized name hit, fuzzy match above threshold, fuzzy below threshold returns none, unknown AMC scoped fuzzy across all schemes | Hand-built `Scheme` fixtures, no bundle dep |
| `tests/test_holdings_overlap.py` | 5: identical funds → ~100%, disjoint funds → 0%, partial overlap math, ISIN-keyed match within funds, name-keyed fallback within funds | |
| `tests/test_amfi_bundle.py` | 3: load bundle, build by_isin index, build by_normalized_name index | Tiny fixture JSON |
| `tests/test_amfi_adapters/test_<amc>.py` × 20 | 1 each: `parse(fixture_file) -> [Scheme(...)]` shape | Each adapter gets a small redacted real fixture committed to `tests/fixtures/amfi/<amc>.{xlsx,xls,pdf}` |
| `tests/test_main.py` | +3: `POST /api/holdings/per-fund` happy + `POST /api/holdings/overlap` happy + 503 when bundle missing | |
| `tests/test_refresh_script.py` | 1 integration: stub network + dispatch through 3 mock adapters → assert merged JSON shape + coverage report | No real AMFI fetch in CI |

### Frontend (Vitest + RTL) — 8 new tests

| File | Tests |
|---|---|
| `__tests__/HoldingsTable.test.tsx` | 3: renders rows, expand toggles inline panel, sort by Value descending |
| `__tests__/OverlapHeatmap.test.tsx` | 2: renders upper-triangle cells, click cell fires onSelect with (i, j) |
| `__tests__/OverlapDrilldown.test.tsx` | 2: empty state, populated state with shared stocks sorted by min weight |
| `__tests__/MatchBadge.test.tsx` | 1: renders correct label for isin/name/none |

**Project totals:** 77 backend → 106; 34 frontend → 42.

### Live verification (manual)

1. Run `make refresh-amfi` → completes in ~1–3 min, emits `data/amfi_holdings.json` ~5–15 MB and `data/amfi_coverage.md` listing parsed/skipped AMCs.
2. `POST /api/holdings/per-fund` against `sample_groww.xlsx`-derived holdings → response has matched + unmatched fund mix; matched funds carry holdings list.
3. `POST /api/holdings/overlap` → matrix includes only matched funds; `shared_stocks_index` populated for non-zero pairs.
4. Browser walkthrough: Holdings tab → per-fund table renders with badges → click row → expanded panel shows top-10 stocks → heatmap renders below → click cell → drill-down panel populates.

---

## New backend dependencies

Added to `task4_open/backend/requirements.txt`:

- `rapidfuzz>=3.10` — fuzzy name matching. ~1.5 MB wheel, BSD-3, pure-C Levenshtein.
- `xlrd>=2.0.1` — reading legacy `.xls` (some AMCs file in xls; openpyxl handles only xlsx).

`pdfplumber`, `openpyxl`, `requests`, `httpx` — already in deps from earlier tasks, reusable for PDF AMC adapters and the refresh script.

---

## Performance

- `/api/holdings/per-fund`: O(N_assets × log N_schemes) for ISIN lookup + O(N_assets × N_schemes_in_amc) for fuzzy fallback. Bundle has ~1800 schemes; user portfolios have ~10–30 funds. <100 ms warm cache.
- `/api/holdings/overlap`: O(N²) pairwise overlap computations, each O(M) over shared stocks. With N=15 and M=100: 105 pairs × ~100 stocks each ≈ 10K ops. <50 ms.
- Bundle load on FastAPI startup: ~200 ms for a 10 MB JSON. One-time, lazy.
- No client-side payload >50 KB.

---

## Migration / rollout

No DB, no auth, no schema migrations. The two new endpoints are additive — old clients see no behavior change. The frontend store gains two new fields with default `null`; existing persisted state under `timecell-portfolio-v1` continues to work unchanged because the new fields are not in `partialize`. The Holdings tab goes from "Coming in Task 4c" stub to live.

The committed `data/amfi_holdings.json` ships with the repo. A reviewer who pulls and runs `make backend-dev frontend-dev` sees the matrix work immediately without running the refresh script.

---

## Decomposition note

Task 4c is one cohesive feature (holdings + overlap) but has clean commit boundaries should the implementation surface unexpected complexity:

1. AMFI bundle loader + match
2. Overlap math + endpoints (per-fund + overlap)
3. Refresh script + 20 per-AMC adapters
4. Frontend Holdings table + expanded-row component
5. Frontend overlap heatmap + drilldown components
6. Final user gate (no push, no PR)
