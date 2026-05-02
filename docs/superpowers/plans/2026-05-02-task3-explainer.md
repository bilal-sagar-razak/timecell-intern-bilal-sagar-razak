# Task 3 — AI-Powered Portfolio Explainer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `task3_explainer/explain_portfolio.py` — loads a portfolio JSON, computes risk metrics by reusing Task 1's `compute_risk_metrics`, asks Anthropic Claude to explain it (4-key JSON), runs an OpenAI `gpt-4o` cross-vendor critique, refines the explanation with Anthropic if the critique disagrees, and prints only the final refined explanation. Critique is logged to stderr but never displayed to the user.

**Architecture:** Flat `task3_explainer/` module — no package, no `__init__.py`, run as scripts. `explain_portfolio.py` holds: imports → `sys.path` insert for Task 1 → constants → 3 prompt builders → 2 LLM call functions → 2 parsers → `format_output` (critique-free) → `_check_api_keys` → `main()`. Prompt templates live in `prompts/*.txt` (loaded via `string.Template`), with historical snapshots in `prompts/iteration_log/`. Two sample portfolios (aggressive + 95% cash) ship for the spec's "verdict varies" acceptance test. `python-dotenv` loads `.env`; `.env.example` is committed as a setup template.

**Tech Stack:** Python 3.10+ (works on 3.9 via `from __future__ import annotations`), `anthropic>=0.40.0`, `openai>=1.50.0`, `python-dotenv>=1.0.0`. `unittest.mock` (stdlib) for tests. No pytest.

**Spec:** [docs/superpowers/specs/2026-05-02-task3-explainer-design.md](../specs/2026-05-02-task3-explainer-design.md)

---

## Task 1: Branch, deps, .env.example, install, confirm Sonnet model

**Files:**
- Modify: `requirements.txt` (currently has yfinance/requests/rich from Task 2)
- Create: `.env.example` (committed template)

- [ ] **Step 1: Verify clean main, create feature branch**

```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak
git status
git log --oneline | head -3
git checkout -b task3/explainer
```

Expected: clean main except untracked `.DS_Store`. `git log` shows merge commit `2f06e35` on top.

- [ ] **Step 2: Append dependencies to `requirements.txt`**

The file currently has `yfinance>=0.2.40`, `requests>=2.31.0`, `rich>=13.7.0`. Append three more lines so the full file becomes:

```
yfinance>=0.2.40
requests>=2.31.0
rich>=13.7.0
anthropic>=0.40.0
openai>=1.50.0
python-dotenv>=1.0.0
```

- [ ] **Step 3: Create `.env.example` (committed template)**

```
# Anthropic (required) — primary LLM for portfolio explanation + refinement
# Get a key: https://console.anthropic.com/
ANTHROPIC_API_KEY=

# OpenAI (optional) — secondary LLM for cross-vendor critique pass
# Used internally to refine the explanation; never displayed to the user
# Get a key: https://platform.openai.com/api-keys
# Leave blank to skip critique + refinement (script still runs end-to-end)
OPENAI_API_KEY=
```

- [ ] **Step 4: Activate venv and install**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: anthropic, openai, python-dotenv (and transitive deps) install. No errors.

- [ ] **Step 5: Verify imports**

```bash
python -c "import anthropic; import openai; from dotenv import load_dotenv; print('imports OK')"
```

Expected: `imports OK`.

- [ ] **Step 6: Confirm latest Anthropic Sonnet model ID via the `claude-api` skill**

Use the `claude-api` skill (Skill tool, `claude-api`) to confirm the current latest Sonnet model ID. As of the spec's draft, `claude-sonnet-4-5` is correct, but a newer Sonnet (e.g., `claude-sonnet-4-6` or `claude-sonnet-4-7`) may have shipped. **Record the confirmed model ID for Task 2 step 1's `DEFAULT_ANTHROPIC_MODEL` constant.** Do NOT proceed without confirming this — using a deprecated model ID will cause the LLM call to fail at runtime.

**Confirmed at implementation time (2026-04-30):** `claude-sonnet-4-6` is the current latest Sonnet (1M context, 64K output). Use this for `DEFAULT_ANTHROPIC_MODEL` in Task 2 step 1.

---

## Task 2: Bootstrap `explain_portfolio.py` skeleton + first failing test

**Files:**
- Create: `task3_explainer/explain_portfolio.py`
- Create: `task3_explainer/test_explain_portfolio.py`

- [ ] **Step 1: Create `explain_portfolio.py` with imports, sys.path insert, constants, dataclass-free stubs**

Use the model ID confirmed in Task 1 step 6 for `DEFAULT_ANTHROPIC_MODEL`: **`claude-sonnet-4-6`** (current latest Sonnet, confirmed 2026-04-30).

```python
"""LLM-powered portfolio risk explainer with cross-vendor critique → refine loop."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from string import Template

# Sibling-folder import: reuse Task 1's compute_risk_metrics (per spec, do not re-implement)
sys.path.insert(0, str(Path(__file__).parent.parent / "task1_risk"))
from risk import compute_risk_metrics  # noqa: E402

# Optional: dotenv loaded in main(); imported lazily so module import doesn't require it


DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"     # confirmed via claude-api skill, Task 1 step 6
DEFAULT_OPENAI_CRITIQUE_MODEL = "gpt-4o"
VALID_VERDICTS = {"Aggressive", "Balanced", "Conservative"}
VALID_TONES = ("beginner", "experienced", "expert")
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_portfolio(path: str) -> dict:
    """Stub — full implementation in Task 3."""
    raise NotImplementedError("see Task 3")
```

- [ ] **Step 2: Create `test_explain_portfolio.py` with imports and the first failing test**

```python
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


if __name__ == "__main__":
    test_load_portfolio_valid_file()
    print("All tests passed")
```

- [ ] **Step 3: Run, verify failure with `NotImplementedError`**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: traceback ending with `NotImplementedError: see Task 3`.

---

## Task 3: Implement `load_portfolio`, add missing-file + bad-JSON tests

**Files:**
- Modify: `task3_explainer/explain_portfolio.py`
- Modify: `task3_explainer/test_explain_portfolio.py`

- [ ] **Step 1: Replace stub `load_portfolio` with real implementation**

```python
def load_portfolio(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"portfolio file not found: {path}")
    with p.open() as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"portfolio file is not valid JSON: {path} — {e}") from e
```

- [ ] **Step 2: Add tests 2 and 3 to `test_explain_portfolio.py`**

Insert before the runner block:

```python
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
```

Update the runner block:

```python
if __name__ == "__main__":
    test_load_portfolio_valid_file()
    test_load_portfolio_missing_file()
    test_load_portfolio_bad_json()
    print("All tests passed")
```

- [ ] **Step 3: Run all 3 tests, verify pass**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed`.

---

## Task 4: Create the two sample portfolio JSON files

**Files:**
- Create: `task3_explainer/sample_portfolio.json`
- Create: `task3_explainer/sample_portfolio_conservative.json`

- [ ] **Step 1: Create `sample_portfolio.json` (aggressive — Task 1's example portfolio)**

```json
{
  "total_value_inr": 10000000,
  "monthly_expenses_inr": 80000,
  "assets": [
    {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
    {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
    {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
    {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct": 0}
  ]
}
```

- [ ] **Step 2: Create `sample_portfolio_conservative.json` (95% cash — expected verdict: Conservative)**

```json
{
  "total_value_inr": 10000000,
  "monthly_expenses_inr": 80000,
  "assets": [
    {"name": "CASH", "allocation_pct": 95, "expected_crash_pct": 0},
    {"name": "GOLD", "allocation_pct": 5,  "expected_crash_pct": -15}
  ]
}
```

- [ ] **Step 3: Sanity-check both files load and validate via Task 1**

```bash
python -c "
import sys
sys.path.insert(0, 'task3_explainer')
sys.path.insert(0, 'task1_risk')
from explain_portfolio import load_portfolio
from risk import compute_risk_metrics
for name in ('sample_portfolio.json', 'sample_portfolio_conservative.json'):
    p = load_portfolio(f'task3_explainer/{name}')
    m = compute_risk_metrics(p)
    print(name, '→ verdict-relevant:', m['ruin_test'], m['largest_risk_asset'], m['concentration_warning'])
"
```

Expected:
```
sample_portfolio.json → verdict-relevant: PASS BTC False
sample_portfolio_conservative.json → verdict-relevant: PASS None False
```

(Aggressive: largest_risk_asset is BTC (30 × 80 = 2400), concentration_warning False because NIFTY is 40 not >40. Conservative: largest_risk_asset is None because... actually wait, GOLD is the only crash asset. Let me recompute: GOLD 5 × 15 = 75; CASH 95 × 0 = 0. Largest is GOLD. Concentration warning is True because CASH 95 > 40.)

Re-checking: conservative portfolio expected output:
- `ruin_test`: PASS (huge cash buffer)
- `largest_risk_asset`: GOLD (only non-zero risk score)
- `concentration_warning`: True (CASH > 40)

Update expected output:
```
sample_portfolio.json → verdict-relevant: PASS BTC False
sample_portfolio_conservative.json → verdict-relevant: PASS GOLD True
```

---

## Task 5: Create the three production prompt templates

**Files:**
- Create: `task3_explainer/prompts/explainer.txt`
- Create: `task3_explainer/prompts/critique.txt`
- Create: `task3_explainer/prompts/refine.txt`

- [ ] **Step 1: Create the `prompts/` directory**

```bash
mkdir -p task3_explainer/prompts
```

- [ ] **Step 2: Create `prompts/explainer.txt`**

Copy the following content verbatim:

```
You are a friendly but honest financial advisor speaking with an Indian high-net-worth client.
Your tone should be warm, direct, and free of jargon. Speak as if you are sitting across from
the client at a coffee table, not writing a regulatory document.

<portfolio>
$portfolio_json
</portfolio>

<computed_risk_metrics>
$metrics_json
</computed_risk_metrics>

<task>
Analyse the portfolio above. Use the pre-computed metrics — do not recompute them yourself,
as you may make arithmetic errors. Produce a JSON response with exactly these four fields:

- "summary": 3 to 4 sentences explaining the overall risk level in plain English.
- "doing_well": One specific positive observation about the portfolio.
- "should_change": One specific concrete change to consider, with the reasoning.
- "verdict": Exactly one of "Aggressive", "Balanced", or "Conservative".
</task>

<rules>
- Output ONLY valid JSON. No markdown, no code fences, no preamble.
- Verdict must be exactly one of the three allowed values, case-sensitive.
- Reference specific numbers from the portfolio in your summary (e.g., "your 30% BTC allocation").
- Keep the language at a $tone level — see definitions below.
- Do not invent data not present in the portfolio.
- Use INR as the currency in all financial references (Crore, Lakh acceptable).
</rules>

<tone_definitions>
- beginner: simple words, no jargon, analogies welcome (e.g., "BTC is the hot stock of crypto")
- experienced: assume familiarity with terms like "allocation", "drawdown", "rebalancing"
- expert: concise, use precise financial terminology, no hand-holding
</tone_definitions>

<example_output>
{
  "summary": "Your portfolio is leaning aggressive — 30% in BTC means a major crash could halve your wealth overnight. The good news is you have 10% in cash and 20% in gold as a buffer. Your post-crash runway of 71 months is excellent, so you can afford this risk if you can stomach the volatility.",
  "doing_well": "You have meaningful diversification across crypto, equities, gold, and cash — many investors at your level go 80%+ into one bucket.",
  "should_change": "Consider trimming BTC from 30% to 15-20%. A single asset with -80% downside concentrates too much tail risk; the same return target can be reached with a slightly larger NIFTY allocation at half the volatility.",
  "verdict": "Aggressive"
}
</example_output>
```

- [ ] **Step 3: Create `prompts/critique.txt`**

```
A junior analyst produced the following portfolio explanation:

<original_explanation>
$primary_response
</original_explanation>

Given the actual portfolio data:

<portfolio>
$portfolio_json
</portfolio>

<computed_metrics>
$metrics_json
</computed_metrics>

Critique the explanation. Are any numbers wrong? Are any major risks missed?
Is the verdict justified?

<rules>
- Output ONLY valid JSON. No markdown, no code fences, no preamble.
- Required fields: "issues_found" (list of strings; empty list if no issues),
  "revised_verdict" (string; if you agree with the original verdict, repeat it).
- The revised_verdict must be exactly one of "Aggressive", "Balanced", or "Conservative".
</rules>

<example_output>
{
  "issues_found": [
    "The summary says runway is 71 months but the metrics show 71.25 — minor rounding, acceptable.",
    "The recommendation to trim BTC doesn't address the 40% NIFTY concentration which is at the spec's warning threshold."
  ],
  "revised_verdict": "Aggressive"
}
</example_output>
```

- [ ] **Step 4: Create `prompts/refine.txt`**

```
You are a friendly but honest financial advisor speaking with an Indian high-net-worth client.
Your tone should be warm, direct, and free of jargon. Speak as if you are sitting across from
the client at a coffee table, not writing a regulatory document.

<portfolio>
$portfolio_json
</portfolio>

<computed_risk_metrics>
$metrics_json
</computed_risk_metrics>

<previous_attempt>
$previous_response
</previous_attempt>

<reviewer_critique>
An independent reviewer raised these concerns:
$critique_issues

The reviewer's suggested verdict: $critique_verdict
</reviewer_critique>

<task>
Produce a REVISED explanation that addresses the critique's concerns. Use the pre-computed
metrics — do not recompute them. Output JSON with the same four fields:

- "summary": 3 to 4 sentences explaining the overall risk level in plain English.
- "doing_well": One specific positive observation about the portfolio.
- "should_change": One specific concrete change to consider, with the reasoning.
- "verdict": Exactly one of "Aggressive", "Balanced", or "Conservative".

If you disagree with the reviewer, you may keep your original conclusion — but you must
explicitly address the specific points they raised.
</task>

<rules>
- Output ONLY valid JSON. No markdown, no code fences, no preamble.
- Verdict must be exactly one of the three allowed values, case-sensitive.
- Reference specific numbers from the portfolio in your summary.
- Keep the language at a $tone level — see definitions below.
- Do not invent data not present in the portfolio.
- Use INR as the currency in all financial references (Crore, Lakh acceptable).
</rules>

<tone_definitions>
- beginner: simple words, no jargon, analogies welcome
- experienced: assume familiarity with terms like "allocation", "drawdown", "rebalancing"
- expert: concise, use precise financial terminology, no hand-holding
</tone_definitions>

<example_output>
{
  "summary": "Your portfolio is leaning aggressive — 30% in BTC and 40% in NIFTY together account for 70% of your wealth in volatile assets. Post-crash runway of 71 months is strong, but the combined equity+crypto exposure means a synchronized downturn would cut your portfolio nearly in half.",
  "doing_well": "Your 10% cash + 20% gold combination provides a meaningful liquidity buffer that many investors at your level skip entirely.",
  "should_change": "Trim BTC from 30% to 15-20% AND consider whether your 40% NIFTY allocation needs rebalancing — the reviewer correctly noted that NIFTY is at the 40% concentration threshold, so any further drift up would trigger our concentration warning.",
  "verdict": "Aggressive"
}
</example_output>
```

- [ ] **Step 5: Verify all three files were created**

```bash
ls -la task3_explainer/prompts/
```

Expected: explainer.txt, critique.txt, refine.txt all present.

---

## Task 6: Create the prompt iteration log (grader-facing history)

**Files:**
- Create: `task3_explainer/prompts/iteration_log/explainer_v1.txt`
- Create: `task3_explainer/prompts/iteration_log/explainer_v2.txt`
- Create: `task3_explainer/prompts/iteration_log/explainer_v3.txt`

These files are NOT loaded by the code — they're text snapshots for the README's prompt-iteration log. They tell the story of how the prompt evolved.

- [ ] **Step 1: Create the directory**

```bash
mkdir -p task3_explainer/prompts/iteration_log
```

- [ ] **Step 2: Create `explainer_v1.txt` — the naive first attempt**

```
You are a financial advisor. Explain this portfolio in JSON.

Portfolio:
$portfolio_json

Computed metrics:
$metrics_json

Output JSON with these fields:
- summary
- doing_well
- should_change
- verdict

Keep the language at a $tone level.
```

- [ ] **Step 3: Create `explainer_v2.txt` — added enum constraint and "no fences" rule**

```
You are a financial advisor. Explain this portfolio in JSON.

Portfolio:
$portfolio_json

Computed metrics:
$metrics_json

Output JSON with these exact fields:
- "summary": plain-English overview
- "doing_well": one positive
- "should_change": one suggested change
- "verdict": MUST be exactly one of "Aggressive", "Balanced", or "Conservative" — case-sensitive

Rules:
- Output ONLY valid JSON. No markdown, no code fences, no preamble.
- Reference specific numbers from the portfolio.
- Do not invent data not in the portfolio.
- Use INR as the currency.

Keep the language at a $tone level.
```

- [ ] **Step 4: Create `explainer_v3.txt` (identical to production `prompts/explainer.txt`)**

Copy the same content from Task 5 step 2 into `task3_explainer/prompts/iteration_log/explainer_v3.txt`. The v3 file is the production version preserved as a snapshot — it will diverge from `explainer.txt` only if someone iterates on the prompt later.

- [ ] **Step 5: Verify all three iteration_log files exist and are readable text**

```bash
ls -la task3_explainer/prompts/iteration_log/
wc -l task3_explainer/prompts/iteration_log/*.txt
```

Expected: all three files present, line counts increase v1 → v2 → v3 (v1 ≈ 16 lines, v2 ≈ 22 lines, v3 ≈ 50 lines).

---

## Task 7: Implement prompt builders + add tone-substitution test

**Files:**
- Modify: `task3_explainer/explain_portfolio.py`
- Modify: `task3_explainer/test_explain_portfolio.py`

- [ ] **Step 1: Add the three prompt builder functions to `explain_portfolio.py`**

Insert after `load_portfolio` and before any future-stub functions:

```python
def build_explainer_prompt(portfolio: dict, metrics: dict, tone: str = "beginner") -> str:
    raw = (PROMPTS_DIR / "explainer.txt").read_text()
    return Template(raw).substitute(
        portfolio_json=json.dumps(portfolio, indent=2),
        metrics_json=json.dumps(metrics, indent=2, default=str),
        tone=tone,
    )


def build_critique_prompt(portfolio: dict, metrics: dict, primary_response: str) -> str:
    raw = (PROMPTS_DIR / "critique.txt").read_text()
    return Template(raw).substitute(
        portfolio_json=json.dumps(portfolio, indent=2),
        metrics_json=json.dumps(metrics, indent=2, default=str),
        primary_response=primary_response,
    )


def build_refine_prompt(
    portfolio: dict,
    metrics: dict,
    previous_response: str,
    critique: dict,
    tone: str = "beginner",
) -> str:
    raw = (PROMPTS_DIR / "refine.txt").read_text()
    issues_block = (
        "\n".join(f"- {i}" for i in critique["issues_found"])
        or "- (no specific issues, but verdict was challenged)"
    )
    return Template(raw).substitute(
        portfolio_json=json.dumps(portfolio, indent=2),
        metrics_json=json.dumps(metrics, indent=2, default=str),
        previous_response=previous_response,
        critique_issues=issues_block,
        critique_verdict=critique["revised_verdict"],
    )
```

- [ ] **Step 2: Add `build_explainer_prompt` to test imports**

Replace the `from explain_portfolio import (...)` block with:

```python
from explain_portfolio import (
    load_portfolio,
    build_explainer_prompt,
)
```

- [ ] **Step 3: Add the tone-substitution test before the runner block**

```python
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
```

Add to runner: `test_build_explainer_prompt_substitutes_tone()`.

- [ ] **Step 4: Run all 4 tests, verify pass**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed`.

---

## Task 8: Implement `parse_response` + add fence-strip test

**Files:**
- Modify: `task3_explainer/explain_portfolio.py`
- Modify: `task3_explainer/test_explain_portfolio.py`

- [ ] **Step 1: Append `parse_response` to `explain_portfolio.py`**

Insert after the prompt builder functions:

```python
def parse_response(raw: str) -> dict:
    """Strip markdown fences, parse JSON, validate schema. Raises ValueError on bad output."""
    cleaned = raw.strip()

    # Strip ```json ... ``` fences if present (despite prompt saying "no fences").
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM response is not valid JSON: {e}\n--- raw response ---\n{raw}"
        ) from e

    required = {"summary", "doing_well", "should_change", "verdict"}
    missing = required - parsed.keys()
    if missing:
        raise ValueError(
            f"LLM response missing required keys: {sorted(missing)}\n"
            f"--- raw response ---\n{raw}"
        )

    if parsed["verdict"] not in VALID_VERDICTS:
        raise ValueError(
            f"verdict must be one of {sorted(VALID_VERDICTS)}, got {parsed['verdict']!r}\n"
            f"--- raw response ---\n{raw}"
        )

    return parsed
```

- [ ] **Step 2: Add `parse_response` to test imports**

```python
from explain_portfolio import (
    load_portfolio,
    build_explainer_prompt,
    parse_response,
)
```

- [ ] **Step 3: Add the fence-strip test before the runner**

```python
def test_parse_response_strips_fences() -> None:
    raw = (
        "```json\n"
        '{"summary": "s", "doing_well": "d", "should_change": "c", "verdict": "Aggressive"}\n'
        "```"
    )
    parsed = parse_response(raw)
    assert parsed["verdict"] == "Aggressive", f"verdict should be 'Aggressive', got {parsed['verdict']!r}"
    assert parsed["summary"] == "s", f"summary should be 's', got {parsed['summary']!r}"
```

Add to runner: `test_parse_response_strips_fences()`.

- [ ] **Step 4: Run all 5 tests, verify pass**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed`.

---

## Task 9: Add bad-verdict test (verifies enum validation in parse_response)

**Files:**
- Modify: `task3_explainer/test_explain_portfolio.py`

- [ ] **Step 1: Add the test before the runner**

```python
def test_parse_response_rejects_bad_verdict() -> None:
    raw = '{"summary": "s", "doing_well": "d", "should_change": "c", "verdict": "moderate"}'
    try:
        parse_response(raw)
    except ValueError as e:
        assert "moderate" in str(e), f"bad verdict missing from error message: {e}"
        return
    raise AssertionError("expected ValueError, none raised")
```

Add to runner: `test_parse_response_rejects_bad_verdict()`.

- [ ] **Step 2: Run all 6 tests, verify pass**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed`.

---

## Task 10: Implement `parse_critique_response` + add validation test

**Files:**
- Modify: `task3_explainer/explain_portfolio.py`
- Modify: `task3_explainer/test_explain_portfolio.py`

- [ ] **Step 1: Append `parse_critique_response` to `explain_portfolio.py`**

```python
def parse_critique_response(raw: str) -> dict:
    """Parse critique JSON. OpenAI's json_object mode means fences are unlikely, but defend anyway."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Critique response is not valid JSON: {e}\n--- raw response ---\n{raw}"
        ) from e

    if "issues_found" not in parsed or "revised_verdict" not in parsed:
        raise ValueError(
            f"Critique missing required keys (need issues_found + revised_verdict)\n"
            f"--- raw response ---\n{raw}"
        )
    if not isinstance(parsed["issues_found"], list):
        raise ValueError(
            f"issues_found must be a list, got {type(parsed['issues_found']).__name__}"
        )
    if parsed["revised_verdict"] not in VALID_VERDICTS:
        raise ValueError(
            f"revised_verdict must be one of {sorted(VALID_VERDICTS)}, "
            f"got {parsed['revised_verdict']!r}"
        )

    return parsed
```

- [ ] **Step 2: Add `parse_critique_response` to test imports**

```python
from explain_portfolio import (
    load_portfolio,
    build_explainer_prompt,
    parse_response,
    parse_critique_response,
)
```

- [ ] **Step 3: Add the test before the runner**

```python
def test_parse_critique_response_validates_revised_verdict() -> None:
    raw = '{"issues_found": [], "revised_verdict": "high"}'
    try:
        parse_critique_response(raw)
    except ValueError as e:
        assert "high" in str(e), f"bad revised_verdict missing from error: {e}"
        return
    raise AssertionError("expected ValueError, none raised")
```

Add to runner: `test_parse_critique_response_validates_revised_verdict()`.

- [ ] **Step 4: Run all 7 tests, verify pass**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed`.

---

## Task 11: Implement `format_output` + add no-critique-section test

**Files:**
- Modify: `task3_explainer/explain_portfolio.py`
- Modify: `task3_explainer/test_explain_portfolio.py`

- [ ] **Step 1: Append `format_output` to `explain_portfolio.py`**

```python
def format_output(parsed: dict) -> str:
    """Pretty-print the (possibly-refined) explanation. Critique never appears here."""
    sep = "═" * 60
    return "\n".join([
        sep,
        "PARSED OUTPUT",
        sep,
        "",
        "Summary:",
        f"  {parsed['summary']}",
        "",
        "Doing Well:",
        f"  {parsed['doing_well']}",
        "",
        "Should Change:",
        f"  {parsed['should_change']}",
        "",
        f"Verdict: {parsed['verdict']}",
    ])
```

- [ ] **Step 2: Add `format_output` to test imports**

```python
from explain_portfolio import (
    load_portfolio,
    build_explainer_prompt,
    parse_response,
    parse_critique_response,
    format_output,
)
```

- [ ] **Step 3: Add the test before the runner**

```python
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
```

Add to runner: `test_format_output_no_critique_section()`.

- [ ] **Step 4: Run all 8 tests, verify pass**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed`.

---

## Task 12: Implement LLM client functions (`call_llm`, `call_critique_llm`)

**Files:**
- Modify: `task3_explainer/explain_portfolio.py`

(No new tests — these wrap SDK calls. They'll be exercised by the manual end-to-end run in Task 15.)

- [ ] **Step 1: Append `call_llm` to `explain_portfolio.py`**

```python
def call_llm(prompt: str, model: str) -> str:
    """Call Anthropic; return raw response text. Raises on any failure."""
    from anthropic import Anthropic
    client = Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

- [ ] **Step 2: Append `call_critique_llm` to `explain_portfolio.py`**

```python
def call_critique_llm(prompt: str, model: str) -> str:
    """Call OpenAI; return raw response text. Raises on any failure (caller catches)."""
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content
```

- [ ] **Step 3: Verify the module still imports cleanly**

```bash
python -c "import sys; sys.path.insert(0, 'task3_explainer'); import explain_portfolio; print('module imports OK')"
```

Expected: `module imports OK`. (Tests 1-8 also still pass — no regression possible since these are new functions.)

- [ ] **Step 4: Re-run the test suite to confirm**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed` (still 8 tests).

---

## Task 13: Implement `_check_api_keys`

**Files:**
- Modify: `task3_explainer/explain_portfolio.py`

(No new tests — this is a CLI-entry-point helper that calls `sys.exit`. Mocking `os.environ` + capturing `sys.exit` for a 30-line function would be more code than the function itself.)

- [ ] **Step 1: Append `_check_api_keys` to `explain_portfolio.py`**

```python
def _check_api_keys() -> tuple[bool, bool]:
    """Verify env vars are set. Exits 1 if Anthropic missing or both missing."""
    have_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    have_openai = bool(os.environ.get("OPENAI_API_KEY"))

    if not have_anthropic and not have_openai:
        print(
            "ERROR: Both ANTHROPIC_API_KEY and OPENAI_API_KEY are missing.\n"
            "Setup: cp .env.example .env, then fill in both keys.\n"
            "  - ANTHROPIC_API_KEY: required for the primary explanation\n"
            "  - OPENAI_API_KEY:    optional, used internally for critique-driven refinement\n"
            "Get keys: https://console.anthropic.com/ and https://platform.openai.com/api-keys",
            file=sys.stderr,
        )
        sys.exit(1)

    if not have_anthropic:
        print(
            "ERROR: ANTHROPIC_API_KEY is not set. Set it in .env or your shell.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "Get a key: https://console.anthropic.com/",
            file=sys.stderr,
        )
        sys.exit(1)

    if not have_openai:
        print(
            "NOTE: OPENAI_API_KEY not set — critique + refinement will be skipped.",
            file=sys.stderr,
        )

    return have_anthropic, have_openai
```

- [ ] **Step 2: Verify module still imports + tests still pass**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed`.

---

## Task 14: Implement `main()` with the refinement loop

**Files:**
- Modify: `task3_explainer/explain_portfolio.py`

- [ ] **Step 1: Append `main()` and the `__main__` block at the end of `explain_portfolio.py`**

```python
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate plain-English portfolio risk explanation via Anthropic + OpenAI critique → refine loop.",
    )
    parser.add_argument("--portfolio", required=True, help="path to portfolio JSON file")
    parser.add_argument(
        "--tone",
        choices=VALID_TONES,
        default="beginner",
        help="explanation register: beginner|experienced|expert (default: beginner)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_ANTHROPIC_MODEL,
        help=f"Anthropic model ID (default: {DEFAULT_ANTHROPIC_MODEL})",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Load .env if present (lazy import — keep import error visible if missing)
    from dotenv import load_dotenv
    load_dotenv()

    have_anthropic, have_openai = _check_api_keys()

    portfolio = load_portfolio(args.portfolio)
    metrics = compute_risk_metrics(portfolio)

    # v1: primary explanation (fail loud on Anthropic errors)
    prompt_v1 = build_explainer_prompt(portfolio, metrics, args.tone)
    raw_v1 = call_llm(prompt_v1, args.model)
    parsed_v1 = parse_response(raw_v1)

    # Refinement loop (gated on OpenAI availability, fail-quiet on errors)
    final_raw, final_parsed = raw_v1, parsed_v1
    if have_openai:
        critique_prompt = build_critique_prompt(portfolio, metrics, raw_v1)
        try:
            critique_raw = call_critique_llm(critique_prompt, DEFAULT_OPENAI_CRITIQUE_MODEL)
            critique = parse_critique_response(critique_raw)
            logging.info(f"critique issues_found: {critique['issues_found']}")
            logging.info(f"critique revised_verdict: {critique['revised_verdict']}")

            needs_refine = (
                bool(critique["issues_found"])
                or critique["revised_verdict"] != parsed_v1["verdict"]
            )
            if needs_refine:
                try:
                    refine_prompt = build_refine_prompt(
                        portfolio, metrics, raw_v1, critique, args.tone,
                    )
                    raw_v2 = call_llm(refine_prompt, args.model)
                    parsed_v2 = parse_response(raw_v2)
                    final_raw, final_parsed = raw_v2, parsed_v2
                    logging.info("explanation refined using critique feedback")
                except Exception as e:
                    logging.warning(
                        f"refinement call failed, falling back to v1: {e}",
                        exc_info=True,
                    )
            else:
                logging.info("critique found no issues; v1 used as final")
        except Exception as e:
            logging.warning(
                f"critique unavailable, no refinement applied: {e}",
                exc_info=True,
            )

    # Output: ONLY the final (possibly-refined) explanation
    sep = "═" * 60
    print(sep)
    print("RAW LLM RESPONSE")
    print(sep)
    print(final_raw)
    print()
    print(format_output(final_parsed))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify module still imports + tests still pass**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed`.

- [ ] **Step 3: Verify `--help` works (no API keys needed)**

```bash
python task3_explainer/explain_portfolio.py --help
```

Expected: argparse usage message listing `--portfolio`, `--tone`, `--model`.

---

## Task 15: End-to-end manual verification

**Files:** none changed.

**Prerequisite:** `cp .env.example .env`, then fill in real `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. The user has these keys; they must be added before running this task.

- [ ] **Step 1: Confirm `.env` exists and is gitignored**

```bash
ls -la .env
git status | grep -i '.env' || echo ".env not in git status (good — gitignored)"
```

Expected: `.env` exists; `git status` does NOT list it (it's already in `.gitignore`).

- [ ] **Step 2: Happy-path live run with aggressive portfolio**

```bash
python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio.json
echo "exit code: $?"
```

Expected: INFO logs on stderr show critique findings + whether refinement happened. Stdout shows `RAW LLM RESPONSE` section + `PARSED OUTPUT` section. Verdict is one of `{Aggressive, Balanced, Conservative}`. Exit code 0.

- [ ] **Step 3: Conservative portfolio (verdict varies — spec acceptance test 2)**

```bash
python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio_conservative.json
echo "exit code: $?"
```

Expected: verdict is `Conservative` (or rarely `Balanced`, but not `Aggressive` — proves no hardcoding).

- [ ] **Step 4: Tone variation (spec acceptance test 3)**

```bash
python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio.json --tone expert
```

Expected: output uses precise financial terminology — words like "drawdown", "tail risk", "concentration", with less hand-holding than `beginner`. Manual eyeball check.

- [ ] **Step 5: Verdict consistency across 3 runs (spec acceptance test 6)**

```bash
for i in 1 2 3; do
    echo "--- run $i ---"
    python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio.json 2>/dev/null | grep "Verdict:"
done
```

Expected: same verdict on all 3 runs (the prompt should be tight enough). If verdicts vary, the prompt is too loose — investigate before declaring done.

- [ ] **Step 6: OpenAI key missing — critique skipped (fail-quiet)**

```bash
OPENAI_API_KEY="" python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio.json
echo "exit code: $?"
```

Expected: stderr says `NOTE: OPENAI_API_KEY not set — critique + refinement will be skipped.` Script runs successfully with v1 explanation only. Exit code 0. (`OPENAI_API_KEY=""` in the command env overrides the .env value — Python reads env vars after `load_dotenv()`, but `os.environ.get("OPENAI_API_KEY")` reflects the empty value.)

Note: if `OPENAI_API_KEY=""` doesn't override (because dotenv won't override existing env), unset it explicitly:

```bash
unset OPENAI_API_KEY  # in a subshell to keep .env intact
python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio.json
```

- [ ] **Step 7: Anthropic key missing — fail loud (spec acceptance test 5)**

```bash
ANTHROPIC_API_KEY="" python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio.json
echo "exit code: $?"
```

Expected: stderr shows `ERROR: ANTHROPIC_API_KEY is not set. ...` setup message. Exit code 1.

- [ ] **Step 8: Bad portfolio JSON file (spec acceptance test 4)**

```bash
echo "{not valid json" > /tmp/bad.json
python task3_explainer/explain_portfolio.py --portfolio /tmp/bad.json
echo "exit code: $?"
rm /tmp/bad.json
```

Expected: clear `ValueError` mentioning `/tmp/bad.json`. Exit code non-zero.

- [ ] **Step 9: Run the test suite one more time**

```bash
python task3_explainer/test_explain_portfolio.py
```

Expected: `All tests passed` (8 tests).

---

## Task 16: First commit on the branch — code, tests, prompts, samples, deps, .env.example, spec, plan

**Files:**
- Add: `task3_explainer/explain_portfolio.py`, `task3_explainer/test_explain_portfolio.py`
- Add: `task3_explainer/prompts/explainer.txt`, `task3_explainer/prompts/critique.txt`, `task3_explainer/prompts/refine.txt`
- Add: `task3_explainer/prompts/iteration_log/explainer_v1.txt`, `_v2.txt`, `_v3.txt`
- Add: `task3_explainer/sample_portfolio.json`, `task3_explainer/sample_portfolio_conservative.json`
- Add: `.env.example`
- Add: `docs/superpowers/specs/2026-05-02-task3-explainer-design.md`
- Add: `docs/superpowers/plans/2026-05-02-task3-explainer.md`
- Modify: `requirements.txt`

- [ ] **Step 1: Confirm `.env` is NOT staged (it must be gitignored)**

```bash
git status
```

Expected: `.env` does NOT appear under any section. If it does, fix `.gitignore` before continuing — committing real API keys is a security incident.

- [ ] **Step 2: Stage explicitly (do not use `git add .`)**

```bash
git add \
    task3_explainer/explain_portfolio.py \
    task3_explainer/test_explain_portfolio.py \
    task3_explainer/prompts/explainer.txt \
    task3_explainer/prompts/critique.txt \
    task3_explainer/prompts/refine.txt \
    task3_explainer/prompts/iteration_log/explainer_v1.txt \
    task3_explainer/prompts/iteration_log/explainer_v2.txt \
    task3_explainer/prompts/iteration_log/explainer_v3.txt \
    task3_explainer/sample_portfolio.json \
    task3_explainer/sample_portfolio_conservative.json \
    .env.example \
    requirements.txt \
    docs/superpowers/specs/2026-05-02-task3-explainer-design.md \
    docs/superpowers/plans/2026-05-02-task3-explainer.md
git status
```

Expected: only the listed files appear under "Changes to be committed". `.DS_Store` and `.env` should NOT appear staged.

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
task3: implement LLM portfolio explainer with cross-vendor critique → refine loop

Adds task3_explainer/explain_portfolio.py — loads a portfolio JSON, computes
risk metrics by reusing Task 1's compute_risk_metrics, asks Anthropic Claude
(Sonnet) to explain it as 4-key JSON, runs an OpenAI gpt-4o cross-vendor
critique, and refines the explanation with Anthropic if the critique
disagrees. The critique itself is logged to stderr but never displayed —
the user sees only the final refined explanation.

Sample portfolios (aggressive + 95% cash) ship for the spec's
"verdict varies" acceptance test. Prompt templates live in prompts/*.txt
loaded via string.Template. prompts/iteration_log/ holds the v1→v2→v3
prompt history for the README's prompt-iteration narrative.

Adds 8 plain-assert tests covering load_portfolio, prompt building, parsing
(both schemas with verdict-enum validation), and verifies format_output
never includes a critique section.

Appends anthropic + openai + python-dotenv to requirements.txt and adds
.env.example as a setup template.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -3
```

Expected: commit succeeds; new commit on top of `2f06e35`.

---

## Task 17: Write `task3_explainer/README.md` and update root `README.md`

**Files:**
- Create: `task3_explainer/README.md`
- Modify: `README.md`

- [ ] **Step 1: Create `task3_explainer/README.md` with placeholders**

```markdown
# Task 3 — AI-Powered Portfolio Explainer

## Summary

`explain_portfolio.py` takes a portfolio JSON, computes risk metrics by reusing
Task 1's `compute_risk_metrics`, and produces a plain-English risk explanation
via Anthropic Claude. A second LLM call to OpenAI `gpt-4o` critiques the
explanation cross-vendor; if the critique surfaces issues or disagrees with the
verdict, Claude is re-prompted to produce a refined version. The user sees only
the final refined explanation — the critique is logged to stderr for
transparency but never displayed.

## Run

```bash
# Setup once: copy the env template and fill in your keys
cp .env.example .env
# then edit .env and paste in your ANTHROPIC_API_KEY and OPENAI_API_KEY

pip install -r requirements.txt

# Aggressive portfolio (BTC 30 / NIFTY 40 / GOLD 20 / CASH 10)
python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio.json

# Conservative portfolio (95% cash)
python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio_conservative.json

# Vary the tone
python task3_explainer/explain_portfolio.py --portfolio task3_explainer/sample_portfolio.json --tone expert

# Run the (mocked) tests
python task3_explainer/test_explain_portfolio.py
```

If `OPENAI_API_KEY` is missing, the critique step is skipped and the script
returns the v1 explanation directly. If `ANTHROPIC_API_KEY` is missing, the
script exits with a clear setup message.

## Acceptance tests (per spec)

- **Happy path:** runs end-to-end on `sample_portfolio.json`; verdict is one of
  `{Aggressive, Balanced, Conservative}`.
- **Verdict varies:** `sample_portfolio_conservative.json` produces verdict
  `Conservative` (proves no hardcoding).
- **Tone variation:** `--tone expert` uses sharper financial vocabulary.
- **Bad JSON:** clear error message naming the file.
- **Missing API key:** `ANTHROPIC_API_KEY` unset → exit 1 with setup message.
- **Verdict consistency:** running the same portfolio 3 times gives the same
  verdict (the prompt is tight).

## Provider chosen + why

- **Primary:** Anthropic Claude Sonnet — the spec calls Anthropic the Timecell
  stack and the same SDK we use for Claude Code. Sonnet's cost/quality is
  appropriate for short structured-output tasks.
- **Critique:** OpenAI `gpt-4o` — using a *different* vendor for the critique
  pass gives a genuine independent assessment, not a model echoing its own
  reasoning. The cross-vendor structure is the design's whole point.

## Prompt iteration log

Three snapshots in [`prompts/iteration_log/`](prompts/iteration_log/) tell
the story:

- **v1** ([explainer_v1.txt](prompts/iteration_log/explainer_v1.txt)) — the
  naive first attempt. No verdict-enum constraint, no example output, no
  explicit "no fences" rule. **What broke:** verdicts came back as
  `"moderate"`, `"high-risk"`, `"balanced-aggressive"` — anything but the
  three valid values. The model also occasionally wrapped its output in
  ```` ```json ```` fences despite no instruction to do so.
- **v2** ([explainer_v2.txt](prompts/iteration_log/explainer_v2.txt)) — added
  the verdict-enum constraint with explicit "MUST be exactly one of" wording,
  added a "no markdown, no fences" rule, and added "reference specific numbers
  / do not invent data" rules. **What broke:** verdicts were valid now, but
  explanations were generic — they didn't reference the actual portfolio
  numbers, and the tone was always corporate-formal regardless of `--tone`.
- **v3** ([explainer_v3.txt](prompts/iteration_log/explainer_v3.txt)) =
  current production [`prompts/explainer.txt`](prompts/explainer.txt). Added
  the `<example_output>` block (one good example > ten rules) and the
  `<tone_definitions>` block. **What worked:** the example locked the JSON
  shape, the conversational register, and the level of specificity. Tone
  variation became visible across runs. Belt-and-suspenders fence-stripping
  in `parse_response` catches the rare residual ```` ``` ``` ```` wrapper.

The fence-stripping is preserved in the parser even though v3 says "no
fences" — model behavior under instructions is probabilistic, and the
defensive parse costs five lines.

## Why pre-compute the metrics

LLMs are bad at arithmetic — even simple multiplications and divisions can
hallucinate. By running Task 1's `compute_risk_metrics` first and passing the
five derived metrics into the prompt, the LLM's job is *narration*, not
*calculation*. The prompt explicitly says "do not recompute these — you may
make arithmetic errors." This shifts the LLM from "compute and explain" to
"interpret and communicate," which it does much better.

## What didn't work

- **Single combined "explain + critique" prompt:** tried to get one LLM call
  to produce both an explanation and self-critique in one JSON. The critique
  was always self-congratulatory ("the explanation is excellent and accurate")
  — same model, same biases. Splitting into two LLMs (different vendors)
  produced honest critiques.
- **Tested forcing the critique LLM with `temperature=0`:** marginal effect
  on consistency, no effect on quality. Removed the override; SDK defaults
  are fine.
- **Tested using OpenAI's `response_format=json_schema` with a strict schema
  definition:** technically more rigorous, but adds a schema definition to
  maintain. The `json_object` mode + post-parse validation is simpler and
  catches the same errors.

## AI tool usage

[Filled in retrospectively after implementation — what Claude Code helped with.]
```

- [ ] **Step 2: Update the Task 3 line in the root `README.md`**

Replace `- Task 3 — AI-Powered Portfolio Explainer (TBD)` with:

```markdown
- [Task 3 — AI-Powered Portfolio Explainer](task3_explainer/README.md)
```

(No other root README changes — the AI-tooling section already covers Task 3.)

- [ ] **Step 3: Skim both files**

```bash
cat task3_explainer/README.md | head -40
echo "---"
cat README.md
```

Expected: both files render cleanly with no broken Markdown.

---

## Task 18: Second commit on the branch — READMEs

**Files:**
- Add: `task3_explainer/README.md`
- Modify: `README.md`

- [ ] **Step 1: Stage and commit**

```bash
git add task3_explainer/README.md README.md
git status
git commit -m "$(cat <<'EOF'
task3: add per-task README and update root README link

Adds task3_explainer/README.md with sections required by spec: summary, run
instructions, acceptance tests, provider chosen + why, prompt iteration log
(narrating the v1→v2→v3 history with what failed and what fixed it), why
pre-compute metrics, what didn't work, and a placeholder for AI tool usage.
Updates the Task 3 entry in the root README from "(TBD)" to a link to the
per-task README.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -4
```

Expected: two commits on the branch ahead of `2f06e35`.

---

## Task 19: Fill in AI-usage notes, amend, then ask the user about pushing/PR

**Files:**
- Modify: `task3_explainer/README.md` (replace AI-usage placeholder)

- [ ] **Step 1: Replace the per-task AI-usage placeholder**

Replace the `## AI tool usage` placeholder paragraph in `task3_explainer/README.md` with a real, honest summary of what Claude Code did during Task 3. Suggested talking points:

- The cross-vendor critique → refine loop was a brainstorming-phase choice (asked the user for B+ii failure behavior; later redesigned to hide the critique entirely and use it for refinement instead).
- The `string.Template` choice (over f-strings) was made specifically to avoid `{{` brace-escaping in the JSON example blocks of prompt files.
- Claude Code surfaced the `bool`-exclusion guard reused conceptually from Task 1, the fence-stripping defense pattern in parse_response, and the cost note about doubling Anthropic call count via the refinement pass.
- The `claude-api` skill was invoked early in implementation to confirm the latest Sonnet model ID.
- Test design: kept tests deterministic by mocking SDKs only as needed (no live network); the spec's manual acceptance tests cover the live happy-path.

Keep the section 4–6 sentences. Be honest about what Claude Code helped with vs. what was straightforward.

- [ ] **Step 2: Amend the README commit**

```bash
git add task3_explainer/README.md
git commit --amend --no-edit
git log --oneline | head -4
```

Expected: still two commits ahead of `2f06e35`; the README commit is updated in place.

- [ ] **Step 3: Stop and ask the user**

Per the workflow rule (CLAUDE.md Part 1, item 2), do NOT push or open the PR unprompted. Surface to the user:

> "Implementation complete on branch `task3/explainer`. Two commits ahead of `main`: code+tests+prompts+samples+requirements+.env.example+spec+plan, then READMEs. All 8 mocked tests pass. Live verification: aggressive portfolio produced verdict X (Aggressive expected); conservative portfolio produced verdict Y (Conservative expected); --tone expert visibly uses more financial terminology; running the aggressive portfolio 3 times produced consistent verdicts. OPENAI_API_KEY-missing path skipped critique cleanly. ANTHROPIC_API_KEY-missing path exited 1 with setup message. Bad portfolio JSON produced a clear error. Ready to push and open PR #3 for review?"

Wait for explicit user approval before running `git push -u origin task3/explainer` or `gh pr create`.

---

## Self-review

**1. Spec coverage:**

| Spec section | Task |
|---|---|
| §1 file layout (explain_portfolio.py + test + prompts/ + iteration_log/ + samples + README) | Tasks 2, 4, 5, 6, 17 |
| §1 module top-to-bottom order (constants → 3 builders → 2 callers → 2 parsers → format → keys → main) | Tasks 2, 7, 8, 10, 11, 12, 13, 14 |
| §1 sys.path import of compute_risk_metrics | Task 2 step 1 |
| §1 .env.example committed | Tasks 1, 16 |
| §2 load_portfolio with FileNotFoundError + JSONDecodeError wrapping | Task 3 |
| §2 metrics step is one line (no wrapper) | Task 14 step 1 |
| §3 string.Template + external prompt files | Tasks 5, 7 |
| §3 default=str in json.dumps for inf | Task 7 step 1 |
| §3 three prompt files (explainer, critique, refine) | Task 5 |
| §4 call_llm + call_critique_llm + json_object mode + lazy SDK imports | Task 12 |
| §4 _check_api_keys with three branches + sys.exit(1) | Task 13 |
| §5 parse_response with fence-stripping + verdict enum | Task 8 |
| §5 parse_critique_response | Task 10 |
| §5 format_output (no critique parameter) | Task 11 |
| §6 main() with refinement-decision matrix logic | Task 14 step 1 |
| §6 RAW LLM RESPONSE printed in main() (not format_output) | Task 14 step 1 |
| §7 8 tests + plain-assert + sibling import + runner | Tasks 2, 3, 7, 8, 9, 10, 11 |
| §8 branching, two commits | Tasks 1, 16, 18 |
| §8 verification commands (8 acceptance scenarios) | Task 15 |
| §8 README with all required sections (provider, prompt iteration log, why pre-compute, what didn't work, AI usage) | Task 17 |
| Workflow rule: confirm Sonnet model via claude-api skill | Task 1 step 6 |
| Workflow rule: ask before push/PR | Task 19 step 3 |

No gaps.

**2. Placeholder scan:** The `[Filled retrospectively...]` string in Task 17 is intentional README content replaced in Task 19. The `claude-sonnet-4-6` constant in Task 2 step 1 was confirmed in Task 1 step 6 (claude-api skill, 2026-04-30). No `TBD`/`TODO`/`add appropriate X` patterns in the plan body itself.

**3. Type/name consistency:**
- Module constants: `DEFAULT_ANTHROPIC_MODEL`, `DEFAULT_OPENAI_CRITIQUE_MODEL`, `VALID_VERDICTS`, `VALID_TONES`, `PROMPTS_DIR` — defined in Task 2, referenced in Tasks 7, 8, 9, 10, 14.
- Function signatures: `load_portfolio(path)`, `build_explainer_prompt(portfolio, metrics, tone="beginner")`, `build_critique_prompt(portfolio, metrics, primary_response)`, `build_refine_prompt(portfolio, metrics, previous_response, critique, tone="beginner")`, `call_llm(prompt, model)`, `call_critique_llm(prompt, model)`, `parse_response(raw)`, `parse_critique_response(raw)`, `format_output(parsed)`, `_check_api_keys()`, `main()`. Match across all references.
- Critique dict keys: `issues_found` (list), `revised_verdict` (str). Used consistently in Tasks 7 (build_refine_prompt reads them), 10 (parse validates them), 14 (main checks both for refinement decision).
- Test names match the spec's table verbatim. Runner block has a corresponding entry for every test added.
- Sample portfolio paths: `task3_explainer/sample_portfolio.json` and `task3_explainer/sample_portfolio_conservative.json` — used identically in Tasks 4, 15, 17.

No inconsistencies.
