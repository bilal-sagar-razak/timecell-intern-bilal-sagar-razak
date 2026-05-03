"""Pydantic request/response models for /api/holdings/per-fund and /api/holdings/overlap."""
from __future__ import annotations

from pydantic import BaseModel

from amfi.match import FundMatch
from parser.schema import NormalizedHoldings


class HoldingsRequest(BaseModel):
    """Request body for both holdings endpoints — just the holdings JSON."""
    holdings: NormalizedHoldings


class PerFundResponse(BaseModel):
    matches: list[FundMatch]


class OverlapFund(BaseModel):
    asset_name: str
    scheme_name: str | None
    matched_by: str  # "isin" | "name" | "none"


class OverlapCell(BaseModel):
    i: int
    j: int
    overlap_pct: float
    shared_count: int


class SharedStock(BaseModel):
    name: str
    isin: str | None
    weight_a: float
    weight_b: float
    min: float


class OverlapResponse(BaseModel):
    funds: list[OverlapFund]
    matrix: list[list[OverlapCell]]
    shared_stocks_index: dict[str, list[SharedStock]]
