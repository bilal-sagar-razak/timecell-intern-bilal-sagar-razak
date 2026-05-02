"""FastAPI app exposing /api/health and /api/parse-and-compute for the Task 4a dashboard."""
from __future__ import annotations

import logging
import os
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

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
from parser.cache import cache_key, read_cache, write_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 10 * 1024 * 1024
PROMPT_TEXT = (Path(__file__).parent / "prompts" / "normalize.txt").read_text()
SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg"}

app = FastAPI(title="Task 4a — Portfolio Intelligence Dashboard backend")


class ParseAndComputeResponse(BaseModel):
    """Full payload returned by /api/parse-and-compute."""
    normalized: NormalizedHoldings
    kpis: KPIs
    allocation: list[AllocationSlice]
    xirr_by_fund: list[XirrEntry]
    category_performance: list[CategoryPerformance]
    cached: bool = False


@app.get("/api/health")
def health() -> dict:
    """Liveness probe + reports whether ANTHROPIC_API_KEY is set and the active model name."""
    return {
        "status": "ok",
        "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "model": DEFAULT_HAIKU_MODEL,
    }


@app.post("/api/parse-and-compute", response_model=ParseAndComputeResponse)
async def parse_and_compute(
    file: UploadFile = File(...),
    force: bool = False,
) -> ParseAndComputeResponse:
    """Accept a holdings file, extract + normalize via LLM, return KPIs/charts."""
    if not file.filename:
        raise HTTPException(status_code=400, detail={"error": "no file provided"})

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail={
                "error": "unsupported file type",
                "supported": sorted(SUPPORTED_EXTENSIONS),
            },
        )

    file_bytes = bytearray()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp.name)
    bytes_written = 0
    try:
        while chunk := await file.read(64 * 1024):
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_BYTES:
                tmp.close()
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail={
                        "error": "file too large",
                        "max_mb": MAX_FILE_BYTES // (1024 * 1024),
                    },
                )
            tmp.write(chunk)
            file_bytes.extend(chunk)
        tmp.close()
    except HTTPException:
        raise
    except Exception:
        tmp.close()
        tmp_path.unlink(missing_ok=True)
        raise

    key = cache_key(bytes(file_bytes), PROMPT_TEXT)
    if not force:
        cached = read_cache(key)
        if cached is not None:
            logger.info("[parser] cache HIT for %s... — $0", key[:8])
            tmp_path.unlink(missing_ok=True)
            cached["cached"] = True
            return ParseAndComputeResponse(**cached)

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
            raise HTTPException(
                status_code=429,
                detail={"error": "daily LLM budget exhausted", "detail": str(e)},
            )
        except NormalizationError as e:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "could not normalize statement after retry",
                    "raw_attempts": e.attempts,
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("LLM call failed")
            raise HTTPException(
                status_code=502,
                detail={"error": "LLM service unavailable", "detail": str(e)},
            )

        _kpis = kpis(normalized)
        _allocation = allocation(normalized)
        _xirr = xirr_by_fund(normalized)
        _cat_perf = category_performance(normalized)
        response = ParseAndComputeResponse(
            normalized=normalized,
            kpis=_kpis,
            allocation=_allocation,
            xirr_by_fund=_xirr,
            category_performance=_cat_perf,
            cached=False,
        )
        try:
            write_cache(key, response.model_dump(mode="json"))
        except OSError as e:
            logger.warning("[cache] write failed for %s...: %s", key[:8], e)
        return response
    finally:
        tmp_path.unlink(missing_ok=True)
