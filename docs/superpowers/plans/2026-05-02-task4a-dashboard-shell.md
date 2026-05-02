# Task 4a — Dashboard Shell + Holdings Parser + Overview Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the FastAPI + Next.js dashboard shell for Task 4 with an LLM-normalized holdings parser (Haiku 4.5, format-agnostic) and a working Overview tab matching mockup image 1's layout, themed with timecell.ai's Ledger palette.

**Architecture:** Two-process app under `task4_open/`. Python FastAPI backend exposes `POST /api/parse-and-compute` (extracts → Haiku-normalizes → computes metrics) and `GET /api/health`. Next.js frontend uploads files, stores results in Zustand, renders 4 tabs (Overview live; Holdings/Market/Rebalance stubbed for 4b/4c). Stateless — no DB, no auth, single-user demo. The Next.js dev server proxies `/api/*` to FastAPI, eliminating CORS.

**Tech Stack:** FastAPI 0.115+, Pydantic v2, Anthropic SDK, openpyxl, BeautifulSoup4, pdfplumber, scipy (XIRR fallback only), Pillow. Next.js (latest, App Router, TypeScript strict), Tailwind CSS, shadcn/ui, Recharts, Lucide React, Zustand, sonner (toasts). Vitest + React Testing Library + Playwright for frontend tests; pytest for backend.

**Branch:** `task4a/dashboard-shell` (already created off main, spec already committed at `2da4b48`).

**Two commits land on this branch:**
1. Sample redaction + `.gitignore` updates + complete backend (parser + metrics + tests + prompts + samples + requirements)
2. Complete frontend + `Makefile` + per-task `README.md` + root `README.md` link

Final task ends with explicit user gate per CLAUDE.md workflow rule — do not push or open PR.

---

## File Structure

### Backend — `task4_open/backend/`

```
backend/
├── main.py                   # FastAPI app + routes + error handlers
├── parser/
│   ├── __init__.py
│   ├── extract.py            # File → ExtractedContent (text, tables, image bytes)
│   ├── normalize.py          # ExtractedContent + Pydantic schema → Haiku → NormalizedHoldings
│   └── schema.py             # Pydantic v2: Asset, PortfolioSummary, NormalizedHoldings
├── metrics/
│   ├── __init__.py
│   └── compute.py            # KPIs, allocation, xirr_by_fund, category_performance — pure functions
├── prompts/
│   └── normalize.txt         # Externalized normalizer prompt (string.Template)
├── tests/
│   ├── __init__.py
│   ├── test_schema.py
│   ├── test_extract.py       # Mocked file readers, real sample files
│   ├── test_normalize.py     # Mocked Anthropic SDK
│   ├── test_metrics.py       # Pure function tests, hand-built fixtures
│   └── test_main.py          # FastAPI TestClient, mocked normalize
├── samples/                  # Redacted versions of the 3 holdings files
│   ├── sample_groww.xlsx
│   ├── sample_camsonline.xls
│   └── sample_zerodha.xlsx
├── requirements.txt
└── pyproject.toml            # ruff config + pytest config
```

### Frontend — `task4_open/frontend/`

```
frontend/
├── app/
│   ├── layout.tsx            # Theme provider, font imports, sonner Toaster
│   ├── globals.css           # Tailwind directives + Ledger CSS variables + body backdrop
│   ├── page.tsx              # "/" — landing with file upload widget
│   └── dashboard/
│       ├── layout.tsx        # Header (holder name, total) + TabNav
│       ├── page.tsx          # "/dashboard" — Overview tab
│       ├── holdings/page.tsx # "/dashboard/holdings" — StubTab
│       ├── market/page.tsx   # "/dashboard/market" — StubTab
│       └── rebalance/page.tsx # "/dashboard/rebalance" — StubTab
├── components/
│   ├── KpiCard.tsx
│   ├── CategoryCard.tsx
│   ├── StubTab.tsx
│   ├── AllocationDonut.tsx   # Recharts PieChart
│   ├── XirrBarChart.tsx      # Recharts BarChart (horizontal)
│   ├── FileUpload.tsx        # Dropzone + progress phases
│   └── TabNav.tsx
├── lib/
│   ├── format.ts             # formatINR (Indian grouping)
│   ├── api.ts                # Typed fetch wrapper
│   ├── store.ts              # Zustand portfolio store
│   └── theme.ts              # Color tokens object (mirrors Tailwind)
├── public/
│   └── timecell-logo.png     # Downloaded once from https://timecell.ai/logo.png
├── __tests__/                # Vitest + RTL component tests
│   ├── format.test.ts
│   ├── KpiCard.test.tsx
│   ├── CategoryCard.test.tsx
│   ├── AllocationDonut.test.tsx
│   ├── XirrBarChart.test.tsx
│   └── StubTab.test.tsx
├── e2e/
│   └── upload.spec.ts        # Playwright smoke test
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js            # /api/* rewrite to localhost:8000
├── postcss.config.js
├── vitest.config.ts
├── playwright.config.ts
└── .eslintrc.json
```

### Top-level — `task4_open/`

```
task4_open/
├── README.md                 # Per-task overview, dev workflow, AI usage
├── Makefile                  # `make install`, `make dev`, `make test`
├── backend/                  # (above)
└── frontend/                 # (above)
```

### Repo-level changes

- `.gitignore` — add `task4_open/Holdings_Statement_*.xlsx`, `task4_open/Portfolio_summary_report*.xls`, `task4_open/holdings-EEM619.xlsx`, `task4_open/backend/.venv/`, `task4_open/frontend/node_modules/`, `task4_open/frontend/.next/`, `task4_open/frontend/playwright-report/`, `task4_open/frontend/test-results/`, `~/.cache/timecell-task4/`
- `README.md` (root) — replace `- Task 4 — Open (TBD)` with `- [Task 4 — Portfolio Intelligence Dashboard (4a: Shell + Parser + Overview)](task4_open/README.md)`

---

## Task 1: Confirm Haiku model ID + create backend directory skeleton

**Files:**
- Create: `task4_open/backend/parser/__init__.py`
- Create: `task4_open/backend/metrics/__init__.py`
- Create: `task4_open/backend/tests/__init__.py`
- Create: `task4_open/backend/prompts/.gitkeep`
- Create: `task4_open/backend/samples/.gitkeep`

- [ ] **Step 1: Verify branch state**

```bash
git status
git log --oneline | head -3
```

Expected: on `task4a/dashboard-shell`, top commit is `2da4b48` (the spec).

- [ ] **Step 2: Confirm latest Anthropic Haiku model ID via the `claude-api` skill**

Use the `claude-api` skill (Skill tool, `claude-api`) to confirm the current latest Haiku model ID. The spec uses `claude-haiku-4-5` (per `shared/models.md` cached table), but a newer Haiku (e.g. `claude-haiku-5-0`) may have shipped. **Record the confirmed model ID for Task 9 step 1's `DEFAULT_HAIKU_MODEL` constant.** Using a deprecated model ID will cause every parse to fail at runtime.

- [ ] **Step 3: Create backend directory tree**

```bash
mkdir -p task4_open/backend/{parser,metrics,prompts,samples,tests}
touch task4_open/backend/parser/__init__.py
touch task4_open/backend/metrics/__init__.py
touch task4_open/backend/tests/__init__.py
touch task4_open/backend/prompts/.gitkeep
touch task4_open/backend/samples/.gitkeep
ls -la task4_open/backend/
```

Expected: 5 directories present (parser, metrics, prompts, samples, tests).

---

## Task 2: Redact 3 sample holdings files + move to backend/samples/ + gitignore originals

**Files:**
- Create: `task4_open/backend/samples/sample_groww.xlsx`
- Create: `task4_open/backend/samples/sample_camsonline.xls`
- Create: `task4_open/backend/samples/sample_zerodha.xlsx`
- Modify: `.gitignore`

The 3 files in `task4_open/` contain real PII. Per the spec's resolved decision (redact, don't gitignore) we replace names/PANs/phone/client IDs with synthetic values while keeping all numeric data.

- [ ] **Step 1: Add originals to `.gitignore`**

Open `.gitignore` and append:

```
# Task 4: real holdings statements with PII (redacted copies live in task4_open/backend/samples/)
task4_open/Holdings_Statement_*.xlsx
task4_open/Portfolio_summary_report*.xls
task4_open/holdings-EEM619.xlsx

# Task 4 backend
task4_open/backend/.venv/
task4_open/backend/__pycache__/
task4_open/backend/**/__pycache__/
task4_open/backend/.pytest_cache/
task4_open/backend/.ruff_cache/

# Task 4 frontend
task4_open/frontend/node_modules/
task4_open/frontend/.next/
task4_open/frontend/playwright-report/
task4_open/frontend/test-results/
task4_open/frontend/coverage/
```

- [ ] **Step 2: Verify the originals are now gitignored**

```bash
git status --short | grep -E "(Holdings_Statement|Portfolio_summary|holdings-EEM619)" && echo "BAD: still tracked" || echo "OK: gitignored"
```

Expected: `OK: gitignored`.

- [ ] **Step 3: Redact the Groww xlsx → `sample_groww.xlsx`**

Run inline:

```bash
python <<'PY'
import openpyxl, shutil
src = "task4_open/Holdings_Statement_2026-05-02.xlsx"
dst = "task4_open/backend/samples/sample_groww.xlsx"
shutil.copy(src, dst)
wb = openpyxl.load_workbook(dst)
ws = wb["Holdings"]
# Header personal-details rows (Name=row4 col2, Mobile=row5 col2, PAN=row6 col2)
ws.cell(row=4, column=2, value="Test User A")
ws.cell(row=5, column=2, value="9999999999")
ws.cell(row=6, column=2, value="AAAAA1234A")
wb.save(dst)
print("redacted:", dst)
PY
```

Verify:

```bash
python -c "
import openpyxl
ws = openpyxl.load_workbook('task4_open/backend/samples/sample_groww.xlsx')['Holdings']
for r in range(3, 7):
    print(r, ws.cell(row=r, column=1).value, '|', ws.cell(row=r, column=2).value)
"
```

Expected: row 4 shows `Name | Test User A`, row 5 `Mobile Number | 9999999999`, row 6 `PAN | AAAAA1234A`. Numeric rows untouched.

- [ ] **Step 4: Redact the Camsonline MHTML → `sample_camsonline.xls`**

Run inline:

```bash
python <<'PY'
src = "task4_open/Portfolio_summary_report_withoutFormatting.xls"
dst = "task4_open/backend/samples/sample_camsonline.xls"
with open(src, "r", encoding="utf-8", errors="replace") as f:
    html = f.read()
# Replace name (appears multiple times — all caps with double space)
html = html.replace("BHAVANA  JAGADEESH", "TEST USER B")
# Replace PAN
html = html.replace("BJGPJ8187F", "BBBBB1234B")
with open(dst, "w", encoding="utf-8") as f:
    f.write(html)
print("redacted:", dst)
PY
```

Verify:

```bash
grep -o "TEST USER B\|BHAVANA\|BBBBB1234B\|BJGPJ8187F" task4_open/backend/samples/sample_camsonline.xls | sort | uniq -c
```

Expected: only `TEST USER B` and `BBBBB1234B` appear (each multiple times). Zero matches for `BHAVANA` or `BJGPJ8187F`.

- [ ] **Step 5: Redact the Zerodha xlsx → `sample_zerodha.xlsx`**

Run inline:

```bash
python <<'PY'
import openpyxl, shutil
src = "task4_open/holdings-EEM619.xlsx"
dst = "task4_open/backend/samples/sample_zerodha.xlsx"
shutil.copy(src, dst)
wb = openpyxl.load_workbook(dst)
# Client ID appears in row 7 col 3 of every sheet
for sn in wb.sheetnames:
    ws = wb[sn]
    for row in ws.iter_rows():
        for cell in row:
            if cell.value == "EEM619":
                cell.value = "TEST01"
wb.save(dst)
print("redacted:", dst)
PY
```

Verify:

```bash
python -c "
import openpyxl
wb = openpyxl.load_workbook('task4_open/backend/samples/sample_zerodha.xlsx')
for sn in wb.sheetnames:
    ws = wb[sn]
    for row in ws.iter_rows():
        for cell in row:
            if cell.value in ('EEM619','TEST01'):
                print(sn, cell.coordinate, cell.value)
"
```

Expected: every match is `TEST01`; zero `EEM619` results.

- [ ] **Step 6: List the redacted samples**

```bash
ls -la task4_open/backend/samples/
```

Expected: `sample_groww.xlsx`, `sample_camsonline.xls`, `sample_zerodha.xlsx`, `.gitkeep`.

---

## Task 3: backend/requirements.txt + pyproject.toml + venv install

**Files:**
- Create: `task4_open/backend/requirements.txt`
- Create: `task4_open/backend/pyproject.toml`

- [ ] **Step 1: Write `task4_open/backend/requirements.txt`**

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.9
pydantic>=2.9.0
anthropic>=0.40.0
openpyxl>=3.1.5
beautifulsoup4>=4.12.0
lxml>=5.3.0
pdfplumber>=0.11.0
Pillow>=10.4.0
scipy>=1.13.0
python-dotenv>=1.0.0
httpx>=0.27.0
pytest>=8.3.0
ruff>=0.7.0
```

- [ ] **Step 2: Write `task4_open/backend/pyproject.toml`**

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP"]
ignore = ["E501"]  # line length is for the formatter

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
```

- [ ] **Step 3: Install deps into the existing repo venv**

```bash
source .venv/bin/activate
pip install -r task4_open/backend/requirements.txt
```

Expected: success (some packages already installed from Tasks 2/3 are no-ops). Note any errors.

- [ ] **Step 4: Verify imports work**

```bash
python -c "
import fastapi, uvicorn, pydantic, anthropic, openpyxl, bs4, pdfplumber, PIL, scipy
from dotenv import load_dotenv
print('all imports OK')
print('pydantic version:', pydantic.VERSION)
print('fastapi version:', fastapi.__version__)
"
```

Expected: `all imports OK`, pydantic version `2.x`, fastapi `0.115+`.

---

## Task 4: Pydantic schema + first failing test

**Files:**
- Create: `task4_open/backend/parser/schema.py`
- Create: `task4_open/backend/tests/test_schema.py`

- [ ] **Step 1: Write `task4_open/backend/parser/schema.py`**

```python
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
    source_format: str  # "groww_xlsx" | "camsonline_mhtml" | "zerodha_console" | "unknown"
    summary: PortfolioSummary
    assets: list[Asset]
    parser_warnings: list[str] = Field(default_factory=list)
```

- [ ] **Step 2: Write `task4_open/backend/tests/test_schema.py`**

```python
"""Tests for parser.schema — Pydantic validation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.schema import Asset, NormalizedHoldings, PortfolioSummary


def _valid_asset_dict() -> dict:
    return {
        "name": "Parag Parikh Flexi Cap Fund Direct",
        "asset_type": "mutual_fund",
        "isin": None,
        "amc": "PPFAS",
        "category": "Equity",
        "sub_category": "Flexi Cap",
        "folio": "13959825",
        "units": 8547.228,
        "invested_value_inr": 624968.74,
        "current_value_inr": 763913.63,
        "xirr_pct": 10.22,
        "pnl_inr": 138944.89,
        "pnl_pct": 22.23,
    }


def test_asset_happy_path() -> None:
    asset = Asset.model_validate(_valid_asset_dict())
    assert asset.name == "Parag Parikh Flexi Cap Fund Direct"
    assert asset.category == "Equity"


def test_asset_rejects_invalid_category() -> None:
    bad = _valid_asset_dict() | {"category": "Crypto"}
    try:
        Asset.model_validate(bad)
    except Exception as e:
        assert "category" in str(e), f"category not in error: {e}"
        return
    raise AssertionError("expected validation error, none raised")


def test_normalized_holdings_minimal() -> None:
    payload = {
        "holder_name": "Test User",
        "source_format": "groww_xlsx",
        "summary": {
            "total_invested_inr": 100.0,
            "total_current_inr": 110.0,
            "total_pnl_inr": 10.0,
            "total_pnl_pct": 10.0,
            "asset_count": 1,
        },
        "assets": [_valid_asset_dict()],
    }
    nh = NormalizedHoldings.model_validate(payload)
    assert nh.holder_name == "Test User"
    assert len(nh.assets) == 1
    assert nh.parser_warnings == []


def test_summary_rejects_negative_count() -> None:
    bad = {
        "total_invested_inr": 0.0,
        "total_current_inr": 0.0,
        "total_pnl_inr": 0.0,
        "total_pnl_pct": 0.0,
        "asset_count": -1,
    }
    try:
        PortfolioSummary.model_validate(bad)
    except Exception as e:
        assert "asset_count" in str(e), f"asset_count not in error: {e}"
        return
    raise AssertionError("expected validation error, none raised")
```

- [ ] **Step 3: Run tests, verify they pass**

```bash
cd task4_open/backend && python -m pytest tests/test_schema.py -v && cd ../..
```

Expected: 4 passed.

---

## Task 5: extract.py — xlsx + xls extractors + tests

**Files:**
- Create: `task4_open/backend/parser/extract.py`
- Create: `task4_open/backend/tests/test_extract.py`

- [ ] **Step 1: Create `task4_open/backend/parser/extract.py`**

```python
"""File-format extraction. Returns ExtractedContent for the LLM normalizer."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

ExtractKind = Literal["tables", "text", "image"]


class ExtractError(Exception):
    """Raised when a file cannot be read (corrupt / unsupported)."""


@dataclass
class ExtractedContent:
    """What extract() returns to normalize()."""
    kind: ExtractKind
    # For "tables": list of (sheet_name, list[list[cell-as-str]])
    tables: list[tuple[str, list[list[str]]]] = field(default_factory=list)
    # For "text": full extracted text (HTML / PDF text)
    text: str = ""
    # For "image": raw bytes + media type
    image_bytes: bytes = b""
    image_media_type: str = ""
    # Source format hint passed to the LLM
    format_hint: str = "unknown"


def _cells_to_str(rows: list[list[object]]) -> list[list[str]]:
    """Stringify cells; None → empty string."""
    return [["" if c is None else str(c) for c in r] for r in rows]


def extract_xlsx(path: Path) -> ExtractedContent:
    """openpyxl extractor. For multi-sheet files, prefers a 'Combined' sheet if present."""
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    sheet_names = wb.sheetnames
    # Prefer 'Combined' sheet for Zerodha-style multi-sheet files
    preferred = next((s for s in sheet_names if s.lower() == "combined"), None)
    if preferred:
        sheet_names = [preferred]

    tables = []
    for sn in sheet_names:
        ws = wb[sn]
        rows = list(ws.iter_rows(values_only=True))
        # Drop fully-empty trailing rows
        while rows and all(c is None for c in rows[-1]):
            rows.pop()
        tables.append((sn, _cells_to_str(rows)))

    fmt = "zerodha_console" if "Combined" in wb.sheetnames or "Mutual Funds" in wb.sheetnames else "groww_xlsx"
    return ExtractedContent(kind="tables", tables=tables, format_hint=fmt)


def extract_xls(path: Path) -> ExtractedContent:
    """Handles both real binary .xls and HTML-disguised .xls (Camsonline format)."""
    head = path.read_bytes()[:200]
    if b"<html" in head.lower() or b"<!doctype html" in head.lower():
        # MHTML / HTML report
        text = path.read_text(encoding="utf-8", errors="replace")
        return ExtractedContent(kind="text", text=text, format_hint="camsonline_mhtml")
    # Real binary xls
    try:
        import xlrd
        wb = xlrd.open_workbook(path)
        tables = []
        for sn in wb.sheet_names():
            ws = wb.sheet_by_name(sn)
            rows = [[ws.cell_value(r, c) for c in range(ws.ncols)] for r in range(ws.nrows)]
            tables.append((sn, _cells_to_str(rows)))
        return ExtractedContent(kind="tables", tables=tables, format_hint="binary_xls")
    except Exception as e:
        raise ExtractError(f"could not read .xls file: {e}") from e


def extract(path: Path) -> ExtractedContent:
    """Dispatch on file extension. Raises ExtractError on unsupported / unreadable."""
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return extract_xlsx(path)
    if suffix == ".xls":
        return extract_xls(path)
    if suffix == ".pdf":
        return extract_pdf(path)
    if suffix in (".png", ".jpg", ".jpeg"):
        return extract_image(path)
    raise ExtractError(f"unsupported file extension: {suffix}")


def extract_pdf(path: Path) -> ExtractedContent:
    """pdfplumber: page-by-page text extraction."""
    import pdfplumber
    parts = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                t = page.extract_text() or ""
                parts.append(f"--- page {i} ---\n{t}")
    except Exception as e:
        raise ExtractError(f"could not read PDF: {e}") from e
    return ExtractedContent(kind="text", text="\n\n".join(parts), format_hint="pdf")


def extract_image(path: Path) -> ExtractedContent:
    """Image: return bytes + media type for vision-capable LLM call."""
    suffix = path.suffix.lower()
    media = "image/png" if suffix == ".png" else "image/jpeg"
    return ExtractedContent(
        kind="image",
        image_bytes=path.read_bytes(),
        image_media_type=media,
        format_hint="image",
    )
```

- [ ] **Step 2: Create `task4_open/backend/tests/test_extract.py`**

```python
"""Tests for parser.extract — runs against real sample files; no LLM, no network."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.extract import (
    ExtractError,
    extract,
    extract_image,
    extract_pdf,
    extract_xls,
    extract_xlsx,
)

SAMPLES = Path(__file__).parent.parent / "samples"


def test_extract_xlsx_groww() -> None:
    content = extract_xlsx(SAMPLES / "sample_groww.xlsx")
    assert content.kind == "tables"
    assert content.format_hint == "groww_xlsx"
    assert len(content.tables) >= 1, "expected at least one sheet"
    sheet_name, rows = content.tables[0]
    assert any("Test User A" in str(cell) for row in rows for cell in row), \
        "redacted holder name not found"


def test_extract_xlsx_zerodha_prefers_combined() -> None:
    content = extract_xlsx(SAMPLES / "sample_zerodha.xlsx")
    assert content.kind == "tables"
    assert content.format_hint == "zerodha_console"
    assert len(content.tables) == 1, \
        f"should pick only Combined sheet, got {len(content.tables)}"
    assert content.tables[0][0].lower() == "combined", \
        f"expected Combined sheet, got {content.tables[0][0]}"


def test_extract_xls_camsonline_html() -> None:
    content = extract_xls(SAMPLES / "sample_camsonline.xls")
    assert content.kind == "text"
    assert content.format_hint == "camsonline_mhtml"
    assert "<html" in content.text.lower()
    assert "TEST USER B" in content.text


def test_extract_dispatches_by_extension() -> None:
    content = extract(SAMPLES / "sample_groww.xlsx")
    assert content.kind == "tables"


def test_extract_rejects_unsupported_extension() -> None:
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp = Path(f.name)
    try:
        try:
            extract(tmp)
        except ExtractError as e:
            assert ".docx" in str(e), f"extension missing from error: {e}"
            return
        raise AssertionError("expected ExtractError, none raised")
    finally:
        tmp.unlink()


def test_extract_image_returns_bytes() -> None:
    # Create a tiny 1x1 PNG
    import struct, zlib
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = b"IHDR" + struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", len(ihdr) - 4) + ihdr + struct.pack(">I", zlib.crc32(ihdr))
    idat_data = zlib.compress(b"\x00\xff\xff\xff")
    idat = b"IDAT" + idat_data
    idat_chunk = struct.pack(">I", len(idat) - 4) + idat + struct.pack(">I", zlib.crc32(idat))
    iend_chunk = b"\x00\x00\x00\x00IEND\xaeB`\x82"
    png_bytes = sig + ihdr_chunk + idat_chunk + iend_chunk

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_bytes)
        tmp = Path(f.name)
    try:
        content = extract_image(tmp)
        assert content.kind == "image"
        assert content.image_media_type == "image/png"
        assert content.image_bytes == png_bytes
    finally:
        tmp.unlink()
```

- [ ] **Step 3: Run tests**

```bash
cd task4_open/backend && python -m pytest tests/test_extract.py -v && cd ../..
```

Expected: 6 passed (xlsx_groww, xlsx_zerodha, xls_camsonline, dispatch, unsupported, image).

---

## Task 6: Normalizer prompt + builder + happy-path normalize() with mocked Anthropic

**Files:**
- Create: `task4_open/backend/prompts/normalize.txt`
- Create: `task4_open/backend/parser/normalize.py`
- Create: `task4_open/backend/tests/test_normalize.py`

- [ ] **Step 1: Create `task4_open/backend/prompts/normalize.txt`**

```
You are a financial data extraction system. Convert the following holdings statement into the
canonical JSON schema below. Output ONLY valid JSON — no markdown, no fences, no preamble.

<extracted_content>
$extracted_content
</extracted_content>

<canonical_schema>
$canonical_schema_json
</canonical_schema>

<rules>
- Extract every asset row (mutual fund or stock).
- For asset_type: "mutual_fund" if name contains "Fund"/"Plan"/"Scheme"; "stock" if it looks
  like an NSE/BSE symbol (all-caps, no spaces); "etf" if name contains "ETF"; otherwise "other".
- For category: map to one of "Equity", "Debt", "Hybrid", "Commodities" based on the row's
  category column, sub-category, or scheme name. If unclear, use null.
- For sub_category: pass through the statement's sub-category text (e.g. "Flexi Cap", "Gilt").
- For pnl_inr: if the statement provides P&L, use it; else compute (current_value - invested_value).
- For pnl_pct: if provided, use it; else compute (pnl / invested * 100).
- Do NOT compute XIRR — pass it through if the statement provides one, else null.
- If the source has multiple sheets (e.g. Zerodha's Equity + Mutual Funds + Combined), prefer
  the Combined sheet. If multiple sheets are passed, dedupe by (isin, name) — emit each unique
  asset only once.
- For source_format: classify as "groww_xlsx" if you see Groww-style columns, "camsonline_mhtml"
  if HTML table structure with category-grouped headers, "zerodha_console" if multi-sheet
  Equity/MF/Combined layout, otherwise "unknown".
- For holder_name: extract from the statement header if present.
- For statement_date: extract any "as on" date if present (ISO format YYYY-MM-DD).
- All currency values MUST be in INR as floats (no commas, no rupee symbols).
- If a field is genuinely absent in the source, use null — do NOT guess.
</rules>

<example_minimal_output>
{
  "holder_name": "Test User B",
  "source_format": "camsonline_mhtml",
  "summary": {
    "total_invested_inr": 4149792.26,
    "total_current_inr": 4481646.82,
    "total_pnl_inr": 331854.56,
    "total_pnl_pct": 8.00,
    "overall_xirr_pct": 4.71,
    "asset_count": 12,
    "statement_date": "2026-03-19"
  },
  "assets": [
    {
      "name": "Parag Parikh Flexi Cap Fund Direct",
      "asset_type": "mutual_fund",
      "isin": null,
      "amc": "PPFAS Mutual Fund",
      "category": "Equity",
      "sub_category": "Flexi Cap",
      "folio": "13959825",
      "units": 8547.228,
      "invested_value_inr": 624968.74,
      "current_value_inr": 763913.63,
      "xirr_pct": 10.22,
      "pnl_inr": 138944.89,
      "pnl_pct": 22.23
    }
  ],
  "parser_warnings": []
}
</example_minimal_output>
```

- [ ] **Step 2: Create `task4_open/backend/parser/normalize.py` (basic happy-path only)**

```python
"""LLM-driven normalization of any holdings statement → canonical Pydantic schema."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from string import Template

from .extract import ExtractedContent
from .schema import NormalizedHoldings

DEFAULT_HAIKU_MODEL = "claude-haiku-4-5"  # confirmed via claude-api skill, Task 1 step 2
MAX_INPUT_TOKENS = 30_000
MAX_OUTPUT_TOKENS = 4096
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Pricing per 1M tokens for cost estimation (Haiku 4.5 as of cached models table)
HAIKU_INPUT_USD_PER_M = 1.0
HAIKU_OUTPUT_USD_PER_M = 5.0

logger = logging.getLogger(__name__)


class NormalizationError(Exception):
    """Raised when the LLM fails to produce valid normalized JSON after retry."""

    def __init__(self, message: str, attempts: list[str], errors: list[str]):
        super().__init__(message)
        self.attempts = attempts
        self.errors = errors


def _format_extracted(content: ExtractedContent) -> str:
    """Render ExtractedContent as a single string for the prompt."""
    if content.kind == "text":
        return content.text
    if content.kind == "tables":
        out = []
        for sheet_name, rows in content.tables:
            out.append(f"=== Sheet: {sheet_name} ===")
            for row in rows:
                out.append("\t".join(row))
        return "\n".join(out)
    if content.kind == "image":
        return "[image content — see attached image]"
    raise ValueError(f"unknown extract kind: {content.kind}")


def _build_prompt(content: ExtractedContent) -> str:
    raw = (PROMPTS_DIR / "normalize.txt").read_text()
    schema_json = json.dumps(NormalizedHoldings.model_json_schema(), indent=2)
    return Template(raw).substitute(
        extracted_content=_format_extracted(content),
        canonical_schema_json=schema_json,
    )


def _strip_fences(raw: str) -> str:
    """Defensive: strip ```json fences if the model wrapped its output."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    return cleaned


def _call_haiku(prompt: str, model: str, content: ExtractedContent) -> tuple[str, dict]:
    """Call Anthropic. Returns (raw_text, usage_dict)."""
    from anthropic import Anthropic
    client = Anthropic()
    if content.kind == "image":
        import base64
        img_b64 = base64.standard_b64encode(content.image_bytes).decode()
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": content.image_media_type, "data": img_b64}},
                {"type": "text", "text": prompt},
            ],
        }]
    else:
        messages = [{"role": "user", "content": prompt}]
    response = client.messages.create(
        model=model,
        max_tokens=MAX_OUTPUT_TOKENS,
        messages=messages,
    )
    raw = response.content[0].text
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return raw, usage


def _estimated_cost_usd(input_tokens: int, output_tokens: int = MAX_OUTPUT_TOKENS) -> float:
    return (input_tokens * HAIKU_INPUT_USD_PER_M / 1_000_000) + (output_tokens * HAIKU_OUTPUT_USD_PER_M / 1_000_000)


def normalize(content: ExtractedContent, model: str = DEFAULT_HAIKU_MODEL) -> NormalizedHoldings:
    """Convert ExtractedContent → NormalizedHoldings via Haiku. Raises NormalizationError after 1 retry."""
    prompt = _build_prompt(content)

    raw, usage = _call_haiku(prompt, model, content)
    cost = _estimated_cost_usd(usage["input_tokens"], usage["output_tokens"])
    logger.info(
        "[parser] actual cost: $%.4f (input: %d tokens, output: %d tokens)",
        cost, usage["input_tokens"], usage["output_tokens"],
    )

    cleaned = _strip_fences(raw)
    try:
        data = json.loads(cleaned)
        return NormalizedHoldings.model_validate(data)
    except (json.JSONDecodeError, Exception) as first_err:
        # Single retry with the validation error appended
        retry_prompt = (
            prompt
            + "\n\n<previous_attempt>\n" + raw + "\n</previous_attempt>"
            + "\n\n<validation_error>\n" + str(first_err) + "\n</validation_error>"
            + "\n\nThe previous response was rejected. Fix the issues and output corrected JSON only."
        )
        raw2, usage2 = _call_haiku(retry_prompt, model, content)
        cost2 = _estimated_cost_usd(usage2["input_tokens"], usage2["output_tokens"])
        logger.info(
            "[parser] retry cost: $%.4f (input: %d, output: %d)",
            cost2, usage2["input_tokens"], usage2["output_tokens"],
        )
        cleaned2 = _strip_fences(raw2)
        try:
            data2 = json.loads(cleaned2)
            return NormalizedHoldings.model_validate(data2)
        except Exception as second_err:
            raise NormalizationError(
                "could not normalize statement after retry",
                attempts=[raw, raw2],
                errors=[str(first_err), str(second_err)],
            ) from second_err
```

- [ ] **Step 3: Create `task4_open/backend/tests/test_normalize.py` (happy path only)**

```python
"""Tests for parser.normalize — Anthropic SDK is mocked; no live calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.extract import ExtractedContent
from parser.normalize import NormalizationError, normalize


VALID_RESPONSE = json.dumps({
    "holder_name": "Test User",
    "source_format": "groww_xlsx",
    "summary": {
        "total_invested_inr": 100.0,
        "total_current_inr": 110.0,
        "total_pnl_inr": 10.0,
        "total_pnl_pct": 10.0,
        "asset_count": 1,
    },
    "assets": [{
        "name": "Test Fund Direct Growth",
        "asset_type": "mutual_fund",
        "amc": "Test AMC",
        "category": "Equity",
        "sub_category": "Flexi Cap",
        "units": 10.0,
        "invested_value_inr": 100.0,
        "current_value_inr": 110.0,
        "pnl_inr": 10.0,
        "pnl_pct": 10.0,
    }],
    "parser_warnings": [],
})


def _mock_anthropic_response(text: str, input_tokens: int = 1000, output_tokens: int = 200) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return response


def test_normalize_happy_path() -> None:
    content = ExtractedContent(kind="text", text="dummy content", format_hint="groww_xlsx")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)
    with patch("parser.normalize.Anthropic", return_value=mock_client):
        result = normalize(content)
    assert result.holder_name == "Test User"
    assert len(result.assets) == 1
    assert result.assets[0].name == "Test Fund Direct Growth"
    assert mock_client.messages.create.call_count == 1, "should only call once on happy path"


def test_normalize_strips_json_fences() -> None:
    fenced = "```json\n" + VALID_RESPONSE + "\n```"
    content = ExtractedContent(kind="text", text="dummy", format_hint="unknown")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_anthropic_response(fenced)
    with patch("parser.normalize.Anthropic", return_value=mock_client):
        result = normalize(content)
    assert result.holder_name == "Test User"
```

- [ ] **Step 4: Run tests**

```bash
cd task4_open/backend && python -m pytest tests/test_normalize.py -v && cd ../..
```

Expected: 2 passed.

---

## Task 7: normalize.py — retry-on-validation-failure + tests

**Files:**
- Modify: `task4_open/backend/tests/test_normalize.py`

The retry path is already implemented in Task 6 step 2 (the `try/except` block in `normalize()`). This task adds the tests.

- [ ] **Step 1: Append retry tests to `task4_open/backend/tests/test_normalize.py`**

Insert before the file's end:

```python
def test_normalize_retries_on_invalid_json() -> None:
    content = ExtractedContent(kind="text", text="dummy", format_hint="unknown")
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _mock_anthropic_response("not valid json {{{"),  # first attempt fails
        _mock_anthropic_response(VALID_RESPONSE),         # retry succeeds
    ]
    with patch("parser.normalize.Anthropic", return_value=mock_client):
        result = normalize(content)
    assert result.holder_name == "Test User"
    assert mock_client.messages.create.call_count == 2, "should call twice (initial + retry)"


def test_normalize_raises_after_retry_failure() -> None:
    content = ExtractedContent(kind="text", text="dummy", format_hint="unknown")
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _mock_anthropic_response("garbage 1"),
        _mock_anthropic_response("garbage 2"),
    ]
    with patch("parser.normalize.Anthropic", return_value=mock_client):
        try:
            normalize(content)
        except NormalizationError as e:
            assert len(e.attempts) == 2, f"expected 2 attempts, got {len(e.attempts)}"
            assert len(e.errors) == 2
            return
    raise AssertionError("expected NormalizationError, none raised")


def test_normalize_retries_on_pydantic_validation_failure() -> None:
    """Valid JSON but missing required field — should retry."""
    invalid_payload = json.dumps({
        "source_format": "groww_xlsx",
        # missing summary, assets — Pydantic will reject
    })
    content = ExtractedContent(kind="text", text="dummy", format_hint="unknown")
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _mock_anthropic_response(invalid_payload),
        _mock_anthropic_response(VALID_RESPONSE),
    ]
    with patch("parser.normalize.Anthropic", return_value=mock_client):
        result = normalize(content)
    assert result.holder_name == "Test User"
    assert mock_client.messages.create.call_count == 2
```

- [ ] **Step 2: Run tests**

```bash
cd task4_open/backend && python -m pytest tests/test_normalize.py -v && cd ../..
```

Expected: 5 passed (2 from Task 6 + 3 from this task).

---

## Task 8: normalize.py — token cap + truncation + tests

**Files:**
- Modify: `task4_open/backend/parser/normalize.py`
- Modify: `task4_open/backend/tests/test_normalize.py`

- [ ] **Step 1: Add token-counting + truncation to `normalize.py`**

Replace the `normalize()` function in `task4_open/backend/parser/normalize.py` with:

```python
def normalize(content: ExtractedContent, model: str = DEFAULT_HAIKU_MODEL) -> NormalizedHoldings:
    """Convert ExtractedContent → NormalizedHoldings via Haiku. Raises NormalizationError after 1 retry."""
    prompt = _build_prompt(content)
    warnings: list[str] = []

    # Token-cap defense — count and truncate if pathological
    from anthropic import Anthropic
    client = Anthropic()
    estimated_input = client.messages.count_tokens(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    ).input_tokens
    if estimated_input > MAX_INPUT_TOKENS:
        # Truncate the extracted_content portion of the prompt; rebuild
        if content.kind == "text":
            char_limit = int(len(content.text) * (MAX_INPUT_TOKENS / estimated_input) * 0.95)
            content = ExtractedContent(
                kind="text",
                text=content.text[:char_limit],
                format_hint=content.format_hint,
            )
        elif content.kind == "tables":
            # Drop trailing rows from the largest table until under limit
            new_tables = []
            for sn, rows in content.tables:
                keep = int(len(rows) * (MAX_INPUT_TOKENS / estimated_input) * 0.95)
                new_tables.append((sn, rows[:max(1, keep)]))
            content = ExtractedContent(kind="tables", tables=new_tables, format_hint=content.format_hint)
        warnings.append(
            f"input truncated from {estimated_input} to ~{MAX_INPUT_TOKENS} tokens — "
            "some assets may be missing from the parsed output"
        )
        prompt = _build_prompt(content)

    pre_cost = _estimated_cost_usd(min(estimated_input, MAX_INPUT_TOKENS))
    logger.info(
        "[parser] estimated cost: $%.4f (input: ~%d tokens, max output: %d, model: %s)",
        pre_cost, min(estimated_input, MAX_INPUT_TOKENS), MAX_OUTPUT_TOKENS, model,
    )

    raw, usage = _call_haiku(prompt, model, content)
    cost = _estimated_cost_usd(usage["input_tokens"], usage["output_tokens"])
    logger.info(
        "[parser] actual cost: $%.4f (input: %d tokens, output: %d tokens)",
        cost, usage["input_tokens"], usage["output_tokens"],
    )

    cleaned = _strip_fences(raw)
    try:
        data = json.loads(cleaned)
        result = NormalizedHoldings.model_validate(data)
    except (json.JSONDecodeError, Exception) as first_err:
        retry_prompt = (
            prompt
            + "\n\n<previous_attempt>\n" + raw + "\n</previous_attempt>"
            + "\n\n<validation_error>\n" + str(first_err) + "\n</validation_error>"
            + "\n\nThe previous response was rejected. Fix the issues and output corrected JSON only."
        )
        raw2, usage2 = _call_haiku(retry_prompt, model, content)
        cost2 = _estimated_cost_usd(usage2["input_tokens"], usage2["output_tokens"])
        logger.info(
            "[parser] retry cost: $%.4f (input: %d, output: %d)",
            cost2, usage2["input_tokens"], usage2["output_tokens"],
        )
        cleaned2 = _strip_fences(raw2)
        try:
            data2 = json.loads(cleaned2)
            result = NormalizedHoldings.model_validate(data2)
        except Exception as second_err:
            raise NormalizationError(
                "could not normalize statement after retry",
                attempts=[raw, raw2],
                errors=[str(first_err), str(second_err)],
            ) from second_err

    # Prepend our warnings to whatever the model already produced
    result.parser_warnings = warnings + result.parser_warnings
    return result
```

- [ ] **Step 2: Add token-cap test**

Append to `task4_open/backend/tests/test_normalize.py`:

```python
def test_normalize_truncates_oversized_input() -> None:
    """When count_tokens reports input over MAX_INPUT_TOKENS, content gets truncated and warned."""
    huge_text = "x" * 200_000
    content = ExtractedContent(kind="text", text=huge_text, format_hint="unknown")
    mock_client = MagicMock()
    # Report 100K input tokens (way over MAX_INPUT_TOKENS=30K)
    mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=100_000)
    mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)
    with patch("parser.normalize.Anthropic", return_value=mock_client):
        result = normalize(content)
    assert any("truncated" in w for w in result.parser_warnings), \
        f"truncation warning missing: {result.parser_warnings}"
```

- [ ] **Step 3: Update existing happy-path tests to mock count_tokens**

The existing tests will fail now because they don't mock `count_tokens`. Find each `mock_client = MagicMock()` line in `test_normalize.py` (Tasks 6 + 7 added several) and add `mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)` immediately after, like:

```python
mock_client = MagicMock()
mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)
mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)
```

Apply the same edit to all 5 existing test functions (`test_normalize_happy_path`, `test_normalize_strips_json_fences`, `test_normalize_retries_on_invalid_json`, `test_normalize_raises_after_retry_failure`, `test_normalize_retries_on_pydantic_validation_failure`).

- [ ] **Step 4: Run tests**

```bash
cd task4_open/backend && python -m pytest tests/test_normalize.py -v && cd ../..
```

Expected: 6 passed.

---

## Task 9: normalize.py — daily budget cache + tests

**Files:**
- Modify: `task4_open/backend/parser/normalize.py`
- Modify: `task4_open/backend/tests/test_normalize.py`

- [ ] **Step 1: Add the budget tracking module-level helpers to `normalize.py`**

At the top of `task4_open/backend/parser/normalize.py`, after the imports, insert:

```python
CACHE_DIR = Path.home() / ".cache" / "timecell-task4"


def _max_daily_usd() -> float | None:
    """Returns daily cap in USD, or None if disabled."""
    raw = os.environ.get("MAX_DAILY_LLM_USD", "2.00")
    if raw.lower() == "disabled":
        return None
    try:
        return float(raw)
    except ValueError:
        return 2.00


def _today_cache_path() -> Path:
    from datetime import date
    return CACHE_DIR / f"usage-{date.today().isoformat()}.json"


def _read_today_usd() -> float:
    p = _today_cache_path()
    if not p.exists():
        return 0.0
    try:
        return float(json.loads(p.read_text()))
    except Exception:
        return 0.0


def _write_today_usd(amount: float) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = _today_cache_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(amount))
    tmp.replace(p)


class BudgetExhausted(Exception):
    """Raised when today's LLM spend would exceed MAX_DAILY_LLM_USD."""
```

- [ ] **Step 2: Insert the budget check into `normalize()`**

Replace the line `pre_cost = _estimated_cost_usd(min(estimated_input, MAX_INPUT_TOKENS))` and the `logger.info("[parser] estimated cost: ...")` block with:

```python
    pre_cost = _estimated_cost_usd(min(estimated_input, MAX_INPUT_TOKENS))
    logger.info(
        "[parser] estimated cost: $%.4f (input: ~%d tokens, max output: %d, model: %s)",
        pre_cost, min(estimated_input, MAX_INPUT_TOKENS), MAX_OUTPUT_TOKENS, model,
    )

    # Daily budget guard
    cap = _max_daily_usd()
    if cap is not None:
        today_so_far = _read_today_usd()
        if today_so_far + pre_cost > cap:
            raise BudgetExhausted(
                f"daily budget ${cap:.2f} would be exceeded "
                f"(spent ${today_so_far:.4f} so far, this call estimated ${pre_cost:.4f})"
            )
```

And after the (potentially-retry) `_call_haiku()` calls, add the cache update at the very end of `normalize()` just before `return result`:

```python
    # Update daily-spend cache with actual cost from this call (only on success)
    actual_total = cost  # cost is from the first call; if retry happened, add cost2
    try:
        actual_total += cost2  # only defined if retry path taken
    except NameError:
        pass
    if cap is not None:
        _write_today_usd(_read_today_usd() + actual_total)
```

Wait — `cost2` is defined inside the except block, so referencing it outside causes NameError. Replace the above block with this cleaner version (and rework the function so the costs accumulate):

Actually, do this differently: track `total_cost` as a local variable accumulated through the function. Replace the retry block + the trailing block with:

```python
    cleaned = _strip_fences(raw)
    total_cost = cost
    try:
        data = json.loads(cleaned)
        result = NormalizedHoldings.model_validate(data)
    except (json.JSONDecodeError, Exception) as first_err:
        retry_prompt = (
            prompt
            + "\n\n<previous_attempt>\n" + raw + "\n</previous_attempt>"
            + "\n\n<validation_error>\n" + str(first_err) + "\n</validation_error>"
            + "\n\nThe previous response was rejected. Fix the issues and output corrected JSON only."
        )
        raw2, usage2 = _call_haiku(retry_prompt, model, content)
        cost2 = _estimated_cost_usd(usage2["input_tokens"], usage2["output_tokens"])
        total_cost += cost2
        logger.info(
            "[parser] retry cost: $%.4f (input: %d, output: %d)",
            cost2, usage2["input_tokens"], usage2["output_tokens"],
        )
        cleaned2 = _strip_fences(raw2)
        try:
            data2 = json.loads(cleaned2)
            result = NormalizedHoldings.model_validate(data2)
        except Exception as second_err:
            raise NormalizationError(
                "could not normalize statement after retry",
                attempts=[raw, raw2],
                errors=[str(first_err), str(second_err)],
            ) from second_err

    result.parser_warnings = warnings + result.parser_warnings
    if cap is not None:
        _write_today_usd(_read_today_usd() + total_cost)
    return result
```

- [ ] **Step 3: Add budget tests**

Append to `task4_open/backend/tests/test_normalize.py`:

```python
import tempfile
from pathlib import Path as PathlibPath


def test_normalize_respects_daily_budget(monkeypatch) -> None:
    from parser.normalize import BudgetExhausted

    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setattr("parser.normalize.CACHE_DIR", PathlibPath(td))
        monkeypatch.setenv("MAX_DAILY_LLM_USD", "0.001")  # tiny cap

        content = ExtractedContent(kind="text", text="dummy", format_hint="unknown")
        mock_client = MagicMock()
        # Report 30K tokens so estimated cost > $0.001 cap
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=30_000)
        mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)

        with patch("parser.normalize.Anthropic", return_value=mock_client):
            try:
                normalize(content)
            except BudgetExhausted as e:
                assert "daily budget" in str(e).lower(), f"unexpected message: {e}"
                # Verify create was NOT called — budget guard fires before the API call
                assert mock_client.messages.create.call_count == 0
                return
        raise AssertionError("expected BudgetExhausted, none raised")


def test_normalize_disabled_budget_allows_call(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setattr("parser.normalize.CACHE_DIR", PathlibPath(td))
        monkeypatch.setenv("MAX_DAILY_LLM_USD", "disabled")

        content = ExtractedContent(kind="text", text="dummy", format_hint="unknown")
        mock_client = MagicMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=30_000)
        mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)

        with patch("parser.normalize.Anthropic", return_value=mock_client):
            result = normalize(content)
        assert result.holder_name == "Test User"


def test_normalize_writes_cache_on_success(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as td:
        cache = PathlibPath(td)
        monkeypatch.setattr("parser.normalize.CACHE_DIR", cache)
        monkeypatch.setenv("MAX_DAILY_LLM_USD", "10.00")

        content = ExtractedContent(kind="text", text="dummy", format_hint="unknown")
        mock_client = MagicMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=1000)
        mock_client.messages.create.return_value = _mock_anthropic_response(VALID_RESPONSE)

        with patch("parser.normalize.Anthropic", return_value=mock_client):
            normalize(content)

        cache_files = list(cache.glob("usage-*.json"))
        assert len(cache_files) == 1, f"expected one cache file, got {cache_files}"
        spent = float(cache_files[0].read_text())
        assert spent > 0, f"expected positive spend, got {spent}"
```

- [ ] **Step 4: Run tests**

```bash
cd task4_open/backend && python -m pytest tests/test_normalize.py -v && cd ../..
```

Expected: 9 passed.

---

## Task 10: metrics/compute.py — kpis + allocation + tests

**Files:**
- Create: `task4_open/backend/metrics/compute.py`
- Create: `task4_open/backend/tests/test_metrics.py`

- [ ] **Step 1: Create `task4_open/backend/metrics/compute.py` with kpis + allocation**

```python
"""Pure-function metrics computed from NormalizedHoldings. No I/O, no LLM."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.schema import NormalizedHoldings


class KPIs(BaseModel):
    invested_inr: float
    current_inr: float
    equity_pct: float
    debt_pct: float
    overall_xirr_pct: float | None = None
    asset_count: int


class AllocationSlice(BaseModel):
    label: str
    value_inr: float
    pct: float


class XirrEntry(BaseModel):
    name: str
    xirr_pct: float
    color: Literal["positive", "negative"]


class CategoryPerformance(BaseModel):
    category: str
    pnl_inr: float
    cagr_pct: float | None = None


def kpis(nh: NormalizedHoldings) -> KPIs:
    total_current = nh.summary.total_current_inr or 1e-9  # avoid div/0
    equity_value = sum(a.current_value_inr for a in nh.assets if a.category == "Equity")
    debt_value = sum(a.current_value_inr for a in nh.assets if a.category == "Debt")
    return KPIs(
        invested_inr=nh.summary.total_invested_inr,
        current_inr=nh.summary.total_current_inr,
        equity_pct=round(equity_value / total_current * 100, 2),
        debt_pct=round(debt_value / total_current * 100, 2),
        overall_xirr_pct=nh.summary.overall_xirr_pct,
        asset_count=nh.summary.asset_count,
    )


def allocation(nh: NormalizedHoldings) -> list[AllocationSlice]:
    """Group by sub_category if present, else by category, else by name."""
    buckets: dict[str, float] = {}
    for a in nh.assets:
        label = a.sub_category or a.category or a.name
        buckets[label] = buckets.get(label, 0) + a.current_value_inr
    total = sum(buckets.values()) or 1e-9
    slices = [
        AllocationSlice(label=label, value_inr=v, pct=round(v / total * 100, 2))
        for label, v in buckets.items()
    ]
    slices.sort(key=lambda s: s.value_inr, reverse=True)
    return slices
```

- [ ] **Step 2: Create `task4_open/backend/tests/test_metrics.py`**

```python
"""Tests for metrics.compute — pure functions, hand-built fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from metrics.compute import allocation, kpis
from parser.schema import Asset, NormalizedHoldings, PortfolioSummary


def _asset(name: str, category: str | None, sub_category: str | None,
           current: float, invested: float, xirr: float | None = None) -> Asset:
    return Asset(
        name=name,
        asset_type="mutual_fund",
        category=category,
        sub_category=sub_category,
        units=1.0,
        invested_value_inr=invested,
        current_value_inr=current,
        xirr_pct=xirr,
        pnl_inr=current - invested,
        pnl_pct=((current - invested) / invested * 100) if invested else 0.0,
    )


def _portfolio(assets: list[Asset], overall_xirr: float | None = 4.71) -> NormalizedHoldings:
    total_invested = sum(a.invested_value_inr for a in assets)
    total_current = sum(a.current_value_inr for a in assets)
    return NormalizedHoldings(
        holder_name="Test",
        source_format="test",
        summary=PortfolioSummary(
            total_invested_inr=total_invested,
            total_current_inr=total_current,
            total_pnl_inr=total_current - total_invested,
            total_pnl_pct=((total_current - total_invested) / total_invested * 100) if total_invested else 0,
            overall_xirr_pct=overall_xirr,
            asset_count=len(assets),
        ),
        assets=assets,
    )


def test_kpis_equity_debt_split() -> None:
    nh = _portfolio([
        _asset("Equity Fund", "Equity", "Flexi Cap", current=600, invested=500),
        _asset("Debt Fund", "Debt", "Gilt", current=400, invested=400),
    ])
    k = kpis(nh)
    assert k.equity_pct == 60.0, f"got {k.equity_pct}"
    assert k.debt_pct == 40.0, f"got {k.debt_pct}"
    assert k.invested_inr == 900.0
    assert k.current_inr == 1000.0
    assert k.overall_xirr_pct == 4.71


def test_kpis_empty_portfolio() -> None:
    nh = _portfolio([], overall_xirr=None)
    k = kpis(nh)
    assert k.equity_pct == 0.0
    assert k.debt_pct == 0.0
    assert k.asset_count == 0


def test_allocation_groups_by_sub_category() -> None:
    nh = _portfolio([
        _asset("Fund A", "Equity", "Flexi Cap", current=500, invested=400),
        _asset("Fund B", "Equity", "Flexi Cap", current=300, invested=300),
        _asset("Fund C", "Debt", "Gilt", current=200, invested=200),
    ])
    slices = allocation(nh)
    by_label = {s.label: s for s in slices}
    assert by_label["Flexi Cap"].value_inr == 800.0
    assert by_label["Flexi Cap"].pct == 80.0
    assert by_label["Gilt"].value_inr == 200.0
    assert by_label["Gilt"].pct == 20.0


def test_allocation_falls_back_to_category_then_name() -> None:
    nh = _portfolio([
        _asset("Fund X", "Equity", None, current=500, invested=500),  # no sub_category
        _asset("Lone", None, None, current=500, invested=500),         # no category either
    ])
    slices = allocation(nh)
    labels = [s.label for s in slices]
    assert "Equity" in labels
    assert "Lone" in labels
```

- [ ] **Step 3: Run tests**

```bash
cd task4_open/backend && python -m pytest tests/test_metrics.py -v && cd ../..
```

Expected: 4 passed.

---

## Task 11: metrics/compute.py — xirr_by_fund + category_performance + tests

**Files:**
- Modify: `task4_open/backend/metrics/compute.py`
- Modify: `task4_open/backend/tests/test_metrics.py`

- [ ] **Step 1: Append to `task4_open/backend/metrics/compute.py`**

```python
def xirr_by_fund(nh: NormalizedHoldings, max_entries: int = 20) -> list[XirrEntry]:
    """Sorted desc by xirr_pct, capped at max_entries, names truncated to 24 chars."""
    entries = []
    for a in nh.assets:
        if a.xirr_pct is None:
            continue
        name = a.name if len(a.name) <= 24 else a.name[:21] + "..."
        entries.append(XirrEntry(
            name=name,
            xirr_pct=a.xirr_pct,
            color="positive" if a.xirr_pct >= 0 else "negative",
        ))
    entries.sort(key=lambda e: e.xirr_pct, reverse=True)
    return entries[:max_entries]


def category_performance(nh: NormalizedHoldings) -> list[CategoryPerformance]:
    """Aggregate P&L per category. CAGR is None unless the source had a per-category XIRR."""
    by_cat: dict[str, dict[str, float]] = {}
    for a in nh.assets:
        cat = a.category or "Other"
        if cat not in by_cat:
            by_cat[cat] = {"pnl": 0.0, "invested": 0.0, "current": 0.0}
        by_cat[cat]["pnl"] += a.pnl_inr
        by_cat[cat]["invested"] += a.invested_value_inr
        by_cat[cat]["current"] += a.current_value_inr
    out = []
    for cat, vals in by_cat.items():
        # Use per-category XIRR mean if available, else None (full-portfolio XIRR is in KPIs)
        cagrs = [a.xirr_pct for a in nh.assets if (a.category or "Other") == cat and a.xirr_pct is not None]
        avg_cagr = sum(cagrs) / len(cagrs) if cagrs else None
        out.append(CategoryPerformance(
            category=cat,
            pnl_inr=round(vals["pnl"], 2),
            cagr_pct=round(avg_cagr, 2) if avg_cagr is not None else None,
        ))
    out.sort(key=lambda c: c.pnl_inr, reverse=True)
    return out
```

- [ ] **Step 2: Append tests to `task4_open/backend/tests/test_metrics.py`**

```python
def test_xirr_by_fund_sorted_desc_with_color() -> None:
    from metrics.compute import xirr_by_fund
    nh = _portfolio([
        _asset("Top Fund", "Equity", "Flexi Cap", current=110, invested=100, xirr=10.5),
        _asset("Negative Fund", "Equity", "Mid Cap", current=90, invested=100, xirr=-5.2),
        _asset("Middle Fund", "Equity", "Large Cap", current=105, invested=100, xirr=2.3),
        _asset("No XIRR Fund", "Equity", "Small Cap", current=100, invested=100, xirr=None),
    ])
    entries = xirr_by_fund(nh)
    assert len(entries) == 3, f"None-XIRR should be skipped, got {len(entries)}"
    assert entries[0].name == "Top Fund"
    assert entries[0].color == "positive"
    assert entries[-1].name == "Negative Fund"
    assert entries[-1].color == "negative"


def test_xirr_by_fund_truncates_long_names() -> None:
    from metrics.compute import xirr_by_fund
    nh = _portfolio([
        _asset("This is an extremely long mutual fund name that exceeds 24 chars",
               "Equity", "Flexi Cap", current=110, invested=100, xirr=5.0),
    ])
    entries = xirr_by_fund(nh)
    assert len(entries[0].name) == 24, f"name not truncated: {entries[0].name}"
    assert entries[0].name.endswith("...")


def test_category_performance_aggregates() -> None:
    from metrics.compute import category_performance
    nh = _portfolio([
        _asset("Fund A", "Equity", "Flexi Cap", current=500, invested=400, xirr=10.0),
        _asset("Fund B", "Equity", "Mid Cap", current=300, invested=300, xirr=0.0),
        _asset("Fund C", "Debt", "Gilt", current=400, invested=350, xirr=5.0),
    ])
    perf = category_performance(nh)
    by_cat = {p.category: p for p in perf}
    assert by_cat["Equity"].pnl_inr == 100.0  # 100 + 0
    assert by_cat["Debt"].pnl_inr == 50.0
    assert by_cat["Equity"].cagr_pct == 5.0   # avg of 10 and 0
    assert by_cat["Debt"].cagr_pct == 5.0
```

- [ ] **Step 3: Run tests**

```bash
cd task4_open/backend && python -m pytest tests/test_metrics.py -v && cd ../..
```

Expected: 7 passed (4 from Task 10 + 3 from this task).

---

## Task 12: backend/main.py — FastAPI app + /api/health + /api/parse-and-compute + tests

**Files:**
- Create: `task4_open/backend/main.py`
- Create: `task4_open/backend/tests/test_main.py`

- [ ] **Step 1: Create `task4_open/backend/main.py`**

```python
"""FastAPI app for Task 4a: parse-and-compute + health endpoints."""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Module path setup so direct uvicorn imports work
import sys
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from parser.extract import ExtractError, extract
from parser.normalize import (
    DEFAULT_HAIKU_MODEL,
    BudgetExhausted,
    NormalizationError,
    normalize,
)
from parser.schema import NormalizedHoldings
from metrics.compute import (
    AllocationSlice,
    CategoryPerformance,
    KPIs,
    XirrEntry,
    allocation,
    category_performance,
    kpis,
    xirr_by_fund,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg"}

app = FastAPI(title="Task 4a — Portfolio Intelligence Dashboard backend")


class ParseAndComputeResponse(BaseModel):
    normalized: NormalizedHoldings
    kpis: KPIs
    allocation: list[AllocationSlice]
    xirr_by_fund: list[XirrEntry]
    category_performance: list[CategoryPerformance]


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "model": DEFAULT_HAIKU_MODEL,
    }


@app.post("/api/parse-and-compute", response_model=ParseAndComputeResponse)
async def parse_and_compute(file: UploadFile = File(...)) -> ParseAndComputeResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail={"error": "no file provided"})

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail={"error": "unsupported file type", "supported": sorted(SUPPORTED_EXTENSIONS)},
        )

    # Stream to tempfile, enforce size cap
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        bytes_written = 0
        while chunk := await file.read(64 * 1024):
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_BYTES:
                tmp.close()
                Path(tmp.name).unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail={"error": "file too large", "max_mb": MAX_FILE_BYTES // (1024 * 1024)},
                )
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    try:
        try:
            content = extract(tmp_path)
        except ExtractError as e:
            raise HTTPException(
                status_code=422,
                detail={"error": "could not extract structured data", "detail": str(e)},
            )

        try:
            normalized = normalize(content)
        except BudgetExhausted as e:
            raise HTTPException(status_code=429, detail={"error": "daily LLM budget exhausted", "detail": str(e)})
        except NormalizationError as e:
            raise HTTPException(
                status_code=502,
                detail={"error": "could not normalize statement after retry", "raw_attempts": e.attempts},
            )
        except Exception as e:
            logger.exception("LLM call failed")
            raise HTTPException(status_code=502, detail={"error": "LLM service unavailable", "detail": str(e)})

        return ParseAndComputeResponse(
            normalized=normalized,
            kpis=kpis(normalized),
            allocation=allocation(normalized),
            xirr_by_fund=xirr_by_fund(normalized),
            category_performance=category_performance(normalized),
        )
    finally:
        tmp_path.unlink(missing_ok=True)
```

- [ ] **Step 2: Create `task4_open/backend/tests/test_main.py`**

```python
"""Tests for main.py — FastAPI TestClient + mocked normalize."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app
from parser.schema import Asset, NormalizedHoldings, PortfolioSummary

client = TestClient(app)

SAMPLE_DIR = Path(__file__).parent.parent / "samples"


def _fake_normalized() -> NormalizedHoldings:
    return NormalizedHoldings(
        holder_name="Test User A",
        source_format="groww_xlsx",
        summary=PortfolioSummary(
            total_invested_inr=187129.48,
            total_current_inr=215166.69,
            total_pnl_inr=28037.21,
            total_pnl_pct=14.98,
            overall_xirr_pct=9.62,
            asset_count=2,
        ),
        assets=[
            Asset(
                name="Test Equity Fund",
                asset_type="mutual_fund",
                category="Equity",
                sub_category="Flexi Cap",
                units=10,
                invested_value_inr=100000,
                current_value_inr=120000,
                pnl_inr=20000,
                pnl_pct=20.0,
                xirr_pct=15.0,
            ),
            Asset(
                name="Test Debt Fund",
                asset_type="mutual_fund",
                category="Debt",
                sub_category="Gilt",
                units=10,
                invested_value_inr=87129.48,
                current_value_inr=95166.69,
                pnl_inr=8037.21,
                pnl_pct=9.22,
                xirr_pct=5.0,
            ),
        ],
    )


def test_health_returns_ok() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "anthropic_key_set" in body
    assert body["model"] == "claude-haiku-4-5"


def test_parse_and_compute_happy_path() -> None:
    with patch("main.normalize", return_value=_fake_normalized()):
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["normalized"]["holder_name"] == "Test User A"
    assert body["kpis"]["asset_count"] == 2
    assert body["kpis"]["equity_pct"] > 0
    assert len(body["allocation"]) >= 1
    assert len(body["xirr_by_fund"]) == 2
    assert len(body["category_performance"]) == 2


def test_parse_and_compute_rejects_unsupported_extension() -> None:
    file = io.BytesIO(b"fake content")
    r = client.post(
        "/api/parse-and-compute",
        files={"file": ("bad.docx", file, "application/octet-stream")},
    )
    assert r.status_code == 415
    body = r.json()
    assert "unsupported" in body["detail"]["error"]


def test_parse_and_compute_rejects_oversized_file() -> None:
    big = io.BytesIO(b"x" * (11 * 1024 * 1024))   # 11 MB
    r = client.post(
        "/api/parse-and-compute",
        files={"file": ("big.xlsx", big, "application/octet-stream")},
    )
    assert r.status_code == 413
    body = r.json()
    assert body["detail"]["error"] == "file too large"


def test_parse_and_compute_handles_normalization_error() -> None:
    from parser.normalize import NormalizationError
    err = NormalizationError("bad", attempts=["x", "y"], errors=["e1", "e2"])
    with patch("main.normalize", side_effect=err):
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r.status_code == 502
    body = r.json()
    assert "could not normalize" in body["detail"]["error"]


def test_parse_and_compute_handles_budget_exhausted() -> None:
    from parser.normalize import BudgetExhausted
    with patch("main.normalize", side_effect=BudgetExhausted("limit")):
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r.status_code == 429
    body = r.json()
    assert "budget" in body["detail"]["error"]
```

- [ ] **Step 3: Run tests**

```bash
cd task4_open/backend && python -m pytest tests/test_main.py -v && cd ../..
```

Expected: 6 passed.

- [ ] **Step 4: Run the full backend test suite**

```bash
cd task4_open/backend && python -m pytest -v && cd ../..
```

Expected: ~28 passed total (4 schema + 6 extract + 9 normalize + 7 metrics + 6 main).

---

## Task 13: Backend manual smoke test — start uvicorn, parse all 3 samples live

**Files:** none changed — pure live verification.

This task uses real Anthropic API credits (~$0.10 total across 3 parses). Make sure `ANTHROPIC_API_KEY` is set in `.env`.

- [ ] **Step 1: Start backend in background**

```bash
cd task4_open/backend && uvicorn main:app --port 8000 &
sleep 3
curl -s http://localhost:8000/api/health
echo ""
```

Expected: JSON `{"status":"ok","anthropic_key_set":true,"model":"claude-haiku-4-5"}`.

- [ ] **Step 2: Parse `sample_groww.xlsx` live**

```bash
curl -s -X POST http://localhost:8000/api/parse-and-compute \
    -F "file=@task4_open/backend/samples/sample_groww.xlsx" \
    | python -c "import json, sys; d=json.load(sys.stdin); print('holder:', d['normalized']['holder_name']); print('source:', d['normalized']['source_format']); print('asset_count:', d['kpis']['asset_count']); print('current:', d['kpis']['current_inr']); print('xirr_entries:', len(d['xirr_by_fund']))"
```

Expected: `holder: Test User A`, `source: groww_xlsx`, asset_count matches the actual file (~8), current_inr ~ 215166, several xirr entries. **No 5xx errors.**

- [ ] **Step 3: Parse `sample_camsonline.xls` live**

```bash
curl -s -X POST http://localhost:8000/api/parse-and-compute \
    -F "file=@task4_open/backend/samples/sample_camsonline.xls" \
    | python -c "import json, sys; d=json.load(sys.stdin); print('holder:', d['normalized']['holder_name']); print('source:', d['normalized']['source_format']); print('asset_count:', d['kpis']['asset_count']); print('current:', d['kpis']['current_inr']); print('equity_pct:', d['kpis']['equity_pct'])"
```

Expected: `holder: Test User B`, `source: camsonline_mhtml`, asset_count: 12, current_inr ≈ 4481646, equity_pct ≈ 64.

- [ ] **Step 4: Parse `sample_zerodha.xlsx` live**

```bash
curl -s -X POST http://localhost:8000/api/parse-and-compute \
    -F "file=@task4_open/backend/samples/sample_zerodha.xlsx" \
    | python -c "import json, sys; d=json.load(sys.stdin); print('holder:', d['normalized']['holder_name']); print('source:', d['normalized']['source_format']); print('asset_count:', d['kpis']['asset_count']); print('current:', d['kpis']['current_inr'])"
```

Expected: holder may be null (Zerodha files use Client ID, not name), source_format: `zerodha_console`, asset_count > 0.

- [ ] **Step 5: Stop the server**

```bash
kill %1 2>/dev/null || true
sleep 1
ps aux | grep -v grep | grep uvicorn || echo "uvicorn stopped"
```

Expected: `uvicorn stopped`.

---

## Task 14: First commit — backend + samples + .gitignore + spec

**Files:**
- Stage: everything backend + samples + .gitignore (excluding the original PII xlsx files)

- [ ] **Step 1: Verify the original PII files are NOT going to be committed**

```bash
git status --short | grep -E "(Holdings_Statement|Portfolio_summary|holdings-EEM619)" && echo "BAD: PII files staged" || echo "OK: PII files gitignored"
```

Expected: `OK: PII files gitignored`.

- [ ] **Step 2: Stage explicitly (do not use `git add .`)**

```bash
git add \
    .gitignore \
    task4_open/backend/main.py \
    task4_open/backend/parser/__init__.py \
    task4_open/backend/parser/schema.py \
    task4_open/backend/parser/extract.py \
    task4_open/backend/parser/normalize.py \
    task4_open/backend/metrics/__init__.py \
    task4_open/backend/metrics/compute.py \
    task4_open/backend/prompts/normalize.txt \
    task4_open/backend/samples/sample_groww.xlsx \
    task4_open/backend/samples/sample_camsonline.xls \
    task4_open/backend/samples/sample_zerodha.xlsx \
    task4_open/backend/tests/__init__.py \
    task4_open/backend/tests/test_schema.py \
    task4_open/backend/tests/test_extract.py \
    task4_open/backend/tests/test_normalize.py \
    task4_open/backend/tests/test_metrics.py \
    task4_open/backend/tests/test_main.py \
    task4_open/backend/requirements.txt \
    task4_open/backend/pyproject.toml
git status --short
```

Expected: only the listed files appear under "Changes to be committed". `.DS_Store` and the original PII xlsx files do NOT appear staged.

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
task4a: add FastAPI backend — LLM-normalized parser + metrics + redacted samples

Implements the backend half of Task 4a's dashboard. POST /api/parse-and-compute
accepts a holdings file (xlsx, xls, pdf, png, jpg), extracts structured data
via openpyxl/BS4/pdfplumber, and asks Anthropic Haiku 4.5 to normalize it into
the canonical Pydantic schema. Then computes KPIs, allocation, XIRR-by-fund,
and category-performance — all pure functions over the normalized output.

Three layers of cost guardrails on the LLM call: 30K-token input cap with
truncation+warning, per-call cost logging to stderr, daily-budget ceiling
($2/day default, opt out via MAX_DAILY_LLM_USD=disabled) tracked in
~/.cache/timecell-task4/usage-YYYY-MM-DD.json with atomic-rename writes.

One retry on Pydantic validation failure with the validation error appended
to the prompt; raises NormalizationError if both attempts fail (returns
HTTP 502 with both raw responses for debugging).

Sample holdings files are redacted versions of three real broker formats
(Groww xlsx, Camsonline MHTML, Zerodha multi-sheet xlsx) — names, PANs,
phone numbers, and Client IDs replaced with synthetic values per the spec's
privacy decision. Numeric data preserved verbatim so acceptance tests can
assert on real headline numbers.

28 pytest tests pass; manual live smoke test validates all 3 sample formats
end-to-end against real Anthropic API.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -3
```

Expected: commit succeeds; new commit on top of `2da4b48`.

---

## Task 15: Frontend scaffold — Next.js + Tailwind + shadcn/ui + Recharts/Lucide/Zustand/sonner

**Files:**
- Create entire `task4_open/frontend/` directory tree via scaffolding

- [ ] **Step 1: Scaffold Next.js app**

```bash
cd task4_open && npx --yes create-next-app@latest frontend \
    --typescript \
    --tailwind \
    --app \
    --no-eslint \
    --no-src-dir \
    --import-alias "@/*" \
    --turbopack \
    --use-npm \
    --skip-install
```

Expected: `task4_open/frontend/` directory created with package.json, app/, etc. (Skipping install for now — we'll batch with our extra deps below.)

- [ ] **Step 2: Add the additional deps to `task4_open/frontend/package.json`**

Open `task4_open/frontend/package.json`, find the `dependencies` block, and add:

```json
"recharts": "^2.13.0",
"lucide-react": "^0.460.0",
"zustand": "^5.0.0",
"sonner": "^1.7.0",
"react-dropzone": "^14.3.0",
"clsx": "^2.1.0",
"tailwind-merge": "^2.5.0"
```

Find the `devDependencies` block, add:

```json
"vitest": "^2.1.0",
"@vitejs/plugin-react": "^4.3.0",
"@testing-library/react": "^16.0.0",
"@testing-library/jest-dom": "^6.6.0",
"@testing-library/user-event": "^14.5.0",
"jsdom": "^25.0.0",
"@playwright/test": "^1.48.0",
"eslint": "^9.14.0",
"eslint-config-next": "^15.0.0",
"@types/node": "^22.9.0"
```

- [ ] **Step 3: Install all deps**

```bash
cd task4_open/frontend && npm install --no-fund --no-audit && cd ../..
```

Expected: success, `node_modules/` populated.

- [ ] **Step 4: Initialize shadcn/ui**

```bash
cd task4_open/frontend && npx --yes shadcn@latest init -d --yes && cd ../..
```

Expected: `components.json`, `lib/utils.ts` created; `tailwind.config.ts` updated.

- [ ] **Step 5: Add the shadcn primitives we'll use**

```bash
cd task4_open/frontend && npx --yes shadcn@latest add button card --yes && cd ../..
```

Expected: `components/ui/button.tsx`, `components/ui/card.tsx` created.

- [ ] **Step 6: Verify scaffold + install Playwright browser binary**

```bash
cd task4_open/frontend && npx playwright install chromium && cd ../..
ls task4_open/frontend/
```

Expected: `app/`, `components/`, `lib/`, `node_modules/`, `package.json`, `tailwind.config.ts`, etc. all present. Playwright Chromium downloaded.

---

## Task 16: Theme bootstrap — download timecell logo + Ledger palette + Fraunces/Geist Mono

**Files:**
- Download: `task4_open/frontend/public/timecell-logo.png`
- Modify: `task4_open/frontend/tailwind.config.ts`
- Modify: `task4_open/frontend/app/globals.css`
- Modify: `task4_open/frontend/app/layout.tsx`

- [ ] **Step 1: Download the timecell logo**

```bash
mkdir -p task4_open/frontend/public
curl -s -o task4_open/frontend/public/timecell-logo.png https://timecell.ai/logo.png
ls -la task4_open/frontend/public/timecell-logo.png
```

Expected: file ~5-30 KB present.

- [ ] **Step 2: Replace `task4_open/frontend/tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Ledger design system — from timecell.ai
        bg: "var(--bg)",
        fg: "var(--fg)",
        "fg-soft": "var(--fg-soft)",
        rule: "var(--rule)",
        "rule-soft": "var(--rule-soft)",
        muted: "var(--muted)",
        "muted-deep": "var(--muted-deep)",
        "muted-deeper": "var(--muted-deeper)",
        brass: "var(--brass)",
        "brass-bright": "var(--brass-bright)",
        oxblood: "var(--oxblood)",
      },
      fontFamily: {
        serif: ["var(--font-fraunces)", "ui-serif", "Georgia", "serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      letterSpacing: {
        "wide-uppercase": "0.22em",
      },
    },
  },
  plugins: [],
}

export default config
```

- [ ] **Step 3: Replace `task4_open/frontend/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  /* Ledger design system — pulled from timecell.ai */
  --bg: #13110f;
  --fg: #efe8da;
  --fg-soft: #a8a08a;
  --rule: #2a2620;
  --rule-soft: #1f1c18;
  --muted: #8a8275;
  --muted-deep: #6a6258;
  --muted-deeper: #5a5240;
  --brass: #a88b4a;
  --brass-bright: #c9a86a;
  --oxblood: #c97a6f;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font-fraunces), ui-serif, Georgia, serif;
  font-weight: 300;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  background-image:
    radial-gradient(
      ellipse 80% 60% at 50% -10%,
      rgba(168, 139, 74, 0.08) 0%,
      rgba(168, 139, 74, 0) 60%
    ),
    repeating-linear-gradient(
      to bottom,
      transparent 0px,
      transparent 47px,
      rgba(42, 38, 32, 0.35) 47px,
      rgba(42, 38, 32, 0.35) 48px
    );
  min-height: 100vh;
}

a { color: inherit; text-decoration: none; }
a:focus-visible, button:focus-visible {
  outline: 1px solid var(--brass);
  outline-offset: 4px;
}
```

- [ ] **Step 4: Replace `task4_open/frontend/app/layout.tsx`**

```tsx
import type { Metadata } from "next"
import { Fraunces, Geist_Mono } from "next/font/google"
import { Toaster } from "sonner"
import "./globals.css"

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-fraunces",
})

const geistMono = Geist_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-geist-mono",
})

export const metadata: Metadata = {
  title: "TimeCell — Portfolio Intelligence Dashboard",
  description: "AI-powered portfolio analysis with cross-vendor critique.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${geistMono.variable}`}>
      <body>
        {children}
        <Toaster position="top-right" theme="dark" />
      </body>
    </html>
  )
}
```

- [ ] **Step 5: Verify dev server boots without errors**

```bash
cd task4_open/frontend && timeout 8 npm run dev 2>&1 | head -30 ; cd ../..
```

Expected: lines including "Ready in N ms" and "Local: http://localhost:3000". No type errors. Server is killed by timeout — that's fine.

---

## Task 17: lib helpers — format, store, api, theme + tests

**Files:**
- Create: `task4_open/frontend/lib/format.ts`
- Create: `task4_open/frontend/lib/store.ts`
- Create: `task4_open/frontend/lib/api.ts`
- Create: `task4_open/frontend/lib/theme.ts`
- Create: `task4_open/frontend/__tests__/format.test.ts`
- Create: `task4_open/frontend/vitest.config.ts`

- [ ] **Step 1: Create `task4_open/frontend/lib/format.ts`**

```typescript
/** Indian-grouping INR formatter. 10000000 → "1,00,00,000". */
export function formatINR(amount: number): string {
  const n = Math.round(amount)
  const sign = n < 0 ? "-" : ""
  const s = String(Math.abs(n))
  if (s.length <= 3) return `${sign}${s}`
  let head = s.slice(0, -3)
  const tail = s.slice(-3)
  const groups: string[] = []
  while (head.length > 2) {
    groups.unshift(head.slice(-2))
    head = head.slice(0, -2)
  }
  if (head) groups.unshift(head)
  return `${sign}${groups.join(",")},${tail}`
}

/** Format a percentage with sign and 2 decimal places. */
export function formatPct(pct: number, withSign = false): string {
  const sign = withSign && pct > 0 ? "+" : ""
  return `${sign}${pct.toFixed(2)}%`
}
```

- [ ] **Step 2: Create `task4_open/frontend/lib/api.ts`**

```typescript
/** TS types mirroring backend Pydantic schema + typed fetch wrapper. */
export type AssetType = "mutual_fund" | "stock" | "etf" | "bond" | "commodity" | "other"
export type Category = "Equity" | "Debt" | "Hybrid" | "Commodities"

export interface Asset {
  name: string
  asset_type: AssetType
  isin: string | null
  amc: string | null
  category: Category | null
  sub_category: string | null
  folio: string | null
  units: number
  invested_value_inr: number
  current_value_inr: number
  xirr_pct: number | null
  pnl_inr: number
  pnl_pct: number
}

export interface PortfolioSummary {
  total_invested_inr: number
  total_current_inr: number
  total_pnl_inr: number
  total_pnl_pct: number
  overall_xirr_pct: number | null
  asset_count: number
  statement_date: string | null
}

export interface NormalizedHoldings {
  holder_name: string | null
  source_format: string
  summary: PortfolioSummary
  assets: Asset[]
  parser_warnings: string[]
}

export interface KPIs {
  invested_inr: number
  current_inr: number
  equity_pct: number
  debt_pct: number
  overall_xirr_pct: number | null
  asset_count: number
}

export interface AllocationSlice {
  label: string
  value_inr: number
  pct: number
}

export interface XirrEntry {
  name: string
  xirr_pct: number
  color: "positive" | "negative"
}

export interface CategoryPerformance {
  category: string
  pnl_inr: number
  cagr_pct: number | null
}

export interface ParseAndComputeResponse {
  normalized: NormalizedHoldings
  kpis: KPIs
  allocation: AllocationSlice[]
  xirr_by_fund: XirrEntry[]
  category_performance: CategoryPerformance[]
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message)
  }
}

export async function parseAndCompute(file: File): Promise<ParseAndComputeResponse> {
  const fd = new FormData()
  fd.append("file", file)
  const r = await fetch("/api/parse-and-compute", { method: "POST", body: fd })
  if (!r.ok) {
    let detail: unknown = null
    try {
      const body = await r.json()
      detail = body.detail
      throw new ApiError(r.status, body.detail?.error || `HTTP ${r.status}`, detail)
    } catch (e) {
      if (e instanceof ApiError) throw e
      throw new ApiError(r.status, `HTTP ${r.status}`)
    }
  }
  return r.json()
}
```

- [ ] **Step 3: Create `task4_open/frontend/lib/store.ts`**

```typescript
import { create } from "zustand"
import type { ParseAndComputeResponse } from "./api"

interface PortfolioState {
  data: ParseAndComputeResponse | null
  setData: (d: ParseAndComputeResponse | null) => void
  clear: () => void
}

export const usePortfolio = create<PortfolioState>((set) => ({
  data: null,
  setData: (d) => set({ data: d }),
  clear: () => set({ data: null }),
}))
```

- [ ] **Step 4: Create `task4_open/frontend/lib/theme.ts`**

```typescript
/** Color tokens matching tailwind.config.ts + globals.css. Used for chart colors. */
export const colors = {
  bg: "#13110f",
  fg: "#efe8da",
  fgSoft: "#a8a08a",
  rule: "#2a2620",
  ruleSoft: "#1f1c18",
  muted: "#8a8275",
  mutedDeep: "#6a6258",
  mutedDeeper: "#5a5240",
  brass: "#a88b4a",
  brassBright: "#c9a86a",
  oxblood: "#c97a6f",
} as const

/** Donut segment palette — rotates these tones for category slices. */
export const donutPalette = [
  colors.brassBright,
  colors.brass,
  colors.muted,
  colors.mutedDeep,
  colors.mutedDeeper,
  colors.fgSoft,
] as const
```

- [ ] **Step 5: Create `task4_open/frontend/vitest.config.ts`**

```typescript
import { defineConfig } from "vitest/config"
import react from "@vitejs/plugin-react"
import path from "path"

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
})
```

- [ ] **Step 6: Create `task4_open/frontend/vitest.setup.ts`**

```typescript
import "@testing-library/jest-dom/vitest"
```

- [ ] **Step 7: Create `task4_open/frontend/__tests__/format.test.ts`**

```typescript
import { describe, expect, test } from "vitest"
import { formatINR, formatPct } from "@/lib/format"

describe("formatINR", () => {
  test("formats 10000000 as Indian grouping", () => {
    expect(formatINR(10000000)).toBe("1,00,00,000")
  })
  test("formats 80000 with thousand separator", () => {
    expect(formatINR(80000)).toBe("80,000")
  })
  test("formats small numbers without separators", () => {
    expect(formatINR(500)).toBe("500")
  })
  test("formats negative numbers with sign prefix", () => {
    expect(formatINR(-12345)).toBe("-12,345")
  })
  test("formats 0", () => {
    expect(formatINR(0)).toBe("0")
  })
})

describe("formatPct", () => {
  test("default no sign for positive", () => {
    expect(formatPct(8.0)).toBe("8.00%")
  })
  test("withSign adds + for positive", () => {
    expect(formatPct(8.0, true)).toBe("+8.00%")
  })
  test("negative always has - regardless of withSign", () => {
    expect(formatPct(-3.21, true)).toBe("-3.21%")
  })
})
```

- [ ] **Step 8: Add test script to `package.json` and run**

In `task4_open/frontend/package.json`, find the `scripts` block and ensure these are present:

```json
"scripts": {
  "dev": "next dev --turbopack",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "test": "vitest run",
  "test:watch": "vitest",
  "test:e2e": "playwright test"
}
```

Then run:

```bash
cd task4_open/frontend && npm test && cd ../..
```

Expected: 8 tests pass.

---

## Task 18: Components — KpiCard + CategoryCard + StubTab + tests

**Files:**
- Create: `task4_open/frontend/components/KpiCard.tsx`
- Create: `task4_open/frontend/components/CategoryCard.tsx`
- Create: `task4_open/frontend/components/StubTab.tsx`
- Create: `task4_open/frontend/__tests__/KpiCard.test.tsx`
- Create: `task4_open/frontend/__tests__/CategoryCard.test.tsx`
- Create: `task4_open/frontend/__tests__/StubTab.test.tsx`

- [ ] **Step 1: Create `task4_open/frontend/components/KpiCard.tsx`**

```tsx
interface KpiCardProps {
  label: string
  value: string
  subline?: string
}

export function KpiCard({ label, value, subline }: KpiCardProps) {
  return (
    <div className="border border-rule bg-rule-soft/30 px-5 py-4">
      <div className="font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        {label}
      </div>
      <div className="mt-2 font-mono text-2xl text-fg tabular-nums">
        {value}
      </div>
      {subline && (
        <div className="mt-1 font-mono text-xs text-fg-soft tabular-nums">
          {subline}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create `task4_open/frontend/components/CategoryCard.tsx`**

```tsx
interface CategoryCardProps {
  category: string
  pnlInr: string
  cagrPct: string | null
  isPositive: boolean
}

export function CategoryCard({ category, pnlInr, cagrPct, isPositive }: CategoryCardProps) {
  const accent = isPositive ? "border-l-brass" : "border-l-oxblood"
  const valueColor = isPositive ? "text-brass-bright" : "text-oxblood"
  return (
    <div className={`border border-rule border-l-2 ${accent} bg-rule-soft/30 px-5 py-4`}>
      <div className="font-serif text-base text-fg">{category}</div>
      <div className="mt-3 flex justify-between font-mono text-sm">
        <span className="text-muted-deep">P&amp;L</span>
        <span className={`tabular-nums ${valueColor}`}>{pnlInr}</span>
      </div>
      {cagrPct !== null && (
        <div className="mt-1 flex justify-between font-mono text-sm">
          <span className="text-muted-deep">CAGR</span>
          <span className={`tabular-nums ${valueColor}`}>{cagrPct}</span>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Create `task4_open/frontend/components/StubTab.tsx`**

```tsx
import { Lock } from "lucide-react"

interface StubTabProps {
  task: "4b" | "4c"
  description: string
}

export function StubTab({ task, description }: StubTabProps) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="max-w-md border border-rule bg-rule-soft/30 px-8 py-10 text-center">
        <Lock className="mx-auto h-8 w-8 text-muted-deep" />
        <div className="mt-4 font-mono text-xs uppercase tracking-[0.22em] text-brass">
          Coming in Task {task}
        </div>
        <p className="mt-3 font-serif text-sm leading-relaxed text-fg-soft">
          {description}
        </p>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create `task4_open/frontend/__tests__/KpiCard.test.tsx`**

```tsx
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { KpiCard } from "@/components/KpiCard"

describe("KpiCard", () => {
  test("renders label and value", () => {
    render(<KpiCard label="INVESTED" value="₹41,49,792" />)
    expect(screen.getByText("INVESTED")).toBeInTheDocument()
    expect(screen.getByText("₹41,49,792")).toBeInTheDocument()
  })
  test("renders subline when provided", () => {
    render(<KpiCard label="CURRENT" value="₹44,81,647" subline="XIRR 4.71%" />)
    expect(screen.getByText("XIRR 4.71%")).toBeInTheDocument()
  })
  test("does not render subline when omitted", () => {
    render(<KpiCard label="EQUITY" value="64.2%" />)
    expect(screen.queryByText(/XIRR/)).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 5: Create `task4_open/frontend/__tests__/CategoryCard.test.tsx`**

```tsx
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { CategoryCard } from "@/components/CategoryCard"

describe("CategoryCard", () => {
  test("renders positive category with brass accent", () => {
    const { container } = render(
      <CategoryCard category="Flexi Cap" pnlInr="+₹1,77,213" cagrPct="+6.64%" isPositive />,
    )
    expect(screen.getByText("Flexi Cap")).toBeInTheDocument()
    expect(screen.getByText("+₹1,77,213")).toBeInTheDocument()
    expect(container.querySelector(".border-l-brass")).toBeTruthy()
  })
  test("renders negative category with oxblood accent", () => {
    const { container } = render(
      <CategoryCard category="Mid Cap" pnlInr="-₹3,888" cagrPct="-0.68%" isPositive={false} />,
    )
    expect(container.querySelector(".border-l-oxblood")).toBeTruthy()
  })
  test("hides CAGR row when null", () => {
    render(<CategoryCard category="X" pnlInr="₹0" cagrPct={null} isPositive />)
    expect(screen.queryByText(/CAGR/)).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 6: Create `task4_open/frontend/__tests__/StubTab.test.tsx`**

```tsx
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { StubTab } from "@/components/StubTab"

describe("StubTab", () => {
  test("shows the task label and description", () => {
    render(<StubTab task="4b" description="Nifty trend + market news will land here." />)
    expect(screen.getByText(/Coming in Task 4b/)).toBeInTheDocument()
    expect(screen.getByText(/Nifty trend/)).toBeInTheDocument()
  })
})
```

- [ ] **Step 7: Run tests**

```bash
cd task4_open/frontend && npm test && cd ../..
```

Expected: 15 passed (8 from format + 3 KpiCard + 3 CategoryCard + 1 StubTab).

---

## Task 19: Components — AllocationDonut + XirrBarChart + tests

**Files:**
- Create: `task4_open/frontend/components/AllocationDonut.tsx`
- Create: `task4_open/frontend/components/XirrBarChart.tsx`
- Create: `task4_open/frontend/__tests__/AllocationDonut.test.tsx`
- Create: `task4_open/frontend/__tests__/XirrBarChart.test.tsx`

- [ ] **Step 1: Create `task4_open/frontend/components/AllocationDonut.tsx`**

```tsx
"use client"
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts"
import { colors, donutPalette } from "@/lib/theme"
import { formatINR } from "@/lib/format"

interface AllocationDonutProps {
  slices: { label: string; value_inr: number; pct: number }[]
  totalInr: number
}

export function AllocationDonut({ slices, totalInr }: AllocationDonutProps) {
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        Allocation
      </div>
      <div className="relative h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={slices}
              dataKey="value_inr"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="90%"
              stroke={colors.bg}
              strokeWidth={2}
            >
              {slices.map((_, i) => (
                <Cell key={i} fill={donutPalette[i % donutPalette.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <div className="font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep">Total</div>
          <div className="font-mono text-lg text-fg tabular-nums">₹{formatINR(totalInr)}</div>
        </div>
      </div>
      <ul className="mt-4 space-y-1 font-mono text-xs">
        {slices.map((s, i) => (
          <li key={s.label} className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-fg-soft">
              <span
                className="inline-block h-2.5 w-2.5"
                style={{ background: donutPalette[i % donutPalette.length] }}
              />
              {s.label}
            </span>
            <span className="tabular-nums text-muted">{s.pct.toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

- [ ] **Step 2: Create `task4_open/frontend/components/XirrBarChart.tsx`**

```tsx
"use client"
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts"
import { colors } from "@/lib/theme"

interface XirrBarChartProps {
  entries: { name: string; xirr_pct: number; color: "positive" | "negative" }[]
}

export function XirrBarChart({ entries }: XirrBarChartProps) {
  const height = Math.max(280, entries.length * 28)
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        XIRR by Fund
      </div>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={entries} layout="vertical" margin={{ left: 10, right: 40, top: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="name"
              width={170}
              tick={{ fill: colors.fgSoft, fontSize: 12, fontFamily: "var(--font-fraunces)" }}
              axisLine={false}
              tickLine={false}
            />
            <Bar dataKey="xirr_pct" radius={[0, 2, 2, 0]} label={{ position: "right", fill: colors.fg, fontSize: 11, fontFamily: "var(--font-geist-mono)", formatter: (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%` }}>
              {entries.map((e, i) => (
                <Cell key={i} fill={e.color === "positive" ? colors.brass : colors.oxblood} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create `task4_open/frontend/__tests__/AllocationDonut.test.tsx`**

```tsx
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { AllocationDonut } from "@/components/AllocationDonut"

describe("AllocationDonut", () => {
  test("renders header and total", () => {
    render(
      <AllocationDonut
        slices={[
          { label: "Flexi Cap", value_inr: 1000000, pct: 60 },
          { label: "Gilt", value_inr: 666666, pct: 40 },
        ]}
        totalInr={1666666}
      />,
    )
    expect(screen.getByText("Allocation")).toBeInTheDocument()
    expect(screen.getByText("₹16,66,666")).toBeInTheDocument()
  })
  test("lists each slice in the legend", () => {
    render(
      <AllocationDonut
        slices={[
          { label: "Flexi Cap", value_inr: 100, pct: 50 },
          { label: "Gilt", value_inr: 100, pct: 50 },
        ]}
        totalInr={200}
      />,
    )
    expect(screen.getByText("Flexi Cap")).toBeInTheDocument()
    expect(screen.getByText("Gilt")).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Create `task4_open/frontend/__tests__/XirrBarChart.test.tsx`**

```tsx
import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { XirrBarChart } from "@/components/XirrBarChart"

describe("XirrBarChart", () => {
  test("renders header", () => {
    render(<XirrBarChart entries={[{ name: "PPFCF", xirr_pct: 10.22, color: "positive" }]} />)
    expect(screen.getByText("XIRR by Fund")).toBeInTheDocument()
  })
  test("includes each fund name", () => {
    render(
      <XirrBarChart
        entries={[
          { name: "Top Fund", xirr_pct: 10, color: "positive" },
          { name: "Bottom Fund", xirr_pct: -5, color: "negative" },
        ]}
      />,
    )
    expect(screen.getByText("Top Fund")).toBeInTheDocument()
    expect(screen.getByText("Bottom Fund")).toBeInTheDocument()
  })
})
```

- [ ] **Step 5: Run tests**

```bash
cd task4_open/frontend && npm test && cd ../..
```

Expected: 19 passed (15 prior + 2 AllocationDonut + 2 XirrBarChart).

---

## Task 20: Components — FileUpload + TabNav

**Files:**
- Create: `task4_open/frontend/components/FileUpload.tsx`
- Create: `task4_open/frontend/components/TabNav.tsx`

- [ ] **Step 1: Create `task4_open/frontend/components/FileUpload.tsx`**

```tsx
"use client"
import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Upload } from "lucide-react"
import { ApiError, parseAndCompute } from "@/lib/api"
import { usePortfolio } from "@/lib/store"

const PHASES = [
  "Reading statement...",
  "Analysing with Claude...",
  "Computing metrics...",
]

export function FileUpload() {
  const router = useRouter()
  const setData = usePortfolio((s) => s.setData)
  const [busy, setBusy] = useState(false)
  const [phase, setPhase] = useState<string>("")

  const onDrop = useCallback(async (files: File[]) => {
    if (files.length === 0) return
    const file = files[0]
    setBusy(true)
    let phaseIdx = 0
    setPhase(PHASES[0])
    const phaseTimer = setInterval(() => {
      phaseIdx = Math.min(phaseIdx + 1, PHASES.length - 1)
      setPhase(PHASES[phaseIdx])
    }, 1500)

    try {
      const data = await parseAndCompute(file)
      setData(data)
      router.push("/dashboard")
    } catch (e) {
      const message = e instanceof ApiError
        ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
        : (e as Error).message
      toast.error(message)
    } finally {
      clearInterval(phaseTimer)
      setBusy(false)
      setPhase("")
    }
  }, [router, setData])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "application/pdf": [".pdf"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
    disabled: busy,
  })

  return (
    <div
      {...getRootProps()}
      className={`flex min-h-[280px] cursor-pointer flex-col items-center justify-center border-2 border-dashed border-rule bg-rule-soft/20 px-10 py-12 transition-colors ${
        isDragActive ? "border-brass" : "hover:border-brass-bright"
      } ${busy ? "cursor-wait opacity-60" : ""}`}
    >
      <input {...getInputProps()} />
      <Upload className="h-10 w-10 text-brass" />
      {busy ? (
        <p className="mt-6 font-mono text-sm text-fg-soft">{phase}</p>
      ) : (
        <>
          <p className="mt-6 font-serif text-lg text-fg">
            {isDragActive ? "Drop your statement..." : "Drop your holdings statement"}
          </p>
          <p className="mt-2 font-mono text-xs uppercase tracking-[0.22em] text-muted-deep">
            xlsx · xls · pdf · png · jpg
          </p>
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create `task4_open/frontend/components/TabNav.tsx`**

```tsx
"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"

const TABS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/holdings", label: "Holdings" },
  { href: "/dashboard/market", label: "Market" },
  { href: "/dashboard/rebalance", label: "Rebalance" },
]

export function TabNav() {
  const pathname = usePathname()
  return (
    <nav className="border-b border-rule">
      <div className="mx-auto flex max-w-6xl gap-8 px-6">
        {TABS.map((t) => {
          const active = pathname === t.href
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`relative py-4 font-mono text-xs uppercase tracking-[0.22em] transition-colors ${
                active ? "text-brass" : "text-muted-deep hover:text-fg-soft"
              }`}
            >
              {t.label}
              {active && <span className="absolute bottom-[-1px] left-0 right-0 h-px bg-brass" />}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
```

(No tests for these two — FileUpload involves router/store/API mocking that's heavy for marginal value; the Playwright smoke test in Task 24 covers the upload flow end-to-end. TabNav is trivial wrapping of Next.js Link.)

---

## Task 21: Pages — landing (`/`) + dashboard layout + Overview tab

**Files:**
- Modify: `task4_open/frontend/app/page.tsx`
- Create: `task4_open/frontend/app/dashboard/layout.tsx`
- Create: `task4_open/frontend/app/dashboard/page.tsx`

- [ ] **Step 1: Replace `task4_open/frontend/app/page.tsx`**

```tsx
import Image from "next/image"
import { FileUpload } from "@/components/FileUpload"

export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl px-6 pt-20 pb-16">
      <div className="mb-12 flex items-center gap-3">
        <Image src="/timecell-logo.png" alt="TimeCell" width={28} height={28} className="opacity-90" />
        <span className="font-mono text-xs uppercase tracking-[0.22em] text-brass">TimeCell</span>
      </div>
      <h1 className="font-serif text-4xl leading-tight text-fg">
        Portfolio Intelligence Dashboard
      </h1>
      <p className="mt-3 font-serif text-lg text-fg-soft">
        Upload your holdings statement — any format, any broker. Claude reads it,
        normalizes it, and renders the picture.
      </p>
      <div className="mt-12">
        <FileUpload />
      </div>
    </main>
  )
}
```

- [ ] **Step 2: Create `task4_open/frontend/app/dashboard/layout.tsx`**

```tsx
"use client"
import { useEffect } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { TabNav } from "@/components/TabNav"
import { usePortfolio } from "@/lib/store"
import { formatINR, formatPct } from "@/lib/format"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const data = usePortfolio((s) => s.data)

  useEffect(() => {
    if (!data) router.replace("/")
  }, [data, router])

  if (!data) return null

  const { normalized, kpis } = data
  const dailyChange = normalized.summary.total_pnl_inr
  const dailyPct = normalized.summary.total_pnl_pct

  return (
    <div>
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <Image src="/timecell-logo.png" alt="TimeCell" width={22} height={22} className="opacity-90" />
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-brass">TimeCell</span>
          </div>
          <div className="text-right">
            <div className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
              Portfolio Intelligence Report
            </div>
            <div className="mt-0.5 font-serif text-base text-fg">
              {normalized.holder_name || "Portfolio"}
            </div>
            <div className="mt-1 font-mono text-sm text-fg tabular-nums">
              ₹{formatINR(kpis.current_inr)}
            </div>
            <div
              className={`font-mono text-xs tabular-nums ${
                dailyChange >= 0 ? "text-brass-bright" : "text-oxblood"
              }`}
            >
              {dailyChange >= 0 ? "+" : ""}₹{formatINR(Math.abs(dailyChange))} ({formatPct(dailyPct, true)})
            </div>
          </div>
        </div>
      </header>
      <TabNav />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  )
}
```

- [ ] **Step 3: Create `task4_open/frontend/app/dashboard/page.tsx` (Overview tab)**

```tsx
"use client"
import { AllocationDonut } from "@/components/AllocationDonut"
import { CategoryCard } from "@/components/CategoryCard"
import { KpiCard } from "@/components/KpiCard"
import { XirrBarChart } from "@/components/XirrBarChart"
import { formatINR, formatPct } from "@/lib/format"
import { usePortfolio } from "@/lib/store"

export default function OverviewPage() {
  const data = usePortfolio((s) => s.data)
  if (!data) return null

  const { kpis, allocation, xirr_by_fund, category_performance } = data
  const equityValue = kpis.current_inr * (kpis.equity_pct / 100)
  const debtValue = kpis.current_inr * (kpis.debt_pct / 100)

  return (
    <div className="space-y-6">
      {/* KPI grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Invested"
          value={`₹${formatINR(kpis.invested_inr)}`}
          subline={`${kpis.asset_count} ${kpis.asset_count === 1 ? "scheme" : "schemes"}`}
        />
        <KpiCard
          label="Current"
          value={`₹${formatINR(kpis.current_inr)}`}
          subline={kpis.overall_xirr_pct !== null ? `XIRR ${formatPct(kpis.overall_xirr_pct)}` : undefined}
        />
        <KpiCard
          label="Equity"
          value={`${kpis.equity_pct.toFixed(1)}%`}
          subline={`₹${formatINR(equityValue)}`}
        />
        <KpiCard
          label="Debt"
          value={`${kpis.debt_pct.toFixed(1)}%`}
          subline={`₹${formatINR(debtValue)}`}
        />
      </div>

      {/* Donut + XIRR row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <AllocationDonut slices={allocation} totalInr={kpis.current_inr} />
        </div>
        <div className="lg:col-span-2">
          <XirrBarChart entries={xirr_by_fund} />
        </div>
      </div>

      {/* Category performance grid */}
      <div>
        <h2 className="mb-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
          Category Performance
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {category_performance.map((c) => (
            <CategoryCard
              key={c.category}
              category={c.category}
              pnlInr={`${c.pnl_inr >= 0 ? "+" : ""}₹${formatINR(Math.abs(c.pnl_inr))}`}
              cagrPct={c.cagr_pct !== null ? formatPct(c.cagr_pct, true) : null}
              isPositive={c.pnl_inr >= 0}
            />
          ))}
        </div>
      </div>

      {/* Parser warnings (only shown if any) */}
      {data.normalized.parser_warnings.length > 0 && (
        <details className="border border-rule bg-rule-soft/30 p-4">
          <summary className="cursor-pointer font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
            Parser notes ({data.normalized.parser_warnings.length})
          </summary>
          <ul className="mt-3 space-y-1 font-mono text-xs text-fg-soft">
            {data.normalized.parser_warnings.map((w, i) => (
              <li key={i}>• {w}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
```

---

## Task 22: Stub tab pages — holdings + market + rebalance

**Files:**
- Create: `task4_open/frontend/app/dashboard/holdings/page.tsx`
- Create: `task4_open/frontend/app/dashboard/market/page.tsx`
- Create: `task4_open/frontend/app/dashboard/rebalance/page.tsx`

- [ ] **Step 1: Create `task4_open/frontend/app/dashboard/holdings/page.tsx`**

```tsx
import { StubTab } from "@/components/StubTab"

export default function HoldingsStubPage() {
  return (
    <StubTab
      task="4c"
      description="Per-fund stock breakdown and the fund-overlap matrix will land here. Sourced from AMFI monthly disclosures keyed on ISIN."
    />
  )
}
```

- [ ] **Step 2: Create `task4_open/frontend/app/dashboard/market/page.tsx`**

```tsx
import { StubTab } from "@/components/StubTab"

export default function MarketStubPage() {
  return (
    <StubTab
      task="4b"
      description="Nifty 50 trend (yfinance, reused from Task 2) and current market news will land here."
    />
  )
}
```

- [ ] **Step 3: Create `task4_open/frontend/app/dashboard/rebalance/page.tsx`**

```tsx
import { StubTab } from "@/components/StubTab"

export default function RebalanceStubPage() {
  return (
    <StubTab
      task="4b"
      description="Anthropic Sonnet agent loop with tool calls — gives rebalancing recommendations grounded in your portfolio + Nifty + news context."
    />
  )
}
```

---

## Task 23: next.config.js + Makefile + ensure dev environment runs

**Files:**
- Modify: `task4_open/frontend/next.config.js` (or `next.config.ts` — whichever the scaffold created)
- Create: `task4_open/Makefile`

- [ ] **Step 1: Add API rewrite to `task4_open/frontend/next.config.js` or `next.config.ts`**

If the scaffold created `next.config.ts`, replace its contents with:

```typescript
import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ]
  },
}

export default nextConfig
```

If it created `next.config.js`, replace with:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ]
  },
}

module.exports = nextConfig
```

- [ ] **Step 2: Create `task4_open/Makefile`**

```makefile
.PHONY: install install-backend install-frontend dev dev-backend dev-frontend test test-backend test-frontend test-e2e clean

install: install-backend install-frontend

install-backend:
	pip install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install --no-fund --no-audit
	cd frontend && npx playwright install chromium

dev:
	@echo "Starting backend on :8000 + frontend on :3000..."
	@$(MAKE) -j 2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest -v

test-frontend:
	cd frontend && npm test

test-e2e:
	cd frontend && npm run test:e2e

clean:
	find backend -name __pycache__ -exec rm -rf {} +
	rm -rf backend/.pytest_cache backend/.ruff_cache
	rm -rf frontend/.next frontend/test-results frontend/playwright-report
```

- [ ] **Step 3: Sanity check — run frontend tests**

```bash
make -C task4_open test-frontend
```

Expected: 19 tests pass.

- [ ] **Step 4: Sanity check — backend tests still pass**

```bash
make -C task4_open test-backend
```

Expected: 28 tests pass (unchanged from Task 12).

---

## Task 24: Playwright smoke test (gated)

**Files:**
- Create: `task4_open/frontend/playwright.config.ts`
- Create: `task4_open/frontend/e2e/upload.spec.ts`

- [ ] **Step 1: Create `task4_open/frontend/playwright.config.ts`**

```typescript
import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
})
```

- [ ] **Step 2: Create `task4_open/frontend/e2e/upload.spec.ts`**

```typescript
import { test, expect } from "@playwright/test"
import path from "path"

test("upload a sample statement, see Overview tab render", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByText("Portfolio Intelligence Dashboard")).toBeVisible()

  const samplePath = path.resolve(
    __dirname,
    "../../backend/samples/sample_zerodha.xlsx",
  )
  // Upload via the file input (set programmatically — bypasses dropzone UI)
  await page.setInputFiles('input[type="file"]', samplePath)

  // Wait up to 60s for the API round-trip + render
  await expect(page.locator("nav a", { hasText: "Overview" }).first()).toBeVisible({ timeout: 60_000 })
  await expect(page.getByText("Allocation")).toBeVisible()
  await expect(page.getByText("XIRR by Fund")).toBeVisible()
  await expect(page.getByText("Category Performance")).toBeVisible()
})
```

- [ ] **Step 3: Run the smoke test (requires both servers running)**

In one terminal: `make -C task4_open dev`. Wait until you see "Ready in N ms" + uvicorn running.

In another terminal:

```bash
make -C task4_open test-e2e
```

Expected: 1 test passes. Stop the dev servers (Ctrl+C in the first terminal) when done.

---

## Task 25: Manual acceptance — 8 spec scenarios end-to-end

**Files:** none changed.

**Prerequisite:** `.env` at repo root has `ANTHROPIC_API_KEY` set (from Task 3 setup).

- [ ] **Step 1: Start both servers**

```bash
make -C task4_open dev
```

Wait for both lines: `[backend] Uvicorn running on http://0.0.0.0:8000` AND `[frontend] Ready in N ms`.

- [ ] **Step 2: Open browser to `http://localhost:3000`** — verify the landing page renders with the Ledger palette (warm dark background, brass accents, Fraunces serif heading, Geist Mono labels).

- [ ] **Step 3: Drop `sample_zerodha.xlsx` (or any of the 3 samples) on the dropzone** — verify:
  - Phase indicator cycles ("Reading statement..." → "Analysing with Claude..." → "Computing metrics...")
  - Page navigates to `/dashboard` showing the Overview tab
  - 4 KPI cards visible (Invested, Current, Equity, Debt) with non-zero values
  - Allocation donut renders with at least 2 slices and a legend
  - XIRR by Fund bar chart renders with brass + oxblood bars
  - Category Performance grid shows at least one card

- [ ] **Step 4: Click each tab (Holdings, Market, Rebalance)** — verify each shows a "Coming in Task 4b/4c" stub card with a Lock icon and a description.

- [ ] **Step 5: Click Overview tab** — verify it returns to the rendered Overview.

- [ ] **Step 6: Refresh the page (Cmd+R)** — verify it redirects to `/` (stateless), the upload widget is visible again.

- [ ] **Step 7: Drop a clearly-bad file (e.g., `echo "not a holdings file" > /tmp/bad.xlsx`)** — verify a toast error appears with an informative message; the app does NOT crash; the dropzone is usable again.

- [ ] **Step 8: Inspect backend stderr** — verify you see `[parser] estimated cost: $...` and `[parser] actual cost: $...` lines for each upload attempt. Verify `ls ~/.cache/timecell-task4/` shows a `usage-YYYY-MM-DD.json` file with a positive number.

- [ ] **Step 9: Stop the dev servers** (Ctrl+C in the `make dev` terminal).

If all 9 manual steps pass, 4a is functionally complete.

---

## Task 26: Commit frontend + Makefile + per-task README + root README

**Files:**
- Create: `task4_open/README.md`
- Modify: `README.md` (root)

- [ ] **Step 1: Create `task4_open/README.md`**

```markdown
# Task 4 — Portfolio Intelligence Dashboard

A FastAPI + Next.js webapp that takes any mutual-fund or stock holdings statement (Groww xlsx,
Camsonline MHTML, Zerodha multi-sheet xlsx, PDFs, even screenshots) and renders a portfolio
overview. Built incrementally across three sub-tasks:

| Sub-task | Status | Tab(s) added |
|---|---|---|
| **4a** (this PR) | ✅ shipped | Shell + parser + Overview |
| **4b** (planned) | stubbed | Market + Rebalance (Anthropic agent loop) |
| **4c** (planned) | stubbed | Holdings + Fund-overlap matrix |

## What 4a ships

- Webapp shell (Next.js + FastAPI) with timecell.ai's Ledger theme
- LLM-normalized parser: any uploaded file → Anthropic Haiku 4.5 → canonical Pydantic schema
- Overview tab: KPI cards + allocation donut + XIRR-by-fund bar chart + category-performance cards
- Three other tabs stubbed with "Coming in 4b/4c" placeholders
- Three layers of cost guardrails on the parser (token cap, cost log, daily budget ceiling)
- Stateless single-user demo — no DB, no auth

## Setup + run

Requires Python 3.10+, Node 20+, and `ANTHROPIC_API_KEY` in `.env` at the repo root.

```bash
# One-time install (Python deps + npm packages + Playwright browser)
make -C task4_open install

# Start backend (:8000) + frontend (:3000) in parallel
make -C task4_open dev
```

Then open http://localhost:3000, drop one of `task4_open/backend/samples/*.xlsx` on the dropzone, and the Overview tab renders.

## Testing

```bash
make -C task4_open test         # backend (28) + frontend (19)
make -C task4_open test-e2e     # Playwright smoke test (needs both servers running)
```

## Sample data

`backend/samples/` ships three redacted holdings statements covering the three most common Indian
broker formats. Names, PANs, phone numbers, and Client IDs are synthetic; numeric data is
preserved verbatim from real exports so end-to-end testing reflects realistic shapes.

| File | Format | Holder (synthetic) |
|---|---|---|
| `sample_groww.xlsx` | Groww xlsx (clean tabular) | Test User A |
| `sample_camsonline.xls` | Camsonline MHTML (HTML-disguised xls) | Test User B |
| `sample_zerodha.xlsx` | Zerodha Console (multi-sheet) | (uses Client ID `TEST01`) |

The original (PII-bearing) versions live in `task4_open/` itself and are gitignored — the redacted
copies in `backend/samples/` are what gets committed and what tests run against.

## Cost guardrails

The parser's three defenses against budget drain on the Anthropic API:

1. **30K input-token cap** — pathological uploads get truncated with a warning, not a runaway cost
2. **Per-call cost log to stderr** — `[parser] actual cost: $0.024 (input: 8200 tokens, output: 1240)`
3. **Daily budget ceiling** — env var `MAX_DAILY_LLM_USD` (default $2/day, opt out with `=disabled`),
   tracked atomically in `~/.cache/timecell-task4/usage-YYYY-MM-DD.json`

## Provider chosen + why

- **Parser:** Haiku 4.5 — structured JSON extraction is its sweet spot; 3-5× cheaper than Sonnet on
  this task with no measurable quality drop. The retry-on-validation-failure loop catches the rare
  malformed JSON without escalating to Sonnet.
- **Theme:** timecell.ai's Ledger palette — warm dark background, brass accents, Fraunces serif +
  Geist Mono labels. Pulled live from the site's published CSS during spec-writing.

## What didn't work (or got rejected during brainstorming)

- **Per-format parser registry** — three formats today, more tomorrow; doesn't fit the AI-task
  theme. LLM-normalization handles arbitrary formats including ones we've never seen, including
  PDFs and image screenshots.
- **Browser localStorage persistence** — adds UX complexity for marginal value in a graded demo.
  Stateless: refresh = re-upload.
- **Fund overlap analysis in 4a** — needs stock-level fund composition data (AMFI monthly
  disclosures), which is its own scraping/ingestion project. Deferred to 4c.

## AI tool usage

[Filled in retrospectively after implementation — what Claude Code helped with.]
```

- [ ] **Step 2: Update root `README.md`**

Open `README.md` and replace the `- Task 4 — Open (TBD)` line with:

```markdown
- [Task 4 — Portfolio Intelligence Dashboard (4a: Shell + Parser + Overview)](task4_open/README.md)
```

- [ ] **Step 3: Verify file lists are correct before staging**

```bash
git status --short
```

Expected: `task4_open/Makefile`, `task4_open/README.md`, README.md, and an enormous list of `task4_open/frontend/**` files (most of `node_modules` is gitignored, but app/components/lib/__tests__/etc. should appear).

- [ ] **Step 4: Stage everything frontend + Makefile + READMEs (carefully)**

```bash
git add task4_open/Makefile task4_open/README.md README.md
git add task4_open/frontend/app/
git add task4_open/frontend/components/
git add task4_open/frontend/lib/
git add task4_open/frontend/__tests__/
git add task4_open/frontend/e2e/
git add task4_open/frontend/public/
git add task4_open/frontend/package.json
git add task4_open/frontend/package-lock.json
git add task4_open/frontend/tsconfig.json
git add task4_open/frontend/tailwind.config.ts
git add task4_open/frontend/postcss.config.mjs 2>/dev/null || git add task4_open/frontend/postcss.config.js 2>/dev/null
git add task4_open/frontend/next.config.ts 2>/dev/null || git add task4_open/frontend/next.config.js 2>/dev/null
git add task4_open/frontend/vitest.config.ts
git add task4_open/frontend/vitest.setup.ts
git add task4_open/frontend/playwright.config.ts
git add task4_open/frontend/components.json
git add task4_open/frontend/next-env.d.ts
git status --short | head -40
```

Expected: only the frontend files + Makefile + READMEs. `node_modules/` and `.next/` should NOT appear.

- [ ] **Step 5: Commit**

```bash
git commit -m "$(cat <<'EOF'
task4a: add Next.js frontend + dev tooling + per-task and root READMEs

Implements the frontend half of Task 4a's dashboard. Next.js (App Router, TS)
with Tailwind + shadcn/ui + Recharts + Lucide + Zustand + sonner, themed end-
to-end with timecell.ai's Ledger palette (warm dark bg, brass + oxblood
accents, Fraunces serif + Geist Mono).

Pages: "/" landing with file dropzone (react-dropzone), "/dashboard" Overview
with KPI grid + allocation donut + XIRR-by-fund bar + category cards,
"/dashboard/{holdings,market,rebalance}" stubs for 4b/4c. Dashboard layout
guards against direct visit with empty store and redirects to "/".

19 Vitest + RTL component tests cover formatINR (Indian-grouping), KpiCard,
CategoryCard, StubTab, AllocationDonut, XirrBarChart. Playwright smoke test
(gated behind npm run test:e2e) uploads sample_zerodha.xlsx end-to-end and
verifies all four Overview sections render.

Makefile gives single-command install + parallel-process dev + test runners.
next.config rewrites /api/* to localhost:8000 to bypass CORS in dev.

Per-task README + root README link complete the spec's deliverables for 4a.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -4
```

Expected: two task4a commits ahead of `2da4b48`.

---

## Task 27: Fill in retrospective AI-usage notes + amend

**Files:**
- Modify: `task4_open/README.md` (replace AI-usage placeholder)

- [ ] **Step 1: Replace the `## AI tool usage` placeholder paragraph**

Open `task4_open/README.md` and replace `[Filled in retrospectively after implementation — what Claude Code helped with.]` with:

```markdown
Built with Claude Code (Opus 4.7) following the `superpowers` chain
(`brainstorming` → `writing-plans` → `subagent-driven-development`). The
brainstorm scoped the project to three sub-tasks (4a/4b/4c) on a shared
webapp shell, locked in FastAPI + Next.js with timecell.ai's Ledger theme,
and chose LLM-normalization over a per-format parser registry — Claude
Haiku 4.5 handles arbitrary holding-statement formats including ones we've
never seen, with retry-on-validation-failure for the rare malformed JSON.

The `claude-api` skill was invoked at implementation time to confirm
`claude-haiku-4-5` as the current latest Haiku model ID. The timecell.ai
theme tokens (Ledger palette colors, Fraunces + Geist Mono fonts, the
ledger-paper backdrop with subtle radial brass glow and 48px rule lines)
were extracted live from the site's published CSS during spec-writing and
baked into `tailwind.config.ts` + `globals.css`.

Three layers of cost guardrails on the parser were a brainstorm decision
specifically because the user has a $25 Anthropic budget shared across all
three sub-tasks: 30K input-token cap with truncation+warning, per-call
cost logging to stderr, and a daily-budget ceiling tracked atomically in a
JSON file under `~/.cache/timecell-task4/`.

The 47-test test suite (28 backend pytest + 19 frontend Vitest) is
deterministic — Anthropic SDK is mocked everywhere; the only live calls
happen during the manual acceptance run against three real sample formats.

Sample data redaction (replacing real names/PANs/phone numbers/Client IDs
with synthetic values while preserving numeric data verbatim) was an
explicit decision recorded in the spec — the repo is public on GitHub so
PII committed once would persist in git history forever.
```

- [ ] **Step 2: Amend the README commit**

```bash
git add task4_open/README.md
git commit --amend --no-edit
git log --oneline | head -4
```

Expected: still two task4a commits ahead of `2da4b48`; the README commit is updated in place.

---

## Task 28: Stop and ask the user about pushing / opening PR

Per the workflow rule (CLAUDE.md Part 1, item 2), do NOT push or open the PR unprompted. Surface to the user:

> "Implementation complete on branch `task4a/dashboard-shell`. Three commits ahead of `main`: spec doc (already at HEAD~2), backend code+tests+samples, then frontend code + Makefile + READMEs. **Tests:** 28 backend pytest + 19 frontend Vitest + 1 Playwright smoke test all pass. **Live verification:** all 3 sample holdings files (Groww, Camsonline, Zerodha) parse end-to-end via real Anthropic Haiku calls; Overview tab renders KPIs + donut + XIRR bar + category cards; stub tabs show 'Coming in 4b/4c' placeholders. **Cost spent:** roughly $0.20 across all live tests (well under the $2/day cap and $25 total budget). Ready to push and open PR #4 for review?"

Wait for explicit user approval before running `git push -u origin task4a/dashboard-shell` or `gh pr create`.

---

## Self-review

**1. Spec coverage:**

| Spec section | Implementation task |
|---|---|
| §Goal — Overview tab + parser + shell | Tasks 4-12 (backend), 15-22 (frontend) |
| §Architecture — FastAPI + Next.js + Haiku 4.5 | Tasks 12 (FastAPI), 15 (Next.js), 6 (Haiku model constant) |
| §Theme — Ledger palette from timecell.ai | Task 16 (curl logo, set CSS variables, font import) |
| §Repo layout | Tasks 1-3 (backend skeleton), 15 (frontend scaffold) |
| §Pydantic schema | Task 4 |
| §`/api/parse-and-compute` + `/api/health` | Task 12 |
| §Parser flow (extract → normalize → compute) | Tasks 5 (extract), 6-9 (normalize), 10-11 (compute) |
| §Normalizer prompt | Task 6 step 1 |
| §Cost guardrails (3 layers) | Task 8 (token cap), Task 9 (budget cache), Task 6 (cost logging — initial; Task 8 confirms) |
| §Frontend pages | Task 21 (landing + dashboard layout + Overview), Task 22 (3 stubs) |
| §Frontend components | Tasks 18 (KPI/Category/Stub), 19 (Donut/Bar), 20 (FileUpload/TabNav) |
| §lib helpers (formatINR, store, api, theme) | Task 17 |
| §Stub tab UX | Task 18 step 3 + Task 22 |
| §Landing page upload flow | Task 20 step 1 (FileUpload) + Task 21 step 1 (page) |
| §Error handling table | Task 12 (HTTP error codes) + Task 20 step 1 (toast) |
| §Backend tests (pytest) | Tasks 4, 5, 7-9, 10-12 |
| §Frontend tests (Vitest + Playwright) | Tasks 17, 18, 19, 24 |
| §Manual acceptance steps | Task 25 |
| §Sample redaction policy | Task 2 |
| §Implementation note: `claude-api` skill | Task 1 step 2 |
| §Implementation note: gitignore originals | Task 2 step 1 |

All sections covered.

**2. Placeholder scan:** The `[Filled in retrospectively after implementation — what Claude Code helped with.]` string in Task 26 step 1 is intentional README content replaced in Task 27. No `TBD`/`TODO`/`add appropriate X` patterns in the plan body itself.

**3. Type consistency:** Backend Pydantic schema (Task 4) names match frontend TS interface (Task 17 step 2). `formatINR` signature is consistent between backend (`_format_inr` in Task 3) and frontend (Task 17 step 1). API endpoint paths (`/api/parse-and-compute`, `/api/health`) consistent across Tasks 12, 17, 20, 23. Color tokens (`brass`, `oxblood`) consistent between Task 16 (CSS), Task 17 step 4 (theme.ts), Tasks 18-19 (component classnames + chart fills). Function names (`extract`, `normalize`, `kpis`, `allocation`, `xirr_by_fund`, `category_performance`) consistent across declaration (Tasks 5, 6, 10, 11), import (Task 12), and test (Tasks 5, 6-9, 10-11, 12).

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-02-task4a-dashboard-shell.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
