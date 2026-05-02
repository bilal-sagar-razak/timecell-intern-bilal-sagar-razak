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

- **Primary:** Anthropic Claude Sonnet (`claude-sonnet-4-6`) — the spec calls
  Anthropic the Timecell stack and the same SDK we use for Claude Code.
  Sonnet's cost/quality is appropriate for short structured-output tasks.
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
defensive parse costs five lines. (This caught a real fence-wrapped response
during live verification on the conservative portfolio.)

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

Built with Claude Code (Opus 4.7) following the `superpowers` chain
(`brainstorming` → `writing-plans` → `subagent-driven-development`). The
cross-vendor critique pass started life as a "show the user the critique too"
design; mid-brainstorm we redesigned to hide the critique entirely and use it
purely to drive a refinement call — the user sees only the final, possibly-
refined explanation, and the unit test `test_format_output_no_critique_section`
guards that invariant. Prompt templates use `string.Template` (`$var`) rather
than f-strings specifically to avoid `{{` brace-escaping in the JSON example
blocks. The `claude-api` skill was invoked at implementation time to confirm
`claude-sonnet-4-6` as the current latest Sonnet (the spec draft's
`claude-sonnet-4-5` would have failed at runtime). The most complex unit —
`main()`'s refinement loop — went through a dedicated spec-compliance review
agent that verified seven invariants (hidden-critique, refinement-decision
logic, fail-quiet boundaries, `have_openai` gating, single metrics call, CLI
surface, `load_dotenv` ordering). Tests are deterministic plain-assert
(mocking the SDKs only where needed); the spec's eight live acceptance
scenarios were run end-to-end against the real Anthropic and OpenAI APIs and
all passed — including a real-world fail-quiet trigger when OpenAI returned
HTTP 429 `insufficient_quota` mid-run and the script correctly fell back to
the v1 explanation.
