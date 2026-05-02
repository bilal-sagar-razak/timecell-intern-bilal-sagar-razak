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


if __name__ == "__main__":
    test_load_portfolio_valid_file()
    test_load_portfolio_missing_file()
    test_load_portfolio_bad_json()
    test_build_explainer_prompt_substitutes_tone()
    test_parse_response_strips_fences()
    test_parse_response_rejects_bad_verdict()
    test_parse_critique_response_validates_revised_verdict()
    test_format_output_no_critique_section()
    print("All tests passed")
