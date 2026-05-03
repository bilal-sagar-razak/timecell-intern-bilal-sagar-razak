"""AMFI bundle loader + by-ISIN / by-normalized-name indexes."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from amfi.normalize import normalize_scheme_name
from amfi.schema import AmfiBundle, Scheme

logger = logging.getLogger(__name__)

BUNDLE_PATH = Path(__file__).parent.parent / "data" / "amfi_holdings.json"


class BundleMissing(Exception):
    """Raised when data/amfi_holdings.json does not exist."""


class BundleMalformed(Exception):
    """Raised when the bundle file exists but cannot be parsed."""


class IndexedBundle:
    """AmfiBundle plus by_isin and by_normalized_name lookup dicts."""
    __slots__ = ("bundle", "by_isin", "by_normalized_name")

    def __init__(self, bundle: AmfiBundle):
        self.bundle = bundle
        self.by_isin: dict[str, Scheme] = {}
        self.by_normalized_name: dict[str, Scheme] = {}
        for scheme in bundle.schemes:
            if scheme.isin:
                self.by_isin[scheme.isin] = scheme
            self.by_normalized_name[normalize_scheme_name(scheme.scheme_name)] = scheme

    @property
    def schemes(self) -> list[Scheme]:
        return self.bundle.schemes


_cached: IndexedBundle | None = None


def load_bundle() -> IndexedBundle:
    """Load the AMFI bundle from disk, build indexes, cache. Lazy + idempotent."""
    global _cached
    if _cached is not None:
        return _cached
    if not BUNDLE_PATH.exists():
        raise BundleMissing(
            f"AMFI bundle not found at {BUNDLE_PATH}. "
            "Run `make refresh-amfi` to fetch + parse the latest disclosures."
        )
    try:
        raw = json.loads(BUNDLE_PATH.read_text())
        bundle = AmfiBundle.model_validate(raw)
    except (json.JSONDecodeError, ValueError) as e:
        raise BundleMalformed(f"AMFI bundle at {BUNDLE_PATH} is malformed: {e}") from e
    indexed = IndexedBundle(bundle)
    _cached = indexed
    logger.info("[amfi] loaded bundle: %d schemes", len(indexed.schemes))
    return indexed
