"""Rebalance agent tools — pure functions over per-request `_ctx`."""
from __future__ import annotations

from anthropic.lib.tools import beta_tool

_ctx: dict = {}

_VALID_PERIODS = {7, 30, 90, 365}


@beta_tool
def get_nifty_trend(period_days: int = 90) -> dict:
    """Return Nifty 50 close-price trend for the requested period in days."""
    if period_days not in _VALID_PERIODS:
        return {"error": f"period_days must be one of {sorted(_VALID_PERIODS)}"}
    snap = _ctx["snapshot"]
    trend = snap.nifty_trend
    points = trend.points if period_days >= trend.period_days else trend.points[-period_days:]
    if points:
        first = points[0].close
        last = points[-1].close
        pct = (last - first) / first * 100 if first else 0.0
    else:
        pct = 0.0
    return {
        "points": [{"date": p.date.isoformat(), "close": p.close} for p in points],
        "pct_change_period": round(pct, 4),
        "current": trend.current,
        "period_days": period_days,
    }


def _serialize_headlines(headlines) -> list[dict]:
    return [
        {
            "title": h.title,
            "publisher": h.publisher,
            "url": h.url,
            "published_at": h.published_at.isoformat(),
            "snippet": h.snippet,
        }
        for h in headlines
    ]


def _match_substr(news, needle: str, limit: int = 5):
    n = needle.lower()
    return [h for h in news if n and n in h.title.lower()][:limit]


@beta_tool
def get_news_for_holding(name: str) -> dict:
    """News for a holding. Falls back to its sub_category then category when the fund name itself
    returns no headlines (mutual funds rarely appear by name in market news)."""
    snap = _ctx["snapshot"]
    holdings = _ctx["holdings"]
    asset = next((a for a in holdings.assets if a.name.lower() == name.lower()), None)

    by_name = _match_substr(snap.news, name)
    if by_name:
        return {"name": name, "matched_by": "name", "query": name, "headlines": _serialize_headlines(by_name)}

    if asset and asset.sub_category:
        sub = asset.sub_category
        by_sub = _match_substr(snap.news, sub)
        if by_sub:
            return {"name": name, "matched_by": "sub_category", "query": sub, "headlines": _serialize_headlines(by_sub)}

    if asset and asset.category:
        cat = asset.category
        by_cat = _match_substr(snap.news, cat)
        if by_cat:
            return {"name": name, "matched_by": "category", "query": cat, "headlines": _serialize_headlines(by_cat)}

    return {"name": name, "matched_by": "none", "query": name, "headlines": []}


@beta_tool
def compute_concentration(threshold_pct: float = 15.0) -> dict:
    """Flag holdings exceeding a portfolio-share threshold and return per-category percentages."""
    holdings = _ctx["holdings"]
    total = sum(a.current_value_inr for a in holdings.assets) or 1e-9
    over_threshold = []
    category_totals: dict = {}
    for a in holdings.assets:
        pct = a.current_value_inr / total * 100
        if pct > threshold_pct:
            over_threshold.append({
                "name": a.name,
                "pct": round(pct, 2),
                "category": a.category,
                "sub_category": a.sub_category,
            })
        key = a.category or "Other"
        category_totals[key] = category_totals.get(key, 0.0) + a.current_value_inr
    category_pct = {k: round(v / total * 100, 2) for k, v in category_totals.items()}
    return {
        "threshold_pct": threshold_pct,
        "over_threshold": over_threshold,
        "category_pct": category_pct,
    }


@beta_tool
def propose_drawdown_simulation(rebalance_proposal: dict) -> dict:
    """Simulate sell/buy proposal (pcts of total) and report new category mix and equity %."""
    holdings = _ctx["holdings"]
    total = sum(a.current_value_inr for a in holdings.assets) or 1e-9
    new_values = {a.name: a.current_value_inr for a in holdings.assets}
    for s in rebalance_proposal.get("sell", []):
        nm = s["name"]
        if nm in new_values:
            new_values[nm] = max(0.0, new_values[nm] - total * (s["pct_to_trim"] / 100.0))
    for b in rebalance_proposal.get("buy", []):
        nm = b["name"]
        if nm in new_values:
            new_values[nm] += total * (b["pct_to_add"] / 100.0)
    new_total = sum(new_values.values()) or 1e-9
    category_totals: dict = {}
    equity_total = 0.0
    for a in holdings.assets:
        v = new_values[a.name]
        key = a.category or "Other"
        category_totals[key] = category_totals.get(key, 0.0) + v
        if a.category == "Equity":
            equity_total += v
    category_pct = {k: round(v / new_total * 100, 2) for k, v in category_totals.items()}
    new_equity_pct = round(equity_total / new_total * 100, 2)
    return {
        "category_pct": category_pct,
        "new_equity_pct": new_equity_pct,
        "fits_risk_band_60_70": 60.0 <= new_equity_pct <= 70.0,
    }


TOOLS = [get_nifty_trend, get_news_for_holding, compute_concentration, propose_drawdown_simulation]
