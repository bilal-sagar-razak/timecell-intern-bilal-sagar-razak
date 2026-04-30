# Task 2 — Live Market Data Fetch

## Role
You are implementing a market data fetcher in Python 3.10+ for the Timecell internship technical test. The script must fetch live prices from public, free APIs and render a clean terminal table — robust to one or more APIs failing.

## Objective
Build `fetch_prices.py` that fetches the current price of **at least 3 assets** (with at least one stock/index AND at least one cryptocurrency), prints a formatted table to the terminal, and handles failures gracefully without crashing.

## Required Asset Coverage
You must include all three categories. Pick one ticker from each:
- **Index or stock** (mandatory): NIFTY 50 (`^NSEI`), Sensex (`^BSESN`), or any NSE stock like `RELIANCE.NS`.
- **Cryptocurrency** (mandatory): BTC, ETH, or SOL via CoinGecko.
- **Third asset** (your choice): Gold (`GC=F` on yfinance), USD/INR (`INR=X`), or any other free-API-accessible asset.

## API Choices (use only these — all free, no key required)
| Asset Type | Library / Endpoint | Notes |
|---|---|---|
| Stocks/Indices | `yfinance` | `pip install yfinance`. Use `Ticker(symbol).history(period='1d')` and read the last `Close`. |
| Crypto | CoinGecko REST | `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd`. No key. Use `requests`. |
| Gold (alt) | `yfinance` `GC=F` | Returns USD/oz. Convert to INR/g if you want, but USD/oz is acceptable. |

Do NOT use Alpha Vantage, Twelve Data, or any service requiring a key — those add friction during grading.

## Required Output Format
Print a table that looks like this (use the `rich` library — `pip install rich`):

```
Asset Prices — fetched at 2026-04-30 14:32:15 IST
┌──────────┬──────────────┬──────────┐
│ Asset    │ Price        │ Currency │
├──────────┼──────────────┼──────────┤
│ BTC      │ 62,341.20    │ USD      │
│ NIFTY50  │ 22,541.80    │ INR      │
│ GOLD     │ 7,312.00     │ INR/g    │
└──────────┴──────────────┴──────────┘
```

If a fetch fails, the row should still appear with the price column showing `FETCH FAILED` (in red, via `rich`'s styling).

## Architectural Requirements

### File: `fetch_prices.py`
Structure the code with these named functions, each doing one thing:

```python
@dataclass
class PriceResult:
    name: str
    price: float | None
    currency: str
    timestamp: datetime
    error: str | None = None

def fetch_yfinance_price(ticker: str, display_name: str, currency: str) -> PriceResult: ...
def fetch_coingecko_price(coin_id: str, display_name: str, vs_currency: str = "usd") -> PriceResult: ...
def render_price_table(results: list[PriceResult]) -> None: ...
def main() -> None: ...
```

### Configuration
Define the asset list as a module-level constant at the top of the file:

```python
ASSETS_TO_FETCH = [
    {"source": "yfinance",  "ticker": "^NSEI",   "name": "NIFTY50", "currency": "INR"},
    {"source": "coingecko", "ticker": "bitcoin", "name": "BTC",     "currency": "USD"},
    {"source": "yfinance",  "ticker": "GC=F",    "name": "GOLD",    "currency": "USD/oz"},
]
```

This makes adding/changing assets a one-line edit.

## Error Handling Specification
This is heavily weighted in grading (8 of 20 points). Get it right.

1. **Network errors** (timeout, connection refused, DNS failure) → catch `requests.RequestException` and yfinance exceptions. Log via `logging.warning(...)`. Set `error` field, leave `price=None`.
2. **API returned empty data** (e.g., yfinance returns empty DataFrame for a delisted ticker) → check `if df.empty:` and treat as a failure with a clear error message like `"No data returned for ticker"`.
3. **Bad JSON / unexpected schema from CoinGecko** → catch `KeyError`, `ValueError`. Don't blindly index nested dicts.
4. **One asset failing must NEVER stop the others.** Each asset is fetched in its own try/except. The table still renders.
5. **Set a request timeout** of 10 seconds for CoinGecko. yfinance uses its own internal timeout but wrap it in a try/except anyway.
6. Use the `logging` module configured at INFO level. Don't use bare `print` for errors.

## Logging Setup
At the top of `main()`:
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
```
Log:
- INFO when starting each fetch
- WARNING when a fetch fails (include the asset name and the exception message)
- INFO with total elapsed time at the end

## Timestamp Handling
- Use `datetime.now(ZoneInfo("Asia/Kolkata"))` for the IST timestamp.
- Format the header line as: `Asset Prices — fetched at 2026-04-30 14:32:15 IST`.
- All `PriceResult.timestamp` fields should reflect when that specific asset was fetched, not the script start time.

## Number Formatting
- Use `f"{price:,.2f}"` for thousands separators and 2 decimal places.
- For crypto prices over 10,000, 2 decimals is fine. For prices under 1, use 4–6 decimals — but keep it simple, 2 is acceptable.

## Dependencies — `requirements.txt`
```
yfinance>=0.2.40
requests>=2.31.0
rich>=13.7.0
```

Pin minimum versions, not exact — they should still install on reasonably current environments.

## Acceptance Tests
Manually verify these scenarios before marking complete:

1. **Happy path** — `python fetch_prices.py` runs, fetches all 3 assets, table renders with real numbers. No exceptions in stdout/stderr.
2. **Simulated network failure** — temporarily change CoinGecko URL to an invalid one (e.g., `coingecko.com.invalid`). Run again. Other rows still render. `FETCH FAILED` shows in the BTC row. Warning logs appear.
3. **Bad ticker** — change `^NSEI` to `^NOTAREALTICKER`. Other rows still render. Warning logs appear.
4. **Offline** — disable wifi, run script. Script should not crash; all three rows show `FETCH FAILED`; you see clean warning logs; the script exits with a non-zero exit code if you implement that bonus.

## Bonus Features (optional, only if base task is solid)
- Cache results to a local JSON file with a 60-second TTL so repeated runs don't hammer APIs.
- Add a `--watch` flag that re-fetches every N seconds and re-renders the table in place (use `rich.live.Live`).
- Convert all prices to INR using a single FX call (USD/INR via yfinance `INR=X`) and add a "Price (INR)" column.
- Exit with code 1 if any fetch failed (useful for CI).

## README Documentation Required
After implementation, append a section to the project README titled **"Task 2 — Live Market Data Fetch"** containing:
- 2–3 sentence summary.
- Run instructions: `pip install -r requirements.txt && python fetch_prices.py`.
- Which APIs you used and why (e.g., "CoinGecko for crypto because no key required and the simple/price endpoint is rock-solid").
- A note on what AI tools you used (e.g., "Used Claude Code to suggest the dataclass shape and to remind me to set timeouts on requests.get").
- A short note on how to add a new asset (one-line edit in `ASSETS_TO_FETCH`).

## What Done Looks Like
- `python fetch_prices.py` prints a clean Rich table with 3+ rows of real, current data.
- Killing the network mid-run or using a bad ticker does not crash the script — failed rows show `FETCH FAILED`.
- Logs are visible and informative, not spammy.
- Adding a new asset is a one-line config change.
- README section is written.

## Anti-Patterns to Avoid
- Don't `print(traceback.format_exc())` — use `logging.warning(..., exc_info=True)` if you need the traceback.
- Don't `requests.get(url)` without a timeout — that's how scripts hang forever.
- Don't hardcode three separate `try/except` blocks in `main` — push that logic into the per-source fetch functions so `main` is a clean orchestration loop.
- Don't use `tabulate` or `prettytable` — `rich` produces the box-drawing output the spec shows and is the modern choice.
- Don't catch bare `except:` — catch specific exceptions. `except Exception as e:` is the broadest you should go, and only at the orchestration boundary.
- Don't print to stderr what should be a log message.
