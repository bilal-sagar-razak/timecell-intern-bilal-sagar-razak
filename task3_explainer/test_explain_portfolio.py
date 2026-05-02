"""Tests for task3_explainer.explain_portfolio — mocked, no live LLM calls."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent))
from explain_portfolio import (
    load_portfolio,
    build_explainer_prompt,
    parse_response,
    parse_critique_response,
    format_output,
    format_portfolio_summary,
    _format_inr,
)


def test_load_portfolio_valid_file() -> None:
    sample = {"total_value_inr": 100, "monthly_expenses_inr": 10, "assets": []}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample, f)
        tmp_path = f.name
    try:
        loaded = load_portfolio(tmp_path)
        assert loaded == sample, f"expected {sample}, got {loaded}"
    finally:
        Path(tmp_path).unlink()


def test_load_portfolio_missing_file() -> None:
    try:
        load_portfolio("/nonexistent/portfolio.json")
    except FileNotFoundError as e:
        assert "/nonexistent/portfolio.json" in str(e), f"path missing from error: {e}"
        return
    raise AssertionError("expected FileNotFoundError, none raised")


def test_load_portfolio_bad_json() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{not valid json")
        tmp_path = f.name
    try:
        try:
            load_portfolio(tmp_path)
        except ValueError as e:
            assert tmp_path in str(e), f"path missing from error: {e}"
            return
        raise AssertionError("expected ValueError, none raised")
    finally:
        Path(tmp_path).unlink()


def test_build_explainer_prompt_substitutes_tone() -> None:
    portfolio = {
        "total_value_inr": 100,
        "monthly_expenses_inr": 10,
        "assets": [],
    }
    metrics = {
        "post_crash_value": 100.0,
        "runway_months": 10.0,
        "ruin_test": "PASS",
        "largest_risk_asset": None,
        "concentration_warning": False,
    }
    prompt = build_explainer_prompt(portfolio, metrics, tone="expert")
    assert "expert" in prompt, "tone 'expert' not substituted into prompt"
    assert "$tone" not in prompt, "unsubstituted $tone placeholder remains"


def test_parse_response_strips_fences() -> None:
    raw = (
        "```json\n"
        '{"summary": "s", "doing_well": "d", "should_change": "c", "verdict": "Aggressive"}\n'
        "```"
    )
    parsed = parse_response(raw)
    assert parsed["verdict"] == "Aggressive", f"verdict should be 'Aggressive', got {parsed['verdict']!r}"
    assert parsed["summary"] == "s", f"summary should be 's', got {parsed['summary']!r}"


def test_parse_response_rejects_bad_verdict() -> None:
    raw = '{"summary": "s", "doing_well": "d", "should_change": "c", "verdict": "moderate"}'
    try:
        parse_response(raw)
    except ValueError as e:
        assert "moderate" in str(e), f"bad verdict missing from error message: {e}"
        return
    raise AssertionError("expected ValueError, none raised")


def test_parse_critique_response_validates_revised_verdict() -> None:
    raw = '{"issues_found": [], "revised_verdict": "high"}'
    try:
        parse_critique_response(raw)
    except ValueError as e:
        assert "high" in str(e), f"bad revised_verdict missing from error: {e}"
        return
    raise AssertionError("expected ValueError, none raised")


def test_format_output_no_critique_section() -> None:
    parsed = {
        "summary": "test summary",
        "doing_well": "test positive",
        "should_change": "test suggestion",
        "verdict": "Aggressive",
    }
    output = format_output(parsed)
    assert "Summary:" in output, "missing 'Summary:' header"
    assert "test summary" in output, "summary content not in output"
    assert "Verdict: Aggressive" in output, "verdict not in output"
    assert "CRITIQUE" not in output, \
        "critique should never appear in user-facing output (per redesign)"


def test_format_inr_indian_grouping() -> None:
    assert _format_inr(10000000) == "1,00,00,000", f"got {_format_inr(10000000)!r}"
    assert _format_inr(80000) == "80,000", f"got {_format_inr(80000)!r}"
    assert _format_inr(500) == "500", f"got {_format_inr(500)!r}"


def test_format_portfolio_summary_shows_all_assets() -> None:
    portfolio = {
        "total_value_inr": 10000000,
        "monthly_expenses_inr": 80000,
        "assets": [
            {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
            {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
            {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
            {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct": 0},
        ],
    }
    out = format_portfolio_summary(portfolio)
    assert "PORTFOLIO" in out, "missing PORTFOLIO header"
    assert "1,00,00,000" in out, "total value (Indian-grouped) missing"
    assert "80,000" in out, "monthly expenses missing"
    for name in ("BTC", "NIFTY50", "GOLD", "CASH"):
        assert name in out, f"asset {name} missing from summary"
    assert "Total" in out and "100%" in out, "allocation total row missing"


if __name__ == "__main__":
    test_load_portfolio_valid_file()
    test_load_portfolio_missing_file()
    test_load_portfolio_bad_json()
    test_build_explainer_prompt_substitutes_tone()
    test_parse_response_strips_fences()
    test_parse_response_rejects_bad_verdict()
    test_parse_critique_response_validates_revised_verdict()
    test_format_output_no_critique_section()
    test_format_inr_indian_grouping()
    test_format_portfolio_summary_shows_all_assets()
    print("All tests passed")
