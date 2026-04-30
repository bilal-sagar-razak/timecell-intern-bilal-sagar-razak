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

Built with Claude Code (Opus 4.7) using the `superpowers` skill chain end-to-end:
`brainstorming` to lock scope (base only, bonuses deferred) and decisions like
the `bool`-exclusion guard for numeric fields and the float-tolerance window
`[99.99, 100.01]` for the allocation-sum warning; `writing-plans` to produce a
TDD task list with full code blocks; `subagent-driven-development` to execute
substantive units (4-metric build, validator, `__main__`+docstring, READMEs)
via fresh Sonnet subagents while trivial mechanical edits (test additions,
git ops) ran in the main session. The committed design and plan documents
(`docs/superpowers/specs/`, `docs/superpowers/plans/`) capture the reasoning
trail for grading.
