# Task 1 — Portfolio Risk Calculator

## Role
You are implementing a portfolio risk calculator in Python 3.10+ for the Timecell internship technical test. Build clean, production-quality code that a wealth manager would trust.

## Objective
Write a single Python module `risk.py` that exposes a function `compute_risk_metrics(portfolio: dict) -> dict` and computes five risk metrics for a given portfolio under a crash scenario.

## Input Schema
The function receives a dictionary with this exact shape:

```python
portfolio = {
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

- `total_value_inr` — total portfolio value in INR (int or float, always >= 0)
- `monthly_expenses_inr` — monthly burn rate in INR (int or float, always >= 0)
- `assets` — list of asset dicts. Each has `name` (str), `allocation_pct` (0–100), `expected_crash_pct` (negative number, e.g. -80 means an 80% drop)

## Required Output
Return a dictionary with exactly these keys:

| Key | Type | Definition |
|---|---|---|
| `post_crash_value` | float | Sum of each asset's value after applying its `expected_crash_pct` |
| `runway_months` | float | `post_crash_value / monthly_expenses_inr`. If expenses are 0, return `float('inf')` |
| `ruin_test` | str | `'PASS'` if `runway_months > 12` else `'FAIL'` |
| `largest_risk_asset` | str | Name of asset with highest `allocation_pct * abs(expected_crash_pct)` |
| `concentration_warning` | bool | `True` if any single asset has `allocation_pct > 40` |

## Math Specification
For each asset:
```
asset_value_inr     = total_value_inr * (allocation_pct / 100)
post_crash_asset    = asset_value_inr * (1 + expected_crash_pct / 100)
```
Then `post_crash_value = sum(post_crash_asset for all assets)`.

Risk score for "largest_risk_asset": `allocation_pct * abs(expected_crash_pct)`. Tie-break by first appearance in the list.

## Edge Cases You Must Handle
1. Empty `assets` list → `post_crash_value = 0`, `largest_risk_asset = None`, `concentration_warning = False`.
2. `monthly_expenses_inr == 0` → `runway_months = float('inf')`, `ruin_test = 'PASS'`.
3. Allocations don't sum to 100 → compute anyway based on the percentages given. Do NOT raise. Optionally print a warning to stderr.
4. 100% cash portfolio → all metrics still compute correctly; `post_crash_value == total_value_inr`.
5. `total_value_inr == 0` → all values become 0, runway = 0, ruin_test = 'FAIL'.
6. Negative or missing fields → raise `ValueError` with a clear message.

## Code Structure Requirements
- One file: `risk.py`.
- Pure function `compute_risk_metrics(portfolio)` — no side effects, no I/O inside it.
- A small helper `_asset_post_crash_value(asset, total_value_inr) -> float`.
- A small helper `_validate_portfolio(portfolio) -> None` that raises `ValueError` on bad input.
- Type hints on every function signature.
- A docstring on `compute_risk_metrics` explaining inputs, outputs, and edge cases.
- An `if __name__ == "__main__":` block that runs the example portfolio above and pretty-prints the result with `json.dumps(..., indent=2)`.
- No external dependencies. Standard library only.

## Bonus Features (implement only if base task is complete and tested)

### Bonus 1 — Moderate scenario comparison
Add a function `compare_scenarios(portfolio: dict) -> dict` that returns:
```python
{
    "severe": <result of compute_risk_metrics with crash percentages as-is>,
    "moderate": <result with each expected_crash_pct halved>,
}
```
Print both side by side in the `__main__` block as a two-column comparison.

### Bonus 2 — CLI bar chart
Add `print_allocation_chart(portfolio: dict) -> None` that prints something like:
```
BTC     ██████████████████████████████ 30%
NIFTY50 ████████████████████████████████████████ 40%
GOLD    ████████████████████ 20%
CASH    ██████████ 10%
```
Use `█` (U+2588) repeated `int(allocation_pct)` times. No external libraries. Right-pad asset names so bars align.

## Acceptance Tests
Before marking complete, verify these test cases pass. Write them as a small `test_risk.py` (using `assert`, not pytest, to keep it dependency-free):

1. **Sample input** → `post_crash_value == 5,700,000`. Verify the math:
   - BTC: 10M × 0.30 = 3M, post-crash = 3M × 0.20 = 600,000
   - NIFTY50: 10M × 0.40 = 4M, post-crash = 4M × 0.60 = 2,400,000
   - GOLD: 10M × 0.20 = 2M, post-crash = 2M × 0.85 = 1,700,000
   - CASH: 10M × 0.10 = 1M, post-crash unchanged = 1,000,000
   - Total: 5,700,000
2. **Sample input** → `runway_months == 71.25`, `ruin_test == 'PASS'` (5,700,000 / 80,000 = 71.25).
3. **Sample input** → `largest_risk_asset == 'BTC'`. Risk scores: BTC = 30 × 80 = 2400, NIFTY50 = 40 × 40 = 1600, GOLD = 20 × 15 = 300, CASH = 0. BTC wins.
4. **Sample input** → `concentration_warning == False` (NIFTY is exactly 40, not strictly > 40).
5. **Zero expenses** → `runway_months == float('inf')`, `ruin_test == 'PASS'`.
6. **Empty assets list** → no crash, returns sensible zeros/None.
7. **Single asset at 50%** → `concentration_warning == True`.

## README Documentation Required
After implementation, append a section to the project README titled **"Task 1 — Portfolio Risk Calculator"** containing:
- A 2–3 sentence summary of what the module does.
- Run instructions: `python risk.py`.
- A short note on AI tool usage (e.g., "Used Claude Code to scaffold the validation logic and to suggest edge cases I hadn't considered like the zero-expenses divide-by-zero case").
- Any assumptions or design decisions worth flagging.

## What Done Looks Like
- `python risk.py` runs and prints clean JSON output with all five keys.
- `python test_risk.py` runs all assertions and prints "All tests passed".
- No exceptions on edge cases listed above.
- Code passes a self-review for: clear names, no commented-out code, no magic numbers (use named constants like `RUIN_THRESHOLD_MONTHS = 12` and `CONCENTRATION_THRESHOLD_PCT = 40`).
- README section is written.

## Anti-Patterns to Avoid
- Don't put I/O (print, input, file reads) inside `compute_risk_metrics`.
- Don't mutate the input `portfolio` dict.
- Don't use `eval`, `exec`, or string-based math.
- Don't import pandas/numpy for this — it's overkill and signals you reach for heavy tools when stdlib works.
- Don't skip the validation function. Bad input handling is part of the grade.
