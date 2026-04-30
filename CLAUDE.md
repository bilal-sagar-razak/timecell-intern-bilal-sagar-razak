# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Part 1 — Universal behavioral guidelines

Behavioral guidelines to reduce common LLM coding mistakes. **Tradeoff:** these bias toward caution over speed. For trivial tasks, use judgment. Each guideline names the superpowers skill that operationalizes it — invoke the skill rather than improvising the discipline.

### 1. Think before coding → `superpowers:brainstorming`

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

Use `superpowers:brainstorming` first to surface intent and tradeoffs before any code or plan is written.

### 2. Simplicity first → `superpowers:writing-plans`

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

Use `superpowers:writing-plans` to lock scope before implementing — a written plan makes scope creep visible.

### 3. Surgical changes → `superpowers:executing-plans` + `superpowers:test-driven-development`

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

Use `superpowers:executing-plans` to follow the locked plan step-by-step, and `superpowers:test-driven-development` so each change is anchored to a failing test rather than a tangent.

### 4. Goal-driven execution → `superpowers:verification-before-completion`

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

Use `superpowers:verification-before-completion` before claiming "done" — run the checks and show the output. Use `superpowers:systematic-debugging` when something fails the check.

### Workflow rules for this repo

These are non-negotiable for any change in this project, and they sit alongside the four guidelines above:

1. **Branch before any change.** Create a new git branch before editing — never commit directly to `main`.
2. **Commit, then request PR review.** After implementing, commit and ask the user for PR review approval. Do not merge unilaterally — `superpowers:requesting-code-review` covers the handoff.
3. **Delete merged branches.** Once the user approves the merge, delete the branch (local, and remote if pushed). `superpowers:finishing-a-development-branch` covers the cleanup options.
4. **Skip the superpowers cycle only for trivial single-line fixes.** Everything else goes brainstorm → plan → execute → verify.

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## Part 2 — Project context

### What this repo is

A Timecell internship technical test consisting of four discrete Python 3.10+ tasks. Each lives in its own `taskN_*/` directory. The repo is currently a scaffold — the only files inside each task directory are detailed `taskN_instruction.md` specs; no implementation files have been written yet.

**Always read `taskN_instruction.md` in full before starting work on a task.** The specs are exhaustive (function signatures, edge cases, acceptance tests, anti-patterns, README requirements) and graded — do not infer requirements from the directory name.

### Tasks at a glance

| Dir | Module to build | Stack constraint | Notes |
|---|---|---|---|
| `task1_risk/` | `risk.py` (+ `test_risk.py`) | **stdlib only** — no pandas/numpy | Pure functions, no I/O inside `compute_risk_metrics`. |
| `task2_market/` | `fetch_prices.py` | `yfinance`, `requests`, `rich` (free, no API keys) | Each asset fetched in own try/except — one failure must never stop others. |
| `task3_explainer/` | `explain_portfolio.py` | LLM SDK (Anthropic recommended) + reuses Task 1's `compute_risk_metrics` | API key from env var only. **Pre-compute metrics with Task 1; LLM narrates, never calculates.** |
| `task4_open/` | open-ended | TBD | Currently empty. |

**Cross-task dependency:** Task 3 imports from Task 1. When changing `compute_risk_metrics`'s return shape, update Task 3's prompt builder too.

### Commands

```bash
# Setup (top-level requirements.txt collects deps from task2 + task3)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Per-task run
python task1_risk/risk.py
python task1_risk/test_risk.py        # stdlib asserts, not pytest
python task2_market/fetch_prices.py
python task3_explainer/explain_portfolio.py --portfolio path/to/portfolio.json [--tone beginner|experienced|expert]
```

There is no project-wide test runner, linter, or build system. Each task is self-contained.

### Per-task gotchas (from the specs — easy to miss)

- **Task 1**: `concentration_warning` is `allocation_pct > 40`, strictly greater (40 itself does NOT trigger). `monthly_expenses_inr == 0` → runway is `inf` AND `ruin_test == 'PASS'`. Don't mutate the input dict.
- **Task 2**: Always set `timeout=10` on `requests.get`. Use `logging.warning(..., exc_info=True)` — never `print(traceback.format_exc())`. Use `rich`, not `tabulate`/`prettytable`. Keep the asset list as a module-level `ASSETS_TO_FETCH` constant so adding an asset is a one-line edit.
- **Task 3**: The `verdict` field MUST be exactly `"Aggressive" | "Balanced" | "Conservative"` — validate after parsing, not just in the prompt. The grading rubric weights the README's prompt-iteration log heavily — when you iterate the prompt, log V1/V2/V3 with what failed and what fixed it, in real time. Strip ```` ```json ```` fences in the parser even though the prompt says not to use them.

### README convention

The project README is intentionally empty at scaffold time. Each task's spec requires you to **append** a section (`## Task N — <Title>`) to the root `README.md` after implementation, including AI tool usage notes. Don't rewrite earlier sections when adding a new one.
