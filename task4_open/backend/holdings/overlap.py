"""Symmetric weighted fund-overlap math + matrix builder."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from amfi.schema import FundHolding, Scheme

_PUNCT_RE = re.compile(r"[^\w\s&]")
_WS_RE = re.compile(r"\s+")


def _stock_key(h: FundHolding) -> str:
    """ISIN if present, else normalized name. Used to align stocks across two schemes."""
    if h.isin:
        return f"isin:{h.isin}"
    s = _PUNCT_RE.sub("", h.name.lower())
    s = _WS_RE.sub(" ", s).strip()
    return f"name:{s}"


@dataclass
class OverlapPair:
    overlap_pct: float
    shared_count: int
    shared_stocks: list[dict[str, Any]]


def pairwise_overlap(scheme_a: Scheme, scheme_b: Scheme) -> OverlapPair:
    """Symmetric weighted overlap: sum_over_shared(min(weight_in_a, weight_in_b))."""
    a_by_key = {_stock_key(h): h for h in scheme_a.holdings}
    b_by_key = {_stock_key(h): h for h in scheme_b.holdings}
    shared: list[dict[str, Any]] = []
    total_min = 0.0
    for key, ha in a_by_key.items():
        hb = b_by_key.get(key)
        if hb is None:
            continue
        min_w = min(ha.weight_pct, hb.weight_pct)
        total_min += min_w
        shared.append({
            "name": ha.name,
            "isin": ha.isin,
            "weight_a": ha.weight_pct,
            "weight_b": hb.weight_pct,
            "min": min_w,
        })
    shared.sort(key=lambda s: s["min"], reverse=True)
    return OverlapPair(
        overlap_pct=round(total_min, 4),
        shared_count=len(shared),
        shared_stocks=shared,
    )


def build_matrix(matched_funds: list[dict]) -> dict:
    """Build the full N×N matrix + shared_stocks_index keyed by 'i_j' (i<j).

    Args:
        matched_funds: list of {"asset_name", "scheme_name", "matched_by", "scheme": Scheme}.
    """
    n = len(matched_funds)
    matrix: list[list[dict]] = [
        [{"i": i, "j": j, "overlap_pct": 0.0, "shared_count": 0} for j in range(n)]
        for i in range(n)
    ]
    shared_index: dict[str, list[dict]] = {}
    for i in range(n):
        for j in range(i, n):
            res = pairwise_overlap(matched_funds[i]["scheme"], matched_funds[j]["scheme"])
            cell = {"i": i, "j": j, "overlap_pct": res.overlap_pct, "shared_count": res.shared_count}
            matrix[i][j] = cell
            matrix[j][i] = {"i": j, "j": i, "overlap_pct": res.overlap_pct, "shared_count": res.shared_count}
            if i < j and res.shared_count > 0:
                shared_index[f"{i}_{j}"] = res.shared_stocks
    return {"matrix": matrix, "shared_stocks_index": shared_index}
