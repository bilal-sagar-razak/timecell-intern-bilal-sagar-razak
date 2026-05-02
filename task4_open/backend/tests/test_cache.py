"""Tests for parser.cache — pure-function disk cache."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.cache import (
    cache_key,
    read_cache,
    write_cache,
)


def test_cache_key_deterministic_for_same_inputs() -> None:
    k1 = cache_key(b"hello world", "prompt v1")
    k2 = cache_key(b"hello world", "prompt v1")
    assert k1 == k2, f"same inputs should give same key, got {k1!r} vs {k2!r}"
    assert len(k1) == 64, f"sha256 hex digest is 64 chars, got {len(k1)}"


def test_cache_key_changes_when_file_bytes_change() -> None:
    k1 = cache_key(b"hello", "prompt")
    k2 = cache_key(b"world", "prompt")
    assert k1 != k2, "different bytes must give different keys"


def test_cache_key_changes_when_prompt_changes() -> None:
    k1 = cache_key(b"same bytes", "prompt v1")
    k2 = cache_key(b"same bytes", "prompt v2 with edits")
    assert k1 != k2, "prompt edits must invalidate the key"


def test_write_cache_is_atomic_and_readable(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    payload = {"foo": "bar", "n": 42, "nested": {"ok": True}}
    write_cache("abc123", payload)
    files = list(tmp_path.iterdir())
    assert len(files) == 1, f"expected 1 file, got {[f.name for f in files]}"
    assert files[0].name == "abc123.json"
    out = read_cache("abc123")
    assert out == payload, f"round-trip mismatch: {out!r} vs {payload!r}"


def test_read_cache_handles_corrupt_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    p = tmp_path / "deadbeef.json"
    p.write_text("{this is not valid json")
    out = read_cache("deadbeef")
    assert out is None, f"corrupt file should return None, got {out!r}"
    assert not p.exists(), "corrupt file should have been deleted"
