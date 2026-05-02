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
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"portfolio file not found: {path}")
    with p.open() as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"portfolio file is not valid JSON: {path} — {e}") from e


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
