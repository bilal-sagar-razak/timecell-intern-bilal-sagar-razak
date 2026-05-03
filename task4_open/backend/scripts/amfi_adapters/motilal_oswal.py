"""Placeholder adapter for Motilal Oswal. Returns []. Replace with a real parser when needed."""
from __future__ import annotations

import logging
from pathlib import Path

from amfi.schema import Scheme

logger = logging.getLogger(__name__)
AMC_NAME = "Motilal Oswal"


def parse(file_path: Path) -> list[Scheme]:
    logger.warning("[amfi_adapters/%s] placeholder — not parsing %s", AMC_NAME, file_path)
    return []
