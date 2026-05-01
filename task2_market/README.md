# Task 2 — Live Market Data Fetch

## Summary

`fetch_prices.py` pulls live prices for three assets — NIFTY50 (`^NSEI`) and
RELIANCE (`RELIANCE.NS`) via `yfinance`, and Bitcoin via the CoinGecko REST
API — and renders them as a `rich` table. Each asset is fetched in its own
try/except so one failing API never blocks the others, and successful results
are cached to a local JSON file with a 60-second TTL so repeated runs don't
hammer the upstream services.

## Run

```bash
pip install -r requirements.txt
python task2_market/fetch_prices.py        # rich table + INFO logs to stderr
python task2_market/test_fetch_prices.py   # 8 mocked tests

# To force fresh fetches (bypass cache):
rm task2_market/.price_cache.json
```

## Manual acceptance tests (per spec)

- **Bad ticker:** change `^NSEI` to `^NOTAREALTICKER` in `ASSETS_TO_FETCH`,
  re-run. The NIFTY50 row shows `FETCH FAILED` (red); the other rows still
  render with real prices. WARNING log appears. Exit code 1.
- **Offline:** disable wifi, re-run. All 3 rows show `FETCH FAILED`; WARNING
  logs for each; exit code 1.

## Design notes

- **`if/elif` dispatcher in `main()`** routes each asset config entry to the
  right fetcher (`fetch_yfinance_price` or `fetch_coingecko_price`). Adding a
  new asset is a one-line edit to `ASSETS_TO_FETCH`.
- **yfinance fetcher** uses `except Exception` because yfinance's exception
  surface is sprawling and version-dependent. CoinGecko's narrow except
  (`RequestException`, `KeyError`, `ValueError`) is precise because the
  `requests`/JSON exception surface is well-defined.
- **Logging** is configured in `main()` and goes to stderr only — no log
  file is written.
- **Cache** lives at `task2_market/.price_cache.json` (gitignored). Only
  successful fetches are cached; failures are never written. Cache-hit rows
  show the original fetch timestamp, so the table header reflects data
  freshness, not run time. Cache logic lives at the `main()` layer — fetcher
  functions stay pure.
- **Exit code 1** if any fetch failed (bonus 4) — useful for CI/cron
  integration. The table still prints first, then the script exits.

## AI tool usage

Built with Claude Code (Opus 4.7) using the `superpowers` skill chain:
`brainstorming` to lock the asset selection (NIFTY50 + RELIANCE + BTC,
chosen to exercise both index and individual-equity yfinance paths plus a
distinct CoinGecko source) and to design the cache schema with a flat
display-name keying and `.tmp + os.replace` atomic write; `writing-plans`
to produce a TDD task list with full code blocks and 5 mermaid flow
diagrams; `subagent-driven-development` to execute substantive units (each
fetcher, the cache helpers, `main()`, the READMEs) via fresh Sonnet
subagents while trivial mechanical edits (test additions, git ops, manual
verification) ran in the main session. Claude Code surfaced the
`raise_for_status()` failure mode that would otherwise produce a confusing
`KeyError` on JSON access, and the cache-at-`main()`-layer placement that
keeps fetchers pure (matching the spec's required signatures). The
committed design and plan documents (`docs/superpowers/specs/`,
`docs/superpowers/plans/`) capture the full reasoning trail.
