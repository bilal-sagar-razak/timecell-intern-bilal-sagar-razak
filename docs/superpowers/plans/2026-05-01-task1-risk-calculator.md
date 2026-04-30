# Task 1 — Portfolio Risk Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `compute_risk_metrics(portfolio: dict) -> dict` in `task1_risk/risk.py` that returns the 5 spec-required risk metrics for a portfolio under a crash scenario, with stdlib-only code, plain-`assert` tests, and per-task + root README updates.

**Architecture:** Flat `task1_risk/` module — no package, no `__init__.py`, run as scripts. `risk.py` holds named constants → validator → math helper → orchestrator → `__main__` block, in that order. `test_risk.py` sits next to it as a sibling import. Tests are added incrementally TDD-style; commits are batched into the two approved commits per the design.

**Tech Stack:** Python 3.10+, stdlib only (`json`, `sys`, `copy`, `math`). No third-party deps. No test runner — plain `assert` + `python file.py`.

**Spec:** [docs/superpowers/specs/2026-05-01-task1-risk-design.md](../specs/2026-05-01-task1-risk-design.md)

---

## Task 1: Initial scaffold commit on `main`, then create feature branch

**Files:**
- Create: `task4_open/.gitkeep` (empty file so the directory survives git)
- Already exist (will be added): `.gitignore`, `CLAUDE.md`, `README.md`, `requirements.txt`, `task1_risk/task1_instruction.md`, `task2_market/task2_instruction.md`, `task3_explainer/task3_instruction.md`, `docs/superpowers/specs/2026-05-01-task1-risk-design.md`, `docs/superpowers/plans/2026-05-01-task1-risk-calculator.md` (this file)

- [ ] **Step 1: Verify clean working state and zero-commit `main`**

```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak
git status
git log --oneline 2>&1 | head -5
```

Expected: `git status` shows untracked scaffold files. `git log` reports `fatal: your current branch 'main' does not have any commits yet`.

- [ ] **Step 2: Add `task4_open/.gitkeep` so the empty dir is tracked**

```bash
touch task4_open/.gitkeep
```

- [ ] **Step 3: Stage scaffold files explicitly (do NOT use `git add .`)**

```bash
git add .gitignore CLAUDE.md README.md requirements.txt \
    task1_risk/task1_instruction.md \
    task2_market/task2_instruction.md \
    task3_explainer/task3_instruction.md \
    task4_open/.gitkeep \
    docs/superpowers/specs/2026-05-01-task1-risk-design.md \
    docs/superpowers/plans/2026-05-01-task1-risk-calculator.md
git status
```

Expected: only the listed files appear under "Changes to be committed". `.DS_Store` and `.venv/` should NOT appear (verify they are still untracked or ignored).

- [ ] **Step 4: Commit the scaffold on `main`**

```bash
git commit -m "$(cat <<'EOF'
chore: initial scaffold — task instructions, CLAUDE.md, Task 1 design+plan

Adds the four task instruction files, CLAUDE.md (workflow guidelines + project
context), .gitignore, empty README.md and requirements.txt, and the Task 1
design + implementation plan under docs/superpowers/.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds. `git log --oneline` shows one commit on `main`.

- [ ] **Step 5: Create and switch to feature branch**

```bash
git checkout -b task1/risk-calculator
git status
```

Expected: `On branch task1/risk-calculator. nothing to commit, working tree clean.`

---

## Task 2: TDD test 1 — `post_crash_value` on sample portfolio

**Files:**
- Create: `task1_risk/risk.py`
- Create: `task1_risk/test_risk.py`

- [ ] **Step 1: Write `test_risk.py` with the sample fixture and the first failing test**

```python
"""Tests for task1_risk.risk — plain-assert, no pytest."""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

# Sibling import: ensure task1_risk/ is on sys.path when running from repo root
sys.path.insert(0, str(Path(__file__).parent))

from risk import compute_risk_metrics  # noqa: E402


SAMPLE = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 80_000,
    "assets": [
        {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct": 0},
    ],
}


def test_post_crash_value_sample() -> None:
    result = compute_risk_metrics(SAMPLE)
    assert math.isclose(result["post_crash_value"], 5_700_000, rel_tol=1e-9), \
        f"expected 5_700_000, got {result['post_crash_value']}"


if __name__ == "__main__":
    test_post_crash_value_sample()
    print("All tests passed")
```

- [ ] **Step 2: Run the test and verify it fails**

```bash
python task1_risk/test_risk.py
```

Expected: `ModuleNotFoundError: No module named 'risk'` (because `risk.py` doesn't exist yet).

- [ ] **Step 3: Create minimal `risk.py` with stub validator + helper + orchestrator**

```python
"""Portfolio risk calculator — stdlib only."""
from __future__ import annotations

import json
import sys
from typing import Any


RUIN_THRESHOLD_MONTHS = 12
CONCENTRATION_THRESHOLD_PCT = 40
_VALID_ASSET_KEYS = ("name", "allocation_pct", "expected_crash_pct")


def _validate_portfolio(portfolio: dict) -> None:
    """Stub — full validation added in Task 9."""
    return None


def _asset_post_crash_value(asset: dict, total_value_inr: float) -> float:
    asset_value = total_value_inr * (asset["allocation_pct"] / 100)
    return asset_value * (1 + asset["expected_crash_pct"] / 100)


def compute_risk_metrics(portfolio: dict) -> dict[str, Any]:
    _validate_portfolio(portfolio)
    assets = portfolio["assets"]
    total_value = portfolio["total_value_inr"]

    post_crash_value = sum(_asset_post_crash_value(a, total_value) for a in assets)

    return {
        "post_crash_value": post_crash_value,
    }
```

- [ ] **Step 4: Run the test and verify it passes**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`.

---

## Task 3: TDD test 2 — `runway_months` and `ruin_test`

**Files:**
- Modify: `task1_risk/test_risk.py` (append a test, update runner)
- Modify: `task1_risk/risk.py` (extend `compute_risk_metrics` return)

- [ ] **Step 1: Add the failing test above the runner block in `test_risk.py`**

Insert this function after `test_post_crash_value_sample` and before `if __name__ == "__main__":`:

```python
def test_runway_and_ruin_test_sample() -> None:
    result = compute_risk_metrics(SAMPLE)
    assert math.isclose(result["runway_months"], 71.25, rel_tol=1e-9), \
        f"expected 71.25, got {result['runway_months']}"
    assert result["ruin_test"] == "PASS", \
        f"expected 'PASS', got {result['ruin_test']!r}"
```

Update the runner block:

```python
if __name__ == "__main__":
    test_post_crash_value_sample()
    test_runway_and_ruin_test_sample()
    print("All tests passed")
```

- [ ] **Step 2: Run and verify it fails with `KeyError: 'runway_months'`**

```bash
python task1_risk/test_risk.py
```

Expected: `KeyError: 'runway_months'`.

- [ ] **Step 3: Extend `compute_risk_metrics` in `risk.py`**

Replace the function body with:

```python
def compute_risk_metrics(portfolio: dict) -> dict[str, Any]:
    _validate_portfolio(portfolio)
    assets = portfolio["assets"]
    total_value = portfolio["total_value_inr"]
    monthly_expenses = portfolio["monthly_expenses_inr"]

    post_crash_value = sum(_asset_post_crash_value(a, total_value) for a in assets)

    if monthly_expenses == 0:
        runway_months = float("inf")
    else:
        runway_months = post_crash_value / monthly_expenses

    ruin_test = "PASS" if runway_months > RUIN_THRESHOLD_MONTHS else "FAIL"

    return {
        "post_crash_value": post_crash_value,
        "runway_months": runway_months,
        "ruin_test": ruin_test,
    }
```

- [ ] **Step 4: Run and verify both tests pass**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`.

---

## Task 4: TDD test 3 — `largest_risk_asset`

**Files:**
- Modify: `task1_risk/test_risk.py`
- Modify: `task1_risk/risk.py`

- [ ] **Step 1: Add the failing test in `test_risk.py`**

Insert before the runner block:

```python
def test_largest_risk_asset_sample() -> None:
    result = compute_risk_metrics(SAMPLE)
    assert result["largest_risk_asset"] == "BTC", \
        f"expected 'BTC', got {result['largest_risk_asset']!r}"
```

Add to the runner block:

```python
    test_largest_risk_asset_sample()
```

- [ ] **Step 2: Run and verify failure**

```bash
python task1_risk/test_risk.py
```

Expected: `KeyError: 'largest_risk_asset'`.

- [ ] **Step 3: Extend `compute_risk_metrics`**

Insert this calculation block in `compute_risk_metrics` after the `ruin_test` line, before the `return`:

```python
    if assets:
        largest_risk_asset = max(
            assets,
            key=lambda a: a["allocation_pct"] * abs(a["expected_crash_pct"]),
        )["name"]
    else:
        largest_risk_asset = None
```

Add `"largest_risk_asset": largest_risk_asset,` to the return dict (place it after `ruin_test`).

- [ ] **Step 4: Run and verify all three tests pass**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`.

---

## Task 5: TDD test 4 — `concentration_warning` boundary check

**Files:**
- Modify: `task1_risk/test_risk.py`
- Modify: `task1_risk/risk.py`

- [ ] **Step 1: Add failing test**

Insert before the runner block:

```python
def test_concentration_boundary() -> None:
    result = compute_risk_metrics(SAMPLE)
    # NIFTY50 is exactly 40 — must NOT trigger (strict > 40 only)
    assert result["concentration_warning"] is False, \
        f"expected False, got {result['concentration_warning']!r}"
```

Add to runner: `test_concentration_boundary()`.

- [ ] **Step 2: Run and verify failure**

```bash
python task1_risk/test_risk.py
```

Expected: `KeyError: 'concentration_warning'`.

- [ ] **Step 3: Extend `compute_risk_metrics`**

Add this line in `compute_risk_metrics` before the `return`:

```python
    concentration_warning = any(
        a["allocation_pct"] > CONCENTRATION_THRESHOLD_PCT for a in assets
    )
```

Add `"concentration_warning": concentration_warning,` as the last entry in the return dict.

- [ ] **Step 4: Run and verify all four tests pass**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`.

---

## Task 6: TDD test 5 — zero-expenses edge case

**Files:**
- Modify: `task1_risk/test_risk.py`

(No `risk.py` change expected — the `monthly_expenses == 0` branch was already added in Task 3.)

- [ ] **Step 1: Add failing test**

Insert before the runner block:

```python
def test_zero_expenses() -> None:
    portfolio = copy.deepcopy(SAMPLE)
    portfolio["monthly_expenses_inr"] = 0
    result = compute_risk_metrics(portfolio)
    assert result["runway_months"] == float("inf"), \
        f"expected inf, got {result['runway_months']}"
    assert result["ruin_test"] == "PASS", \
        f"expected 'PASS', got {result['ruin_test']!r}"
```

Add to runner: `test_zero_expenses()`.

- [ ] **Step 2: Run and verify the test passes (first run)**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`. (If it fails, the zero-expenses branch from Task 3 is wrong — debug before continuing.)

---

## Task 7: TDD test 6 — empty-assets edge case

**Files:**
- Modify: `task1_risk/test_risk.py`

(The empty-assets branches in `largest_risk_asset` and `sum(...)` were already added in earlier tasks.)

- [ ] **Step 1: Add failing test**

Insert before the runner block:

```python
def test_empty_assets() -> None:
    portfolio = {
        "total_value_inr": 1_000_000,
        "monthly_expenses_inr": 50_000,
        "assets": [],
    }
    result = compute_risk_metrics(portfolio)
    assert result["post_crash_value"] == 0, \
        f"expected 0, got {result['post_crash_value']}"
    assert result["largest_risk_asset"] is None, \
        f"expected None, got {result['largest_risk_asset']!r}"
    assert result["concentration_warning"] is False, \
        f"expected False, got {result['concentration_warning']!r}"
```

Add to runner: `test_empty_assets()`.

- [ ] **Step 2: Run and verify the test passes**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`. (If it fails, the `if assets else None` branch in `largest_risk_asset` is wrong — debug.)

---

## Task 8: TDD test 7 — single asset at 50% triggers concentration warning

**Files:**
- Modify: `task1_risk/test_risk.py`

- [ ] **Step 1: Add failing test**

Insert before the runner block:

```python
def test_single_asset_50pct() -> None:
    portfolio = {
        "total_value_inr": 1_000_000,
        "monthly_expenses_inr": 10_000,
        "assets": [
            {"name": "ONLY", "allocation_pct": 50, "expected_crash_pct": -20},
        ],
    }
    result = compute_risk_metrics(portfolio)
    assert result["concentration_warning"] is True, \
        f"expected True, got {result['concentration_warning']!r}"
```

Add to runner: `test_single_asset_50pct()`.

- [ ] **Step 2: Run and verify the test passes**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`.

---

## Task 9: TDD test 9 — validator raises on missing key, then implement full validator

**Files:**
- Modify: `task1_risk/test_risk.py`
- Modify: `task1_risk/risk.py` (replace stub validator with full implementation)

- [ ] **Step 1: Add failing test**

Insert before the runner block:

```python
def test_validation_raises_on_missing_key() -> None:
    try:
        compute_risk_metrics({})
    except ValueError:
        return
    raise AssertionError("expected ValueError, none raised")
```

Add to runner: `test_validation_raises_on_missing_key()`.

- [ ] **Step 2: Run and verify failure**

```bash
python task1_risk/test_risk.py
```

Expected: `KeyError: 'assets'` (the stub validator passes, then `portfolio["assets"]` raises `KeyError`, not `ValueError`).

- [ ] **Step 3: Replace the stub `_validate_portfolio` with the full implementation**

Replace the stub function body with:

```python
def _validate_portfolio(portfolio: dict) -> None:
    """Raise ValueError on bad input. Allocation-sum mismatch only warns."""
    if not isinstance(portfolio, dict):
        raise ValueError("portfolio must be a dict")

    for key in ("total_value_inr", "monthly_expenses_inr", "assets"):
        if key not in portfolio:
            raise ValueError(f"missing required key: {key}")

    for field in ("total_value_inr", "monthly_expenses_inr"):
        value = portfolio[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be a number, got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"{field} must be >= 0, got {value}")

    assets = portfolio["assets"]
    if not isinstance(assets, list):
        raise ValueError("assets must be a list")

    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise ValueError(f"asset[{i}] must be a dict")
        for key in _VALID_ASSET_KEYS:
            if key not in asset:
                raise ValueError(f"asset[{i}].{key}: missing")

        name = asset["name"]
        if not isinstance(name, str) or not name:
            raise ValueError(f"asset[{i}].name: must be a non-empty string")

        alloc = asset["allocation_pct"]
        if isinstance(alloc, bool) or not isinstance(alloc, (int, float)):
            raise ValueError(f"asset[{i}].allocation_pct: must be a number")
        if not (0 <= alloc <= 100):
            raise ValueError(f"asset[{i}].allocation_pct: must be in [0, 100], got {alloc}")

        crash = asset["expected_crash_pct"]
        if isinstance(crash, bool) or not isinstance(crash, (int, float)):
            raise ValueError(f"asset[{i}].expected_crash_pct: must be a number")
        if crash > 0:
            raise ValueError(f"asset[{i}].expected_crash_pct: must be <= 0, got {crash}")

    if assets:
        total_alloc = sum(a["allocation_pct"] for a in assets)
        if not (99.99 <= total_alloc <= 100.01):
            print(
                f"warning: allocations sum to {total_alloc:.2f}, not 100",
                file=sys.stderr,
            )
```

- [ ] **Step 4: Run and verify all seven tests pass**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`.

---

## Task 10: TDD test 8 — input is not mutated

**Files:**
- Modify: `task1_risk/test_risk.py`

(No `risk.py` change expected — `compute_risk_metrics` already does not mutate, but this test is the safety net.)

- [ ] **Step 1: Add the test**

Insert before the runner block:

```python
def test_input_not_mutated() -> None:
    snapshot = copy.deepcopy(SAMPLE)
    compute_risk_metrics(SAMPLE)
    assert SAMPLE == snapshot, "compute_risk_metrics mutated its input"
```

Add to runner: `test_input_not_mutated()`.

- [ ] **Step 2: Run and verify it passes**

```bash
python task1_risk/test_risk.py
```

Expected: `All tests passed`. If it fails, find the mutation site in `risk.py` and fix it (no defensive `copy.deepcopy(portfolio)` — fix the actual write).

---

## Task 11: Add `__main__` block to `risk.py` and verify JSON output

**Files:**
- Modify: `task1_risk/risk.py` (append `__main__` block)

- [ ] **Step 1: Append the `__main__` block at the end of `risk.py`**

```python
if __name__ == "__main__":
    sample = {
        "total_value_inr": 10_000_000,
        "monthly_expenses_inr": 80_000,
        "assets": [
            {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
            {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
            {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
            {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct": 0},
        ],
    }
    print(json.dumps(compute_risk_metrics(sample), indent=2))
```

- [ ] **Step 2: Run `risk.py` and inspect the output**

```bash
python task1_risk/risk.py
```

Expected output (exact values; `Infinity` not present here since expenses > 0):

```
{
  "post_crash_value": 5700000.0,
  "runway_months": 71.25,
  "ruin_test": "PASS",
  "largest_risk_asset": "BTC",
  "concentration_warning": false
}
```

- [ ] **Step 3: Add the `compute_risk_metrics` docstring**

Replace the line `def compute_risk_metrics(portfolio: dict) -> dict[str, Any]:` with the same line followed by this docstring (place immediately after the `def` line):

```python
    """Compute five risk metrics for a portfolio under a crash scenario.

    Args:
        portfolio: dict with keys total_value_inr (>= 0), monthly_expenses_inr
            (>= 0), and assets (list of dicts with name/allocation_pct/
            expected_crash_pct).

    Returns:
        dict with keys post_crash_value (float), runway_months (float; inf
        when expenses == 0), ruin_test ('PASS' if runway > 12 months else
        'FAIL'), largest_risk_asset (asset name with max allocation_pct *
        |expected_crash_pct|, None if no assets, ties broken by first
        appearance), concentration_warning (True if any asset's
        allocation_pct > 40).

    Raises:
        ValueError: on missing keys, wrong types, or negative numeric fields.
            Allocations not summing to 100 only emit a stderr warning.
    """
```

- [ ] **Step 4: Re-run `risk.py` to confirm the docstring didn't break anything**

```bash
python task1_risk/risk.py && python task1_risk/test_risk.py
```

Expected: JSON output (same as Step 2), then `All tests passed`.

---

## Task 12: First commit on the branch — code + tests

**Files:**
- Add: `task1_risk/risk.py`, `task1_risk/test_risk.py`

- [ ] **Step 1: Run the verification checks from Section 5 of the spec**

```bash
python task1_risk/risk.py
python task1_risk/test_risk.py
(cd task1_risk && python -c "from risk import compute_risk_metrics; compute_risk_metrics({})") 2>&1 | tail -3
```

Expected for the third command: `ValueError: missing required key: total_value_inr` (with traceback above it). Non-zero exit code is fine — we're verifying it raises.

- [ ] **Step 2: Stage and commit**

```bash
git add task1_risk/risk.py task1_risk/test_risk.py
git status
git commit -m "$(cat <<'EOF'
task1: implement compute_risk_metrics with validation and tests

Adds task1_risk/risk.py with the five required risk metrics
(post_crash_value, runway_months, ruin_test, largest_risk_asset,
concentration_warning) and task1_risk/test_risk.py with 9 plain-assert
tests covering the spec's 7 acceptance cases plus input-immutability and
validator-wired guards.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -3
```

Expected: two commits — the new one on top, the scaffold commit below.

---

## Task 13: Write `task1_risk/README.md` and seed root `README.md`

**Files:**
- Create: `task1_risk/README.md`
- Modify: `README.md` (currently empty)

- [ ] **Step 1: Create `task1_risk/README.md`**

```markdown
# Task 1 — Portfolio Risk Calculator

## Summary

`compute_risk_metrics(portfolio)` takes a portfolio dict and returns five risk
metrics under a crash scenario: the total post-crash value (INR), the runway
in months at the given monthly burn rate, a `PASS`/`FAIL` ruin test against a
12-month threshold, the name of the asset contributing the most tail risk
(allocation × |expected crash|), and a boolean concentration warning when any
single asset exceeds 40% of the portfolio. Stdlib only — no pandas, no numpy.

## Run

```bash
python task1_risk/risk.py        # prints sample portfolio metrics as JSON
python task1_risk/test_risk.py   # runs 9 assertions, prints "All tests passed"
```

## Design notes

- **Stdlib only** — spec constraint. `json`, `sys`, `copy`, `math` cover it.
- **Pure orchestrator** — `compute_risk_metrics` does not perform I/O and does
  not mutate its input. The `__main__` block is the only place that prints.
- **Tie-break on `largest_risk_asset`** — relies on Python's `max()` returning
  the first occurrence on ties, matching the spec's "first appearance" rule.
- **Allocation-sum mismatch is a warning, not a raise** — per spec edge case 3,
  the function still computes; the warning goes to `stderr`.
- **`bool` excluded from numeric fields** — `isinstance(True, int)` is `True`
  in Python, so `total_value_inr=True` would silently become `1` without an
  explicit `bool` rejection.

## AI tool usage

[Filled in retrospectively after implementation — what Claude Code helped with.]
```

- [ ] **Step 2: Replace the empty root `README.md` with the seed**

```markdown
# Timecell internship technical test

Four self-contained Python tasks. Each task lives in its own folder with a
per-task README.

## Tasks

- [Task 1 — Portfolio Risk Calculator](task1_risk/README.md)
- Task 2 — Live Market Data Fetch (TBD)
- Task 3 — AI-Powered Portfolio Explainer (TBD)
- Task 4 — Open (TBD)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # currently empty; populated by tasks 2 and 3
```

## AI tooling

[Project-wide note on how Claude Code was used across tasks — appended as tasks land.]
```

- [ ] **Step 3: Skim both files in a terminal**

```bash
cat task1_risk/README.md
echo "---"
cat README.md
```

Expected: both render cleanly with no broken Markdown.

---

## Task 14: Second commit on the branch — READMEs

**Files:**
- Add: `task1_risk/README.md`
- Modify: `README.md`

- [ ] **Step 1: Stage and commit**

```bash
git add task1_risk/README.md README.md
git status
git commit -m "$(cat <<'EOF'
task1: add per-task README and link from root README

Adds task1_risk/README.md (summary, run instructions, design notes, and
placeholder AI-usage section) and seeds the root README.md with a project
overview that links to the per-task README.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -4
```

Expected: three commits — READMEs commit on top, code+tests commit, scaffold commit.

---

## Task 15: Fill in AI-usage notes, then ask the user about pushing/PR

**Files:**
- Modify: `task1_risk/README.md` (replace AI-usage placeholder)
- Modify: `README.md` (replace AI-tooling placeholder)

- [ ] **Step 1: Replace the per-task AI-usage placeholder**

Replace the placeholder paragraph in `task1_risk/README.md` with a real, honest summary of what Claude Code did during Task 1 (e.g., "Used Claude Code to draft the validator's edge-case list including the `isinstance(True, int)` boolean trap and the float-tolerance window for the allocation-sum check; both made it into the final code"). Keep it 2–4 sentences.

- [ ] **Step 2: Replace the project-wide AI-tooling placeholder**

Replace the placeholder paragraph in `README.md` with 1–2 sentences describing the workflow used (e.g., "Each task was developed using the `superpowers` skill chain — `brainstorming` → `writing-plans` → `executing-plans` — with a per-task design and plan committed under `docs/superpowers/`"). Keep it short; per-task READMEs carry the detail.

- [ ] **Step 3: Amend the README commit**

```bash
git add task1_risk/README.md README.md
git commit --amend --no-edit
git log --oneline | head -4
```

Expected: still three commits; the README commit is updated in place.

- [ ] **Step 4: Stop and ask the user**

Per the workflow rule (CLAUDE.md Part 1, item 2), do NOT push or open the PR unprompted. Surface to the user:

> "Implementation complete on branch `task1/risk-calculator`. Three commits ahead of `main`: scaffold (on main), code+tests, READMEs. All 9 tests pass; `python task1_risk/risk.py` prints valid JSON; validator raises `ValueError` on bad input. Ready to push and open a PR for review?"

Wait for explicit user approval before running `git push -u origin task1/risk-calculator` or `gh pr create`.

---

## Self-review

**1. Spec coverage:**

| Spec section | Task |
|---|---|
| §1 file layout (`risk.py` + `test_risk.py` + per-task README) | Tasks 2, 12, 13 |
| §1 root README seed | Task 13 |
| §2 validation rules (1–6, including bool exclusion + stderr warning) | Task 9 |
| §3 computation flow (5 keys, helper, return order) | Tasks 2–5 (incremental), Task 11 (docstring) |
| §3 subtleties (tie-break, zero-expenses, empty assets compose) | Tasks 4, 6, 7 |
| §4 9 tests + sample fixture + runner | Tasks 2–10 |
| §5 branching & two-commit shape | Tasks 1, 12, 14 |
| §5 verification commands (run risk.py, run tests, validator raises) | Task 12 step 1 |
| §5 out-of-scope (bonuses, requirements.txt) | Honored — no bonus tasks, no `requirements.txt` change |
| Workflow rule: ask before push/PR | Task 15 step 4 |

No gaps.

**2. Placeholder scan:** The two `[Filled in retrospectively...]` strings are intentional placeholders for README *content* and are explicitly replaced in Task 15. No `TBD`/`TODO`/`add appropriate X` patterns in the plan itself.

**3. Type/name consistency check:**
- `compute_risk_metrics`, `_validate_portfolio`, `_asset_post_crash_value` — used identically across all tasks.
- `RUIN_THRESHOLD_MONTHS`, `CONCENTRATION_THRESHOLD_PCT`, `_VALID_ASSET_KEYS` — defined in Task 2, referenced in Tasks 3, 5, 9.
- Output dict keys: `post_crash_value`, `runway_months`, `ruin_test`, `largest_risk_asset`, `concentration_warning` — consistent across Tasks 2–5 and the docstring in Task 11.
- Test names — match the spec's table verbatim.

No inconsistencies.
