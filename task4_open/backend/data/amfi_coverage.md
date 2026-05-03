# AMFI bundle coverage

**As of:** 2026-04
**Generated:** 2026-05-03 (committed seed; regenerate via `make refresh-amfi`)

## Schemes in this bundle (28 total)

| AMC | Scheme | ISIN |
|---|---|---|
| PPFAS | Parag Parikh Flexi Cap Fund | INF879O01027 |
| HDFC | HDFC Flexi Cap Fund | INF179K01YV8 |
| HDFC | HDFC Large and Mid Cap Fund | INF179KA1Y84 |
| HDFC | HDFC Silver ETF FoF | INF179KC1Q67 |
| ICICI Pru | ICICI Prudential Multi Asset Fund | INF109K016L0 |
| ICICI Pru | ICICI Prudential Short Term Fund | INF109K01530 |
| ICICI Pru | ICICI Pru Gilt Fund | INF109K01ZF6 |
| ICICI Pru | ICICI Prudential BHARAT 22 FOF | INF109KC1Q83 |
| Nippon | Nippon India Power & Infra Fund | INF204K01YA5 |
| Nippon | Nippon India Small Cap Fund | INF204K01ZG1 |
| Nippon | Nippon India Large Cap Fund | INF204K01ED4 |
| Motilal Oswal | Motilal Oswal Midcap Fund | INF247L01890 |
| Bandhan | Bandhan Infrastructure Fund | INF194K01HG8 |
| Bandhan | Bandhan Small Cap Fund | INF194KB1KP3 |
| Invesco | Invesco India PSU Equity Fund | INF205K01CE2 |
| Tata | Tata Gold ETF FoF | INF277KA1WG3 |
| Tata | Tata Small Cap Fund | INF277K01YH8 |
| SBI | SBI Gold Fund | INF200K01TM1 |
| SBI | SBI Silver ETF FoF | INF200KA1JR0 |
| SBI | SBI PSU Fund | INF200K01YJ7 |
| SBI | SBI Gilt Fund | INF200K01N28 |
| Quant | Quant Active Fund | INF966L01366 |
| Quant | Quant Small Cap Fund | INF966L01689 |
| Quant | Quant Infrastructure Fund | INF966L01473 |
| Quant | Quant Flexi Cap Fund | INF966L01515 |
| Edelweiss | Edelweiss Mid Cap Fund | INF754K01OL3 |
| Kotak | Kotak Gilt Fund | INF174K01QC1 |
| Canara Robeco | Canara Robeco Large Cap Fund | INF760K01795 |

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
