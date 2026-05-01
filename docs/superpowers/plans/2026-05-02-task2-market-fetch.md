# Task 2 — Live Market Data Fetch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `task2_market/fetch_prices.py` that fetches live prices for NIFTY50, RELIANCE, and BTC from yfinance + CoinGecko, displays them in a `rich` table, degrades gracefully on per-asset failures, caches results to a 60s-TTL JSON file, and exits with code 1 if any fetch failed.

**Architecture:** Flat `task2_market/` module — no package, no `__init__.py`, run as scripts. `fetch_prices.py` holds: imports → constants → `PriceResult` dataclass → cache helpers → fetcher functions → `render_price_table` → `main` → `__main__` block. `test_fetch_prices.py` sits next to it as a sibling import. Cache lives at the `main()` layer; fetchers stay pure (matches spec's required signatures). Tests are added incrementally TDD-style; commits are batched into the two approved commits per the design.

**Tech Stack:** Python 3.10+, `yfinance>=0.2.40`, `requests>=2.31.0`, `rich>=13.7.0`. `unittest.mock` (stdlib) for tests. No pytest.

**Spec:** [docs/superpowers/specs/2026-05-02-task2-market-design.md](../specs/2026-05-02-task2-market-design.md)

---

## Task 1: Create feature branch, append deps, update `.gitignore`, install

**Files:**
- Modify: `requirements.txt` (currently empty)
- Modify: `.gitignore`

- [ ] **Step 1: Verify clean main, create feature branch**

```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak
git status
git log --oneline | head -3
git checkout -b task2/market-fetch
```

Expected: `git status` clean (only untracked `.DS_Store`). `git log` shows merge commit `c2f5231` on top. Branch switch succeeds.

- [ ] **Step 2: Append dependencies to `requirements.txt`**

Replace the empty `requirements.txt` with:

```
yfinance>=0.2.40
requests>=2.31.0
rich>=13.7.0
```

- [ ] **Step 3: Append cache-file pattern to `.gitignore`**

Append one line to the existing `.gitignore` (so it becomes 5 lines total):

```
.venv/
__pycache__/
.env
*.pyc
task2_market/.price_cache*
```

- [ ] **Step 4: Activate venv and install**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: pip downloads and installs yfinance + requests + rich (and their transitive deps like pandas, numpy, certifi). No errors.

- [ ] **Step 5: Verify imports work**

```bash
python -c "import yfinance; import requests; import rich; print('imports OK')"
```

Expected: `imports OK`.

---

## Task 2: Bootstrap `fetch_prices.py` skeleton + first failing test

**Files:**
- Create: `task2_market/fetch_prices.py`
- Create: `task2_market/test_fetch_prices.py`

- [ ] **Step 1: Create `fetch_prices.py` with imports, constants, dataclass, `_now_ist` helper, and stub fetchers/main**

```python
"""Fetch live market prices from yfinance and CoinGecko, with 60s cache."""
from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yfinance as yf
from rich.console import Console
from rich.table import Table


COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3/simple/price"
REQUEST_TIMEOUT_SECONDS = 10
IST = ZoneInfo("Asia/Kolkata")
CACHE_FILE = Path(__file__).parent / ".price_cache.json"
CACHE_TTL_SECONDS = 60

ASSETS_TO_FETCH = [
    {"source": "yfinance",  "ticker": "^NSEI",       "name": "NIFTY50",  "currency": "INR"},
    {"source": "yfinance",  "ticker": "RELIANCE.NS", "name": "RELIANCE", "currency": "INR"},
    {"source": "coingecko", "ticker": "bitcoin",     "name": "BTC",      "currency": "USD"},
]


@dataclass
class PriceResult:
    name: str
    price: float | None
    currency: str
    timestamp: datetime
    error: str | None = None


def _now_ist() -> datetime:
    return datetime.now(IST)


def fetch_yfinance_price(
    ticker: str, display_name: str, currency: str
) -> PriceResult:
    """Stub — full implementation in Task 3."""
    raise NotImplementedError("see Task 3")
```

- [ ] **Step 2: Create `test_fetch_prices.py` with imports and the first failing test**

```python
"""Tests for task2_market.fetch_prices — error paths + cache, no live network."""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock

import requests

sys.path.insert(0, str(Path(__file__).parent))
from fetch_prices import (
    IST,
    fetch_yfinance_price,
)


def test_yfinance_empty_dataframe() -> None:
    mock_ticker = Mock()
    mock_ticker.history.return_value = Mock(empty=True)
    with patch("fetch_prices.yf.Ticker", return_value=mock_ticker):
        result = fetch_yfinance_price("^NSEI", "NIFTY50", "INR")
    assert result.price is None, f"expected None, got {result.price}"
    assert "no data" in result.error.lower(), \
        f"error should mention 'no data', got {result.error!r}"


if __name__ == "__main__":
    test_yfinance_empty_dataframe()
    print("All tests passed")
```

- [ ] **Step 3: Run test, verify it fails with `NotImplementedError`**

```bash
python task2_market/test_fetch_prices.py
```

Expected: traceback ending with `NotImplementedError: see Task 3`.

---

## Task 3: Implement `fetch_yfinance_price`

**Files:**
- Modify: `task2_market/fetch_prices.py`

- [ ] **Step 1: Replace the stub with the full implementation**

Replace the entire `fetch_yfinance_price` function body with:

```python
def fetch_yfinance_price(
    ticker: str, display_name: str, currency: str
) -> PriceResult:
    logging.info(f"fetching {display_name} from yfinance ({ticker})")
    try:
        df = yf.Ticker(ticker).history(period="1d")
        if df.empty:
            return PriceResult(
                name=display_name,
                price=None,
                currency=currency,
                timestamp=_now_ist(),
                error="no data returned for ticker",
            )
        price = float(df["Close"].iloc[-1])
        return PriceResult(
            name=display_name,
            price=price,
            currency=currency,
            timestamp=_now_ist(),
        )
    except Exception as e:
        logging.warning(
            f"{display_name}: yfinance fetch failed", exc_info=True
        )
        return PriceResult(
            name=display_name,
            price=None,
            currency=currency,
            timestamp=_now_ist(),
            error=str(e),
        )
```

- [ ] **Step 2: Run test, verify it passes**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed`.

---

## Task 4: Add yfinance-exception test (verifies `except Exception` branch)

**Files:**
- Modify: `task2_market/test_fetch_prices.py`

- [ ] **Step 1: Add `test_yfinance_raises_exception` before the runner block**

Insert after `test_yfinance_empty_dataframe` and before `if __name__ == "__main__":`:

```python
def test_yfinance_raises_exception() -> None:
    with patch(
        "fetch_prices.yf.Ticker",
        side_effect=Exception("simulated network failure"),
    ):
        result = fetch_yfinance_price("^NSEI", "NIFTY50", "INR")
    assert result.price is None, f"expected None, got {result.price}"
    assert result.error, f"error should be set, got {result.error!r}"
```

Update the runner:

```python
if __name__ == "__main__":
    test_yfinance_empty_dataframe()
    test_yfinance_raises_exception()
    print("All tests passed")
```

- [ ] **Step 2: Run and verify both tests pass**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed`.

---

## Task 5: Add CoinGecko request-exception test + stub `fetch_coingecko_price`

**Files:**
- Modify: `task2_market/fetch_prices.py`
- Modify: `task2_market/test_fetch_prices.py`

- [ ] **Step 1: Append a stub `fetch_coingecko_price` to `fetch_prices.py`**

Add after `fetch_yfinance_price`:

```python
def fetch_coingecko_price(
    coin_id: str, display_name: str, vs_currency: str = "usd"
) -> PriceResult:
    """Stub — full implementation in Task 6."""
    raise NotImplementedError("see Task 6")
```

- [ ] **Step 2: Add `fetch_coingecko_price` to the test imports**

Replace the `from fetch_prices import (...)` block with:

```python
from fetch_prices import (
    IST,
    fetch_yfinance_price,
    fetch_coingecko_price,
)
```

- [ ] **Step 3: Add `test_coingecko_request_exception` before the runner**

```python
def test_coingecko_request_exception() -> None:
    with patch(
        "fetch_prices.requests.get",
        side_effect=requests.RequestException("connection refused"),
    ):
        result = fetch_coingecko_price("bitcoin", "BTC", "usd")
    assert result.price is None, f"expected None, got {result.price}"
    assert result.error, f"error should be set, got {result.error!r}"
```

Add to runner: `test_coingecko_request_exception()`.

- [ ] **Step 4: Run, verify failure with `NotImplementedError`**

```bash
python task2_market/test_fetch_prices.py
```

Expected: traceback ending with `NotImplementedError: see Task 6`.

---

## Task 6: Implement `fetch_coingecko_price`

**Files:**
- Modify: `task2_market/fetch_prices.py`

- [ ] **Step 1: Replace the stub with the full implementation**

```python
def fetch_coingecko_price(
    coin_id: str, display_name: str, vs_currency: str = "usd"
) -> PriceResult:
    logging.info(
        f"fetching {display_name} from coingecko ({coin_id}/{vs_currency})"
    )
    try:
        resp = requests.get(
            COINGECKO_BASE_URL,
            params={"ids": coin_id, "vs_currencies": vs_currency},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        payload = resp.json()
        price = float(payload[coin_id][vs_currency])
        return PriceResult(
            name=display_name,
            price=price,
            currency=vs_currency.upper(),
            timestamp=_now_ist(),
        )
    except (requests.RequestException, KeyError, ValueError) as e:
        logging.warning(
            f"{display_name}: coingecko fetch failed", exc_info=True
        )
        return PriceResult(
            name=display_name,
            price=None,
            currency=vs_currency.upper(),
            timestamp=_now_ist(),
            error=str(e),
        )
```

- [ ] **Step 2: Run, verify all 3 tests pass**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed`.

---

## Task 7: Add CoinGecko schema and timeout tests (verify existing behavior)

**Files:**
- Modify: `task2_market/test_fetch_prices.py`

- [ ] **Step 1: Add two tests before the runner block**

```python
def test_coingecko_bad_schema() -> None:
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"unexpected": "shape"}
    with patch("fetch_prices.requests.get", return_value=mock_resp):
        result = fetch_coingecko_price("bitcoin", "BTC", "usd")
    assert result.price is None, f"expected None, got {result.price}"
    assert result.error, f"error should be set, got {result.error!r}"


def test_coingecko_timeout_is_set() -> None:
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"bitcoin": {"usd": 60000.0}}
    with patch("fetch_prices.requests.get", return_value=mock_resp) as mock_get:
        fetch_coingecko_price("bitcoin", "BTC", "usd")
    assert mock_get.call_args.kwargs["timeout"] == 10, \
        f"timeout should be 10, got {mock_get.call_args.kwargs.get('timeout')}"
```

Add to runner: `test_coingecko_bad_schema()` and `test_coingecko_timeout_is_set()`.

- [ ] **Step 2: Run, verify all 5 tests pass**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed`.

---

## Task 8: Add cache-fresh-hit test + stub `_cache_lookup`

**Files:**
- Modify: `task2_market/fetch_prices.py`
- Modify: `task2_market/test_fetch_prices.py`

- [ ] **Step 1: Append a stub `_cache_lookup` and `_load_cache` to `fetch_prices.py`**

Insert immediately after the `_now_ist` helper (and before `fetch_yfinance_price`):

```python
def _load_cache() -> dict:
    """Stub — full implementation in Task 12."""
    return {}


def _cache_lookup(cache: dict, name: str) -> PriceResult | None:
    """Stub — full implementation in Task 9."""
    raise NotImplementedError("see Task 9")
```

- [ ] **Step 2: Add `_cache_lookup` and `_load_cache` to the test imports**

Replace the `from fetch_prices import (...)` block with:

```python
from fetch_prices import (
    IST,
    fetch_yfinance_price,
    fetch_coingecko_price,
    _cache_lookup,
    _load_cache,
)
```

- [ ] **Step 3: Add `test_cache_lookup_fresh_hit` before the runner**

```python
def test_cache_lookup_fresh_hit() -> None:
    fresh_time = datetime.now(IST) - timedelta(seconds=10)
    cache = {
        "BTC": {
            "price": 60000.0,
            "currency": "USD",
            "fetched_at": fresh_time.isoformat(),
        }
    }
    result = _cache_lookup(cache, "BTC")
    assert result is not None, "expected fresh hit, got None"
    assert result.price == 60000.0, f"expected 60000.0, got {result.price}"
```

Add to runner: `test_cache_lookup_fresh_hit()`.

- [ ] **Step 4: Run, verify failure with `NotImplementedError`**

```bash
python task2_market/test_fetch_prices.py
```

Expected: traceback ending with `NotImplementedError: see Task 9`.

---

## Task 9: Implement `_cache_lookup`

**Files:**
- Modify: `task2_market/fetch_prices.py`

- [ ] **Step 1: Replace the stub `_cache_lookup` with the real implementation**

```python
def _cache_lookup(cache: dict, name: str) -> PriceResult | None:
    entry = cache.get(name)
    if not entry:
        return None
    fetched_at = datetime.fromisoformat(entry["fetched_at"])
    age = (datetime.now(IST) - fetched_at).total_seconds()
    if age > CACHE_TTL_SECONDS:
        return None
    return PriceResult(
        name=name,
        price=entry["price"],
        currency=entry["currency"],
        timestamp=fetched_at,
    )
```

- [ ] **Step 2: Run, verify 6 tests pass**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed`.

---

## Task 10: Add cache-stale-miss test (verifies the age check)

**Files:**
- Modify: `task2_market/test_fetch_prices.py`

- [ ] **Step 1: Add `test_cache_lookup_stale_miss` before the runner**

```python
def test_cache_lookup_stale_miss() -> None:
    stale_time = datetime.now(IST) - timedelta(seconds=120)
    cache = {
        "BTC": {
            "price": 60000.0,
            "currency": "USD",
            "fetched_at": stale_time.isoformat(),
        }
    }
    result = _cache_lookup(cache, "BTC")
    assert result is None, f"expected None for stale entry, got {result}"
```

Add to runner: `test_cache_lookup_stale_miss()`.

- [ ] **Step 2: Run, verify all 7 tests pass**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed`.

---

## Task 11: Add corrupted-cache test (drives full `_load_cache` implementation)

**Files:**
- Modify: `task2_market/test_fetch_prices.py`

- [ ] **Step 1: Add `test_load_cache_corrupted_returns_empty` before the runner**

```python
def test_load_cache_corrupted_returns_empty() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        f.write("not valid json {{{")
        tmp_path = Path(f.name)
    try:
        with patch("fetch_prices.CACHE_FILE", tmp_path):
            result = _load_cache()
        assert result == {}, f"expected empty dict, got {result}"
    finally:
        tmp_path.unlink()
```

Add to runner: `test_load_cache_corrupted_returns_empty()`.

- [ ] **Step 2: Run, verify the test passes**

The current stub `_load_cache` already returns `{}` unconditionally, so the test passes by accident. We'll fix that in Task 12 with the real implementation.

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed` (8 tests).

---

## Task 12: Implement real `_load_cache` and `_save_cache`

**Files:**
- Modify: `task2_market/fetch_prices.py`

- [ ] **Step 1: Replace the stub `_load_cache` with the real implementation**

```python
def _load_cache() -> dict:
    """Return cache dict, or {} on missing/corrupted file."""
    try:
        with CACHE_FILE.open() as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
```

- [ ] **Step 2: Append `_save_cache` after `_cache_lookup`**

```python
def _save_cache(cache: dict) -> None:
    """Atomic write via temp + rename."""
    tmp = CACHE_FILE.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(cache, f, indent=2)
    tmp.replace(CACHE_FILE)
```

- [ ] **Step 3: Run all 8 tests, verify pass**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed`.

---

## Task 13: Implement `render_price_table`

**Files:**
- Modify: `task2_market/fetch_prices.py`

(No new test — visual output is brittle to unit-test; manual verification in Task 15 covers it.)

- [ ] **Step 1: Append `render_price_table` after the fetcher functions**

```python
def render_price_table(results: list[PriceResult]) -> None:
    console = Console()
    ts = next(
        (r.timestamp for r in results if r.error is None),
        _now_ist(),
    )
    header = f"Asset Prices — fetched at {ts.strftime('%Y-%m-%d %H:%M:%S')} IST"

    table = Table(title=header)
    table.add_column("Asset")
    table.add_column("Price", justify="right")
    table.add_column("Currency")

    for r in results:
        if r.error is None:
            price_cell = f"{r.price:,.2f}"
        else:
            price_cell = "[red]FETCH FAILED[/red]"
        table.add_row(r.name, price_cell, r.currency)

    console.print(table)
```

- [ ] **Step 2: Sanity-check by rendering a fake result list from a one-liner**

```bash
python -c "
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, 'task2_market')
from fetch_prices import PriceResult, render_price_table
ts = datetime.now(ZoneInfo('Asia/Kolkata'))
render_price_table([
    PriceResult('NIFTY50', 22541.80, 'INR', ts),
    PriceResult('RELIANCE', None, 'INR', ts, error='simulated'),
    PriceResult('BTC', 62341.20, 'USD', ts),
])
"
```

Expected: a 3-row table prints with NIFTY50 + BTC showing prices and RELIANCE showing red `FETCH FAILED`. Header line shows the timestamp.

---

## Task 14: Implement `main()`

**Files:**
- Modify: `task2_market/fetch_prices.py`

- [ ] **Step 1: Append `main()` and the `__main__` block at the end of the file**

```python
def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    start = time.monotonic()
    cache = _load_cache()

    results: list[PriceResult] = []
    for asset in ASSETS_TO_FETCH:
        hit = _cache_lookup(cache, asset["name"])
        if hit is not None:
            age = (datetime.now(IST) - hit.timestamp).total_seconds()
            logging.info(
                f"using cached {asset['name']} ({age:.0f}s old)"
            )
            results.append(hit)
            continue
        if asset["source"] == "yfinance":
            r = fetch_yfinance_price(
                asset["ticker"], asset["name"], asset["currency"]
            )
        elif asset["source"] == "coingecko":
            r = fetch_coingecko_price(
                asset["ticker"], asset["name"], asset["currency"].lower()
            )
        else:
            logging.error(
                f"unknown source in ASSETS_TO_FETCH: {asset['source']!r} "
                f"(asset name={asset['name']!r}). "
                f"Code bug — fix the config or add a fetcher."
            )
            raise ValueError(f"unknown source: {asset['source']}")
        results.append(r)

    for r in results:
        if r.error is None:
            cache[r.name] = {
                "price": r.price,
                "currency": r.currency,
                "fetched_at": r.timestamp.isoformat(),
            }
    _save_cache(cache)

    render_price_table(results)

    elapsed = time.monotonic() - start
    logging.info(f"fetched {len(results)} assets in {elapsed:.2f}s")

    if any(r.error for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Re-run the test suite to confirm nothing regressed**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed` (8 tests).

---

## Task 15: End-to-end manual verification

**Files:** none changed.

- [ ] **Step 1: Remove any pre-existing cache, run live**

```bash
rm -f task2_market/.price_cache.json
python task2_market/fetch_prices.py
echo "exit code: $?"
```

Expected: 3 INFO log lines (one per asset), then a `rich` table with 3 real-data rows. Exit code 0 (assuming all 3 APIs are reachable).

- [ ] **Step 2: Re-run within 60s and confirm cache hits**

```bash
python task2_market/fetch_prices.py
echo "exit code: $?"
```

Expected: 3 INFO log lines reading `using cached NIFTY50 (Xs old)`, etc. The table renders the same prices with the original fetch timestamp in the header. Exit code 0.

- [ ] **Step 3: Verify the cache file exists and is well-formed**

```bash
cat task2_market/.price_cache.json
```

Expected: a JSON dict with keys `NIFTY50`, `RELIANCE`, `BTC`, each containing `price`, `currency`, `fetched_at`.

- [ ] **Step 4: Test a bad-ticker failure mode (one asset fails, others continue)**

Edit `task2_market/fetch_prices.py` ASSETS_TO_FETCH: change `"^NSEI"` to `"^NOTAREALTICKER"`. Then:

```bash
rm task2_market/.price_cache.json
python task2_market/fetch_prices.py
echo "exit code: $?"
```

Expected: NIFTY50 row shows `FETCH FAILED` (red); RELIANCE + BTC rows show prices. WARNING log line for NIFTY50. Exit code 1 (bonus 4).

- [ ] **Step 5: Revert the bad-ticker change**

Restore `"^NSEI"` in ASSETS_TO_FETCH.

```bash
git diff task2_market/fetch_prices.py
```

Expected: empty diff (file restored to previous state).

- [ ] **Step 6: Run tests one final time**

```bash
python task2_market/test_fetch_prices.py
```

Expected: `All tests passed`.

---

## Task 16: Commit code + tests + requirements + .gitignore

**Files:**
- Add: `task2_market/fetch_prices.py`, `task2_market/test_fetch_prices.py`
- Stage modified: `requirements.txt`, `.gitignore`

- [ ] **Step 1: Verify the cache file is not staged (gitignored correctly)**

```bash
git status
```

Expected: `task2_market/.price_cache.json` does NOT appear under untracked (because `.gitignore` excludes it). Untracked: `.DS_Store` (intentionally not staged) and the two new task2_market source files. Modified: `.gitignore`, `requirements.txt`.

- [ ] **Step 2: Stage explicitly (do not use `git add .`)**

```bash
git add task2_market/fetch_prices.py task2_market/test_fetch_prices.py requirements.txt .gitignore
git status
```

Expected: only the four listed files appear under "Changes to be committed".

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
task2: implement live market data fetcher with cache and mocked tests

Adds task2_market/fetch_prices.py — fetches NIFTY50 + RELIANCE from yfinance
and BTC from CoinGecko, displays a rich table, degrades gracefully on
per-asset failures, caches successful results to .price_cache.json with a
60s TTL, and exits with code 1 if any fetch failed (bonus 4).

Adds task2_market/test_fetch_prices.py with 8 plain-assert tests covering
yfinance/coingecko error paths and cache-helper edge cases (mocked, no
live network).

Appends yfinance + requests + rich to requirements.txt and adds the cache
file pattern to .gitignore.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -3
```

Expected: commit succeeds; new commit on top of `c2f5231`.

---

## Task 17: Write `task2_market/README.md` and update root `README.md`

**Files:**
- Create: `task2_market/README.md`
- Modify: `README.md`

- [ ] **Step 1: Create `task2_market/README.md`**

```markdown
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

[Filled in retrospectively after implementation — what Claude Code helped with.]
```

- [ ] **Step 2: Update the Task 2 line in the root `README.md`**

Replace the line `- Task 2 — Live Market Data Fetch (TBD)` with:

```markdown
- [Task 2 — Live Market Data Fetch](task2_market/README.md)
```

(No other root README changes — the AI-tooling section already covers Task 2 since it's a project-wide note.)

- [ ] **Step 3: Skim both files**

```bash
cat task2_market/README.md
echo "---"
cat README.md
```

Expected: both render cleanly with no broken Markdown.

---

## Task 18: Commit READMEs

**Files:**
- Add: `task2_market/README.md`
- Modify: `README.md`

- [ ] **Step 1: Stage and commit**

```bash
git add task2_market/README.md README.md
git status
git commit -m "$(cat <<'EOF'
task2: add per-task README and update root README link

Adds task2_market/README.md (summary, run instructions, manual acceptance
tests, design notes, placeholder AI-usage section) and updates the Task 2
entry in the root README from "(TBD)" to a link to the per-task README.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -4
```

Expected: two commits on the branch ahead of `c2f5231`.

---

## Task 19: Fill in AI-usage notes and amend

**Files:**
- Modify: `task2_market/README.md` (replace the AI-usage placeholder)

- [ ] **Step 1: Replace the per-task AI-usage placeholder**

Replace the placeholder paragraph in `task2_market/README.md` with a real, honest summary of what Claude Code helped with during Task 2 (e.g., "Used Claude Code to design the cache schema and the at-`main()`-layer placement of cache logic so fetchers stayed pure; the bool-exclusion guard was reused conceptually from Task 1 but didn't apply here. Claude Code also surfaced the `raise_for_status()` failure mode where 4xx/5xx responses would otherwise produce a confusing `KeyError` on the JSON access."). Keep it 2-4 sentences.

- [ ] **Step 2: Amend the README commit**

```bash
git add task2_market/README.md
git commit --amend --no-edit
git log --oneline | head -4
```

Expected: still two commits ahead of `c2f5231`; the README commit is updated in place.

- [ ] **Step 3: Stop and ask the user**

Per the workflow rule (CLAUDE.md Part 1, item 2), do NOT push or open the PR unprompted. Surface to the user:

> "Implementation complete on branch `task2/market-fetch`. Two commits ahead of `main`: code+tests+requirements+gitignore, then READMEs. All 8 mocked tests pass; `python task2_market/fetch_prices.py` prints the rich table; bad-ticker manual test produced expected `FETCH FAILED` row + exit code 1; cache hits work on re-run. Ready to push and open a PR for review?"

Wait for explicit user approval before running `git push -u origin task2/market-fetch` or `gh pr create`.

---

## Self-review

**1. Spec coverage:**

| Spec section | Task |
|---|---|
| §1 file layout (`fetch_prices.py`, `test_fetch_prices.py`, README, requirements, .gitignore) | Tasks 1, 2, 16, 17 |
| §1 module top-to-bottom order (constants → dataclass → cache → fetchers → render → main) | Tasks 2, 8, 12, 13, 14 |
| §2 cache helpers (`_load_cache`, `_cache_lookup`, `_save_cache`, atomic write, schema, gitignored) | Tasks 8, 9, 12, plus Task 1 for `.gitignore` |
| §3 fetcher functions (yfinance `except Exception`, coingecko narrow except, vs_currency casing, raise_for_status, per-asset timestamp) | Tasks 3, 6 |
| §4 `main()` orchestration (cache lookup → dispatch → save → render → elapsed log → exit code) | Task 14 |
| §4 unknown-source crashes with `logging.error` then `raise ValueError` | Task 14 step 1 |
| §5 flow diagrams | (Documentation in spec — no code task; reviewer reads the spec) |
| §6 `render_price_table` (`Table(title=...)`, right-justified Price, inline `[red]` markup, header from first successful timestamp) | Task 13 |
| §7 8 tests + plain-assert + sibling import + runner block | Tasks 2, 4, 5, 7, 8, 10, 11 |
| §8 branching, two commits | Tasks 1, 16, 18 |
| §8 verification commands (live run, cache-hit re-run, test suite, bad-ticker manual test, fresh `pip install`) | Task 15 |
| §8 out-of-scope (bonuses 2 + 3, live happy-path tests, other tasks) | Honored — no related code touched |
| Workflow rule: ask before push/PR | Task 19 step 3 |

No gaps.

**2. Placeholder scan:** The `[Filled in retrospectively...]` string in Task 17 is intentionally a placeholder for README *content*, replaced in Task 19 step 1. No `TBD`/`TODO`/`add appropriate X` patterns in the plan.

**3. Type/name consistency:**
- `PriceResult` dataclass fields: `name`, `price: float | None`, `currency`, `timestamp: datetime`, `error: str | None = None` — used identically across Tasks 2-14.
- Function signatures: `fetch_yfinance_price(ticker, display_name, currency)`, `fetch_coingecko_price(coin_id, display_name, vs_currency="usd")`, `_cache_lookup(cache, name)`, `_load_cache()`, `_save_cache(cache)`, `render_price_table(results)`, `main()`. Match across all references.
- Module constants: `COINGECKO_BASE_URL`, `REQUEST_TIMEOUT_SECONDS`, `IST`, `CACHE_FILE`, `CACHE_TTL_SECONDS`, `ASSETS_TO_FETCH`. Defined in Task 2, referenced in Tasks 3, 6, 9, 11, 12, 14.
- Test names match the spec's table verbatim. Runner block has a corresponding entry for every test added.

No inconsistencies.
