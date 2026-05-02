"""Content-addressed disk cache for parse-and-compute responses."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from .normalize import CACHE_DIR

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1"
PARSE_CACHE_DIR = CACHE_DIR / "parse-cache"


def cache_key(file_bytes: bytes, prompt_text: str) -> str:
    """SHA-256 of (file_bytes, prompt_text, SCHEMA_VERSION) joined by NUL bytes."""
    h = hashlib.sha256()
    h.update(file_bytes)
    h.update(b"\x00")
    h.update(prompt_text.encode("utf-8"))
    h.update(b"\x00")
    h.update(SCHEMA_VERSION.encode("utf-8"))
    return h.hexdigest()


def read_cache(key: str) -> dict | None:
    """Returns the cached response dict, or None on miss / corrupt file."""
    p = PARSE_CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text())
        return payload["response"]
    except (json.JSONDecodeError, KeyError, OSError) as e:
        logger.warning("[cache] dropping corrupt entry %s: %s", key[:8], e)
        try:
            p.unlink()
        except OSError:
            pass
        return None


def write_cache(key: str, response_dict: dict) -> None:
    """Atomic write: <key>.json.tmp then rename to <key>.json."""
    PARSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = PARSE_CACHE_DIR / f"{key}.json"
    tmp = p.with_suffix(".json.tmp")
    payload = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "response": response_dict,
    }
    tmp.write_text(json.dumps(payload))
    tmp.replace(p)
