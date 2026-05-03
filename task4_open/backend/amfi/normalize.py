"""Scheme-name normalization shared by the bundle loader, matcher, and adapters."""
from __future__ import annotations

import re

_PAREN_QUAL_RE = re.compile(r"\((?:direct|growth|g|idcw|dividend|plan\s*[a-z0-9]+)\)", re.IGNORECASE)
_SHORT_PAREN_RE = re.compile(r"\([dg]\)", re.IGNORECASE)
_SUFFIX_RE = re.compile(
    r"\s*-?\s*(?:direct\s+plan|direct\s+growth|direct|growth\s+plan|growth|regular|dividend|idcw|plan\s+[a-z0-9]+)\s*$",
    re.IGNORECASE,
)
_PUNCT_RE = re.compile(r"[^\w\s&]")
_WS_RE = re.compile(r"\s+")


def normalize_scheme_name(name: str) -> str:
    """Lowercase, strip plan/idcw/growth qualifiers, collapse whitespace.

    Used by both the bundle indexer and the matcher so two callers always agree."""
    s = name.lower()
    s = _PAREN_QUAL_RE.sub("", s)
    s = _SHORT_PAREN_RE.sub("", s)
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    while True:
        new = _SUFFIX_RE.sub("", s).strip()
        if new == s:
            break
        s = new
    s = _WS_RE.sub(" ", s).strip()
    return s
