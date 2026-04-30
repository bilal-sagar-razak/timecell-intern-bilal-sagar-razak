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

Each task is developed with Claude Code (Opus 4.7) using the `superpowers`
skill chain — `brainstorming` → `writing-plans` → `subagent-driven-development`
— with a per-task design and plan committed under `docs/superpowers/`. The
per-task READMEs carry the specific AI-usage notes for each task.
