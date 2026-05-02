# Task 4a Result Caching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a content-addressed backend cache + Zustand-persisted frontend store so refreshing the dashboard never re-calls the LLM, and re-uploading the same file is instant + free.

**Architecture:** Two independent layers stacked back-to-back. Backend keys responses on `SHA-256(file_bytes + prompt_text + schema_version)` and serves cache hits from `~/.cache/timecell-task4/parse-cache/<key>.json` with a `cached: true` flag. Frontend wraps the existing Zustand store with the `persist` middleware backed by `localStorage`, gates the dashboard's redirect-to-`/` on a hydration flag, and adds three header controls (badge, Re-parse, Upload another).

**Tech Stack:** Python 3.9 / pytest / FastAPI (backend); TypeScript / Next.js / Zustand `persist` middleware / Vitest + RTL (frontend).

**Branch state:** Already on `task4a/result-caching`, off `task4a/dashboard-shell` at `d297469` (spec already committed). Two new commits will land on this branch.

---

## File Structure

### Backend changes
- **Create:** `task4_open/backend/parser/cache.py` (~55 lines) — `cache_key()`, `read_cache()`, `write_cache()`. Pure functions, no FastAPI imports, testable in isolation.
- **Create:** `task4_open/backend/tests/test_cache.py` (~80 lines) — 5 unit tests for the cache module.
- **Modify:** `task4_open/backend/main.py` — add `cached: bool = False` to `ParseAndComputeResponse`; read prompt text once at module top; add `force: bool = False` query param; wrap existing pipeline in cache lookup/write.
- **Modify:** `task4_open/backend/tests/test_main.py` — append 3 new tests covering cache hit / force bypass / no-cache-on-error.

### Frontend changes
- **Modify:** `task4_open/frontend/lib/api.ts` — add `cached: boolean` to `ParseAndComputeResponse`; add `opts: { force?: boolean }` parameter to `parseAndCompute()`.
- **Modify:** `task4_open/frontend/lib/store.ts` — wrap with `persist` middleware backed by `localStorage`; add `lastFile`, `hasHydrated`, `setLastFile`; have `clear()` purge the persisted key.
- **Create:** `task4_open/frontend/__tests__/store.test.ts` (~60 lines) — 3 tests: persist round-trip, clear empties storage, hydration flag flips.
- **Modify:** `task4_open/frontend/components/FileUpload.tsx` — call `setLastFile(file)` after successful parse so Re-parse can re-submit it.
- **Modify:** `task4_open/frontend/app/dashboard/layout.tsx` — gate the redirect on `hasHydrated`; add three header controls (cached badge, Re-parse, Upload another).

### No-touch files
The components (`KpiCard`, `CategoryCard`, `AllocationDonut`, `XirrBarChart`, `TabNav`, stub pages) and the `parser/{extract,normalize,schema}.py` + `metrics/compute.py` modules are not modified. Existing 35 backend + 20 frontend tests must continue to pass.

---

## Task 1: Backend cache module + 5 unit tests

**Files:**
- Create: `task4_open/backend/parser/cache.py`
- Create: `task4_open/backend/tests/test_cache.py`

- [ ] **Step 1: Write the failing tests at `task4_open/backend/tests/test_cache.py`**

```python
"""Tests for parser.cache — pure-function disk cache."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.cache import (
    SCHEMA_VERSION,
    PARSE_CACHE_DIR,
    cache_key,
    read_cache,
    write_cache,
)


def test_cache_key_deterministic_for_same_inputs() -> None:
    k1 = cache_key(b"hello world", "prompt v1")
    k2 = cache_key(b"hello world", "prompt v1")
    assert k1 == k2, f"same inputs should give same key, got {k1!r} vs {k2!r}"
    assert len(k1) == 64, f"sha256 hex digest is 64 chars, got {len(k1)}"


def test_cache_key_changes_when_file_bytes_change() -> None:
    k1 = cache_key(b"hello", "prompt")
    k2 = cache_key(b"world", "prompt")
    assert k1 != k2, "different bytes must give different keys"


def test_cache_key_changes_when_prompt_changes() -> None:
    k1 = cache_key(b"same bytes", "prompt v1")
    k2 = cache_key(b"same bytes", "prompt v2 with edits")
    assert k1 != k2, "prompt edits must invalidate the key"


def test_write_cache_is_atomic_and_readable(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    payload = {"foo": "bar", "n": 42, "nested": {"ok": True}}
    write_cache("abc123", payload)
    files = list(tmp_path.iterdir())
    assert len(files) == 1, f"expected 1 file, got {[f.name for f in files]}"
    assert files[0].name == "abc123.json"
    out = read_cache("abc123")
    assert out == payload, f"round-trip mismatch: {out!r} vs {payload!r}"


def test_read_cache_handles_corrupt_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    p = tmp_path / "deadbeef.json"
    p.write_text("{this is not valid json")
    out = read_cache("deadbeef")
    assert out is None, f"corrupt file should return None, got {out!r}"
    assert not p.exists(), "corrupt file should have been deleted"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/.venv/bin/activate
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/backend
python -m pytest tests/test_cache.py -v
```

Expected: ImportError or ModuleNotFoundError on `from parser.cache import ...`.

- [ ] **Step 3: Create `task4_open/backend/parser/cache.py`**

```python
"""Content-addressed disk cache for parse-and-compute responses."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .normalize import CACHE_DIR

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1"
PARSE_CACHE_DIR = CACHE_DIR / "parse-cache"


def cache_key(file_bytes: bytes, prompt_text: str) -> str:
    """SHA-256 of (file_bytes, prompt_text, SCHEMA_VERSION) joined by NUL bytes."""
    h = hashlib.sha256()
    h.update(file_bytes)
    h.update(b"\x00")
    h.update(prompt_text.encode("utf-8"))
    h.update(b"\x00")
    h.update(SCHEMA_VERSION.encode("utf-8"))
    return h.hexdigest()


def read_cache(key: str) -> dict | None:
    """Returns the cached response dict, or None on miss / corrupt file."""
    p = PARSE_CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text())
        return payload["response"]
    except (json.JSONDecodeError, KeyError, OSError) as e:
        logger.warning("[cache] dropping corrupt entry %s: %s", key[:8], e)
        try:
            p.unlink()
        except OSError:
            pass
        return None


def write_cache(key: str, response_dict: dict) -> None:
    """Atomic write: <key>.json.tmp then rename to <key>.json."""
    PARSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = PARSE_CACHE_DIR / f"{key}.json"
    tmp = p.with_suffix(".json.tmp")
    payload = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "response": response_dict,
    }
    tmp.write_text(json.dumps(payload))
    tmp.replace(p)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_cache.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Run the full backend suite to confirm no regressions**

```bash
python -m pytest tests/ -v
```

Expected: 40 passed (35 existing + 5 new).

---

## Task 2: Wire cache into FastAPI endpoint + 3 added tests

**Files:**
- Modify: `task4_open/backend/main.py`
- Modify: `task4_open/backend/tests/test_main.py`

- [ ] **Step 1: Read the current `parse_and_compute` shape**

Open `task4_open/backend/main.py` and locate the `parse_and_compute` function. The existing structure:
1. Validate filename + extension
2. Stream upload to temp file with size cap
3. `extract(tmp_path)` → catch `ExtractError` → 422
4. `normalize(content)` → catch `BudgetExhausted` → 429, `NormalizationError` → 502, generic → 502
5. Build `ParseAndComputeResponse` with computed metrics
6. tmp file cleanup in `finally`

The cache wraps step 3-5: read bytes once, compute key, look up, return on hit; otherwise run the pipeline and write on success.

- [ ] **Step 2: Add 3 new failing tests at the end of `task4_open/backend/tests/test_main.py`**

Append these tests after the existing `test_parse_and_compute_handles_budget_exhausted`:

```python
def test_parse_and_compute_cache_hit_skips_normalize(tmp_path, monkeypatch) -> None:
    """Two requests with the same file body → normalize called only once."""
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    fake = _fake_normalized()
    with patch("main.normalize", return_value=fake) as mock_norm:
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r1 = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r2 = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["cached"] is False, "first call should be a miss"
    assert r2.json()["cached"] is True, "second call should be a hit"
    assert mock_norm.call_count == 1, \
        f"normalize should run once across two same-file requests, got {mock_norm.call_count}"


def test_parse_and_compute_force_bypasses_cache(tmp_path, monkeypatch) -> None:
    """?force=true skips lookup and re-runs normalize."""
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    fake = _fake_normalized()
    with patch("main.normalize", return_value=fake) as mock_norm:
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r2 = client.post(
                "/api/parse-and-compute?force=true",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r2.status_code == 200
    assert r2.json()["cached"] is False, "force=true must produce a fresh response"
    assert mock_norm.call_count == 2, \
        f"normalize must run on both calls when second uses force, got {mock_norm.call_count}"


def test_parse_and_compute_does_not_cache_on_error(tmp_path, monkeypatch) -> None:
    """NormalizationError → 502 → no file written under PARSE_CACHE_DIR."""
    from parser.normalize import NormalizationError
    monkeypatch.setattr("parser.cache.PARSE_CACHE_DIR", tmp_path)
    err = NormalizationError("boom", attempts=["x", "y"], errors=["e1", "e2"])
    with patch("main.normalize", side_effect=err):
        with open(SAMPLE_DIR / "sample_groww.xlsx", "rb") as f:
            r = client.post(
                "/api/parse-and-compute",
                files={"file": ("sample_groww.xlsx", f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
    assert r.status_code == 502
    cache_files = list(tmp_path.iterdir())
    assert cache_files == [], f"no cache should be written on error, got {cache_files}"
```

- [ ] **Step 3: Run the new tests to verify they fail**

```bash
python -m pytest tests/test_main.py::test_parse_and_compute_cache_hit_skips_normalize tests/test_main.py::test_parse_and_compute_force_bypasses_cache tests/test_main.py::test_parse_and_compute_does_not_cache_on_error -v
```

Expected: 3 failures (no `cached` field in response, `force` query param ignored).

- [ ] **Step 4: Modify `task4_open/backend/main.py`**

Add cache imports and read prompt text once at module top. Find the import block ending in `from metrics.compute import ...` and add immediately after:

```python
from parser.cache import cache_key, read_cache, write_cache
```

Then find the line `MAX_FILE_BYTES = 10 * 1024 * 1024` and add right after it:

```python
PROMPT_TEXT = (Path(__file__).parent / "prompts" / "normalize.txt").read_text()
```

Find the `class ParseAndComputeResponse(BaseModel):` block and add `cached: bool = False` as the last field:

```python
class ParseAndComputeResponse(BaseModel):
    """Full payload returned by /api/parse-and-compute."""
    normalized: NormalizedHoldings
    kpis: KPIs
    allocation: list[AllocationSlice]
    xirr_by_fund: list[XirrEntry]
    category_performance: list[CategoryPerformance]
    cached: bool = False
```

Find the endpoint signature `async def parse_and_compute(file: UploadFile = File(...)) -> ParseAndComputeResponse:` and replace it with:

```python
async def parse_and_compute(
    file: UploadFile = File(...),
    force: bool = False,
) -> ParseAndComputeResponse:
```

Inside the function, locate the streaming-to-tempfile block. The existing code accumulates bytes via `chunk := await file.read(64 * 1024)`. We need to also keep the bytes in memory for the SHA-256 hash. Find the existing block:

```python
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
```

Replace the whole block with:

```python
    file_bytes = bytearray()
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
            file_bytes.extend(chunk)
        tmp_path = Path(tmp.name)

    key = cache_key(bytes(file_bytes), PROMPT_TEXT)
    if not force:
        cached = read_cache(key)
        if cached is not None:
            logger.info("[parser] cache HIT for %s... — $0", key[:8])
            tmp_path.unlink(missing_ok=True)
            cached["cached"] = True
            return ParseAndComputeResponse(**cached)
```

Now find the existing return statement at the bottom of the try block:

```python
        return ParseAndComputeResponse(
            normalized=_n,
            kpis=_k,
            allocation=_a,
            xirr_by_fund=_x,
            category_performance=_c,
        )
```

Replace it with:

```python
        response = ParseAndComputeResponse(
            normalized=_n,
            kpis=_k,
            allocation=_a,
            xirr_by_fund=_x,
            category_performance=_c,
            cached=False,
        )
        try:
            write_cache(key, response.model_dump(mode="json"))
        except OSError as e:
            logger.warning("[cache] write failed for %s...: %s", key[:8], e)
        return response
```

- [ ] **Step 5: Run the new tests to verify they pass**

```bash
python -m pytest tests/test_main.py::test_parse_and_compute_cache_hit_skips_normalize tests/test_main.py::test_parse_and_compute_force_bypasses_cache tests/test_main.py::test_parse_and_compute_does_not_cache_on_error -v
```

Expected: 3 passed.

- [ ] **Step 6: Run the full backend suite**

```bash
python -m pytest tests/ -v
```

Expected: 43 passed (35 original + 5 from Task 1 + 3 from this task).

---

## Task 3: Backend manual smoke — confirm hit/miss/force live

**Files:** none changed.

- [ ] **Step 1: Make sure no stale cache from previous runs interferes**

```bash
rm -rf ~/.cache/timecell-task4/parse-cache
```

- [ ] **Step 2: Start backend in background**

```bash
source /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/.venv/bin/activate
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/backend
uvicorn main:app --port 8001 &
until curl -sf http://localhost:8001/api/health > /dev/null; do sleep 1; done
```

- [ ] **Step 3: First call — confirm MISS**

```bash
curl -s -X POST http://localhost:8001/api/parse-and-compute \
    -F "file=@/Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/backend/samples/sample_groww.xlsx" \
    | python -c "import json,sys; d=json.load(sys.stdin); print('cached:', d['cached']); print('asset_count:', d['kpis']['asset_count'])"
```

Expected: `cached: False`, asset_count > 0. Backend stderr shows the usual `[parser] estimated cost` + `[parser] actual cost` lines.

- [ ] **Step 4: Second call with same file — confirm HIT**

```bash
curl -s -X POST http://localhost:8001/api/parse-and-compute \
    -F "file=@/Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/backend/samples/sample_groww.xlsx" \
    | python -c "import json,sys; d=json.load(sys.stdin); print('cached:', d['cached']); print('asset_count:', d['kpis']['asset_count'])"
```

Expected: `cached: True`, same asset_count. Backend stderr shows `[parser] cache HIT for <8-hex>... — $0`. No `actual cost` line.

- [ ] **Step 5: Third call with `?force=true` — confirm fresh MISS**

```bash
curl -s -X POST 'http://localhost:8001/api/parse-and-compute?force=true' \
    -F "file=@/Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/backend/samples/sample_groww.xlsx" \
    | python -c "import json,sys; d=json.load(sys.stdin); print('cached:', d['cached'])"
```

Expected: `cached: False`. Backend stderr shows a fresh `[parser] actual cost` line.

- [ ] **Step 6: Verify the cache file exists**

```bash
ls -la ~/.cache/timecell-task4/parse-cache/
```

Expected: one `*.json` file (the SHA-256 hex of the Groww sample). No `.tmp` files.

- [ ] **Step 7: Stop the server**

```bash
kill %1 2>/dev/null || true
```

---

## Task 4: First commit — backend cache + tests

**Files:**
- Stage: `task4_open/backend/parser/cache.py`, `task4_open/backend/main.py`, `task4_open/backend/tests/test_cache.py`, `task4_open/backend/tests/test_main.py`

- [ ] **Step 1: Verify what's staged**

```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak
git status --short
```

Expected: 4 files modified/added under `task4_open/backend/`. No frontend files yet.

- [ ] **Step 2: Stage explicitly**

```bash
git add \
    task4_open/backend/parser/cache.py \
    task4_open/backend/main.py \
    task4_open/backend/tests/test_cache.py \
    task4_open/backend/tests/test_main.py
git status --short
```

Expected: only those 4 files under "Changes to be committed".

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
task4a: add backend parse-cache (sha256 keyed, schema-versioned, atomic)

POST /api/parse-and-compute now returns a `cached: bool` flag and accepts
`?force=true` to bypass the cache. Hits are served from
~/.cache/timecell-task4/parse-cache/<sha>.json in <50 ms with $0 LLM
spend; the budget guard never fires on a hit.

Cache key = SHA-256(file_bytes, prompt_text, schema_version) so editing
prompts/normalize.txt or bumping SCHEMA_VERSION invalidates cleanly. Atomic
.tmp+rename writes match the existing daily-budget cache pattern. Corrupt
cache files are detected on read, deleted, and treated as a miss.

Errors (extract failure, budget exhausted, normalize failure) never write a
cache entry — only successful responses are cached.

8 new pytest tests (5 unit + 3 endpoint integration); 43 total backend
tests pass.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -3
```

Expected: new commit on top of `d297469`.

---

## Task 5: Frontend `api.ts` — `cached` field + `force` parameter

**Files:**
- Modify: `task4_open/frontend/lib/api.ts`

- [ ] **Step 1: Add `cached` to the `ParseAndComputeResponse` interface**

In `task4_open/frontend/lib/api.ts`, find:

```typescript
export interface ParseAndComputeResponse {
  normalized: NormalizedHoldings
  kpis: KPIs
  allocation: AllocationSlice[]
  xirr_by_fund: XirrEntry[]
  category_performance: CategoryPerformance[]
}
```

Replace with:

```typescript
export interface ParseAndComputeResponse {
  normalized: NormalizedHoldings
  kpis: KPIs
  allocation: AllocationSlice[]
  xirr_by_fund: XirrEntry[]
  category_performance: CategoryPerformance[]
  cached: boolean
}
```

- [ ] **Step 2: Add `force` parameter to `parseAndCompute()`**

Find:

```typescript
export async function parseAndCompute(file: File): Promise<ParseAndComputeResponse> {
  const fd = new FormData()
  fd.append("file", file)
  const r = await fetch("/api/parse-and-compute", { method: "POST", body: fd })
```

Replace with:

```typescript
export async function parseAndCompute(
  file: File,
  opts: { force?: boolean } = {},
): Promise<ParseAndComputeResponse> {
  const fd = new FormData()
  fd.append("file", file)
  const url = opts.force
    ? "/api/parse-and-compute?force=true"
    : "/api/parse-and-compute"
  const r = await fetch(url, { method: "POST", body: fd })
```

(The rest of the function — error parsing — is unchanged.)

- [ ] **Step 3: Type-check**

```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/frontend
npx tsc --noEmit
```

Expected: no output (clean). Compile errors at this point would be from callers using the old shape — the existing `FileUpload.tsx` calls `parseAndCompute(file)` with no opts, which still type-checks because `opts` defaults to `{}`. The dashboard layout consumes `data.cached` only after Task 8, so no compile error here.

- [ ] **Step 4: Run existing tests to confirm no regression**

```bash
npm test
```

Expected: 20 passed.

---

## Task 6: Frontend store — Zustand `persist` + `lastFile` + `hasHydrated` + 3 tests

**Files:**
- Modify: `task4_open/frontend/lib/store.ts`
- Create: `task4_open/frontend/__tests__/store.test.ts`

- [ ] **Step 1: Write the failing tests at `task4_open/frontend/__tests__/store.test.ts`**

```typescript
import { afterEach, beforeEach, describe, expect, test } from "vitest"
import { usePortfolio } from "@/lib/store"
import type { ParseAndComputeResponse } from "@/lib/api"

const STORAGE_KEY = "timecell-portfolio-v1"

function fakeResponse(): ParseAndComputeResponse {
  return {
    normalized: {
      holder_name: "Alice",
      source_format: "test",
      summary: {
        total_invested_inr: 100,
        total_current_inr: 110,
        total_pnl_inr: 10,
        total_pnl_pct: 10,
        overall_xirr_pct: null,
        asset_count: 0,
        statement_date: null,
      },
      assets: [],
      parser_warnings: [],
    },
    kpis: { invested_inr: 100, current_inr: 110, equity_pct: 0, debt_pct: 0, overall_xirr_pct: null, asset_count: 0 },
    allocation: [],
    xirr_by_fund: [],
    category_performance: [],
    cached: false,
  }
}

beforeEach(() => {
  localStorage.clear()
  usePortfolio.setState({ data: null, lastFile: null })
})

afterEach(() => {
  localStorage.clear()
})


test("persist round-trip: setData writes to localStorage", () => {
  const r = fakeResponse()
  usePortfolio.getState().setData(r)
  const raw = localStorage.getItem(STORAGE_KEY)
  expect(raw).not.toBeNull()
  const parsed = JSON.parse(raw!)
  expect(parsed.state.data.normalized.holder_name).toBe("Alice")
})


test("clear empties both store state and localStorage", () => {
  usePortfolio.getState().setData(fakeResponse())
  expect(localStorage.getItem(STORAGE_KEY)).not.toBeNull()
  usePortfolio.getState().clear()
  expect(usePortfolio.getState().data).toBeNull()
  expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
})


test("lastFile is held in memory but excluded from persisted state", () => {
  const file = new File(["bytes"], "test.xlsx")
  usePortfolio.getState().setData(fakeResponse())
  usePortfolio.getState().setLastFile(file)
  expect(usePortfolio.getState().lastFile).toBe(file)
  const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY)!)
  expect(parsed.state.lastFile).toBeUndefined()
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/frontend
npm test -- store.test
```

Expected: failures — `setLastFile is not a function`, or persist behaviour absent.

- [ ] **Step 3: Replace `task4_open/frontend/lib/store.ts`**

```typescript
import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"
import type { ParseAndComputeResponse } from "./api"

interface PortfolioState {
  data: ParseAndComputeResponse | null
  lastFile: File | null
  hasHydrated: boolean
  setData: (d: ParseAndComputeResponse | null) => void
  setLastFile: (f: File | null) => void
  clear: () => void
}

export const usePortfolio = create<PortfolioState>()(
  persist(
    (set) => ({
      data: null,
      lastFile: null,
      hasHydrated: false,
      setData: (d) => set({ data: d }),
      setLastFile: (f) => set({ lastFile: f }),
      clear: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("timecell-portfolio-v1")
        }
        set({ data: null, lastFile: null })
      },
    }),
    {
      name: "timecell-portfolio-v1",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ data: s.data }),
      onRehydrateStorage: () => (state) => {
        if (state) state.hasHydrated = true
      },
    },
  ),
)
```

- [ ] **Step 4: Run the new tests to verify they pass**

```bash
npm test -- store.test
```

Expected: 3 passed.

- [ ] **Step 5: Run the full frontend suite**

```bash
npm test
```

Expected: 23 passed (20 existing + 3 from this task).

---

## Task 7: FileUpload — capture `lastFile` after successful parse

**Files:**
- Modify: `task4_open/frontend/components/FileUpload.tsx`

- [ ] **Step 1: Pull `setLastFile` from the store**

In `task4_open/frontend/components/FileUpload.tsx`, find:

```typescript
  const setData = usePortfolio((s) => s.setData)
```

Replace with:

```typescript
  const setData = usePortfolio((s) => s.setData)
  const setLastFile = usePortfolio((s) => s.setLastFile)
```

- [ ] **Step 2: Save the file after a successful parse**

Find:

```typescript
    try {
      const data = await parseAndCompute(file)
      setData(data)
      router.push("/dashboard")
```

Replace with:

```typescript
    try {
      const data = await parseAndCompute(file)
      setLastFile(file)
      setData(data)
      router.push("/dashboard")
```

- [ ] **Step 3: Update the `useCallback` dep array**

Find:

```typescript
  }, [router, setData])
```

Replace with:

```typescript
  }, [router, setData, setLastFile])
```

- [ ] **Step 4: Type-check + tests**

```bash
npx tsc --noEmit
npm test
```

Expected: tsc clean; 23 passed.

---

## Task 8: Dashboard layout — hydration gate + 3 header controls

**Files:**
- Modify: `task4_open/frontend/app/dashboard/layout.tsx`

- [ ] **Step 1: Replace `task4_open/frontend/app/dashboard/layout.tsx`**

```tsx
"use client"
import { useCallback, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { toast } from "sonner"
import { TabNav } from "@/components/TabNav"
import { ApiError, parseAndCompute } from "@/lib/api"
import { usePortfolio } from "@/lib/store"
import { formatINR, formatPct } from "@/lib/format"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const data = usePortfolio((s) => s.data)
  const lastFile = usePortfolio((s) => s.lastFile)
  const hasHydrated = usePortfolio((s) => s.hasHydrated)
  const setData = usePortfolio((s) => s.setData)
  const clear = usePortfolio((s) => s.clear)
  const [reparsing, setReparsing] = useState(false)

  useEffect(() => {
    if (hasHydrated && !data) router.replace("/")
  }, [hasHydrated, data, router])

  const handleReparse = useCallback(async () => {
    if (!lastFile) return
    setReparsing(true)
    try {
      const fresh = await parseAndCompute(lastFile, { force: true })
      setData(fresh)
    } catch (e) {
      const message = e instanceof ApiError
        ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
        : (e as Error).message
      toast.error(message)
    } finally {
      setReparsing(false)
    }
  }, [lastFile, setData])

  const handleUploadAnother = useCallback(() => {
    clear()
    router.push("/")
  }, [clear, router])

  if (!hasHydrated) return null
  if (!data) return null

  const { normalized, kpis } = data
  const totalPnl = normalized.summary.total_pnl_inr
  const totalPnlPct = normalized.summary.total_pnl_pct

  return (
    <div>
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-6xl items-start justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <Image src="/timecell-logo.png" alt="TimeCell" width={22} height={22} className="opacity-90" />
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-brass">TimeCell</span>
          </div>

          <div className="flex flex-col items-end gap-3">
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
              <div className="mt-1 font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
                Since invested
              </div>
              <div
                className={`font-mono text-xs tabular-nums ${
                  totalPnl >= 0 ? "text-brass-bright" : "text-oxblood"
                }`}
              >
                {totalPnl >= 0 ? "+" : ""}₹{formatINR(Math.abs(totalPnl))} ({formatPct(totalPnlPct, true)})
              </div>
            </div>

            <div className="flex items-center gap-2">
              {data.cached && (
                <span className="border border-brass px-2 py-0.5 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-brass-bright">
                  cached · ₹0.00
                </span>
              )}
              {lastFile && (
                <button
                  onClick={handleReparse}
                  disabled={reparsing}
                  className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass disabled:opacity-50"
                >
                  {reparsing ? "Re-parsing…" : "↻ Re-parse"}
                </button>
              )}
              <button
                onClick={handleUploadAnother}
                className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass"
              >
                ⊕ Upload another
              </button>
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

- [ ] **Step 2: Type-check + tests**

```bash
npx tsc --noEmit
npm test
```

Expected: tsc clean; 23 passed (no existing test imports the layout; the layout consumes only existing store + lib).

---

## Task 9: Frontend manual smoke — refresh + cached badge + Re-parse + Upload another

**Files:** none changed.

This validates the full user-visible flow. Both servers must be running.

- [ ] **Step 1: Make sure backend has at least one cached entry**

```bash
ls ~/.cache/timecell-task4/parse-cache/
```

If empty, do Task 3 step 3-4 first to populate one entry for `sample_groww.xlsx`.

- [ ] **Step 2: Start both servers (in two terminals or via the Makefile)**

```bash
# Terminal A:
source /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/.venv/bin/activate
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/backend
uvicorn main:app --port 8001 &

# Terminal B:
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak/task4_open/frontend
npm run dev
```

The proxy in `next.config.ts` is set to `:8001` for this session.

- [ ] **Step 3: Open `http://localhost:3001` in a fresh browser window (no extensions, normal mode)**

- [ ] **Step 4: Drop `sample_groww.xlsx` on the dropzone**

Expected:
- Phase indicator cycles, then dashboard renders.
- Top-right shows `cached · ₹0.00` brass-bright pill (because Task 3 already populated this entry).
- `↻ Re-parse` button visible (we just uploaded — `lastFile` is set).
- `⊕ Upload another` button visible.

- [ ] **Step 5: Refresh the page (Cmd+R / Ctrl+R)**

Expected:
- Dashboard re-renders immediately (no spinner, no flash of `/`).
- DevTools Network tab shows ZERO requests to `/api/parse-and-compute`.
- `cached · ₹0.00` badge still visible (we persisted the cached response itself).
- `↻ Re-parse` button is GONE (lastFile was not persisted; this is the β tradeoff).
- `⊕ Upload another` button still visible.

- [ ] **Step 6: Click `⊕ Upload another`**

Expected: navigate to `/`, dropzone visible, no data on landing page.

- [ ] **Step 7: Drop `sample_groww.xlsx` again**

Expected: dashboard renders in <500 ms (backend cache hit), `cached · ₹0.00` visible, `↻ Re-parse` visible (we just uploaded again).

- [ ] **Step 8: Click `↻ Re-parse`**

Expected: button text becomes "Re-parsing…", briefly disabled. After ~3-5 s the response refreshes; `cached · ₹0.00` badge disappears (fresh response is `cached: false`); backend stderr shows fresh `[parser] actual cost` line.

- [ ] **Step 9: Open DevTools → Application → Local Storage → `http://localhost:3001`**

Expected: a key `timecell-portfolio-v1` whose value is JSON containing `state.data.normalized.holder_name` etc. No `lastFile` in the persisted JSON.

- [ ] **Step 10: Stop both servers**

```bash
# Terminal A: kill the uvicorn job
kill %1 2>/dev/null || true
# Terminal B: Ctrl+C the next dev
```

If all 10 steps pass, the caching feature is functionally complete.

---

## Task 10: Second commit — frontend persist + header controls

**Files:**
- Stage: `task4_open/frontend/lib/api.ts`, `task4_open/frontend/lib/store.ts`, `task4_open/frontend/components/FileUpload.tsx`, `task4_open/frontend/app/dashboard/layout.tsx`, `task4_open/frontend/__tests__/store.test.ts`

- [ ] **Step 1: Verify the staged file list**

```bash
cd /Users/bilalrazak/Desktop/Apps/timecell-intern-bilal-sagar-razak
git status --short
```

Expected: 4 modified + 1 added file under `task4_open/frontend/`. Backend should be clean.

- [ ] **Step 2: Stage explicitly**

```bash
git add \
    task4_open/frontend/lib/api.ts \
    task4_open/frontend/lib/store.ts \
    task4_open/frontend/components/FileUpload.tsx \
    task4_open/frontend/app/dashboard/layout.tsx \
    task4_open/frontend/__tests__/store.test.ts
git status --short
```

Expected: only those 5 files under "Changes to be committed".

- [ ] **Step 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
task4a: persist portfolio store to localStorage + add cache UX controls

Wraps the Zustand store with the persist middleware so the dashboard
survives Cmd+R — the parsed response is keyed under timecell-portfolio-v1.
Hydration is gated by a hasHydrated flag so the redirect-to-/ effect waits
for localStorage to load instead of bouncing on first paint.

Three new header controls on /dashboard:
- "cached · ₹0.00" brass-bright pill when data.cached === true
- "↻ Re-parse" button (POSTs ?force=true with the in-memory File ref;
  hidden after refresh since File can't be JSON-persisted)
- "⊕ Upload another" button (clears localStorage + navigates to /)

api.ts gains a `cached: boolean` field on ParseAndComputeResponse and an
`opts.force` parameter on parseAndCompute() that adds ?force=true to the URL.

3 new Vitest tests (persist round-trip, clear empties storage, lastFile
excluded from partialize); 23 frontend tests pass.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git log --oneline | head -4
```

Expected: 3 commits on `task4a/result-caching` ahead of `task4a/dashboard-shell`.

---

## Task 11: Stop and ask the user about pushing / opening PR

Per the workflow rule (CLAUDE.md Part 1, item 2), do NOT push or open the PR unprompted. Surface to the user:

> "Result caching landed on branch `task4a/result-caching` (3 commits ahead of `task4a/dashboard-shell`: spec, backend cache, frontend persist + UX). **Tests:** 43 backend pytest + 23 frontend Vitest all pass. **Live verification:** sample_groww.xlsx round-trips through MISS → HIT → force=MISS as expected; refreshing /dashboard skips the network entirely; localStorage holds the persisted response. Ready to push and open a PR for review (likely against `task4a/dashboard-shell` or `main` depending on which lands first)?"

Wait for explicit user approval before running `git push -u origin task4a/result-caching` or `gh pr create`.

---

## Self-review

**1. Spec coverage:**

| Spec section | Implementation task |
|---|---|
| Goal: refresh-resilience | Task 6 (persist middleware) + Task 8 (hydration gate) |
| Goal: same-file dedup | Task 1 (cache module) + Task 2 (endpoint wiring) |
| Goal: visible cost saving | Task 8 (cached badge) |
| Goal: manual override | Task 8 (Re-parse button) + Task 2 (?force=true) |
| Goal: reset path | Task 8 (Upload another button) + Task 6 (clear() purges localStorage) |
| Architecture diagram | Tasks 1-2 (backend layer), Tasks 5-8 (frontend layer) |
| Backend: cache directory + key derivation | Task 1 step 3 |
| Backend: cache file format + atomic write | Task 1 step 3 |
| Backend: wiring inside parse_and_compute | Task 2 step 4 |
| Backend: endpoint signature + response model | Task 2 step 4 |
| Backend: cost interaction (no budget on hit) | Task 2 step 4 (return before normalize on hit) |
| Frontend: store shape + persist + partialize | Task 6 step 3 |
| Frontend: hydration handling in layout | Task 8 step 1 |
| Frontend: FileUpload setLastFile | Task 7 |
| Frontend: 3 header controls | Task 8 step 1 |
| Frontend: parseAndCompute force param | Task 5 step 2 |
| Error: corrupt cache file | Task 1 step 3 (read_cache try/except + delete) |
| Error: cache dir cannot be created | Task 2 step 4 (try/except OSError around write_cache) |
| Error: localStorage quota exceeded | Zustand persist middleware handles internally — no app code |
| Error: ?force=true while budget exhausted | Existing BudgetExhausted path → 429 toast (unchanged) |
| Error: schema version bump | Task 1 step 3 (SCHEMA_VERSION constant in cache_key) |
| Testing: backend test_cache.py 5 tests | Task 1 step 1 |
| Testing: backend test_main.py 3 tests | Task 2 step 2 |
| Testing: frontend store.test.ts 3 tests | Task 6 step 1 |
| Testing: manual acceptance | Task 9 |

All sections covered.

**2. Placeholder scan:** No `TBD` / `TODO` / `add appropriate X` / `similar to Task N` patterns. Every step shows complete code or commands. The Re-parse button's "hidden after refresh" behavior is the spec's β tradeoff — explicit in Task 8.

**3. Type consistency:**
- `cached: bool` (Pydantic, Task 2 step 4) ↔ `cached: boolean` (TS, Task 5 step 1) ↔ `data.cached === true` (Task 8 step 1) — consistent.
- `force: bool` query param (Task 2 step 4) ↔ `opts.force?: boolean` (Task 5 step 2) ↔ `parseAndCompute(lastFile, { force: true })` (Task 8 step 1) — consistent.
- `cache_key(file_bytes, prompt_text)` declared in Task 1 step 3 ↔ called in Task 2 step 4 with `cache_key(bytes(file_bytes), PROMPT_TEXT)` — consistent (PROMPT_TEXT is read at module top, declared in same Task 2 step 4).
- `setLastFile`, `lastFile`, `hasHydrated`, `clear()` declared in Task 6 step 3 ↔ consumed in Task 7 (`setLastFile`) and Task 8 (all four) — consistent.
- localStorage key `timecell-portfolio-v1` consistent across Task 6 step 3 (definition) and Task 6 step 1 (test assertion).

No mismatches.
