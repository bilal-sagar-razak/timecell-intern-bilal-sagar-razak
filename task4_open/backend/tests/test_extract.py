"""Tests for parser.extract — runs against real sample files; no LLM, no network."""
from __future__ import annotations

import struct
import sys
import tempfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parser.extract import (
    ExtractError,
    extract,
    extract_image,
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
