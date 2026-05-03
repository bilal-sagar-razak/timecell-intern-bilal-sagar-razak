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
    """Discover the latest per-AMC disclosure files from AMFI's portfolio-disclosure
    hub at https://www.amfiindia.com/online-center/portfolio-disclosure, download
    them into cache_dir, return that directory.

    AMFI links to each AMC's own disclosure file (xls/xlsx/pdf) for the latest
    month. Format varies per AMC — that's why scripts/amfi_adapters/ has one
    parser per AMC. Per-scheme PDFs also live at
    https://portal.amfiindia.com/spages/<scheme_id>.pdf.

    Real implementation TBD by maintainer; stub for tests via monkeypatch.
    """
    raise NotImplementedError(
        "Auto-discovery from amfiindia.com is intentionally deferred for v1. "
        "The maintainer downloads each AMC's monthly disclosure manually from "
        "https://www.amfiindia.com/online-center/portfolio-disclosure and "
        "points this script at the unpacked directory via cache_dir.")


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
        "# AMFI bundle coverage",
        "",
        f"**As of:** {bundle.as_of_month}",
        f"**Generated:** {bundle.fetched_at.isoformat()}",
        f"**Scheme count:** {len(final_schemes)}",
        f"**AMC count parsed:** {len(parsed_amcs)}",
        "",
        "## AMCs parsed",
        "",
        *(f"- {a}" for a in sorted(parsed_amcs)),
        "",
        "## Files skipped",
        "",
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
