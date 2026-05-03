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
