# Task 4a — Result Caching Design

Adds two independent caching layers to Task 4a so refreshing the dashboard does not re-call the LLM, and re-uploading the same file is instant + free.

**Built on top of:** the shipped Task 4a backend (`task4_open/backend/{main,parser,metrics}/...`) and frontend (`task4_open/frontend/{app,components,lib}/...`). No backend or frontend rewrite — additive only.

---

## Goals

1. **Refresh-resilience.** Hitting Cmd+R on `/dashboard` continues to render the same view without any network call or LLM spend.
2. **Same-file dedup.** Re-uploading the same file (same bytes, same prompt, same schema version) returns the previous parse from a content-addressed disk cache in <100 ms with $0 LLM spend.
3. **Visible cost saving.** A "cached · ₹0.00" badge surfaces when the served response came from the disk cache.
4. **Manual override.** A "Re-parse" button forces a fresh LLM call (same-session only — see β tradeoff below).
5. **Reset path.** An "Upload another file" button clears persisted state and returns to `/`.

Non-goals: multi-user cache scoping (no auth in the demo), shared/remote cache, cache size eviction (YAGNI today), persisting the original file bytes across refresh.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser                                                            │
│  ┌──────────────────────┐   ┌────────────────────────────────────┐  │
│  │  /dashboard          │←──┤  Zustand store (localStorage)      │  │
│  │  Renders from store  │   │  Survives refresh + tab restart    │  │
│  └──────────────────────┘   └────────────────────────────────────┘  │
│           ▲                                                         │
│           │  POST /api/parse-and-compute  (only on new upload)      │
└───────────┼─────────────────────────────────────────────────────────┘
            ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  1. SHA-256 file bytes + prompt text + schema version → key     │ │
│  │  2. Look up ~/.cache/timecell-task4/parse-cache/<key>.json      │ │
│  │  3. HIT  → return cached response with "cached": true (no LLM)  │ │
│  │     MISS → run extract → normalize → compute → write cache      │ │
│  │  4. ?force=true bypasses lookup but still writes on success     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

The two layers are independent. Backend cache works without the frontend change; frontend persistence works without the backend change. Together they give the obvious user experience.

---

## Backend cache

### Files

- **New:** `task4_open/backend/parser/cache.py` (~50 lines) — pure functions: `cache_key()`, `read_cache()`, `write_cache()`. No I/O on import. No FastAPI imports — testable in isolation.
- **Modified:** `task4_open/backend/main.py` — `parse_and_compute()` gains a `force: bool = False` query param and wraps the existing pipeline in a cache lookup. `ParseAndComputeResponse` gains a `cached: bool = False` field.
- **New:** `task4_open/backend/tests/test_cache.py` — 5 tests covering key derivation, atomic write, missing file, schema-version invalidation, force bypass.

### Cache directory

`~/.cache/timecell-task4/parse-cache/` — sibling to the existing `usage-YYYY-MM-DD.json` daily-budget files. Reuses `CACHE_DIR` from `parser/normalize.py` as the parent so both share the same root.

### Key derivation

```python
SCHEMA_VERSION = "1"  # bump when NormalizedHoldings shape changes

def cache_key(file_bytes: bytes, prompt_text: str) -> str:
    h = hashlib.sha256()
    h.update(file_bytes)
    h.update(b"\x00")
    h.update(prompt_text.encode("utf-8"))
    h.update(b"\x00")
    h.update(SCHEMA_VERSION.encode("utf-8"))
    return h.hexdigest()
```

`prompt_text` is read once at module import from `prompts/normalize.txt`. The null bytes between the three inputs prevent boundary collisions (file bytes ending in `"prompt"` confused with the prompt itself).

### Cache file format

```json
{
  "cached_at": "2026-05-02T22:14:33+00:00",
  "response": { /* full ParseAndComputeResponse, untouched */ }
}
```

The cached `response` is the byte-for-byte dict the API returned on the original miss, except `cached` is rewritten to `true` when served from disk.

### Atomic write

```python
def write_cache(key: str, response_dict: dict) -> None:
    PARSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = PARSE_CACHE_DIR / f"{key}.json"
    tmp = p.with_suffix(".json.tmp")
    payload = {"cached_at": _now_iso(), "response": response_dict}
    tmp.write_text(json.dumps(payload))
    tmp.replace(p)
```

Same atomic-rename pattern as the existing budget cache. A crash mid-write leaves the old `.json` intact.

### Wiring inside `parse_and_compute()`

The existing flow stays as-is. We wrap it:

1. Read file into memory (already done for the size cap — it's only ~10 MB max).
2. Compute `key = cache_key(file_bytes, PROMPT_TEXT)`.
3. If `not force` AND `read_cache(key)` returns a value: log `[parser] cache HIT for {key[:8]}... — $0`, set `response["cached"] = True`, return it. No extract, no normalize, no compute.
4. Otherwise: existing extract → normalize → compute pipeline. Set `response["cached"] = False`. On success, `write_cache(key, response.dict())`. Return.
5. On any error (extract/normalize/budget/LLM): do NOT write cache. Errors propagate as before.

### Endpoint signature

```python
@app.post("/api/parse-and-compute", response_model=ParseAndComputeResponse)
async def parse_and_compute(
    file: UploadFile = File(...),
    force: bool = False,
) -> ParseAndComputeResponse: ...
```

### Response model

```python
class ParseAndComputeResponse(BaseModel):
    normalized: NormalizedHoldings
    kpis: KPIs
    allocation: list[AllocationSlice]
    xirr_by_fund: list[XirrEntry]
    category_performance: list[CategoryPerformance]
    cached: bool = False  # new
```

Default `False` keeps the schema backward-compatible with anything reading the JSON.

### Cost interaction

- Cache HIT: budget guard not consulted, `~/.cache/timecell-task4/usage-YYYY-MM-DD.json` not updated. Hit costs $0 — that's the whole point.
- Cache MISS: budget guard runs as today (in `normalize()`). On success, normalize updates the daily budget. On `BudgetExhausted`, no cache write.
- `?force=true`: same as MISS — budget guard runs. Useful safeguard against the user accidentally racking up cost via repeated forced re-parses.

---

## Frontend persistence + new buttons

### Files

- **Modified:** `task4_open/frontend/lib/store.ts` — wrap the existing Zustand store with the `persist` middleware backed by `localStorage`. Add a `_hasHydrated` boolean flag set true via `onRehydrateStorage`.
- **Modified:** `task4_open/frontend/lib/api.ts` — add `cached: boolean` to `ParseAndComputeResponse` interface; add `force?: boolean` parameter to `parseAndCompute()` so the URL becomes `/api/parse-and-compute?force=true` when set.
- **Modified:** `task4_open/frontend/app/dashboard/layout.tsx` — gate the redirect on `_hasHydrated`; add the three header controls.
- **Modified:** `task4_open/frontend/components/FileUpload.tsx` — store the dropped `File` object in a non-persisted module-level ref (or as a transient store field marked `partialize`-excluded) so Re-parse can re-submit it within the same session.
- **New:** `task4_open/frontend/__tests__/store.test.ts` — 3 tests: persist round-trip, clear empties storage, hydration flag flips.
- **Modified:** `task4_open/frontend/__tests__/CategoryCard.test.tsx` and others — no changes needed; existing tests don't touch the persisted store.

### Store shape

```typescript
import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"

interface PortfolioState {
  data: ParseAndComputeResponse | null
  lastFile: File | null            // not persisted; for Re-parse
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
        localStorage.removeItem("timecell-portfolio-v1")
        set({ data: null, lastFile: null })
      },
    }),
    {
      name: "timecell-portfolio-v1",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ data: s.data }),  // only persist `data`
      onRehydrateStorage: () => (state) => {
        state?.hasHydrated && (state.hasHydrated = true)
        // safer: schedule a microtask to set the flag
      },
    },
  ),
)
```

The `-v1` suffix in the storage key lets us bump it later without colliding with old shapes. `partialize` excludes `lastFile` (Files can't be JSON-serialised cleanly anyway) and `hasHydrated` (transient).

### Hydration handling in dashboard layout

```tsx
const data = usePortfolio((s) => s.data)
const hasHydrated = usePortfolio((s) => s.hasHydrated)

useEffect(() => {
  if (hasHydrated && !data) router.replace("/")
}, [hasHydrated, data, router])

if (!hasHydrated) return null  // brief blank during rehydrate
if (!data) return null          // we've hydrated and there's nothing — wait for redirect
```

Without the hydration gate, the layout sees `data=null` on first paint, kicks off the redirect, and the user sees a flash of `/` before localStorage has been read.

### FileUpload change

After a successful parse:
```tsx
setLastFile(file)   // for Re-parse
setData(response)   // existing
router.push("/dashboard")
```

### Header controls in dashboard layout

Right side of header, between the Portfolio summary block and the page edge. Small mono-uppercase buttons styled like the existing TabNav links.

| Control | Visible when | Action |
|---|---|---|
| `cached · ₹0.00` badge | `data.cached === true` | Display only — small brass-bright pill |
| `↻ Re-parse` | `lastFile !== null` (i.e. same session as upload, no refresh in between) | `parseAndCompute(lastFile, { force: true })` → `setData(response)`. Toast on error. |
| `⊕ Upload another` | Always | `clear()` then `router.push("/")` |

After a refresh, `lastFile` is null (it's not persisted), so Re-parse is hidden. The user uses Upload another → re-drops → fresh parse runs. This is option β from the design discussion.

### `parseAndCompute()` signature

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
  // existing error handling stays
  return r.json()
}
```

---

## Error handling

| Failure | Behavior |
|---|---|
| Cache file is corrupt JSON | `read_cache()` catches `json.JSONDecodeError`, deletes the corrupt file, returns `None`. Caller treats as MISS. Logged at WARN. |
| Cache file is valid JSON but missing required keys | Same as corrupt: delete + treat as MISS. |
| Cache dir cannot be created (permission denied) | `write_cache` lets the OSError propagate; `parse_and_compute` catches it inside a try/except, logs WARN, returns the response without caching. The user's request still succeeds. |
| `localStorage` quota exceeded | Zustand `persist` middleware swallows the QuotaExceededError and logs it. Store still works in-memory for the session — refresh resilience is lost but the app doesn't crash. Acceptable since our payloads are <50 KB. |
| `localStorage` disabled (private mode) | Same as quota: in-memory only, refresh kicks back to `/`. |
| `?force=true` while `MAX_DAILY_LLM_USD` cap reached | `BudgetExhausted` propagates → 429 → toast. The cache is not touched. |
| Two concurrent uploads of the same new file | Both miss cache → both run LLM → both write cache (last write wins, same content so safe). Acceptable since this is single-user. |
| Schema version bump mid-session | Old cache files have a different key, so they're ignored on lookup. Stale files sit on disk forever (acceptable per non-goals). |
| `_hasHydrated` flag never flips (Zustand bug or no localStorage) | Layout shows blank forever. Mitigation: a fallback `useEffect` with a 1 s timer that force-flips `hasHydrated = true`. |

---

## Testing

### Backend (`task4_open/backend/tests/test_cache.py` — 5 new tests)

1. `test_cache_key_deterministic_for_same_inputs` — same `(bytes, prompt)` → same hex digest.
2. `test_cache_key_changes_when_file_bytes_change` — flipping a single byte changes the key.
3. `test_cache_key_changes_when_prompt_changes` — modifying the prompt invalidates the key.
4. `test_write_cache_is_atomic_and_readable` — write then read returns the same dict; tmpfile is gone.
5. `test_read_cache_handles_corrupt_file` — write garbage to `<key>.json`, `read_cache` returns None and removes the file.

### Backend (`task4_open/backend/tests/test_main.py` — 3 added tests)

6. `test_parse_and_compute_cache_hit_skips_normalize` — first call mocks normalize to return X; second call to same file should NOT invoke `main.normalize` (assert `mock_normalize.call_count == 1` after 2 requests). Response on second call has `cached: true`.
7. `test_parse_and_compute_force_bypasses_cache` — same setup; pass `?force=true` on second call → normalize IS called again. Response has `cached: false`.
8. `test_parse_and_compute_does_not_cache_on_error` — mock normalize to raise NormalizationError. Hit endpoint → 502. Confirm no file in cache dir.

### Frontend (`task4_open/frontend/__tests__/store.test.ts` — 3 new tests)

9. `test_persist_round_trip` — set data, simulate page reload by re-importing the store module, assert `data` is restored from localStorage.
10. `test_clear_empties_localstorage` — set data, call `clear()`, assert localStorage no longer has the key.
11. `test_hydrated_flag_starts_false_then_flips` — fresh store has `hasHydrated === false`; after `useEffect` tick, it's `true`.

(Frontend tests use `localStorage` from jsdom, which is provided by default. The Zustand persist middleware reads it synchronously on first store access in jsdom.)

### Manual acceptance

1. Upload `sample_groww.xlsx` → see Overview render. Note `cached: false` in response.
2. Refresh `/dashboard` → still see Overview, no network call (verify in DevTools Network tab).
3. Click "Upload another" → land on `/`, dropzone empty.
4. Drop the same `sample_groww.xlsx` again → Overview renders in <500 ms with `cached · ₹0.00` badge visible.
5. Click "Re-parse" → spinner briefly, badge disappears, fresh response.
6. Drop a different sample → fresh parse (different SHA → cache miss), no badge.

---

## Performance

- Cache HIT round-trip: ~30 ms file upload + ~5 ms SHA-256 + ~2 ms file read = **~40 ms** total. The previous "uncached" path was 3-8 s.
- Cache file size: ~5-50 KB per entry. 100 distinct uploads ≈ 5 MB on disk.
- Frontend hydration latency: <10 ms (localStorage read is synchronous).
- localStorage payload: same 5-50 KB. Well under the 5 MB browser quota.

---

## Migration / rollout

No DB, no auth, single-user demo — there's no migration. Deploying this change against an existing browser session: the localStorage key is new (`timecell-portfolio-v1`), so old in-memory state is simply not preserved across the deploy. First refresh after the deploy bounces to `/` once. After that, refresh-resilience is on.

The first request after deploy populates `~/.cache/timecell-task4/parse-cache/` lazily — no warm-up needed.
