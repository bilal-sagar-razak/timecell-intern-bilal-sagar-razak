# Task 4c — Holdings + Fund-Overlap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Holdings stub on the Task 4a dashboard with a per-fund detail table (sortable, expandable to show each fund's underlying stocks) and a fund-overlap matrix heatmap with drill-down into shared stocks. Both backed by a committed snapshot of AMFI's monthly portfolio disclosures.

**Architecture:** Two new backend modules — `amfi/` (bundle loader + matching) and `holdings/` (overlap math + endpoints). One standalone refresh CLI under `scripts/` with per-AMC parser adapters. Frontend gains 5 components and replaces the existing stub page. Zero LLM calls; everything is deterministic parsing + math.

**Tech Stack:** FastAPI, Pydantic v2, `rapidfuzz` (fuzzy matching), `openpyxl` + `xlrd` + `pdfplumber` (per-AMC adapters), `requests` (AMFI fetch), Next.js 16 + React 19, Tailwind v4.

**Reference spec:** `docs/superpowers/specs/2026-05-03-task4c-holdings-overlap-design.md`

**Branch:** `task4c/holdings-overlap` (created off `main` at `b77ecc0`; spec committed at `43a0316`).

**Commit grouping:**
1. Tasks 1–4 → `amfi/` package (schema, normalize, bundle loader, match.py) + tests
2. Tasks 5–7 → `holdings/` package (overlap math) + 2 endpoints + main.py wiring + tests
3. Tasks 8–11 → refresh script + 2 real adapters (HDFC, ICICI Pru) + 18 stub adapters + Makefile target + tests
4. Tasks 12–15 → frontend Holdings table + HoldingExpandedRow + MatchBadge + store/api wiring + tests
5. Tasks 16–18 → frontend OverlapHeatmap + OverlapDrilldown + page assembly + tests
6. Task 19 → final user gate (no push, no PR)

**Critical scope rule:** v1 ships with **2 real per-AMC adapters** (HDFC, ICICI Pru) and **18 placeholder adapters** that return `[]`. The committed `data/amfi_holdings.json` is a small fixture covering ~30 schemes from the 2 real adapters' AMCs (enough to demo the table + matrix end-to-end). Full adapter coverage is explicit non-goal for v1; missing adapters degrade gracefully (`match=none` for those funds). This is documented in `data/amfi_coverage.md`.

**Test isolation rule:** Backend tests that load the bundle MUST monkeypatch `amfi.bundle.BUNDLE_PATH` to a per-test fixture, never read the real `data/amfi_holdings.json`. The refresh-script integration test stubs `requests.get` — never hits AMFI.

---

## File Structure

**Backend (new):**

- `task4_open/backend/amfi/__init__.py` — package marker.
- `task4_open/backend/amfi/schema.py` — Pydantic models: `FundHolding`, `Scheme`, `AmfiBundle`.
- `task4_open/backend/amfi/normalize.py` — `normalize_scheme_name(name: str) -> str`. Pure string function.
- `task4_open/backend/amfi/bundle.py` — `load_bundle()`, `BundleMissing`, `BundleMalformed`, lazy module-level singleton.
- `task4_open/backend/amfi/match.py` — `match_user_funds(assets, bundle) -> list[FundMatch]` + `FundMatch` dataclass/model.
- `task4_open/backend/holdings/__init__.py` — package marker.
- `task4_open/backend/holdings/overlap.py` — `pairwise_overlap(a, b) -> OverlapPair`, `build_matrix(matched_schemes) -> dict`.
- `task4_open/backend/holdings/api.py` — request/response Pydantic models for the two endpoints.
- `task4_open/backend/data/amfi_holdings.json` — committed bundle fixture (~30 schemes, enough to exercise both endpoints).
- `task4_open/backend/data/amfi_coverage.md` — committed alongside the bundle, lists which AMCs/schemes are present.
- `task4_open/backend/scripts/__init__.py` — package marker.
- `task4_open/backend/scripts/refresh_amfi.py` — CLI: discover → fetch → dispatch adapters → emit JSON + coverage.md.
- `task4_open/backend/scripts/amfi_adapters/__init__.py` — package marker; `ADAPTERS` dict keyed by AMC code.
- `task4_open/backend/scripts/amfi_adapters/hdfc.py` — real adapter.
- `task4_open/backend/scripts/amfi_adapters/icici_pru.py` — real adapter.
- `task4_open/backend/scripts/amfi_adapters/{nippon,sbi,aditya_birla,kotak,axis,uti,dsp,mirae,tata,edelweiss,ppfas,quant,motilal_oswal,invesco,bandhan,franklin_templeton,hsbc,sundaram}.py` — 18 placeholder adapters returning `[]` with a `WARN` log.
- `task4_open/backend/tests/test_amfi_normalize.py` — 4 tests.
- `task4_open/backend/tests/test_amfi_bundle.py` — 3 tests.
- `task4_open/backend/tests/test_amfi_match.py` — 5 tests.
- `task4_open/backend/tests/test_holdings_overlap.py` — 5 tests.
- `task4_open/backend/tests/test_refresh_script.py` — 1 integration test (stubbed network).
- `task4_open/backend/tests/test_amfi_adapters/__init__.py`.
- `task4_open/backend/tests/test_amfi_adapters/test_hdfc.py` — 1 test.
- `task4_open/backend/tests/test_amfi_adapters/test_icici_pru.py` — 1 test.
- `task4_open/backend/tests/fixtures/amfi/hdfc_sample.xlsx` — small redacted fixture.
- `task4_open/backend/tests/fixtures/amfi/icici_pru_sample.xlsx` — small redacted fixture.
- `task4_open/backend/tests/fixtures/amfi/bundle_tiny.json` — tiny 4-scheme fixture for bundle/match/overlap tests.

**Backend (modified):**
- `task4_open/backend/main.py` — add `HoldingsRequest` + `/api/holdings/per-fund` + `/api/holdings/overlap` endpoints; import `amfi.bundle.load_bundle`, `amfi.match.match_user_funds`, `holdings.overlap.build_matrix`.
- `task4_open/backend/tests/test_main.py` — add 3 tests (per-fund happy, overlap happy, 503 when bundle missing).
- `task4_open/backend/requirements.txt` — add `rapidfuzz>=3.10`, `xlrd>=2.0.1`.
- `task4_open/Makefile` — add `refresh-amfi` target.

**Frontend (new):**
- `task4_open/frontend/components/HoldingsTable.tsx` — sortable per-fund table.
- `task4_open/frontend/components/HoldingExpandedRow.tsx` — expanded inline panel.
- `task4_open/frontend/components/MatchBadge.tsx` — `ISIN`/`name`/`none` chip.
- `task4_open/frontend/components/OverlapHeatmap.tsx` — CSS-grid heatmap.
- `task4_open/frontend/components/OverlapDrilldown.tsx` — right-hand shared-stocks panel.
- `task4_open/frontend/__tests__/HoldingsTable.test.tsx` — 3 tests.
- `task4_open/frontend/__tests__/MatchBadge.test.tsx` — 1 test.
- `task4_open/frontend/__tests__/OverlapHeatmap.test.tsx` — 2 tests.
- `task4_open/frontend/__tests__/OverlapDrilldown.test.tsx` — 2 tests.

**Frontend (modified):**
- `task4_open/frontend/lib/api.ts` — add `FundHolding`, `AmfiScheme`, `FundMatch`, `HoldingsResponse`, `OverlapCell`, `OverlapFund`, `SharedStock`, `OverlapResponse` types and `fetchHoldingsPerFund()`, `fetchOverlap()` functions.
- `task4_open/frontend/lib/store.ts` — add `holdingsData`, `overlapData` fields and setters (NOT in `partialize`).
- `task4_open/frontend/app/dashboard/holdings/page.tsx` — replace the stub.

---

### Task 1: AMFI schema + normalize

**Files:**
- Create: `task4_open/backend/amfi/__init__.py`
- Create: `task4_open/backend/amfi/schema.py`
- Create: `task4_open/backend/amfi/normalize.py`
- Create: `task4_open/backend/tests/test_amfi_normalize.py`

- [ ] **Step 1: Create package marker**

```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak
mkdir -p task4_open/backend/amfi
touch task4_open/backend/amfi/__init__.py
```

- [ ] **Step 2: Write the schema file**

Create `task4_open/backend/amfi/schema.py`:

```python
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
```

- [ ] **Step 3: Write the failing test**

Create `task4_open/backend/tests/test_amfi_normalize.py`:

```python
"""Unit tests for amfi/normalize.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_normalize_strips_direct_growth_suffix():
    from amfi.normalize import normalize_scheme_name
    assert (
        normalize_scheme_name("Parag Parikh Flexi Cap Fund - Direct Growth")
        == normalize_scheme_name("Parag Parikh Flexi Cap Fund")
    )


def test_normalize_strips_idcw_and_dividend_qualifiers():
    from amfi.normalize import normalize_scheme_name
    out = normalize_scheme_name("HDFC Flexi Cap Fund (IDCW)")
    assert "idcw" not in out
    assert normalize_scheme_name("HDFC Flexi Cap Fund - Dividend") == out


def test_normalize_collapses_whitespace_and_lowercases():
    from amfi.normalize import normalize_scheme_name
    assert normalize_scheme_name("  Quant   Active   Fund  ") == "quant active fund"


def test_normalize_strips_punctuation_except_ampersand_and_digits():
    from amfi.normalize import normalize_scheme_name
    assert normalize_scheme_name("S&P BSE 500 Fund - Direct, Plan A") == "s&p bse 500 fund"
```

- [ ] **Step 4: Run test to verify failure**

Run:
```bash
. /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/.venv/bin/activate
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/backend
python -m pytest tests/test_amfi_normalize.py -v
```
Expected: 4 failed (`ModuleNotFoundError: No module named 'amfi.normalize'`).

- [ ] **Step 5: Implement normalize.py**

Create `task4_open/backend/amfi/normalize.py`:

```python
"""Scheme-name normalization shared by the bundle loader, matcher, and adapters."""
from __future__ import annotations

import re

# Plan/IDCW/dividend qualifiers in parentheses
_PAREN_QUAL_RE = re.compile(r"\((?:direct|growth|g|idcw|dividend|plan\s*[a-z0-9]+)\)", re.IGNORECASE)
# Same qualifiers as trailing suffix after " - " or " "
_SUFFIX_RE = re.compile(
    r"\s*-?\s*(?:direct\s+plan|direct\s+growth|direct|growth|regular|dividend|idcw|growth\s+plan)\s*$",
    re.IGNORECASE,
)
# Fund-house code suffix like "(d)" or "(g)"
_SHORT_PAREN_RE = re.compile(r"\([dg]\)", re.IGNORECASE)
# Punctuation to strip (keep & and digits)
_PUNCT_RE = re.compile(r"[^\w\s&]")
_WS_RE = re.compile(r"\s+")


def normalize_scheme_name(name: str) -> str:
    """Lowercase, strip plan/idcw/growth qualifiers, collapse whitespace.

    Used by both the bundle indexer and the matcher so two callers always agree."""
    s = name.lower()
    s = _PAREN_QUAL_RE.sub("", s)
    s = _SHORT_PAREN_RE.sub("", s)
    # Strip trailing qualifiers repeatedly (handle "fund - direct - growth")
    while True:
        new = _SUFFIX_RE.sub("", s)
        if new == s:
            break
        s = new
    s = _PUNCT_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return s
```

- [ ] **Step 6: Run tests to verify pass**

Run: `python -m pytest tests/test_amfi_normalize.py -v`
Expected: 4 passed.

- [ ] **Step 7: Do NOT commit yet** (held until Task 4 — single commit for the whole `amfi/` module).

---

### Task 2: AMFI bundle loader

**Files:**
- Create: `task4_open/backend/amfi/bundle.py`
- Create: `task4_open/backend/tests/fixtures/amfi/bundle_tiny.json`
- Create: `task4_open/backend/tests/test_amfi_bundle.py`

- [ ] **Step 1: Create the tiny bundle fixture**

```bash
mkdir -p task4_open/backend/tests/fixtures/amfi
```

Create `task4_open/backend/tests/fixtures/amfi/bundle_tiny.json`:

```json
{
  "version": 1,
  "as_of_month": "2026-04",
  "fetched_at": "2026-05-03T12:00:00Z",
  "schemes": [
    {
      "scheme_name": "Parag Parikh Flexi Cap Fund - Direct Growth",
      "isin": "INF879O01027",
      "amc": "PPFAS",
      "scheme_aum_inr": 87543210000,
      "as_of_date": "2026-04-30",
      "holdings": [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 8.42, "value_inr": 7372000000, "kind": "equity"},
        {"name": "Bajaj Holdings", "isin": "INE118A01012", "weight_pct": 7.10, "value_inr": 6215000000, "kind": "equity"}
      ],
      "cash_pct": 4.20
    },
    {
      "scheme_name": "HDFC Flexi Cap Fund - Direct Growth",
      "isin": "INF179K01YV8",
      "amc": "HDFC",
      "scheme_aum_inr": 65000000000,
      "as_of_date": "2026-04-30",
      "holdings": [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 9.20, "value_inr": 5980000000, "kind": "equity"},
        {"name": "ICICI Bank", "isin": "INE090A01021", "weight_pct": 6.50, "value_inr": 4225000000, "kind": "equity"}
      ],
      "cash_pct": 3.10
    },
    {
      "scheme_name": "ICICI Pru Gilt Fund - Direct Growth",
      "isin": "INF109K01ZF6",
      "amc": "ICICI Pru",
      "scheme_aum_inr": 12000000000,
      "as_of_date": "2026-04-30",
      "holdings": [
        {"name": "GOI 7.18% 2033", "isin": null, "weight_pct": 45.0, "value_inr": 5400000000, "kind": "debt"}
      ],
      "cash_pct": 8.50
    },
    {
      "scheme_name": "Quant Active Fund - Direct Growth",
      "isin": "INF966L01366",
      "amc": "Quant",
      "scheme_aum_inr": 22000000000,
      "as_of_date": "2026-04-30",
      "holdings": [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 5.10, "value_inr": 1122000000, "kind": "equity"},
        {"name": "Reliance Industries", "isin": "INE002A01018", "weight_pct": 4.20, "value_inr": 924000000, "kind": "equity"}
      ],
      "cash_pct": 2.10
    }
  ]
}
```

- [ ] **Step 2: Write the failing test**

Create `task4_open/backend/tests/test_amfi_bundle.py`:

```python
"""Tests for amfi/bundle.py loader + indexes."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURE = Path(__file__).parent / "fixtures" / "amfi" / "bundle_tiny.json"


@pytest.fixture(autouse=True)
def _reset_bundle(monkeypatch):
    """Point loader at the test fixture and clear any cached singleton."""
    monkeypatch.setattr("amfi.bundle.BUNDLE_PATH", FIXTURE)
    from amfi import bundle
    bundle._cached = None
    yield
    bundle._cached = None


def test_load_bundle_returns_4_schemes():
    from amfi.bundle import load_bundle
    b = load_bundle()
    assert len(b.schemes) == 4


def test_by_isin_index_lookup_hits():
    from amfi.bundle import load_bundle
    b = load_bundle()
    assert b.by_isin["INF879O01027"].scheme_name.startswith("Parag Parikh Flexi Cap")


def test_by_normalized_name_index_lookup_hits():
    from amfi.bundle import load_bundle
    from amfi.normalize import normalize_scheme_name
    b = load_bundle()
    key = normalize_scheme_name("HDFC Flexi Cap Fund")
    assert b.by_normalized_name[key].isin == "INF179K01YV8"


def test_load_bundle_missing_raises(monkeypatch, tmp_path):
    from amfi.bundle import BundleMissing, load_bundle
    monkeypatch.setattr("amfi.bundle.BUNDLE_PATH", tmp_path / "nope.json")
    from amfi import bundle
    bundle._cached = None
    with pytest.raises(BundleMissing):
        load_bundle()
```

- [ ] **Step 3: Run test to verify failure**

Run: `python -m pytest tests/test_amfi_bundle.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'amfi.bundle'`.

- [ ] **Step 4: Implement bundle.py**

Create `task4_open/backend/amfi/bundle.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify pass**

Run: `python -m pytest tests/test_amfi_bundle.py -v`
Expected: 4 passed (3 spec'd + the missing-bundle test).

- [ ] **Step 6: Do NOT commit yet** (held until Task 4).

---

### Task 3: AMFI fund matcher

**Files:**
- Create: `task4_open/backend/amfi/match.py`
- Modify: `task4_open/backend/requirements.txt`
- Create: `task4_open/backend/tests/test_amfi_match.py`

- [ ] **Step 1: Add rapidfuzz to requirements**

Append to `task4_open/backend/requirements.txt`:

```
rapidfuzz>=3.10
xlrd>=2.0.1
```

Install: `pip install rapidfuzz xlrd`
Expected: `Successfully installed rapidfuzz-3.x xlrd-2.0.x` (or "Requirement already satisfied").

- [ ] **Step 2: Smoke-import**

Run: `python -c "import rapidfuzz; print(rapidfuzz.__version__)"`
Expected: prints a version string.

- [ ] **Step 3: Write the failing test**

Create `task4_open/backend/tests/test_amfi_match.py`:

```python
"""Unit tests for amfi/match.py — uses the tiny bundle fixture."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURE = Path(__file__).parent / "fixtures" / "amfi" / "bundle_tiny.json"


@pytest.fixture(autouse=True)
def _reset_bundle(monkeypatch):
    monkeypatch.setattr("amfi.bundle.BUNDLE_PATH", FIXTURE)
    from amfi import bundle
    bundle._cached = None
    yield
    bundle._cached = None


def _asset(name: str, isin: str | None = None, amc: str | None = None):
    from parser.schema import Asset
    return Asset(
        name=name, asset_type="mutual_fund", isin=isin, amc=amc,
        units=1.0, invested_value_inr=1000.0, current_value_inr=1100.0,
        pnl_inr=100.0, pnl_pct=10.0,
    )


def test_match_by_isin_exact():
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    matches = match_user_funds([_asset("Parag Parikh Flexi Cap Fund", isin="INF879O01027")], b)
    assert matches[0].matched is True
    assert matches[0].matched_by == "isin"
    assert matches[0].confidence == 1.0
    assert matches[0].scheme.isin == "INF879O01027"


def test_match_by_normalized_name_exact():
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    matches = match_user_funds([_asset("HDFC Flexi Cap Fund - Direct Growth")], b)
    assert matches[0].matched is True
    assert matches[0].matched_by == "name"
    assert matches[0].confidence >= 0.9
    assert matches[0].scheme.isin == "INF179K01YV8"


def test_match_by_fuzzy_name_above_threshold():
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    # Slightly typo'd name should still fuzzy-match HDFC Flexi Cap Fund
    matches = match_user_funds([_asset("HDFC FlexiCap Fund Direct Plan")], b)
    assert matches[0].matched is True
    assert matches[0].matched_by == "name"
    assert 0.85 <= matches[0].confidence < 1.0


def test_match_no_isin_or_name_returns_none():
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    matches = match_user_funds([_asset("Made Up Fund That Does Not Exist Anywhere")], b)
    assert matches[0].matched is False
    assert matches[0].matched_by == "none"
    assert matches[0].scheme is None


def test_match_scoped_to_amc_when_provided():
    """When asset.amc is provided, fuzzy lookup is restricted to that AMC's schemes."""
    from amfi.bundle import load_bundle
    from amfi.match import match_user_funds
    b = load_bundle()
    # "Flexi Cap Fund" alone is ambiguous (HDFC + PPFAS); scope by AMC=HDFC
    matches = match_user_funds([_asset("Flexi Cap Fund", amc="HDFC")], b)
    assert matches[0].matched is True
    assert matches[0].scheme.amc == "HDFC"
```

- [ ] **Step 4: Run test to verify failure**

Run: `python -m pytest tests/test_amfi_match.py -v`
Expected: 5 failed (`ModuleNotFoundError: No module named 'amfi.match'`).

- [ ] **Step 5: Implement match.py**

Create `task4_open/backend/amfi/match.py`:

```python
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
        score = fuzz.token_set_ratio(norm, normalize_scheme_name(scheme.scheme_name)) / 100.0
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
```

- [ ] **Step 6: Run tests to verify pass**

Run: `python -m pytest tests/test_amfi_match.py -v`
Expected: 5 passed.

- [ ] **Step 7: Run full backend suite (no regressions)**

Run: `python -m pytest tests/ -q`
Expected: 77 baseline + 13 new (4 normalize + 4 bundle + 5 match) = 90 passed.

- [ ] **Step 8: Do NOT commit yet** (held until Task 4).

---

### Task 4: Tiny committed bundle fixture + COMMIT 1

**Files:**
- Create: `task4_open/backend/data/amfi_holdings.json`
- Create: `task4_open/backend/data/amfi_coverage.md`

- [ ] **Step 1: Copy the test fixture into the live bundle path**

```bash
mkdir -p task4_open/backend/data
cp task4_open/backend/tests/fixtures/amfi/bundle_tiny.json task4_open/backend/data/amfi_holdings.json
```

This is the smallest possible real bundle — 4 schemes (PPFAS, HDFC, ICICI Pru, Quant). Reviewers can boot the backend and exercise the endpoints immediately. The `make refresh-amfi` script (Task 9–10) will overwrite this with the real fetched data.

- [ ] **Step 2: Write the coverage doc**

Create `task4_open/backend/data/amfi_coverage.md`:

```markdown
# AMFI bundle coverage

**As of:** 2026-04
**Generated:** 2026-05-03 (committed seed; regenerate via `make refresh-amfi`)

## Schemes in this bundle

| AMC | Scheme | ISIN |
|---|---|---|
| PPFAS | Parag Parikh Flexi Cap Fund | INF879O01027 |
| HDFC | HDFC Flexi Cap Fund | INF179K01YV8 |
| ICICI Pru | ICICI Pru Gilt Fund | INF109K01ZF6 |
| Quant | Quant Active Fund | INF966L01366 |

## Adapter status

| AMC | Adapter | Status |
|---|---|---|
| HDFC | `scripts/amfi_adapters/hdfc.py` | implemented |
| ICICI Pru | `scripts/amfi_adapters/icici_pru.py` | implemented |
| Nippon, SBI, Aditya Birla, Kotak, Axis, UTI, DSP, Mirae, Tata, Edelweiss, PPFAS, Quant, Motilal Oswal, Invesco, Bandhan, Franklin Templeton, HSBC, Sundaram | (placeholder) | returns `[]` with WARN log |

## How to refresh

```bash
make refresh-amfi
```

The script downloads the latest monthly disclosure ZIP from amfiindia.com,
dispatches each per-AMC file through its adapter, and rewrites this file
plus `amfi_holdings.json`. Placeholder adapters skip their AMCs silently
(logged as WARN). Adding a new adapter is a single file under
`scripts/amfi_adapters/<amc>.py` exposing `parse(file_path) -> list[Scheme]`.
```

- [ ] **Step 3: Re-run all backend tests against the live bundle path**

Run: `python -m pytest tests/ -q`
Expected: still 90 passed (the bundle tests use their own monkeypatched fixture; the live bundle is only read by future endpoint tests).

- [ ] **Step 4: Commit (commit 1)**

```bash
git add task4_open/backend/amfi/__init__.py \
        task4_open/backend/amfi/schema.py \
        task4_open/backend/amfi/normalize.py \
        task4_open/backend/amfi/bundle.py \
        task4_open/backend/amfi/match.py \
        task4_open/backend/data/amfi_holdings.json \
        task4_open/backend/data/amfi_coverage.md \
        task4_open/backend/requirements.txt \
        task4_open/backend/tests/fixtures/amfi/bundle_tiny.json \
        task4_open/backend/tests/test_amfi_normalize.py \
        task4_open/backend/tests/test_amfi_bundle.py \
        task4_open/backend/tests/test_amfi_match.py
git commit -m "task4c: amfi package — schema, bundle loader, match (ISIN + fuzzy name)"
```

---

### Task 5: Holdings overlap math

**Files:**
- Create: `task4_open/backend/holdings/__init__.py`
- Create: `task4_open/backend/holdings/overlap.py`
- Create: `task4_open/backend/tests/test_holdings_overlap.py`

- [ ] **Step 1: Create package marker**

```bash
mkdir -p task4_open/backend/holdings
touch task4_open/backend/holdings/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `task4_open/backend/tests/test_holdings_overlap.py`:

```python
"""Unit tests for holdings/overlap.py — pure math, no bundle/network."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _scheme(name: str, holdings: list[dict], cash_pct: float = 0.0):
    from amfi.schema import FundHolding, Scheme
    return Scheme(
        scheme_name=name, isin=None, amc="X",
        scheme_aum_inr=1e9, as_of_date=date(2026, 4, 30),
        holdings=[FundHolding(**h) for h in holdings],
        cash_pct=cash_pct,
    )


def test_identical_funds_overlap_close_to_100():
    from holdings.overlap import pairwise_overlap
    a = _scheme("A", [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 50.0, "value_inr": 5e8},
        {"name": "Reliance",  "isin": "INE002A01018", "weight_pct": 50.0, "value_inr": 5e8},
    ])
    res = pairwise_overlap(a, a)
    assert 99.0 <= res.overlap_pct <= 100.01
    assert res.shared_count == 2


def test_disjoint_funds_overlap_zero():
    from holdings.overlap import pairwise_overlap
    a = _scheme("A", [{"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 100.0, "value_inr": 1e9}])
    b = _scheme("B", [{"name": "Reliance",  "isin": "INE002A01018", "weight_pct": 100.0, "value_inr": 1e9}])
    res = pairwise_overlap(a, b)
    assert res.overlap_pct == 0.0
    assert res.shared_count == 0


def test_partial_overlap_uses_min_weight():
    from holdings.overlap import pairwise_overlap
    a = _scheme("A", [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 30.0, "value_inr": 3e8},
        {"name": "Reliance",  "isin": "INE002A01018", "weight_pct": 70.0, "value_inr": 7e8},
    ])
    b = _scheme("B", [
        {"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 50.0, "value_inr": 5e8},
        {"name": "Infosys",   "isin": "INE009A01021", "weight_pct": 50.0, "value_inr": 5e8},
    ])
    res = pairwise_overlap(a, b)
    # min(30, 50) = 30 for HDFC Bank; nothing else shared
    assert abs(res.overlap_pct - 30.0) < 1e-6
    assert res.shared_count == 1
    assert res.shared_stocks[0]["name"] == "HDFC Bank"
    assert res.shared_stocks[0]["min"] == 30.0


def test_match_by_name_when_isin_missing():
    """When ISIN is null on either side, fall back to normalized stock-name match."""
    from holdings.overlap import pairwise_overlap
    a = _scheme("A", [{"name": "HDFC Bank", "isin": None, "weight_pct": 60.0, "value_inr": 6e8}])
    b = _scheme("B", [{"name": "HDFC Bank", "isin": None, "weight_pct": 40.0, "value_inr": 4e8}])
    res = pairwise_overlap(a, b)
    assert abs(res.overlap_pct - 40.0) < 1e-6


def test_build_matrix_emits_full_n_by_n_with_shared_index():
    from holdings.overlap import build_matrix
    a = _scheme("A", [{"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 50.0, "value_inr": 5e8}])
    b = _scheme("B", [{"name": "HDFC Bank", "isin": "INE040A01034", "weight_pct": 30.0, "value_inr": 3e8}])
    funds = [
        {"asset_name": "Fund A", "scheme_name": "A", "matched_by": "isin", "scheme": a},
        {"asset_name": "Fund B", "scheme_name": "B", "matched_by": "isin", "scheme": b},
    ]
    out = build_matrix(funds)
    assert len(out["matrix"]) == 2
    assert len(out["matrix"][0]) == 2
    # Symmetry
    assert out["matrix"][0][1]["overlap_pct"] == out["matrix"][1][0]["overlap_pct"]
    # shared_stocks_index keyed only for i<j
    assert "0_1" in out["shared_stocks_index"]
    assert "1_0" not in out["shared_stocks_index"]
```

- [ ] **Step 3: Run test to verify failure**

Run: `python -m pytest tests/test_holdings_overlap.py -v`
Expected: 5 failed (`ModuleNotFoundError: No module named 'holdings.overlap'`).

- [ ] **Step 4: Implement overlap.py**

Create `task4_open/backend/holdings/overlap.py`:

```python
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
    matrix: list[list[dict]] = [[{"i": i, "j": j, "overlap_pct": 0.0, "shared_count": 0} for j in range(n)] for i in range(n)]
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
```

- [ ] **Step 5: Run tests to verify pass**

Run: `python -m pytest tests/test_holdings_overlap.py -v`
Expected: 5 passed.

- [ ] **Step 6: Do NOT commit yet** (held until Task 7).

---

### Task 6: Holdings API request/response models

**Files:**
- Create: `task4_open/backend/holdings/api.py`

- [ ] **Step 1: Write the API models**

Create `task4_open/backend/holdings/api.py`:

```python
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
```

- [ ] **Step 2: Sanity-import**

Run:
```bash
python -c "from holdings.api import HoldingsRequest, PerFundResponse, OverlapResponse; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Do NOT commit yet** (held until Task 7).

---

### Task 7: Holdings endpoints + COMMIT 2

**Files:**
- Modify: `task4_open/backend/main.py`
- Modify: `task4_open/backend/tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

Append to `task4_open/backend/tests/test_main.py`:

```python
from datetime import date as _d


@pytest.fixture
def _live_bundle(monkeypatch, tmp_path_factory):
    """Point amfi/bundle at the tiny test fixture so endpoint tests don't need data/amfi_holdings.json."""
    src = Path(__file__).parent / "fixtures" / "amfi" / "bundle_tiny.json"
    monkeypatch.setattr("amfi.bundle.BUNDLE_PATH", src)
    from amfi import bundle
    bundle._cached = None
    yield
    bundle._cached = None


def _holdings_with_one_known_fund():
    """A holdings JSON with one fund that matches the tiny bundle by ISIN."""
    return {
        "holder_name": "Test", "source_format": "test",
        "summary": {
            "total_invested_inr": 1000.0, "total_current_inr": 1100.0,
            "total_pnl_inr": 100.0, "total_pnl_pct": 10.0,
            "asset_count": 1, "overall_xirr_pct": None, "statement_date": None,
        },
        "assets": [
            {"name": "Parag Parikh Flexi Cap", "asset_type": "mutual_fund",
             "isin": "INF879O01027", "amc": "PPFAS", "category": "Equity",
             "sub_category": "Flexi Cap", "folio": None, "units": 100.0,
             "invested_value_inr": 1000.0, "current_value_inr": 1100.0,
             "xirr_pct": None, "pnl_inr": 100.0, "pnl_pct": 10.0},
        ],
        "parser_warnings": [],
    }


def test_per_fund_endpoint_happy_path(_live_bundle):
    body = _holdings_with_one_known_fund()
    r = client.post("/api/holdings/per-fund", json={"holdings": body})
    assert r.status_code == 200
    data = r.json()
    assert len(data["matches"]) == 1
    assert data["matches"][0]["matched"] is True
    assert data["matches"][0]["matched_by"] == "isin"


def test_overlap_endpoint_happy_path(_live_bundle):
    body = _holdings_with_one_known_fund()
    body["assets"].append({
        "name": "HDFC Flexi Cap Fund - Direct Growth", "asset_type": "mutual_fund",
        "isin": "INF179K01YV8", "amc": "HDFC", "category": "Equity",
        "sub_category": "Flexi Cap", "folio": None, "units": 50.0,
        "invested_value_inr": 500.0, "current_value_inr": 550.0,
        "xirr_pct": None, "pnl_inr": 50.0, "pnl_pct": 10.0,
    })
    r = client.post("/api/holdings/overlap", json={"holdings": body})
    assert r.status_code == 200
    data = r.json()
    assert len(data["funds"]) == 2
    assert len(data["matrix"]) == 2
    assert "0_1" in data["shared_stocks_index"]  # PPFAS + HDFC both hold HDFC Bank


def test_per_fund_returns_503_when_bundle_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("amfi.bundle.BUNDLE_PATH", tmp_path / "nope.json")
    from amfi import bundle
    bundle._cached = None
    body = _holdings_with_one_known_fund()
    r = client.post("/api/holdings/per-fund", json={"holdings": body})
    assert r.status_code == 503
    assert "bundle missing" in r.json()["detail"]["error"].lower()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_main.py::test_per_fund_endpoint_happy_path tests/test_main.py::test_overlap_endpoint_happy_path tests/test_main.py::test_per_fund_returns_503_when_bundle_missing -v`
Expected: 3 failed (404 — endpoints don't exist).

- [ ] **Step 3: Add the imports + endpoints to main.py**

In `task4_open/backend/main.py`, add to the import block (next to other modules):

```python
from amfi.bundle import BundleMalformed, BundleMissing, load_bundle
from amfi.match import match_user_funds
from holdings.api import (
    HoldingsRequest, OverlapResponse, PerFundResponse,
    OverlapFund, OverlapCell, SharedStock,
)
from holdings.overlap import build_matrix
```

Add the two endpoints at the end of the file:

```python
@app.post("/api/holdings/per-fund", response_model=PerFundResponse)
def holdings_per_fund(req: HoldingsRequest) -> PerFundResponse:
    """Return per-fund AMFI scheme matches (ISIN-first, fuzzy name fallback)."""
    try:
        bundle = load_bundle()
    except BundleMissing as e:
        raise HTTPException(status_code=503, detail={"error": "bundle missing", "detail": str(e)})
    except BundleMalformed as e:
        raise HTTPException(status_code=503, detail={"error": "bundle malformed", "detail": str(e)})
    matches = match_user_funds(req.holdings.assets, bundle)
    return PerFundResponse(matches=matches)


@app.post("/api/holdings/overlap", response_model=OverlapResponse)
def holdings_overlap(req: HoldingsRequest) -> OverlapResponse:
    """Return symmetric weighted overlap matrix + shared-stocks index."""
    try:
        bundle = load_bundle()
    except BundleMissing as e:
        raise HTTPException(status_code=503, detail={"error": "bundle missing", "detail": str(e)})
    except BundleMalformed as e:
        raise HTTPException(status_code=503, detail={"error": "bundle malformed", "detail": str(e)})
    matches = match_user_funds(req.holdings.assets, bundle)
    matched_with_schemes = [
        {"asset_name": m.asset_name, "scheme_name": m.scheme.scheme_name,
         "matched_by": m.matched_by, "scheme": m.scheme}
        for m in matches if m.matched and m.scheme is not None
    ]
    out = build_matrix(matched_with_schemes)
    funds = [
        OverlapFund(asset_name=m["asset_name"], scheme_name=m["scheme_name"], matched_by=m["matched_by"])
        for m in matched_with_schemes
    ]
    matrix = [
        [OverlapCell(**cell) for cell in row] for row in out["matrix"]
    ]
    shared_index = {
        k: [SharedStock(**s) for s in v] for k, v in out["shared_stocks_index"].items()
    }
    return OverlapResponse(funds=funds, matrix=matrix, shared_stocks_index=shared_index)
```

- [ ] **Step 4: Run all backend tests**

Run: `python -m pytest tests/ -q`
Expected: 90 baseline + 5 overlap + 3 main = 98 passed.

- [ ] **Step 5: Commit (commit 2)**

```bash
git add task4_open/backend/holdings/__init__.py \
        task4_open/backend/holdings/overlap.py \
        task4_open/backend/holdings/api.py \
        task4_open/backend/main.py \
        task4_open/backend/tests/test_holdings_overlap.py \
        task4_open/backend/tests/test_main.py
git commit -m "task4c: holdings overlap math + per-fund + overlap endpoints"
```

---

### Task 8: AMFI adapter package + 18 placeholders

**Files:**
- Create: `task4_open/backend/scripts/__init__.py`
- Create: `task4_open/backend/scripts/amfi_adapters/__init__.py`
- Create: `task4_open/backend/scripts/amfi_adapters/{nippon,sbi,aditya_birla,kotak,axis,uti,dsp,mirae,tata,edelweiss,ppfas,quant,motilal_oswal,invesco,bandhan,franklin_templeton,hsbc,sundaram}.py`

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p task4_open/backend/scripts/amfi_adapters
touch task4_open/backend/scripts/__init__.py
```

- [ ] **Step 2: Write the placeholder template**

Create one placeholder, then duplicate. Start with `task4_open/backend/scripts/amfi_adapters/nippon.py`:

```python
"""Placeholder adapter for Nippon. Returns []. Replace with a real parser when needed."""
from __future__ import annotations

import logging
from pathlib import Path

from amfi.schema import Scheme

logger = logging.getLogger(__name__)
AMC_NAME = "Nippon"


def parse(file_path: Path) -> list[Scheme]:
    logger.warning("[amfi_adapters/%s] placeholder — not parsing %s", AMC_NAME, file_path)
    return []
```

- [ ] **Step 3: Generate the other 17 placeholders**

Run:
```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/backend
for amc_pair in "sbi:SBI" "aditya_birla:Aditya Birla" "kotak:Kotak" "axis:Axis" "uti:UTI" "dsp:DSP" "mirae:Mirae" "tata:Tata" "edelweiss:Edelweiss" "ppfas:PPFAS" "quant:Quant" "motilal_oswal:Motilal Oswal" "invesco:Invesco" "bandhan:Bandhan" "franklin_templeton:Franklin Templeton" "hsbc:HSBC" "sundaram:Sundaram"; do
  fname="${amc_pair%%:*}"
  display="${amc_pair##*:}"
  cat > "scripts/amfi_adapters/${fname}.py" <<PYEOF
"""Placeholder adapter for ${display}. Returns []. Replace with a real parser when needed."""
from __future__ import annotations

import logging
from pathlib import Path

from amfi.schema import Scheme

logger = logging.getLogger(__name__)
AMC_NAME = "${display}"


def parse(file_path: Path) -> list[Scheme]:
    logger.warning("[amfi_adapters/%s] placeholder — not parsing %s", AMC_NAME, file_path)
    return []
PYEOF
done
ls scripts/amfi_adapters/ | wc -l
```
Expected: `19` (18 placeholders + nippon.py + __init__.py is already there, so actually 19 files including __init__.py — verify count).

- [ ] **Step 4: Write the package registry**

Create `task4_open/backend/scripts/amfi_adapters/__init__.py`:

```python
"""Per-AMC adapter registry. Real adapters override their entries here."""
from __future__ import annotations

from typing import Callable

from amfi.schema import Scheme

from . import (
    aditya_birla, axis, bandhan, dsp, edelweiss, franklin_templeton,
    hdfc, hsbc, icici_pru, invesco, kotak, mirae, motilal_oswal, nippon,
    ppfas, quant, sbi, sundaram, tata, uti,
)

ADAPTERS: dict[str, Callable[..., list[Scheme]]] = {
    "HDFC": hdfc.parse,
    "ICICI Pru": icici_pru.parse,
    "Nippon": nippon.parse,
    "SBI": sbi.parse,
    "Aditya Birla": aditya_birla.parse,
    "Kotak": kotak.parse,
    "Axis": axis.parse,
    "UTI": uti.parse,
    "DSP": dsp.parse,
    "Mirae": mirae.parse,
    "Tata": tata.parse,
    "Edelweiss": edelweiss.parse,
    "PPFAS": ppfas.parse,
    "Quant": quant.parse,
    "Motilal Oswal": motilal_oswal.parse,
    "Invesco": invesco.parse,
    "Bandhan": bandhan.parse,
    "Franklin Templeton": franklin_templeton.parse,
    "HSBC": hsbc.parse,
    "Sundaram": sundaram.parse,
}


def detect_amc_from_filename(filename: str) -> str | None:
    """Map a filename like 'HDFC_Mutual_Fund_2024_April.xlsx' to an AMC key in ADAPTERS."""
    lower = filename.lower()
    for key in ADAPTERS:
        token = key.lower().replace(" ", "")
        compact = lower.replace("_", "").replace("-", "").replace(" ", "")
        if token in compact:
            return key
    return None
```

> NOTE: This file imports `hdfc` and `icici_pru` which don't exist yet. Tasks 9 and 10 create them. Don't run any test that imports this until Task 10.

- [ ] **Step 5: Do NOT commit yet** (held until Task 11).

---

### Task 9: HDFC adapter (real, with fixture + test)

**Files:**
- Create: `task4_open/backend/scripts/amfi_adapters/hdfc.py`
- Create: `task4_open/backend/tests/fixtures/amfi/hdfc_sample.xlsx`
- Create: `task4_open/backend/tests/test_amfi_adapters/__init__.py`
- Create: `task4_open/backend/tests/test_amfi_adapters/test_hdfc.py`

- [ ] **Step 1: Generate the test fixture**

Run a one-shot Python script to build a minimal xlsx fixture:

```bash
mkdir -p task4_open/backend/tests/test_amfi_adapters
mkdir -p task4_open/backend/tests/fixtures/amfi
python <<'PY'
from openpyxl import Workbook
wb = Workbook()
ws = wb.active
ws.title = "HDFC Flexi Cap Fund"
# Header row that the adapter recognizes
ws.append(["Name of the Instrument", "ISIN", "Industry/Rating", "Quantity", "Market Value (Rs. in Lakhs)", "% to NAV"])
ws.append(["HDFC Bank Limited", "INE040A01034", "Banks", 1000000, 59800.50, 9.20])
ws.append(["ICICI Bank Limited", "INE090A01021", "Banks",  800000, 42250.00, 6.50])
ws.append(["Reliance Industries Limited", "INE002A01018", "Petroleum", 500000, 32100.00, 4.94])
ws.append(["Cash & Cash Equivalents", None, None, None, 20140.00, 3.10])
wb.save("task4_open/backend/tests/fixtures/amfi/hdfc_sample.xlsx")
print("ok")
PY
ls -la task4_open/backend/tests/fixtures/amfi/hdfc_sample.xlsx
```
Expected: file created, ~5–8 KB.

- [ ] **Step 2: Write the failing test**

Create `task4_open/backend/tests/test_amfi_adapters/__init__.py`: (empty)

Create `task4_open/backend/tests/test_amfi_adapters/test_hdfc.py`:

```python
"""HDFC adapter test against a tiny xlsx fixture."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FIXTURE = Path(__file__).parent.parent / "fixtures" / "amfi" / "hdfc_sample.xlsx"


def test_hdfc_adapter_parses_one_scheme_with_3_holdings():
    from scripts.amfi_adapters import hdfc
    schemes = hdfc.parse(FIXTURE)
    assert len(schemes) == 1
    s = schemes[0]
    assert s.amc == "HDFC"
    assert s.scheme_name == "HDFC Flexi Cap Fund"
    assert len(s.holdings) == 3  # 3 stocks; cash row excluded
    h0 = next(h for h in s.holdings if h.isin == "INE040A01034")
    assert h0.name == "HDFC Bank Limited"
    assert abs(h0.weight_pct - 9.20) < 1e-6
    assert abs(s.cash_pct - 3.10) < 1e-6
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_amfi_adapters/test_hdfc.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'scripts.amfi_adapters.hdfc'`).

- [ ] **Step 4: Implement hdfc.py**

Create `task4_open/backend/scripts/amfi_adapters/hdfc.py`:

```python
"""HDFC AMC monthly portfolio-disclosure adapter (xlsx)."""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

from amfi.schema import FundHolding, Scheme

logger = logging.getLogger(__name__)
AMC_NAME = "HDFC"

_NAME_COL_HEADERS = {"name of the instrument", "name of instrument", "instrument name"}
_ISIN_COL_HEADERS = {"isin"}
_PCT_COL_HEADERS = {"% to nav", "% of nav", "%nav"}
_VALUE_COL_HEADERS = {"market value (rs. in lakhs)", "market value (rs in lakhs)", "market value"}


def _find_col(headers: list, candidates: set[str]) -> int | None:
    for i, h in enumerate(headers):
        if h is None:
            continue
        s = str(h).strip().lower()
        if s in candidates:
            return i
    return None


def parse(file_path: Path) -> list[Scheme]:
    """Parse one HDFC monthly disclosure xlsx into Scheme objects (one per worksheet)."""
    wb = load_workbook(file_path, read_only=True, data_only=True)
    schemes: list[Scheme] = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(c).strip() if c else None for c in rows[0]]
        name_idx = _find_col(headers, _NAME_COL_HEADERS)
        isin_idx = _find_col(headers, _ISIN_COL_HEADERS)
        pct_idx = _find_col(headers, _PCT_COL_HEADERS)
        val_idx = _find_col(headers, _VALUE_COL_HEADERS)
        if name_idx is None or pct_idx is None:
            logger.warning("[hdfc] sheet %s has no recognized headers, skipping", ws.title)
            continue
        holdings: list[FundHolding] = []
        cash_pct = 0.0
        for row in rows[1:]:
            if not row or row[name_idx] is None:
                continue
            name = str(row[name_idx]).strip()
            pct_raw = row[pct_idx]
            if pct_raw is None:
                continue
            try:
                pct = float(pct_raw)
            except (TypeError, ValueError):
                continue
            isin = str(row[isin_idx]).strip() if (isin_idx is not None and row[isin_idx]) else None
            value = float(row[val_idx]) * 100000 if (val_idx is not None and row[val_idx] is not None) else 0.0
            if "cash" in name.lower() or isin is None and "equiv" in name.lower():
                cash_pct = pct
                continue
            holdings.append(FundHolding(
                name=name, isin=isin, weight_pct=pct, value_inr=value, kind="equity",
            ))
        if not holdings:
            continue
        schemes.append(Scheme(
            scheme_name=ws.title,
            isin=None,
            amc=AMC_NAME,
            scheme_aum_inr=sum(h.value_inr for h in holdings) / max(0.01, sum(h.weight_pct for h in holdings) / 100),
            as_of_date=date.today(),
            holdings=holdings,
            cash_pct=cash_pct,
        ))
    return schemes
```

- [ ] **Step 5: Run test to verify pass**

Run: `python -m pytest tests/test_amfi_adapters/test_hdfc.py -v`
Expected: 1 passed.

- [ ] **Step 6: Do NOT commit yet** (held until Task 11).

---

### Task 10: ICICI Pru adapter (real, with fixture + test)

**Files:**
- Create: `task4_open/backend/scripts/amfi_adapters/icici_pru.py`
- Create: `task4_open/backend/tests/fixtures/amfi/icici_pru_sample.xlsx`
- Create: `task4_open/backend/tests/test_amfi_adapters/test_icici_pru.py`

- [ ] **Step 1: Generate the fixture**

```bash
python <<'PY'
from openpyxl import Workbook
wb = Workbook()
ws = wb.active
ws.title = "ICICI Pru Gilt Fund"
ws.append(["Instrument", "ISIN", "Rating", "% to Net Assets", "Market Value (Rs Lakhs)"])
ws.append(["7.18% GOI 2033", None, "Sovereign", 45.0, 540000.00])
ws.append(["7.26% GOI 2032", None, "Sovereign", 30.0, 360000.00])
ws.append(["TREPS / Cash", None, None, 8.50, 102000.00])
wb.save("task4_open/backend/tests/fixtures/amfi/icici_pru_sample.xlsx")
print("ok")
PY
```

- [ ] **Step 2: Write the failing test**

Create `task4_open/backend/tests/test_amfi_adapters/test_icici_pru.py`:

```python
"""ICICI Pru adapter test."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FIXTURE = Path(__file__).parent.parent / "fixtures" / "amfi" / "icici_pru_sample.xlsx"


def test_icici_pru_adapter_parses_gilt_fund():
    from scripts.amfi_adapters import icici_pru
    schemes = icici_pru.parse(FIXTURE)
    assert len(schemes) == 1
    s = schemes[0]
    assert s.amc == "ICICI Pru"
    assert s.scheme_name == "ICICI Pru Gilt Fund"
    assert len(s.holdings) == 2  # 2 GOI bonds; cash excluded
    assert all(h.kind == "debt" for h in s.holdings)
    assert abs(s.cash_pct - 8.50) < 1e-6
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_amfi_adapters/test_icici_pru.py -v`
Expected: FAIL.

- [ ] **Step 4: Implement icici_pru.py**

Create `task4_open/backend/scripts/amfi_adapters/icici_pru.py`:

```python
"""ICICI Pru AMC monthly portfolio-disclosure adapter (xlsx)."""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

from amfi.schema import FundHolding, Scheme

logger = logging.getLogger(__name__)
AMC_NAME = "ICICI Pru"

_NAME_HEADERS = {"instrument", "name of the instrument", "name of instrument"}
_ISIN_HEADERS = {"isin"}
_PCT_HEADERS = {"% to net assets", "% to nav", "% nav"}
_VALUE_HEADERS = {"market value (rs lakhs)", "market value (rs. in lakhs)", "market value"}
_DEBT_HINTS = ("goi", "g-sec", "ncd", "bond", "debenture", "treasury", "treps", "g sec")


def _find(headers: list, candidates: set[str]) -> int | None:
    for i, h in enumerate(headers):
        if h is None:
            continue
        if str(h).strip().lower() in candidates:
            return i
    return None


def _kind_for(name: str) -> str:
    n = name.lower()
    if any(h in n for h in _DEBT_HINTS):
        return "debt"
    return "equity"


def parse(file_path: Path) -> list[Scheme]:
    wb = load_workbook(file_path, read_only=True, data_only=True)
    schemes: list[Scheme] = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(c).strip() if c else None for c in rows[0]]
        name_i = _find(headers, _NAME_HEADERS)
        isin_i = _find(headers, _ISIN_HEADERS)
        pct_i = _find(headers, _PCT_HEADERS)
        val_i = _find(headers, _VALUE_HEADERS)
        if name_i is None or pct_i is None:
            logger.warning("[icici_pru] sheet %s missing headers, skipping", ws.title)
            continue
        holdings: list[FundHolding] = []
        cash_pct = 0.0
        for row in rows[1:]:
            if not row or row[name_i] is None:
                continue
            name = str(row[name_i]).strip()
            pct_raw = row[pct_i]
            if pct_raw is None:
                continue
            try:
                pct = float(pct_raw)
            except (TypeError, ValueError):
                continue
            isin = str(row[isin_i]).strip() if (isin_i is not None and row[isin_i]) else None
            value = float(row[val_i]) * 100000 if (val_i is not None and row[val_i] is not None) else 0.0
            n_lower = name.lower()
            if "cash" in n_lower or "treps" in n_lower:
                cash_pct = pct
                continue
            holdings.append(FundHolding(
                name=name, isin=isin, weight_pct=pct, value_inr=value, kind=_kind_for(name),
            ))
        if not holdings:
            continue
        schemes.append(Scheme(
            scheme_name=ws.title,
            isin=None,
            amc=AMC_NAME,
            scheme_aum_inr=sum(h.value_inr for h in holdings) / max(0.01, sum(h.weight_pct for h in holdings) / 100),
            as_of_date=date.today(),
            holdings=holdings,
            cash_pct=cash_pct,
        ))
    return schemes
```

- [ ] **Step 5: Run test to verify pass**

Run: `python -m pytest tests/test_amfi_adapters/test_icici_pru.py -v`
Expected: 1 passed.

- [ ] **Step 6: Run full backend suite**

Run: `python -m pytest tests/ -q`
Expected: 98 baseline + 2 adapter = 100 passed.

- [ ] **Step 7: Do NOT commit yet** (held until Task 11).

---

### Task 11: refresh_amfi.py + Makefile target + integration test + COMMIT 3

**Files:**
- Create: `task4_open/backend/scripts/refresh_amfi.py`
- Create: `task4_open/backend/tests/test_refresh_script.py`
- Modify: `task4_open/Makefile`

- [ ] **Step 1: Write the integration test**

Create `task4_open/backend/tests/test_refresh_script.py`:

```python
"""Integration test for refresh_amfi.py — stubbed network + fake adapters."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_refresh_emits_merged_bundle_and_coverage(monkeypatch, tmp_path):
    """End-to-end stubbed: fake fetch + 2 fake adapters → merged JSON + coverage.md."""
    from amfi.schema import FundHolding, Scheme
    from scripts import refresh_amfi as r

    # Stub fetch_zip to write 2 fake per-AMC files
    fake_amc_dir = tmp_path / "fake_amc_inputs"
    fake_amc_dir.mkdir()
    (fake_amc_dir / "HDFC_Apr2026.xlsx").write_bytes(b"fake-hdfc")
    (fake_amc_dir / "ICICIPru_Apr2026.xlsx").write_bytes(b"fake-icici")
    monkeypatch.setattr(r, "discover_and_fetch", lambda cache_dir: fake_amc_dir)

    # Stub adapter dispatch with two fake adapters
    fake_hdfc_scheme = Scheme(
        scheme_name="HDFC Flexi Cap Fund", isin="INF179K01YV8", amc="HDFC",
        scheme_aum_inr=1e10, as_of_date=date(2026, 4, 30),
        holdings=[FundHolding(name="HDFC Bank", isin="INE040A01034",
                              weight_pct=9.0, value_inr=9e8, kind="equity")],
        cash_pct=2.0,
    )
    fake_icici_scheme = Scheme(
        scheme_name="ICICI Pru Gilt Fund", isin="INF109K01ZF6", amc="ICICI Pru",
        scheme_aum_inr=2e9, as_of_date=date(2026, 4, 30),
        holdings=[FundHolding(name="GOI 7.18% 2033", isin=None,
                              weight_pct=45.0, value_inr=9e8, kind="debt")],
        cash_pct=8.5,
    )
    fake_adapters = {
        "HDFC": MagicMock(return_value=[fake_hdfc_scheme]),
        "ICICI Pru": MagicMock(return_value=[fake_icici_scheme]),
    }
    monkeypatch.setattr(r, "ADAPTERS", fake_adapters)
    monkeypatch.setattr(r, "detect_amc_from_filename", lambda fn: "HDFC" if "hdfc" in fn.lower() else "ICICI Pru")

    bundle_path = tmp_path / "amfi_holdings.json"
    coverage_path = tmp_path / "amfi_coverage.md"
    summary = r.run(bundle_path=bundle_path, coverage_path=coverage_path)

    data = json.loads(bundle_path.read_text())
    assert data["version"] == 1
    assert len(data["schemes"]) == 2
    assert any(s["amc"] == "HDFC" for s in data["schemes"])
    assert "amfi_coverage" in coverage_path.read_text().lower() or "## " in coverage_path.read_text()
    assert summary["scheme_count"] == 2
    assert summary["amc_count"] == 2
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_refresh_script.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'scripts.refresh_amfi'`).

- [ ] **Step 3: Implement refresh_amfi.py**

Create `task4_open/backend/scripts/refresh_amfi.py`:

```python
"""One-shot CLI: fetch latest AMFI monthly disclosures, dispatch per-AMC adapters,
emit data/amfi_holdings.json + data/amfi_coverage.md.

Run via `make refresh-amfi`. Not imported by the FastAPI app.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from amfi.schema import AmfiBundle, Scheme
from scripts.amfi_adapters import ADAPTERS, detect_amc_from_filename

logger = logging.getLogger(__name__)

DEFAULT_BUNDLE_PATH = Path(__file__).parent.parent / "data" / "amfi_holdings.json"
DEFAULT_COVERAGE_PATH = Path(__file__).parent.parent / "data" / "amfi_coverage.md"
DEFAULT_CACHE_DIR = Path(__file__).parent / "cache"


def discover_and_fetch(cache_dir: Path) -> Path:
    """Discover the latest disclosure URL on amfiindia.com, download per-AMC files
    into cache_dir, return that directory.

    Real implementation TBD by maintainer; stub for tests via monkeypatch.
    """
    raise NotImplementedError(
        "Run `make refresh-amfi` interactively the first time and paste the AMFI "
        "disclosure ZIP URL. The auto-discovery scraper is intentionally minimal "
        "for v1 — the maintainer downloads the ZIP manually and points this script "
        "at the unpacked directory via cache_dir.")


def run(bundle_path: Path = DEFAULT_BUNDLE_PATH,
        coverage_path: Path = DEFAULT_COVERAGE_PATH,
        cache_dir: Path = DEFAULT_CACHE_DIR) -> dict:
    """Discover → fetch → dispatch → emit bundle + coverage. Returns a summary dict."""
    files_dir = discover_and_fetch(cache_dir)
    schemes: list[Scheme] = []
    parsed_amcs: set[str] = set()
    skipped: list[tuple[str, str]] = []

    for f in sorted(files_dir.iterdir()):
        if not f.is_file():
            continue
        amc = detect_amc_from_filename(f.name)
        if amc is None:
            skipped.append((f.name, "no AMC mapping"))
            continue
        adapter = ADAPTERS.get(amc)
        if adapter is None:
            skipped.append((f.name, f"no adapter for {amc}"))
            continue
        try:
            ams = adapter(f)
        except Exception as e:
            logger.exception("[refresh] %s adapter failed on %s", amc, f.name)
            skipped.append((f.name, f"{amc} adapter exception: {e}"))
            continue
        if ams:
            schemes.extend(ams)
            parsed_amcs.add(amc)
        else:
            skipped.append((f.name, f"{amc} adapter returned 0 schemes (placeholder?)"))

    # Dedup by ISIN (last write wins)
    by_isin: dict[str, Scheme] = {}
    no_isin: list[Scheme] = []
    for s in schemes:
        if s.isin:
            by_isin[s.isin] = s
        else:
            no_isin.append(s)
    final_schemes = sorted(list(by_isin.values()) + no_isin, key=lambda s: (s.amc, s.scheme_name))

    bundle = AmfiBundle(
        version=1,
        as_of_month=date.today().strftime("%Y-%m"),
        fetched_at=datetime.now(timezone.utc),
        schemes=final_schemes,
    )
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(bundle.model_dump_json(indent=2))

    coverage_lines = [
        f"# AMFI bundle coverage",
        f"",
        f"**As of:** {bundle.as_of_month}",
        f"**Generated:** {bundle.fetched_at.isoformat()}",
        f"**Scheme count:** {len(final_schemes)}",
        f"**AMC count parsed:** {len(parsed_amcs)}",
        f"",
        f"## AMCs parsed",
        f"",
        *(f"- {a}" for a in sorted(parsed_amcs)),
        f"",
        f"## Files skipped",
        f"",
        *(f"- `{fname}` — {reason}" for fname, reason in skipped),
    ]
    coverage_path.write_text("\n".join(coverage_lines))

    summary = {
        "scheme_count": len(final_schemes),
        "amc_count": len(parsed_amcs),
        "skipped_count": len(skipped),
    }
    print(f"refresh_amfi: {summary}")
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sys.exit(0 if run() else 1)
```

- [ ] **Step 4: Add Makefile target**

Append to `task4_open/Makefile`:

```makefile

refresh-amfi:
	cd backend && python -m scripts.refresh_amfi
```

- [ ] **Step 5: Run integration test**

Run: `python -m pytest tests/test_refresh_script.py -v`
Expected: 1 passed.

- [ ] **Step 6: Run full backend suite**

Run: `python -m pytest tests/ -q`
Expected: 100 baseline + 1 refresh = 101 passed.

- [ ] **Step 7: Commit (commit 3)**

```bash
git add task4_open/backend/scripts/__init__.py \
        task4_open/backend/scripts/amfi_adapters/__init__.py \
        task4_open/backend/scripts/amfi_adapters/*.py \
        task4_open/backend/scripts/refresh_amfi.py \
        task4_open/backend/tests/test_amfi_adapters/__init__.py \
        task4_open/backend/tests/test_amfi_adapters/test_hdfc.py \
        task4_open/backend/tests/test_amfi_adapters/test_icici_pru.py \
        task4_open/backend/tests/fixtures/amfi/hdfc_sample.xlsx \
        task4_open/backend/tests/fixtures/amfi/icici_pru_sample.xlsx \
        task4_open/backend/tests/test_refresh_script.py \
        task4_open/Makefile
git commit -m "task4c: refresh_amfi script + 2 real adapters (HDFC, ICICI Pru) + 18 placeholder adapters"
```

---

### Task 12: Frontend types + API client + store

**Files:**
- Modify: `task4_open/frontend/lib/api.ts`
- Modify: `task4_open/frontend/lib/store.ts`

- [ ] **Step 1: Add types to api.ts**

Append to `task4_open/frontend/lib/api.ts` (just before `export class ApiError`):

```typescript
export interface FundHolding {
  name: string
  isin: string | null
  weight_pct: number
  value_inr: number
  kind: string
}

export interface AmfiScheme {
  scheme_name: string
  isin: string | null
  amc: string
  scheme_aum_inr: number
  as_of_date: string
  holdings: FundHolding[]
  cash_pct: number
}

export interface FundMatch {
  asset_name: string
  asset_isin: string | null
  matched: boolean
  matched_by: "isin" | "name" | "none"
  confidence: number
  scheme: AmfiScheme | null
}

export interface HoldingsResponse {
  matches: FundMatch[]
}

export interface OverlapFund {
  asset_name: string
  scheme_name: string | null
  matched_by: "isin" | "name" | "none"
}

export interface OverlapCell {
  i: number
  j: number
  overlap_pct: number
  shared_count: number
}

export interface SharedStock {
  name: string
  isin: string | null
  weight_a: number
  weight_b: number
  min: number
}

export interface OverlapResponse {
  funds: OverlapFund[]
  matrix: OverlapCell[][]
  shared_stocks_index: Record<string, SharedStock[]>
}
```

- [ ] **Step 2: Add the two fetch functions**

Append at end of `task4_open/frontend/lib/api.ts`:

```typescript
export function fetchHoldingsPerFund(
  holdings: NormalizedHoldings,
): Promise<HoldingsResponse> {
  return _postJson<HoldingsResponse>("/api/holdings/per-fund", { holdings })
}

export function fetchOverlap(
  holdings: NormalizedHoldings,
): Promise<OverlapResponse> {
  return _postJson<OverlapResponse>("/api/holdings/overlap", { holdings })
}
```

- [ ] **Step 3: Extend store.ts**

Replace `task4_open/frontend/lib/store.ts` interior to add the new fields. Specifically, change:

```typescript
import type { MarketSnapshot, ParseAndComputeResponse, RebalanceResult } from "./api"
```
to:
```typescript
import type {
  HoldingsResponse, MarketSnapshot, OverlapResponse,
  ParseAndComputeResponse, RebalanceResult,
} from "./api"
```

Add to the `PortfolioState` interface (next to the other field declarations):
```typescript
  holdingsData: HoldingsResponse | null
  overlapData: OverlapResponse | null
  setHoldingsData: (h: HoldingsResponse | null) => void
  setOverlapData: (o: OverlapResponse | null) => void
```

Add to the `create<PortfolioState>()(persist((set) => ({...}), …))` initialiser (next to the other defaults):
```typescript
      holdingsData: null,
      overlapData: null,
      setHoldingsData: (h) => set({ holdingsData: h }),
      setOverlapData: (o) => set({ overlapData: o }),
```

Add to `clear()`'s `set({ … })` block:
```typescript
          holdingsData: null,
          overlapData: null,
```

`partialize` stays unchanged — `holdingsData`/`overlapData` are session-only (reproducible from holdings).

- [ ] **Step 4: Type-check**

Run: `cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/frontend && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 5: Do NOT commit yet** (held until Task 15).

---

### Task 13: MatchBadge + HoldingExpandedRow components

**Files:**
- Create: `task4_open/frontend/components/MatchBadge.tsx`
- Create: `task4_open/frontend/components/HoldingExpandedRow.tsx`
- Create: `task4_open/frontend/__tests__/MatchBadge.test.tsx`

- [ ] **Step 1: Write MatchBadge test**

Create `task4_open/frontend/__tests__/MatchBadge.test.tsx`:

```typescript
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { MatchBadge } from "@/components/MatchBadge"

describe("MatchBadge", () => {
  test("renders label for each match type", () => {
    const { rerender } = render(<MatchBadge matchedBy="isin" />)
    expect(screen.getByText("ISIN")).toBeInTheDocument()
    rerender(<MatchBadge matchedBy="name" />)
    expect(screen.getByText("name")).toBeInTheDocument()
    rerender(<MatchBadge matchedBy="none" />)
    expect(screen.getByText("none")).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/frontend && npx vitest run __tests__/MatchBadge.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement MatchBadge.tsx**

Create `task4_open/frontend/components/MatchBadge.tsx`:

```typescript
type Match = "isin" | "name" | "none"

const STYLES: Record<Match, string> = {
  isin: "border-brass text-brass-bright",
  name: "border-brass/50 text-brass",
  none: "border-oxblood text-oxblood",
}

const LABEL: Record<Match, string> = {
  isin: "ISIN",
  name: "name",
  none: "none",
}

export function MatchBadge({ matchedBy }: { matchedBy: Match }) {
  return (
    <span
      className={`inline-block border px-1.5 py-0.5 font-mono text-[0.55rem] uppercase tracking-[0.18em] ${STYLES[matchedBy]}`}
    >
      {LABEL[matchedBy]}
    </span>
  )
}
```

- [ ] **Step 4: Verify MatchBadge test passes**

Run: `npx vitest run __tests__/MatchBadge.test.tsx`
Expected: 1 passed.

- [ ] **Step 5: Implement HoldingExpandedRow.tsx**

Create `task4_open/frontend/components/HoldingExpandedRow.tsx`:

```typescript
"use client"
import { useState } from "react"
import type { AmfiScheme } from "@/lib/api"
import { formatINR } from "@/lib/format"

interface Props {
  scheme: AmfiScheme
}

export function HoldingExpandedRow({ scheme }: Props) {
  const [showAll, setShowAll] = useState(false)
  const sorted = [...scheme.holdings].sort((a, b) => b.weight_pct - a.weight_pct)
  const visible = showAll ? sorted : sorted.slice(0, 10)
  const remaining = sorted.length - visible.length

  return (
    <div className="border-l-2 border-brass/40 bg-rule-soft/20 px-5 py-3">
      <div className="mb-2 flex items-baseline justify-between">
        <span className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
          Top holdings (snapshot {scheme.as_of_date})
        </span>
        <span className="font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep">
          AMC: {scheme.amc}
        </span>
      </div>
      <table className="w-full">
        <tbody>
          {visible.map((h) => (
            <tr key={h.isin || h.name} className="border-b border-rule/30">
              <td className="py-1 font-serif text-sm text-fg">{h.name}</td>
              <td className="py-1 text-right font-mono text-xs tabular-nums text-fg">
                {h.weight_pct.toFixed(2)}%
              </td>
              <td className="py-1 text-right font-mono text-xs tabular-nums text-fg-soft">
                ₹{formatINR(h.value_inr)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {remaining > 0 && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-2 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass"
        >
          show all {sorted.length}
        </button>
      )}
      <div className="mt-2 font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
        Cash &amp; equivalents: {scheme.cash_pct.toFixed(2)}%
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Type-check**

Run: `npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 7: Do NOT commit yet** (held until Task 15).

---

### Task 14: HoldingsTable component + tests

**Files:**
- Create: `task4_open/frontend/components/HoldingsTable.tsx`
- Create: `task4_open/frontend/__tests__/HoldingsTable.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `task4_open/frontend/__tests__/HoldingsTable.test.tsx`:

```typescript
import { describe, expect, test } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { HoldingsTable } from "@/components/HoldingsTable"

const sampleAssets = [
  {
    name: "Parag Parikh Flexi Cap Fund", asset_type: "mutual_fund" as const,
    isin: "INF879O01027", amc: "PPFAS", category: "Equity" as const, sub_category: "Flexi Cap",
    folio: null, units: 100, invested_value_inr: 100000, current_value_inr: 145000,
    xirr_pct: 14.32, pnl_inr: 45000, pnl_pct: 45.0,
  },
  {
    name: "ICICI Pru Gilt Fund", asset_type: "mutual_fund" as const,
    isin: "INF109K01ZF6", amc: "ICICI Pru", category: "Debt" as const, sub_category: "Gilt",
    folio: null, units: 50, invested_value_inr: 50000, current_value_inr: 52000,
    xirr_pct: 4.10, pnl_inr: 2000, pnl_pct: 4.0,
  },
]

const sampleMatches = [
  {
    asset_name: "Parag Parikh Flexi Cap Fund", asset_isin: "INF879O01027",
    matched: true, matched_by: "isin" as const, confidence: 1.0,
    scheme: {
      scheme_name: "Parag Parikh Flexi Cap Fund - Direct Growth",
      isin: "INF879O01027", amc: "PPFAS", scheme_aum_inr: 8.7e10,
      as_of_date: "2026-04-30", cash_pct: 4.2,
      holdings: [{name: "HDFC Bank", isin: "INE040A01034", weight_pct: 8.42, value_inr: 7.3e9, kind: "equity"}],
    },
  },
  {
    asset_name: "ICICI Pru Gilt Fund", asset_isin: "INF109K01ZF6",
    matched: false, matched_by: "none" as const, confidence: 0.0, scheme: null,
  },
]

describe("HoldingsTable", () => {
  test("renders one row per fund", () => {
    render(<HoldingsTable assets={sampleAssets} matches={sampleMatches} />)
    expect(screen.getByText("Parag Parikh Flexi Cap Fund")).toBeInTheDocument()
    expect(screen.getByText("ICICI Pru Gilt Fund")).toBeInTheDocument()
  })

  test("clicking a matched row reveals the expanded panel", () => {
    render(<HoldingsTable assets={sampleAssets} matches={sampleMatches} />)
    fireEvent.click(screen.getByText("Parag Parikh Flexi Cap Fund"))
    expect(screen.getByText(/Top holdings/i)).toBeInTheDocument()
    expect(screen.getByText("HDFC Bank")).toBeInTheDocument()
  })

  test("clicking the Value header sorts descending", () => {
    render(<HoldingsTable assets={sampleAssets} matches={sampleMatches} />)
    const valueHeader = screen.getByText(/Value/i)
    fireEvent.click(valueHeader)
    const rows = document.querySelectorAll("tbody tr.fund-row")
    // first row is the higher-value fund (PPFAS at ₹145000)
    expect(rows[0].textContent).toContain("Parag Parikh Flexi Cap")
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `npx vitest run __tests__/HoldingsTable.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement HoldingsTable.tsx**

Create `task4_open/frontend/components/HoldingsTable.tsx`:

```typescript
"use client"
import { Fragment, useMemo, useState } from "react"
import type { Asset, FundMatch } from "@/lib/api"
import { formatINR } from "@/lib/format"
import { MatchBadge } from "./MatchBadge"
import { HoldingExpandedRow } from "./HoldingExpandedRow"

interface Props {
  assets: Asset[]
  matches: FundMatch[]
}

type SortKey = "value" | "pct" | "return" | "match" | null

export function HoldingsTable({ assets, matches }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>(null)

  const totalValue = assets.reduce((s, a) => s + a.current_value_inr, 0) || 1
  const matchByName = useMemo(
    () => new Map(matches.map((m) => [m.asset_name, m])),
    [matches],
  )

  const rows = useMemo(() => {
    const out = assets.map((a) => ({
      asset: a,
      pctOfPortfolio: (a.current_value_inr / totalValue) * 100,
      returnPct: a.xirr_pct ?? a.pnl_pct,
      match: matchByName.get(a.name),
    }))
    if (sortKey === "value") out.sort((a, b) => b.asset.current_value_inr - a.asset.current_value_inr)
    else if (sortKey === "pct") out.sort((a, b) => b.pctOfPortfolio - a.pctOfPortfolio)
    else if (sortKey === "return") out.sort((a, b) => (b.returnPct ?? -Infinity) - (a.returnPct ?? -Infinity))
    else if (sortKey === "match") out.sort((a, b) => {
      const order: Record<string, number> = {isin: 0, name: 1, none: 2}
      return (order[a.match?.matched_by || "none"] ?? 3) - (order[b.match?.matched_by || "none"] ?? 3)
    })
    return out
  }, [assets, matchByName, sortKey, totalValue])

  return (
    <div className="border border-rule bg-rule-soft/30">
      <table className="w-full">
        <thead>
          <tr className="border-b border-rule">
            <th className="px-4 py-2 text-left font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">Fund</th>
            <th className="px-4 py-2 text-left font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">Cat</th>
            <th onClick={() => setSortKey("value")} className="cursor-pointer px-4 py-2 text-right font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">Value</th>
            <th onClick={() => setSortKey("pct")} className="cursor-pointer px-4 py-2 text-right font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">%</th>
            <th onClick={() => setSortKey("return")} className="cursor-pointer px-4 py-2 text-right font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">Return</th>
            <th onClick={() => setSortKey("match")} className="cursor-pointer px-4 py-2 text-center font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">Match</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({asset, pctOfPortfolio, returnPct, match}) => {
            const isOpen = expanded === asset.name
            const canExpand = match?.matched && match.scheme
            return (
              <Fragment key={asset.name}>
                <tr
                  className={`fund-row border-b border-rule/40 ${canExpand ? "cursor-pointer hover:bg-brass/5" : "opacity-70"}`}
                  onClick={() => canExpand && setExpanded(isOpen ? null : asset.name)}
                >
                  <td className="px-4 py-2 font-serif text-sm text-fg">
                    <span className="mr-2 font-mono text-xs text-muted-deep">{canExpand ? (isOpen ? "▼" : "▶") : " "}</span>
                    {asset.name}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs uppercase tracking-[0.18em] text-muted-deep">
                    {asset.category || "—"}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-sm tabular-nums text-fg">
                    ₹{formatINR(asset.current_value_inr)}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-xs tabular-nums text-fg-soft">
                    {pctOfPortfolio.toFixed(1)}%
                  </td>
                  <td className={`px-4 py-2 text-right font-mono text-xs tabular-nums ${returnPct >= 0 ? "text-brass-bright" : "text-oxblood"}`}>
                    {returnPct >= 0 ? "+" : ""}{returnPct.toFixed(2)}%
                  </td>
                  <td className="px-4 py-2 text-center">
                    <MatchBadge matchedBy={match?.matched_by || "none"} />
                  </td>
                </tr>
                {isOpen && match?.scheme && (
                  <tr>
                    <td colSpan={6} className="p-0">
                      <HoldingExpandedRow scheme={match.scheme} />
                    </td>
                  </tr>
                )}
              </Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 4: Run HoldingsTable test**

Run: `npx vitest run __tests__/HoldingsTable.test.tsx`
Expected: 3 passed.

- [ ] **Step 5: Run all frontend tests for regression check**

Run: `npx vitest run`
Expected: 34 baseline + 1 MatchBadge + 3 HoldingsTable = 38 passed.

- [ ] **Step 6: Do NOT commit yet** (held until Task 15).

---

### Task 15: COMMIT 4 — frontend store/api + table components

**Files:** none new; consolidate Tasks 12–14 into one commit.

- [ ] **Step 1: Stage + commit**

```bash
git add task4_open/frontend/lib/api.ts \
        task4_open/frontend/lib/store.ts \
        task4_open/frontend/components/MatchBadge.tsx \
        task4_open/frontend/components/HoldingExpandedRow.tsx \
        task4_open/frontend/components/HoldingsTable.tsx \
        task4_open/frontend/__tests__/MatchBadge.test.tsx \
        task4_open/frontend/__tests__/HoldingsTable.test.tsx
git commit -m "task4c: frontend HoldingsTable + ExpandedRow + MatchBadge + types/store"
```

---

### Task 16: OverlapHeatmap component + test

**Files:**
- Create: `task4_open/frontend/components/OverlapHeatmap.tsx`
- Create: `task4_open/frontend/__tests__/OverlapHeatmap.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `task4_open/frontend/__tests__/OverlapHeatmap.test.tsx`:

```typescript
import { describe, expect, test, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { OverlapHeatmap } from "@/components/OverlapHeatmap"

const sample = {
  funds: [
    { asset_name: "PPFAS Flexi Cap", scheme_name: "Parag Parikh Flexi Cap Fund", matched_by: "isin" as const },
    { asset_name: "HDFC Flexi Cap", scheme_name: "HDFC Flexi Cap Fund", matched_by: "isin" as const },
    { asset_name: "Quant Active", scheme_name: "Quant Active Fund", matched_by: "isin" as const },
  ],
  matrix: [
    [
      { i: 0, j: 0, overlap_pct: 95.8, shared_count: 2 },
      { i: 0, j: 1, overlap_pct: 25.5, shared_count: 1 },
      { i: 0, j: 2, overlap_pct: 12.3, shared_count: 1 },
    ],
    [
      { i: 1, j: 0, overlap_pct: 25.5, shared_count: 1 },
      { i: 1, j: 1, overlap_pct: 96.9, shared_count: 2 },
      { i: 1, j: 2, overlap_pct: 8.0, shared_count: 1 },
    ],
    [
      { i: 2, j: 0, overlap_pct: 12.3, shared_count: 1 },
      { i: 2, j: 1, overlap_pct: 8.0, shared_count: 1 },
      { i: 2, j: 2, overlap_pct: 97.9, shared_count: 2 },
    ],
  ],
  shared_stocks_index: {},
}

describe("OverlapHeatmap", () => {
  test("renders one cell per upper-triangle pair", () => {
    render(<OverlapHeatmap data={sample} onSelect={() => {}} />)
    // Upper triangle for N=3 is 3 cells (excluding diagonal): (0,1), (0,2), (1,2)
    const cells = document.querySelectorAll("[data-cell-pair]")
    expect(cells.length).toBe(3)
  })

  test("clicking a cell fires onSelect with i, j", () => {
    const onSelect = vi.fn()
    render(<OverlapHeatmap data={sample} onSelect={onSelect} />)
    const cell = document.querySelector('[data-cell-pair="0_1"]')
    fireEvent.click(cell!)
    expect(onSelect).toHaveBeenCalledWith(0, 1)
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `npx vitest run __tests__/OverlapHeatmap.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement OverlapHeatmap.tsx**

Create `task4_open/frontend/components/OverlapHeatmap.tsx`:

```typescript
"use client"
import type { OverlapResponse } from "@/lib/api"

interface Props {
  data: OverlapResponse
  onSelect: (i: number, j: number) => void
  selected?: { i: number; j: number } | null
}

function shadeFor(pct: number): string {
  // 0% → barely visible; 100% → full brass
  const opacity = Math.max(0.05, Math.min(1, pct / 100))
  return `rgba(176, 141, 87, ${opacity.toFixed(3)})`
}

export function OverlapHeatmap({ data, onSelect, selected }: Props) {
  const n = data.funds.length
  if (n < 2) {
    return (
      <div className="border border-rule bg-rule-soft/30 px-5 py-8 text-center font-mono text-xs text-muted-deep">
        Need at least 2 matched funds to compute overlap.
      </div>
    )
  }
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        Fund overlap
      </div>
      <div
        className="grid gap-1"
        style={{ gridTemplateColumns: `8rem repeat(${n}, minmax(2.5rem, 1fr))` }}
      >
        <div></div>
        {data.funds.map((f, j) => (
          <div key={`col-${j}`} className="overflow-hidden text-ellipsis whitespace-nowrap font-mono text-[0.6rem] uppercase tracking-[0.18em] text-muted-deep">
            {f.asset_name}
          </div>
        ))}
        {data.funds.map((rowFund, i) => (
          <div key={`row-${i}`} className="contents">
            <div className="overflow-hidden text-ellipsis whitespace-nowrap font-mono text-[0.65rem] uppercase tracking-[0.18em] text-muted-deep">
              {rowFund.asset_name}
            </div>
            {data.funds.map((_, j) => {
              const cell = data.matrix[i][j]
              const isDiag = i === j
              const isUpper = j > i
              const isSel = selected && selected.i === Math.min(i, j) && selected.j === Math.max(i, j)
              if (!isUpper) {
                return (
                  <div key={`c-${i}-${j}`} className="h-8" aria-hidden="true">
                    {isDiag && (
                      <div className="h-full w-full bg-rule/30 text-center text-[0.55rem] leading-8 text-muted-deep">·</div>
                    )}
                  </div>
                )
              }
              return (
                <button
                  key={`c-${i}-${j}`}
                  data-cell-pair={`${i}_${j}`}
                  onClick={() => onSelect(i, j)}
                  className={`h-8 transition-opacity hover:ring-1 hover:ring-brass-bright ${isSel ? "ring-2 ring-brass-bright" : ""}`}
                  style={{ backgroundColor: shadeFor(cell.overlap_pct) }}
                  title={`${rowFund.asset_name} ↔ ${data.funds[j].asset_name}: ${cell.overlap_pct.toFixed(1)}%`}
                >
                  <span className="font-mono text-[0.6rem] tabular-nums text-fg">
                    {cell.overlap_pct >= 5 ? cell.overlap_pct.toFixed(0) : ""}
                  </span>
                </button>
              )
            })}
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-3 font-mono text-[0.6rem] uppercase tracking-[0.18em] text-muted-deep">
        <span>Match: <span style={{ background: shadeFor(5) }} className="ml-1 inline-block h-3 w-3 align-middle"></span> &lt;10%</span>
        <span><span style={{ background: shadeFor(20) }} className="inline-block h-3 w-3 align-middle"></span> 10-30%</span>
        <span><span style={{ background: shadeFor(50) }} className="inline-block h-3 w-3 align-middle"></span> 30%+</span>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run heatmap test**

Run: `npx vitest run __tests__/OverlapHeatmap.test.tsx`
Expected: 2 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 18).

---

### Task 17: OverlapDrilldown component + test

**Files:**
- Create: `task4_open/frontend/components/OverlapDrilldown.tsx`
- Create: `task4_open/frontend/__tests__/OverlapDrilldown.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `task4_open/frontend/__tests__/OverlapDrilldown.test.tsx`:

```typescript
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { OverlapDrilldown } from "@/components/OverlapDrilldown"

const sampleShared = [
  { name: "HDFC Bank", isin: "INE040A01034", weight_a: 8.42, weight_b: 5.10, min: 5.10 },
  { name: "Reliance Industries", isin: "INE002A01018", weight_a: 6.0, weight_b: 4.2, min: 4.2 },
]

describe("OverlapDrilldown", () => {
  test("empty state when no pair selected", () => {
    render(<OverlapDrilldown selected={null} />)
    expect(screen.getByText(/click a cell to see shared stocks/i)).toBeInTheDocument()
  })

  test("populated state shows shared stocks sorted by min weight", () => {
    render(<OverlapDrilldown selected={{ fundA: "Fund A", fundB: "Fund B", shared: sampleShared }} />)
    const rows = document.querySelectorAll(".shared-stock-row")
    expect(rows[0].textContent).toContain("HDFC Bank")
    expect(rows[1].textContent).toContain("Reliance Industries")
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `npx vitest run __tests__/OverlapDrilldown.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement OverlapDrilldown.tsx**

Create `task4_open/frontend/components/OverlapDrilldown.tsx`:

```typescript
import type { SharedStock } from "@/lib/api"

interface Props {
  selected: { fundA: string; fundB: string; shared: SharedStock[] } | null
}

export function OverlapDrilldown({ selected }: Props) {
  if (selected === null) {
    return (
      <div className="border border-rule bg-rule-soft/20 px-5 py-8 text-center font-mono text-xs uppercase tracking-[0.18em] text-muted-deep">
        Click a cell to see shared stocks
      </div>
    )
  }
  const sorted = [...selected.shared].sort((a, b) => b.min - a.min)
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-2 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        Shared stocks
      </div>
      <div className="mb-3 font-serif text-sm text-fg">
        {selected.fundA} ↔ {selected.fundB}
      </div>
      {sorted.length === 0 ? (
        <div className="font-mono text-xs text-muted-deep">No shared stocks.</div>
      ) : (
        <ul className="divide-y divide-rule/40">
          {sorted.map((s) => (
            <li key={s.isin || s.name} className="shared-stock-row py-2">
              <div className="font-serif text-sm text-fg">{s.name}</div>
              <div className="mt-0.5 flex gap-4 font-mono text-[0.65rem] tabular-nums text-fg-soft">
                <span>{selected.fundA}: {s.weight_a.toFixed(2)}%</span>
                <span>{selected.fundB}: {s.weight_b.toFixed(2)}%</span>
                <span className="text-brass-bright">min {s.min.toFixed(2)}%</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Run drilldown test**

Run: `npx vitest run __tests__/OverlapDrilldown.test.tsx`
Expected: 2 passed.

- [ ] **Step 5: Do NOT commit yet** (held until Task 18).

---

### Task 18: Holdings page assembly + COMMIT 5

**Files:**
- Modify: `task4_open/frontend/app/dashboard/holdings/page.tsx`

- [ ] **Step 1: Replace the stub**

Overwrite `task4_open/frontend/app/dashboard/holdings/page.tsx`:

```typescript
"use client"
import { useCallback, useEffect, useMemo, useState } from "react"
import { toast } from "sonner"
import {
  ApiError, fetchHoldingsPerFund, fetchOverlap,
} from "@/lib/api"
import { usePortfolio } from "@/lib/store"
import { HoldingsTable } from "@/components/HoldingsTable"
import { OverlapHeatmap } from "@/components/OverlapHeatmap"
import { OverlapDrilldown } from "@/components/OverlapDrilldown"

export default function HoldingsPage() {
  const data = usePortfolio((s) => s.data)
  const holdings = usePortfolio((s) => s.holdingsData)
  const overlap = usePortfolio((s) => s.overlapData)
  const setHoldings = usePortfolio((s) => s.setHoldingsData)
  const setOverlap = usePortfolio((s) => s.setOverlapData)
  const [loading, setLoading] = useState(false)
  const [selectedPair, setSelectedPair] = useState<{ i: number; j: number } | null>(null)

  const load = useCallback(async () => {
    if (!data) return
    setLoading(true)
    try {
      const [h, o] = await Promise.all([
        fetchHoldingsPerFund(data.normalized),
        fetchOverlap(data.normalized),
      ])
      setHoldings(h)
      setOverlap(o)
    } catch (e) {
      const msg = e instanceof ApiError
        ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
        : (e as Error).message
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }, [data, setHoldings, setOverlap])

  useEffect(() => {
    if (data && (!holdings || !overlap)) {
      void load()
    }
  }, [data, holdings, overlap, load])

  const drilldown = useMemo(() => {
    if (!overlap || !selectedPair) return null
    const i = Math.min(selectedPair.i, selectedPair.j)
    const j = Math.max(selectedPair.i, selectedPair.j)
    const key = `${i}_${j}`
    return {
      fundA: overlap.funds[i].asset_name,
      fundB: overlap.funds[j].asset_name,
      shared: overlap.shared_stocks_index[key] || [],
    }
  }, [overlap, selectedPair])

  if (!data) return null

  const unmatched = holdings?.matches.filter((m) => !m.matched) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-xl text-fg">Your funds</h2>
        <button
          onClick={() => void load()}
          disabled={loading}
          className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass disabled:opacity-50"
        >
          {loading ? "Loading…" : "↻ Reload data"}
        </button>
      </div>

      {holdings ? (
        <HoldingsTable assets={data.normalized.assets} matches={holdings.matches} />
      ) : (
        <div className="flex min-h-[20vh] items-center justify-center">
          <span className="font-mono text-sm text-muted-deep">Loading per-fund data…</span>
        </div>
      )}

      <hr className="border-rule" />

      <h2 className="font-serif text-xl text-fg">Fund overlap</h2>
      {overlap && overlap.funds.length >= 2 ? (
        <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
          <OverlapHeatmap data={overlap} onSelect={(i, j) => setSelectedPair({ i, j })} selected={selectedPair} />
          <OverlapDrilldown selected={drilldown} />
        </div>
      ) : overlap ? (
        <div className="border border-rule bg-rule-soft/30 px-5 py-8 text-center font-mono text-xs text-muted-deep">
          Need at least 2 matched funds to compute overlap.
        </div>
      ) : (
        <div className="flex min-h-[20vh] items-center justify-center">
          <span className="font-mono text-sm text-muted-deep">Loading overlap…</span>
        </div>
      )}

      {unmatched.length > 0 && (
        <details className="border border-rule bg-rule-soft/20 p-4">
          <summary className="cursor-pointer font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">
            {unmatched.length} fund{unmatched.length === 1 ? "" : "s"} excluded from matrix (no AMFI match)
          </summary>
          <ul className="mt-2 space-y-1 font-serif text-sm text-fg-soft">
            {unmatched.map((m) => <li key={m.asset_name}>• {m.asset_name}</li>)}
          </ul>
        </details>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Type-check**

Run: `npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 3: Run all frontend tests**

Run: `npx vitest run`
Expected: 38 baseline + 2 OverlapHeatmap + 2 OverlapDrilldown = 42 passed.

- [ ] **Step 4: Manual smoke (optional, requires backend running)**

```bash
# In one terminal:
. /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/.venv/bin/activate
cd task4_open/backend && uvicorn main:app --port 8000 --reload
# In another:
cd task4_open/frontend && npm run dev
```
Visit http://localhost:3000 → upload a sample → click Holdings tab → table renders, expand a row, heatmap renders below, click a cell → drilldown populates.

- [ ] **Step 5: Commit (commit 5)**

```bash
git add task4_open/frontend/components/OverlapHeatmap.tsx \
        task4_open/frontend/components/OverlapDrilldown.tsx \
        task4_open/frontend/app/dashboard/holdings/page.tsx \
        task4_open/frontend/__tests__/OverlapHeatmap.test.tsx \
        task4_open/frontend/__tests__/OverlapDrilldown.test.tsx
git commit -m "task4c: holdings tab — overlap heatmap + drilldown + page assembly"
```

---

### Task 19: Final user gate

**Files:** none.

- [ ] **Step 1: Show the user the branch state**

Run:
```bash
git log main..HEAD --oneline
git status
```
Expected: 6 new commits on top of main (1 spec + 5 implementation), clean working tree.

- [ ] **Step 2: Stop. Do not push. Do not open a PR.**

CLAUDE.md workflow rule: branch → commit → request PR review. Do not merge unilaterally.

Tell the user:

> Task 4c implementation complete on `task4c/holdings-overlap` (5 implementation commits + spec on top of main). Backend 101 tests + frontend 42 tests, all green. The committed AMFI bundle is a 4-scheme seed; running `make refresh-amfi` would normally fetch real data but the discover-and-fetch step is intentionally a stub for v1 (real network discovery deferred). Ready for your review — I haven't pushed and I haven't opened a PR. When you're ready, tell me to `git push -u origin task4c/holdings-overlap` and `gh pr create`.

- [ ] **Step 3: Wait for user instruction**

Do not run `git push` or `gh pr create` until the user confirms.

---

## Self-Review Notes

**Spec coverage:** Every section of the spec maps to a task — schema (T1), bundle (T2), match (T3), overlap (T5), API models (T6), endpoints (T7), refresh script + 2 real adapters + 18 placeholders + Makefile (T8–T11), frontend types/store (T12), MatchBadge + ExpandedRow (T13), HoldingsTable (T14), OverlapHeatmap (T16), OverlapDrilldown (T17), page assembly (T18). The 503 "bundle missing" path is covered by both `test_amfi_bundle.py` (loader) and `test_main.py` (endpoint).

**Type consistency:** `FundMatch` (Pydantic) shape matches `FundMatch` TS interface. `OverlapResponse` matches across `holdings/api.py` and `lib/api.ts`. `IndexedBundle` is consistently used in match.py and exposed via `load_bundle()`. `shared_stocks_index` keying convention `"i_j"` with `i<j` is consistent in spec, overlap.py, page assembly.

**Adapter scope realism:** The plan caps real adapter work at 2 (HDFC, ICICI Pru). The other 18 are placeholder files generated by the bash one-liner in T8 — collectively <2 minutes of work. The committed bundle is a 4-scheme seed, sufficient for the endpoints + UI to demo end-to-end without anyone needing to actually run `make refresh-amfi`.

**Refresh script's `discover_and_fetch` is intentionally `NotImplementedError`.** Auto-discovering AMFI's monthly disclosure URL requires HTML scraping that's brittle and out of scope for v1. The maintainer downloads the ZIP manually and points the script at the unpacked directory. This is documented in the function docstring + the user-gate message. Tests stub `discover_and_fetch` so coverage works without a real fetch.

**Test isolation:** Backend tests that load the bundle monkeypatch `BUNDLE_PATH` to a fixture. The endpoint tests use a single `_live_bundle` fixture pointing at `bundle_tiny.json`. The refresh script test stubs `discover_and_fetch` + `ADAPTERS` + `detect_amc_from_filename` — never hits AMFI.

**Workflow rule:** Final task (T19) is the explicit "do not push, do not PR" stop, matching CLAUDE.md.
