"""LLM-driven holdings normalizer: ExtractedContent -> NormalizedHoldings."""
from __future__ import annotations

import base64
import json
import logging
import os
import re
from datetime import date
from pathlib import Path
from string import Template

from anthropic import Anthropic

from parser.extract import ExtractedContent
from parser.schema import NormalizedHoldings

logger = logging.getLogger(__name__)

DEFAULT_HAIKU_MODEL = "claude-haiku-4-5"
MAX_INPUT_TOKENS = 30_000
MAX_OUTPUT_TOKENS = 4096
HAIKU_INPUT_USD_PER_M = 1.0
HAIKU_OUTPUT_USD_PER_M = 5.0
CACHE_DIR = Path.home() / ".cache" / "timecell-task4"

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "normalize.txt"
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class NormalizationError(Exception):
    """Raised when the LLM cannot produce valid NormalizedHoldings after one retry."""

    def __init__(self, message: str, attempts: list[str], errors: list[str]) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.errors = errors


class BudgetExhausted(Exception):
    """Raised when the daily LLM spend cap would be exceeded by this call."""


def _max_daily_usd() -> float | None:
    raw = os.environ.get("MAX_DAILY_LLM_USD", "2.00")
    if raw.strip().lower() == "disabled":
        return None
    try:
        return float(raw)
    except ValueError:
        return 2.00


def _today_cache_path() -> Path:
    return CACHE_DIR / f"usage-{date.today().isoformat()}.json"


def _read_today_usd() -> float:
    p = _today_cache_path()
    if not p.exists():
        return 0.0
    try:
        return float(json.loads(p.read_text())["usd"])
    except Exception:
        return 0.0


def _write_today_usd(amount: float) -> None:
    p = _today_cache_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps({"usd": amount}))
    tmp.replace(p)


def _estimated_cost_usd(input_tokens: int, output_tokens: int = MAX_OUTPUT_TOKENS) -> float:
    return (
        input_tokens * HAIKU_INPUT_USD_PER_M / 1_000_000
        + output_tokens * HAIKU_OUTPUT_USD_PER_M / 1_000_000
    )


def _format_extracted(content: ExtractedContent) -> str:
    if content.kind == "tables":
        parts = []
        for sheet, rows in content.tables:
            parts.append(f"### sheet: {sheet}")
            for row in rows:
                parts.append("\t".join(row))
        return "\n".join(parts)
    if content.kind == "text":
        return content.text
    return "[image content sent as vision message]"


def _build_prompt(content: ExtractedContent) -> str:
    template = Template(_PROMPT_PATH.read_text())
    return template.substitute(
        extracted_content=_format_extracted(content),
        canonical_schema_json=json.dumps(NormalizedHoldings.model_json_schema(), indent=2),
    )


def _strip_fences(raw: str) -> str:
    return _FENCE_RE.sub("", raw).strip()


def _call_haiku(
    client: Anthropic, prompt: str, model: str, content: ExtractedContent
) -> tuple[str, dict]:
    if content.kind == "image" and content.image_bytes:
        img_b64 = base64.standard_b64encode(content.image_bytes).decode("ascii")
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": content.image_media_type, "data": img_b64}},
                {"type": "text", "text": prompt},
            ],
        }]
    else:
        messages = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=model,
        max_tokens=MAX_OUTPUT_TOKENS,
        messages=messages,
    )
    raw = response.content[0].text
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return raw, usage


def _truncate(content: ExtractedContent, ratio: float) -> ExtractedContent:
    factor = ratio * 0.95
    if content.kind == "text":
        char_limit = int(len(content.text) * factor)
        return ExtractedContent(
            kind="text",
            text=content.text[:char_limit],
            format_hint=content.format_hint,
        )
    if content.kind == "tables":
        new_tables = []
        for sheet, rows in content.tables:
            keep = max(1, int(len(rows) * factor))
            new_tables.append((sheet, rows[:keep]))
        return ExtractedContent(
            kind="tables",
            tables=new_tables,
            format_hint=content.format_hint,
        )
    return content


def normalize(
    content: ExtractedContent, model: str = DEFAULT_HAIKU_MODEL
) -> NormalizedHoldings:
    """Convert extracted content to a validated NormalizedHoldings via Haiku, with one retry."""
    prompt = _build_prompt(content)
    client = Anthropic()
    warnings: list[str] = []

    count_resp = client.messages.count_tokens(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    estimated_input = count_resp.input_tokens

    if estimated_input > MAX_INPUT_TOKENS:
        ratio = MAX_INPUT_TOKENS / estimated_input
        content = _truncate(content, ratio)
        warnings.append(
            f"input truncated from {estimated_input} to ~{MAX_INPUT_TOKENS} tokens "
            "— some assets may be missing from the parsed output"
        )
        prompt = _build_prompt(content)

    pre_cost = _estimated_cost_usd(min(estimated_input, MAX_INPUT_TOKENS))
    logger.info("normalize: estimated cost $%.4f (input ~%d tokens)", pre_cost, estimated_input)

    cap = _max_daily_usd()
    if cap is not None:
        today_so_far = _read_today_usd()
        if today_so_far + pre_cost > cap:
            raise BudgetExhausted(
                f"daily budget ${cap:.2f} would be exceeded "
                f"(spent ${today_so_far:.4f} so far, this call estimated ${pre_cost:.4f})"
            )

    raw, usage = _call_haiku(client, prompt, model, content)
    cost = _estimated_cost_usd(usage["input_tokens"], usage["output_tokens"])
    total_cost = cost
    logger.info("normalize: actual cost $%.4f", cost)

    first_err: Exception | None = None
    try:
        data = json.loads(_strip_fences(raw))
        result = NormalizedHoldings.model_validate(data)
    except Exception as e:
        first_err = e
        retry_prompt = (
            prompt
            + "\n\n<previous_attempt>\n"
            + raw
            + "\n</previous_attempt>\n\n<validation_error>\n"
            + str(e)
            + "\n</validation_error>\n\nReturn corrected JSON only."
        )
        raw2, usage2 = _call_haiku(client, retry_prompt, model, content)
        total_cost += _estimated_cost_usd(usage2["input_tokens"], usage2["output_tokens"])
        try:
            data2 = json.loads(_strip_fences(raw2))
            result = NormalizedHoldings.model_validate(data2)
        except Exception as e2:
            raise NormalizationError(
                "could not normalize statement after retry",
                attempts=[raw, raw2],
                errors=[str(first_err), str(e2)],
            ) from e2

    result.parser_warnings = warnings + list(result.parser_warnings)

    if cap is not None:
        _write_today_usd(_read_today_usd() + total_cost)

    return result
