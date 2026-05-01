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


def _load_cache() -> dict:
    """Return cache dict, or {} on missing/corrupted file."""
    try:
        with CACHE_FILE.open() as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


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


def _save_cache(cache: dict) -> None:
    """Atomic write via temp + rename."""
    tmp = CACHE_FILE.with_suffix(".json.tmp")
    with tmp.open("w") as f:
        json.dump(cache, f, indent=2)
    tmp.replace(CACHE_FILE)


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
