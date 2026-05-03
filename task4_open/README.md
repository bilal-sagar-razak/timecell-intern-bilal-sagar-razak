# Task 4 — Portfolio Intelligence Dashboard

A FastAPI + Next.js webapp that takes any mutual-fund or stock holdings statement (Groww xlsx,
Camsonline MHTML, Zerodha multi-sheet xlsx, PDFs, even screenshots) and renders a portfolio
overview. Built incrementally across three sub-tasks:

| Sub-task | Status | Tab(s) added |
|---|---|---|
| **4a** | shipped | Shell + parser + Overview |
| **4b** | shipped | Market + Rebalance (Anthropic agent loop) |
| **4c** | shipped | Holdings + Fund-overlap matrix |

## What 4a ships

- Webapp shell (Next.js + FastAPI) with timecell.ai's Ledger theme
- LLM-normalized parser: any uploaded file → Anthropic Haiku 4.5 → canonical Pydantic schema
- Overview tab: KPI cards + allocation donut + XIRR-by-fund bar chart + category-performance cards
- Three other tabs stubbed with "Coming in 4b/4c" placeholders
- Three layers of cost guardrails on the parser (token cap, cost log, daily budget ceiling)
- Stateless single-user demo — no DB, no auth

## Setup + run

Requires Python 3.10+ (the repo venv is 3.9 with `eval_type_backport`), Node 20+, and
`ANTHROPIC_API_KEY` in `.env` at the repo root.

```bash
make -C task4_open install         # Python deps + npm packages + Playwright Chromium
make -C task4_open dev             # backend on :8000, frontend on :3000
```

Then open http://localhost:3000, drop one of `task4_open/backend/samples/*.xlsx` on the
dropzone, and the Overview tab renders.

## Testing

```bash
make -C task4_open test            # backend (32 pytest) + frontend (19 Vitest)
make -C task4_open test-e2e        # Playwright smoke (requires both servers running)
```

## Sample data

`backend/samples/` ships three redacted holdings statements covering the three most common Indian
broker formats. Names, PANs, phone numbers, and Client IDs are synthetic; numeric data is
preserved verbatim from real exports so end-to-end testing reflects realistic shapes.

| File | Format | Holder (synthetic) |
|---|---|---|
| `sample_groww.xlsx` | Groww xlsx (clean tabular) | Test User A |
| `sample_camsonline.xls` | Camsonline MHTML (HTML-disguised xls) | TEST USER B |
| `sample_zerodha.xlsx` | Zerodha Console (multi-sheet) | (uses Client ID `TEST01`) |

The original (PII-bearing) versions live in `task4_open/` itself and are gitignored — the
redacted copies in `backend/samples/` are what gets committed and what tests run against.

## Cost guardrails

The parser's three defenses against budget drain on the Anthropic API:

1. **30K input-token cap** — pathological uploads get truncated with a warning, not a runaway cost
2. **Per-call cost log to stderr** — `[parser] actual cost: $0.024 (input: 8200 tokens, output: 1240)`
3. **Daily budget ceiling** — env var `MAX_DAILY_LLM_USD` (default $2/day, opt out with `=disabled`),
   tracked atomically in `~/.cache/timecell-task4/usage-YYYY-MM-DD.json`

## Provider chosen + why

- **Parser:** Haiku 4.5 — structured JSON extraction is its sweet spot; 3-5× cheaper than Sonnet on
  this task with no measurable quality drop. The retry-on-validation-failure loop catches the rare
  malformed JSON without escalating to Sonnet.
- **Theme:** timecell.ai's Ledger palette — warm dark background, brass accents, Fraunces serif +
  Geist Mono labels.

## What didn't work (or got rejected during brainstorming)

- **Per-format parser registry** — three formats today, more tomorrow; doesn't fit the AI-task
  theme. LLM-normalization handles arbitrary formats including ones we've never seen, including
  PDFs and image screenshots.
- **Browser localStorage persistence** — adds UX complexity for marginal value in a graded demo.
  Stateless: refresh = re-upload.
- **Fund overlap analysis in 4a** — needs stock-level fund composition data (AMFI monthly
  disclosures), which is its own scraping/ingestion project. Deferred to 4c.

## AI tool usage

Built with Claude Code (Opus 4.7) following the `superpowers` chain
(`brainstorming` → `writing-plans` → `subagent-driven-development`). The
brainstorm scoped the project to three sub-tasks (4a/4b/4c) on a shared
webapp shell, locked in FastAPI + Next.js with timecell.ai's Ledger theme,
and chose LLM-normalization over a per-format parser registry — Claude
Haiku 4.5 handles arbitrary holding-statement formats including ones we've
never seen, with retry-on-validation-failure for the rare malformed JSON.

The `claude-api` skill was invoked at implementation time to confirm
`claude-haiku-4-5` as the current latest Haiku model ID. The timecell.ai
theme tokens (Ledger palette colors, Fraunces + Geist Mono fonts, the
ledger-paper backdrop with subtle radial brass glow and 48px rule lines)
were extracted live from the site's published CSS during spec-writing and
baked into `globals.css` (Tailwind v4's `@theme` block).

Three layers of cost guardrails on the parser were a brainstorm decision
specifically because the user has a $25 Anthropic budget shared across all
three sub-tasks: 30K input-token cap with truncation+warning, per-call
cost logging to stderr, and a daily-budget ceiling tracked atomically in a
JSON file under `~/.cache/timecell-task4/`.

The 51-test suite (32 backend pytest + 19 frontend Vitest) is
deterministic — Anthropic SDK is mocked everywhere; the only live calls
happen during the manual acceptance run against three real sample formats.

Two of the three substantive code units (LLM normalize.py + FastAPI main.py
+ Overview page assembly) were dispatched to fresh implementer subagents
with two-stage review (spec compliance, then code quality). The reviewers
caught a real cache-write-on-failure bug in `normalize.py` and a misleading
"daily change" label in the dashboard header that actually showed lifetime
P&L — both fixed before the work landed.

Sample data redaction (replacing real names/PANs/phone numbers/Client IDs
with synthetic values while preserving numeric data verbatim) was an
explicit decision recorded in the spec — the repo is public on GitHub so
PII committed once would persist in git history forever.

---

## What 4b ships — Market + Rebalance tabs

- **Market tab.** Nifty 50 trend chart (last 30 days, Recharts area) + a
  curated headline panel filtered to your portfolio (Google News RSS via
  `feedparser`, scored by your held tickers/sector keywords).
- **Rebalance tab.** A Claude Sonnet 4.6 agent loop — given your normalized
  holdings + a market snapshot, it iterates with three tools
  (`get_news_for_holding`, `get_nifty_context`, `get_holding_xirr`) until
  it produces a 3-suggestion rebalance plan. The full tool-call trace is
  rendered alongside the markdown advice for transparency, so the user can
  see *why* each suggestion was made (which headlines, which CAGR, which
  context tokens). Cost ≈$0.05 per run, cached server-side per holdings
  hash so re-renders are free.
- **Cache invalidation.** New file upload or `↻ Re-parse` wipes
  `marketSnapshot`, `rebalanceResult`, `holdingsData`, `overlapData` from
  the Zustand store so derived results never lag the underlying portfolio.

### What didn't work in 4b

- **Single-shot LLM rebalance prompt** (no tools, all market context
  jammed into the system prompt) — the model hallucinated returns and
  invented news headlines. The agent loop with tool grounding fixed both.
- **Filtering news by fund name** — most Indian mutual funds never appear
  by name in financial RSS. Updated `get_news_for_holding` to fall back
  through `name → sub_category → category`, returning a `matched_by`
  field so the agent knows when "no headlines" means "silent absence",
  not "opacity risk".
- **Next.js dev proxy** dropped the long-running rebalance call (~30s)
  with `ECONNRESET`. The frontend now bypasses the proxy and POSTs
  directly to `http://localhost:8000` for the agent endpoint; backend
  added explicit CORS for localhost:3000-3002.

---

## What 4c ships — Holdings + Fund-overlap matrix

- **Holdings tab leads with the matrix.** Symmetric weighted fund-overlap
  heatmap (CSS grid, brass-shaded by overlap percentage) + a right-hand
  drilldown panel listing the actual shared stocks when you click any
  cell. Below the matrix: a sortable per-fund table where each row
  expands inline to show the fund's underlying holdings.
- **Two-tier fund matching.** ISIN-first (1.0 confidence), then exact
  normalized scheme name (0.95), then fuzzy via
  `max(rapidfuzz.fuzz.ratio, fuzz.token_set_ratio) ≥ 0.85`. Tracked per
  fund as `matched_by ∈ {isin, name, none}` and surfaced as an inline
  badge so the user can see which funds were excluded from the matrix.
- **Symmetric weighted overlap math.** Per pair:
  `sum over shared stocks of min(weight_in_a, weight_in_b)`. Stocks are
  aligned by ISIN when present, normalized name otherwise. Output is a
  full N×N matrix (mirrored for symmetry) plus a `shared_stocks_index`
  keyed `"i_j"` for `i<j` only.
- **AMFI bundle.** 28-scheme committed seed at
  `backend/data/amfi_holdings.json` covers the AMCs that show up most in
  Indian retail portfolios (PPFAS, HDFC, ICICI Pru, SBI, Quant, Nippon,
  Bandhan, Tata, Motilal Oswal, Edelweiss, Kotak, Invesco, Canara Robeco).
  See `backend/data/amfi_coverage.md` for the full scheme list.
- **Refresh script** (`scripts/refresh_amfi.py`, invoked via
  `make refresh-amfi`) is wired up with 2 real per-AMC adapters (HDFC,
  ICICI Pru) + 18 placeholders. The `discover_and_fetch` step is
  intentionally a `NotImplementedError` stub for v1 — the maintainer
  downloads each AMC's monthly disclosure manually from
  https://www.amfiindia.com/online-center/portfolio-disclosure and
  points the script at the unpacked directory.

### Cost guardrails (zero LLM cost on 4c)

The Holdings tab makes **zero** LLM calls — everything is deterministic
parsing + math. No per-render cost. The matcher and overlap math run in
single-digit milliseconds against the in-process indexed bundle.

### What didn't work in 4c

- **Pure `fuzz.token_set_ratio`** (the plan's spec) failed the plan's own
  test for `"HDFC FlexiCap Fund Direct Plan"` matching `"HDFC Flexi Cap
  Fund - Direct Growth"` — 81 < 85 threshold. Combined with `fuzz.ratio`
  (which catches concatenated typos) the score jumps to 97. Documented
  divergence from the plan, all spec tests pass.
- **Native `title=""` tooltips** for full fund names on the heatmap labels
  — browser delay made the cursor-help affordance feel broken. Replaced
  with Tailwind `group`/`group-hover` CSS tooltips that appear instantly.
- **Auto-discovery of AMFI's monthly disclosure** ZIP — AMFI's site
  changes structure occasionally and there's no machine-readable feed.
  Punted to manual fetch + `make refresh-amfi` for v1; the per-AMC
  adapters are the actual interesting code.

## AI tool usage (4b + 4c)

Both sub-tasks followed the same `superpowers` chain
(`brainstorming` → `writing-plans` → `subagent-driven-development`)
described above for 4a, with the design + plan documents committed under
`docs/superpowers/specs/` and `docs/superpowers/plans/` respectively.

In **4b**, the highest-risk units (the agent loop, the trace renderer,
the rebalance markdown parser) were dispatched to fresh subagents with
two-stage spec + code-quality review. End-to-end browser testing
uncovered five production bugs that all required real-world fixes:
HTTP 502 from `tool_result.content` not being a string, missing tool
schema due to `**kwargs` wrapper, Next.js dev proxy `ECONNRESET` on
30s+ requests, broken markdown rendering of the agent's preamble +
trailer, and a race condition where double-clicking the rebalance
button burned $0.05 twice. All traced to root causes and fixed before
merge.

In **4c**, only two units went via subagent (the AMFI matcher's
fuzzy-ranking + ISIN-first ordering, and the overlap math + N×N matrix
builder) — the remaining 17 tasks are mechanical xlsx/JSON code that
stayed in the main session per the coalescing strategy. The committed
seed bundle started at 4 schemes and grew twice during live testing
against real portfolios — once to 19 schemes when a generic test
portfolio surfaced 16 unmatched funds, then again to 28 schemes when a
second test portfolio (Diya Bala) surfaced 7 more. Each expansion was a
JSON edit + a quick matcher sanity-check script, not a code change.
