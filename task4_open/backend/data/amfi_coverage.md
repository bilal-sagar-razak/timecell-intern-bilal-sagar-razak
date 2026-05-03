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
