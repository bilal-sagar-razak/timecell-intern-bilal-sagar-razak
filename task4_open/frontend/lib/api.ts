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
