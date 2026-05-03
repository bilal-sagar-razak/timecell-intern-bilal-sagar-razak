# Timecell internship technical test

Four self-contained Python tasks. Each task lives in its own folder with a
per-task README.

## Tasks

- [Task 1 — Portfolio Risk Calculator](task1_risk/README.md)
- [Task 2 — Live Market Data Fetch](task2_market/README.md)
- [Task 3 — AI-Powered Portfolio Explainer](task3_explainer/README.md)
- [Task 4 — Portfolio Intelligence Dashboard (4a Overview + 4b Market/Rebalance + 4c Holdings/Overlap)](task4_open/README.md)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # task2 + task3 deps
make -C task4_open install        # task4: backend reqs + npm + Playwright Chromium
```

Drop your keys into a repo-root `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...    # optional (task 3 critique step)
```

## Quick demo run

```bash
. .venv/bin/activate

# Task 1 — pure-stdlib risk math (instant, no key)
python task1_risk/risk.py

# Task 2 — live prices via yfinance + CoinGecko (~10s, no key)
python task2_market/fetch_prices.py

# Task 3 — Anthropic explainer (use --no-critique if no OpenAI key/quota)
python task3_explainer/explain_portfolio.py \
    --portfolio task3_explainer/sample_portfolio.json --tone beginner --no-critique

# Task 4 — full webapp on :8000 / :3000
make -C task4_open dev   # then open http://localhost:3000
```

## AI tooling

Each task is developed with Claude Code (Opus 4.7) using the `superpowers`
skill chain — `brainstorming` → `writing-plans` → `subagent-driven-development`
— with a per-task design and plan committed under `docs/superpowers/`. The
per-task READMEs carry the specific AI-usage notes for each task.
