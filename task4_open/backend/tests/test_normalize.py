"""Tests for parser.normalize — all Anthropic calls mocked, no live API."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.extract import ExtractedContent
from parser.normalize import (
    BudgetExhausted,
    NormalizationError,
    normalize,
)

VALID_RESPONSE = json.dumps({
    "holder_name": "Test User",
    "source_format": "groww_xlsx",
    "summary": {
        "total_invested_inr": 100.0,
        "total_current_inr": 110.0,
        "total_pnl_inr": 10.0,
        "total_pnl_pct": 10.0,
        "asset_count": 1,
    },
    "assets": [{
        "name": "Parag Parikh Flexi Cap Fund Direct",
        "asset_type": "mutual_fund",
        "isin": None,
        "amc": "PPFAS",
        "category": "Equity",
        "sub_category": "Flexi Cap",
        "folio": "13959825",
        "units": 8547.228,
        "invested_value_inr": 100.0,
        "current_value_inr": 110.0,
        "xirr_pct": 10.22,
        "pnl_inr": 10.0,
        "pnl_pct": 10.0,
    }],
    "parser_warnings": [],
})


def _mock_anthropic_response(text: str, input_tokens: int = 1000, output_tokens: int = 200) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return response


def _make_content() -> ExtractedContent:
    return ExtractedContent(kind="text", text="some statement", format_hint="groww_xlsx")


def test_normalize_happy_path() -> None:
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)
        mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)

        result = normalize(_make_content())

        assert result.holder_name == "Test User"
        assert len(result.assets) == 1
        assert mock_client.messages.create.call_count == 1


def test_normalize_strips_json_fences() -> None:
    fenced = "```json\n" + VALID_RESPONSE + "\n```"
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)
        mock_client.messages.create.return_value = _mock_anthropic_response(fenced)

        result = normalize(_make_content())

        assert result.holder_name == "Test User"


def test_normalize_retries_on_invalid_json() -> None:
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)
        mock_client.messages.create.side_effect = [
            _mock_anthropic_response("not valid json at all {{{"),
            _mock_anthropic_response(VALID_RESPONSE),
        ]

        result = normalize(_make_content())

        assert result.holder_name == "Test User"
        assert mock_client.messages.create.call_count == 2


def test_normalize_raises_after_retry_failure() -> None:
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)
        mock_client.messages.create.side_effect = [
            _mock_anthropic_response("garbage one"),
            _mock_anthropic_response("garbage two"),
        ]

        try:
            normalize(_make_content())
        except NormalizationError as e:
            assert len(e.attempts) == 2
            assert len(e.errors) == 2
            return
        raise AssertionError("expected NormalizationError, none raised")


def test_normalize_retries_on_pydantic_validation_failure() -> None:
    incomplete = json.dumps({
        "source_format": "groww_xlsx",
        "assets": [],
    })
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)
        mock_client.messages.create.side_effect = [
            _mock_anthropic_response(incomplete),
            _mock_anthropic_response(VALID_RESPONSE),
        ]

        result = normalize(_make_content())

        assert result.holder_name == "Test User"
        assert mock_client.messages.create.call_count == 2


def test_normalize_truncates_oversized_input() -> None:
    big_content = ExtractedContent(kind="text", text="x" * 200_000, format_hint="groww_xlsx")
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=100_000)
        mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)

        result = normalize(big_content)

        assert any("truncated" in w for w in result.parser_warnings), \
            f"no truncation warning in {result.parser_warnings}"


def test_normalize_respects_daily_budget(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("parser.normalize.CACHE_DIR", tmp_path)
    monkeypatch.setenv("MAX_DAILY_LLM_USD", "0.001")
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=30_000)
        mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)

        try:
            normalize(_make_content())
        except BudgetExhausted:
            assert mock_client.messages.create.call_count == 0
            return
        raise AssertionError("expected BudgetExhausted, none raised")


def test_normalize_disabled_budget_allows_call(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("parser.normalize.CACHE_DIR", tmp_path)
    monkeypatch.setenv("MAX_DAILY_LLM_USD", "disabled")
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=30_000)
        mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)

        result = normalize(_make_content())

        assert result.holder_name == "Test User"


def test_normalize_writes_cache_on_success(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("parser.normalize.CACHE_DIR", tmp_path)
    monkeypatch.setenv("MAX_DAILY_LLM_USD", "10.00")
    with patch("parser.normalize.Anthropic") as MockAnthropic:
        mock_client = MagicMock()
        MockAnthropic.return_value = mock_client
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)
        mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)

        normalize(_make_content())

        cache_files = list(tmp_path.glob("usage-*.json"))
        assert len(cache_files) == 1, f"expected 1 cache file, got {cache_files}"
        data = json.loads(cache_files[0].read_text())
        assert data["usd"] > 0
