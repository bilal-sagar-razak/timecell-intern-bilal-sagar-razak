"""Pydantic v2 canonical schema for normalized holdings."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

AssetType = Literal["mutual_fund", "stock", "etf", "bond", "commodity", "other"]
Category = Literal["Equity", "Debt", "Hybrid", "Commodities"]


class Asset(BaseModel):
    """One row in a holdings statement — stock or mutual fund."""
    name: str = Field(..., min_length=1)
    asset_type: AssetType
    isin: str | None = None
    amc: str | None = None
    category: Category | None = None
    sub_category: str | None = None
    folio: str | None = None
    units: float
    invested_value_inr: float
    current_value_inr: float
    xirr_pct: float | None = None
    pnl_inr: float
    pnl_pct: float


class PortfolioSummary(BaseModel):
    """Top-level numbers from the statement (or computed from assets if absent)."""
    total_invested_inr: float
    total_current_inr: float
    total_pnl_inr: float
    total_pnl_pct: float
    overall_xirr_pct: float | None = None
    asset_count: int = Field(..., ge=0)
    statement_date: date | None = None


class NormalizedHoldings(BaseModel):
    """Top-level container — what the parser returns."""
    holder_name: str | None = None
    source_format: str
    summary: PortfolioSummary
    assets: list[Asset]
    parser_warnings: list[str] = Field(default_factory=list)
