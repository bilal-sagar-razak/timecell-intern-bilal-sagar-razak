# Task 1 — Portfolio Risk Calculator: Design

**Status:** Approved 2026-05-01
**Source spec:** `task1_risk/task1_instruction.md` (authoritative — this design is the implementation plan that interprets it)
**Scope:** Base task only. Bonuses 1 (`compare_scenarios`) and 2 (`print_allocation_chart`) are deferred to a follow-up branch after base merges.

---

## 1. Architecture & file layout

Two files inside `task1_risk/`, plus a per-task README:

```
task1_risk/
├── risk.py          # ~80–100 lines, stdlib only
├── test_risk.py     # ~50 lines, plain `assert`, no pytest
└── README.md        # task-specific: summary, run instructions,
                     #   design notes, AI-tool-usage for THIS task
```

The **root `README.md`** is project-level only — overview of the four tasks, top-level setup, and an overall AI-tooling note. The Task 1 PR seeds it with a project overview and a link to `task1_risk/README.md`. The substantive Task 1 documentation lives in the per-task README, not the root.

`risk.py` top-to-bottom order:
1. Module docstring (1 line) + `from __future__ import annotations`, `import json`, `import sys`, `from typing import Any`.
2. Named constants: `RUIN_THRESHOLD_MONTHS = 12`, `CONCENTRATION_THRESHOLD_PCT = 40`, `_VALID_ASSET_KEYS = {"name", "allocation_pct", "expected_crash_pct"}`.
3. `_validate_portfolio(portfolio: dict) -> None` — raises `ValueError` on bad input, prints stderr warning if allocations don't sum to 100.
4. `_asset_post_crash_value(asset: dict, total_value_inr: float) -> float` — pure math helper.
5. `compute_risk_metrics(portfolio: dict) -> dict[str, Any]` — orchestrator with full docstring (inputs/outputs/edge cases).
6. `if __name__ == "__main__":` — runs the spec's example portfolio, `print(json.dumps(result, indent=2))`.

No `__init__.py`. Files are run as scripts (`python task1_risk/risk.py`), not imported as a package. Task 3's later import will use a path-manipulation approach — out of scope here.

## 2. Validation rules

`_validate_portfolio` is the only function that raises. Everything downstream trusts the input. Rules in order:

1. **Top-level type** — `portfolio` must be `dict`. Else `ValueError("portfolio must be a dict")`.
2. **Required keys present** — `total_value_inr`, `monthly_expenses_inr`, `assets`. Missing → `ValueError(f"missing required key: {key}")`.
3. **Numeric fields** — `total_value_inr` and `monthly_expenses_inr` must be `int | float`, **not `bool`**, and `>= 0`. Else `ValueError` naming the field and value.
4. **Assets is a list** — else `ValueError("assets must be a list")`. Empty list is valid (spec edge case 1).
5. **Per-asset checks** — for each asset dict:
   - Must have `name` (non-empty `str`), `allocation_pct` (`int | float`, `0 <= x <= 100`), `expected_crash_pct` (`int | float`, `<= 0`).
   - Missing or wrong type → `ValueError(f"asset[{i}].{field}: ...")` with the index.
6. **Allocation sum sanity** — compute `sum(a['allocation_pct'] for a in assets)`. If not in `[99.99, 100.01]` (float-tolerance) **and** assets is non-empty, print `f"warning: allocations sum to {total:.2f}, not 100"` to `sys.stderr`. Do **not** raise — spec edge case 3 says compute anyway.

**Boolean exclusion note:** `isinstance(True, int)` is `True` in Python, so numeric checks explicitly reject `bool` via `not isinstance(x, bool) and isinstance(x, (int, float))`. Without this, `total_value_inr=True` would silently become `1`.

**Not validated:**
- Duplicate asset names — spec doesn't forbid; tie-break already handles ordering.
- Allocations summing to >100 — covered by the warning.
- `expected_crash_pct < -100` — spec only says "negative number"; we compute as-given.

## 3. Computation flow

`compute_risk_metrics(portfolio)` body:

```
1. _validate_portfolio(portfolio)               # raises on bad input
2. assets = portfolio["assets"]
3. total_value = portfolio["total_value_inr"]
4. monthly_expenses = portfolio["monthly_expenses_inr"]

5. post_crash_values = [_asset_post_crash_value(a, total_value) for a in assets]
6. post_crash_value = sum(post_crash_values)    # 0.0 if assets is empty

7. runway_months = float('inf') if monthly_expenses == 0 else post_crash_value / monthly_expenses

8. ruin_test = 'PASS' if runway_months > RUIN_THRESHOLD_MONTHS else 'FAIL'

9. largest_risk_asset = (
       max(assets, key=lambda a: a['allocation_pct'] * abs(a['expected_crash_pct']))['name']
       if assets else None
   )

10. concentration_warning = any(a['allocation_pct'] > CONCENTRATION_THRESHOLD_PCT for a in assets)

11. return {                                    # exact key order from spec
        'post_crash_value': post_crash_value,
        'runway_months': runway_months,
        'ruin_test': ruin_test,
        'largest_risk_asset': largest_risk_asset,
        'concentration_warning': concentration_warning,
    }
```

Helper:
```
_asset_post_crash_value(asset, total_value_inr) -> float:
    asset_value = total_value_inr * (asset['allocation_pct'] / 100)
    return asset_value * (1 + asset['expected_crash_pct'] / 100)
```

**Subtleties:**
- **Tie-break on `largest_risk_asset`** — Python's `max()` returns the first occurrence on ties, matching spec's "tie-break by first appearance." No custom loop needed.
- **Zero-expenses + `runway_months > 12`** — `float('inf') > 12` is `True`, so `ruin_test='PASS'` falls out without a special case.
- **Empty assets + zero expenses** — composes cleanly: `post_crash_value=0`, `runway_months=inf`, `ruin_test='PASS'`.

**Anti-patterns avoided** (per spec):
- No mutation of `portfolio` or asset dicts.
- No `eval`/`exec`/string math.
- No rounding — return raw floats; pretty-print only in `__main__` via `json.dumps(indent=2)`.

## 4. Test plan — `test_risk.py`

Dependency-free: plain `assert`, runnable as `python task1_risk/test_risk.py`. One named function per test for clear failure messages, fixture defined once at module top.

**Imports:** `import copy`, `import math`, and `from risk import compute_risk_metrics` (sibling-file import; both files in `task1_risk/`, run as scripts from that directory or with `task1_risk/` on `sys.path`).

**Sample fixture (used by tests 1–4):**
```python
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
```

**Tests:**

| # | Name | Asserts |
|---|---|---|
| 1 | `test_post_crash_value_sample` | `post_crash_value == 5_700_000` (use `math.isclose`, `rel_tol=1e-9`) |
| 2 | `test_runway_and_ruin_test_sample` | `runway_months == 71.25` (isclose) and `ruin_test == 'PASS'` |
| 3 | `test_largest_risk_asset_sample` | `largest_risk_asset == 'BTC'` |
| 4 | `test_concentration_boundary` | `concentration_warning is False` (NIFTY50 at exactly 40 must NOT trigger) |
| 5 | `test_zero_expenses` | `monthly_expenses_inr=0` → `runway_months == float('inf')`, `ruin_test == 'PASS'` |
| 6 | `test_empty_assets` | `assets=[]` → `post_crash_value == 0`, `largest_risk_asset is None`, `concentration_warning is False` |
| 7 | `test_single_asset_50pct` | Single asset at `allocation_pct=50` → `concentration_warning is True` |
| 8 | `test_input_not_mutated` | Deep-copy SAMPLE before/after `compute_risk_metrics`; assert equality |
| 9 | `test_validation_raises_on_missing_key` | `compute_risk_metrics({})` raises `ValueError` |

**Runner block:**
```python
if __name__ == "__main__":
    test_post_crash_value_sample()
    test_runway_and_ruin_test_sample()
    test_largest_risk_asset_sample()
    test_concentration_boundary()
    test_zero_expenses()
    test_empty_assets()
    test_single_asset_50pct()
    test_input_not_mutated()
    test_validation_raises_on_missing_key()
    print("All tests passed")
```

**Not tested (intentional):**
- `_asset_post_crash_value` directly — fully covered by test 1.
- The stderr allocation-sum warning — requires capture fixtures for a side channel; spec marks the print as optional.
- `total_value_inr == 0` (spec edge case 5) — implied by test 1's multiplication path.

## 5. Workflow, README, and how this lands in git

### Branching & commit sequence

1. **On `main` (currently zero commits):** single scaffold commit including the four `taskN_instruction.md` files, `CLAUDE.md`, `.gitignore`, empty `README.md` and `requirements.txt`, **and this design doc**.
2. `git checkout -b task1/risk-calculator`
3. Implement → test → write per-task README → commit on the branch.
4. Push branch, open PR, ask for review.
5. On approval: merge, then `git branch -d task1/risk-calculator` (and remote delete if pushed).

**Two commits on the feature branch** (not one):
- `task1: implement compute_risk_metrics with validation and tests` (`risk.py` + `test_risk.py`)
- `task1: add per-task README and link from root README` (the two README files)

### `task1_risk/README.md` outline

```
# Task 1 — Portfolio Risk Calculator

## Summary
2–3 sentences: what compute_risk_metrics does, what the 5 outputs mean.

## Run
python task1_risk/risk.py        # prints sample portfolio metrics as JSON
python task1_risk/test_risk.py   # runs 9 assertions, prints "All tests passed"

## Design notes
- Stdlib only — no pandas/numpy (spec constraint).
- Pure function: no I/O inside compute_risk_metrics, no input mutation.
- Tie-break on largest_risk_asset relies on Python's max() returning first occurrence.
- Allocation sum != 100 → stderr warning, not a raise (spec edge case 3).

## AI tool usage
[Filled in retrospectively after implementation — what Claude Code helped with.]
```

### Root `README.md` — minimal seed in this PR

```
# Timecell internship technical test

Four self-contained Python tasks. Each task lives in its own folder
with a per-task README.

## Tasks
- [Task 1 — Portfolio Risk Calculator](task1_risk/README.md)
- Task 2 — Live Market Data Fetch (TBD)
- Task 3 — AI-Powered Portfolio Explainer (TBD)
- Task 4 — Open (TBD)

## Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # currently empty; populated by tasks 2 and 3

## AI tooling
[Project-wide note on how Claude Code was used across tasks — appended as tasks land.]
```

### Verification before declaring done

Per `superpowers:verification-before-completion`, before requesting PR review:
1. `python task1_risk/risk.py` — show JSON output (must include all 5 keys).
2. `python task1_risk/test_risk.py` — show "All tests passed".
3. `(cd task1_risk && python -c "from risk import compute_risk_metrics; compute_risk_metrics({})")` — confirm `ValueError` is raised cleanly. (No `__init__.py`, so script-style invocation, not package import.)

### Out of scope for this PR

- Bonus 1 (`compare_scenarios`) and Bonus 2 (`print_allocation_chart`) — separate follow-up branch after base merges.
- Substantive AI-usage notes — placeholder text in this PR; real text appended after implementation.
- Anything in `task2_market/`, `task3_explainer/`, `task4_open/`.
- Changes to `requirements.txt` — Task 1 is stdlib-only.
