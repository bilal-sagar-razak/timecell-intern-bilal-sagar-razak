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
    fetch_coingecko_price,
    _cache_lookup,
    _load_cache,
)


def test_yfinance_empty_dataframe() -> None:
    mock_ticker = Mock()
    mock_ticker.history.return_value = Mock(empty=True)
    with patch("fetch_prices.yf.Ticker", return_value=mock_ticker):
        result = fetch_yfinance_price("^NSEI", "NIFTY50", "INR")
    assert result.price is None, f"expected None, got {result.price}"
    assert "no data" in result.error.lower(), \
        f"error should mention 'no data', got {result.error!r}"


def test_yfinance_raises_exception() -> None:
    with patch(
        "fetch_prices.yf.Ticker",
        side_effect=Exception("simulated network failure"),
    ):
        result = fetch_yfinance_price("^NSEI", "NIFTY50", "INR")
    assert result.price is None, f"expected None, got {result.price}"
    assert result.error, f"error should be set, got {result.error!r}"


def test_coingecko_request_exception() -> None:
    with patch(
        "fetch_prices.requests.get",
        side_effect=requests.RequestException("connection refused"),
    ):
        result = fetch_coingecko_price("bitcoin", "BTC", "usd")
    assert result.price is None, f"expected None, got {result.price}"
    assert result.error, f"error should be set, got {result.error!r}"


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


if __name__ == "__main__":
    test_yfinance_empty_dataframe()
    test_yfinance_raises_exception()
    test_coingecko_request_exception()
    test_coingecko_bad_schema()
    test_coingecko_timeout_is_set()
    test_cache_lookup_fresh_hit()
    test_cache_lookup_stale_miss()
    test_load_cache_corrupted_returns_empty()
    print("All tests passed")
