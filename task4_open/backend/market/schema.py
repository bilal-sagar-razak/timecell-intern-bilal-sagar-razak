"""Pydantic models for market data (Nifty trend + news headlines)."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class NiftyPoint(BaseModel):
    """One day's Nifty 50 close price."""
    date: date
    close: float


class NiftyTrend(BaseModel):
    """Sequence of Nifty close prices + period summary."""
    points: list[NiftyPoint]
    pct_change_period: float
    current: float
    period_days: int = Field(..., ge=1)


class Headline(BaseModel):
    """One news headline pulled from an RSS feed."""
    title: str = Field(..., min_length=1)
    publisher: str
    url: str
    published_at: datetime
    snippet: str | None = None


class MarketSnapshot(BaseModel):
    """The full payload of /api/market — Nifty trend + portfolio-filtered news."""
    nifty_trend: NiftyTrend
    news: list[Headline]
    news_fallback_used: bool = False
    cached_at: datetime
