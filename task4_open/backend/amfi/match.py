"""Match a user's holdings to AMFI bundle schemes via ISIN-first then fuzzy name."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from rapidfuzz import fuzz

from amfi.bundle import IndexedBundle
from amfi.normalize import normalize_scheme_name
from amfi.schema import Scheme
from parser.schema import Asset

FUZZY_THRESHOLD = 0.85
MatchedBy = Literal["isin", "name", "none"]


class FundMatch(BaseModel):
    """One row of the per-fund payload."""
    asset_name: str
    asset_isin: str | None
    matched: bool
    matched_by: MatchedBy
    confidence: float
    scheme: Scheme | None


def _candidate_schemes(bundle: IndexedBundle, amc: str | None) -> list[Scheme]:
    if amc is None:
        return bundle.schemes
    amc_lower = amc.lower()
    scoped = [s for s in bundle.schemes if s.amc.lower() == amc_lower]
    return scoped if scoped else bundle.schemes  # fall back if amc string doesn't match any


def _match_one(asset: Asset, bundle: IndexedBundle) -> FundMatch:
    if asset.isin and asset.isin in bundle.by_isin:
        return FundMatch(
            asset_name=asset.name, asset_isin=asset.isin,
            matched=True, matched_by="isin", confidence=1.0,
            scheme=bundle.by_isin[asset.isin],
        )

    norm = normalize_scheme_name(asset.name)
    if norm in bundle.by_normalized_name:
        return FundMatch(
            asset_name=asset.name, asset_isin=asset.isin,
            matched=True, matched_by="name", confidence=0.95,
            scheme=bundle.by_normalized_name[norm],
        )

    candidates = _candidate_schemes(bundle, asset.amc)
    best_score = 0.0
    best_scheme: Scheme | None = None
    for scheme in candidates:
        scheme_norm = normalize_scheme_name(scheme.scheme_name)
        # Combine ratio (catches "FlexiCap" vs "Flexi Cap") with token_set_ratio
        # (catches partial-name matches like "Flexi Cap Fund" vs "HDFC Flexi Cap Fund").
        score = max(
            fuzz.ratio(norm, scheme_norm),
            fuzz.token_set_ratio(norm, scheme_norm),
        ) / 100.0
        if score > best_score:
            best_score = score
            best_scheme = scheme
    if best_score >= FUZZY_THRESHOLD and best_scheme is not None:
        return FundMatch(
            asset_name=asset.name, asset_isin=asset.isin,
            matched=True, matched_by="name", confidence=round(best_score, 4),
            scheme=best_scheme,
        )

    return FundMatch(
        asset_name=asset.name, asset_isin=asset.isin,
        matched=False, matched_by="none", confidence=0.0, scheme=None,
    )


def match_user_funds(assets: list[Asset], bundle: IndexedBundle) -> list[FundMatch]:
    """Return one FundMatch per asset, in input order."""
    return [_match_one(a, bundle) for a in assets]
