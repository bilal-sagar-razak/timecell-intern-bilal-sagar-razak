# Timecell internship technical test

Four self-contained Python tasks. Each task lives in its own folder with a
per-task README.

## Tasks

- [Task 1 — Portfolio Risk Calculator](task1_risk/README.md)
- [Task 2 — Live Market Data Fetch](task2_market/README.md)
- [Task 3 — AI-Powered Portfolio Explainer](task3_explainer/README.md)
- [Task 4 — Portfolio Intelligence Dashboard (4a: Shell + Parser + Overview)](task4_open/README.md)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # task2 deps now; task3 will add LLM SDK
```

## AI tooling

Each task is developed with Claude Code (Opus 4.7) using the `superpowers`
skill chain — `brainstorming` → `writing-plans` → `subagent-driven-development`
— with a per-task design and plan committed under `docs/superpowers/`. The
per-task READMEs carry the specific AI-usage notes for each task.
