"""Pydantic models for the AMFI portfolio-disclosure bundle."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

HoldingKind = Literal["equity", "debt", "cash", "other"]


class FundHolding(BaseModel):
    """One stock/bond in a scheme's portfolio."""
    name: str = Field(..., min_length=1)
    isin: str | None = None
    weight_pct: float = Field(..., ge=0, le=100)
    value_inr: float = Field(..., ge=0)
    kind: HoldingKind = "equity"


class Scheme(BaseModel):
    """One mutual-fund scheme + its current holdings."""
    scheme_name: str = Field(..., min_length=1)
    isin: str | None = None
    amc: str = Field(..., min_length=1)
    scheme_aum_inr: float = Field(..., ge=0)
    as_of_date: date
    holdings: list[FundHolding] = Field(default_factory=list)
    cash_pct: float = Field(0.0, ge=0, le=100)


class AmfiBundle(BaseModel):
    """Top-level bundle file emitted by scripts/refresh_amfi.py and read by amfi/bundle.py."""
    version: int = 1
    as_of_month: str
    fetched_at: datetime
    schemes: list[Scheme]
