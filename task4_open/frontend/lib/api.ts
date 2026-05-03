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

export interface SubCategoryBreakdown {
  label: string
  pnl_inr: number
  cagr_pct: number | null
}

export interface CategoryPerformance {
  category: string
  pnl_inr: number
  cagr_pct: number | null
  sub_breakdowns: SubCategoryBreakdown[]
}

export interface ParseAndComputeResponse {
  normalized: NormalizedHoldings
  kpis: KPIs
  allocation: AllocationSlice[]
  xirr_by_fund: XirrEntry[]
  category_performance: CategoryPerformance[]
  cached: boolean
}

export interface NiftyPoint { date: string; close: number }

export interface NiftyTrend {
  points: NiftyPoint[]
  pct_change_period: number
  current: number
  period_days: number
}

export interface Headline {
  title: string
  publisher: string
  url: string
  published_at: string
  snippet: string | null
}

export interface MarketSnapshot {
  nifty_trend: NiftyTrend
  news: Headline[]
  news_fallback_used: boolean
  cached_at: string
}

export interface ToolCall {
  tool_name: string
  input_json: Record<string, unknown>
  output_json: Record<string, unknown>
  ts: string
  duration_ms: number
}

export interface RebalanceResult {
  advice_markdown: string
  trace: ToolCall[]
  iterations: number
  truncated: boolean
  cost_usd: number
}

export interface FundHolding {
  name: string
  isin: string | null
  weight_pct: number
  value_inr: number
  kind: string
}

export interface AmfiScheme {
  scheme_name: string
  isin: string | null
  amc: string
  scheme_aum_inr: number
  as_of_date: string
  holdings: FundHolding[]
  cash_pct: number
}

export interface FundMatch {
  asset_name: string
  asset_isin: string | null
  matched: boolean
  matched_by: "isin" | "name" | "none"
  confidence: number
  scheme: AmfiScheme | null
}

export interface HoldingsResponse {
  matches: FundMatch[]
}

export interface OverlapFund {
  asset_name: string
  scheme_name: string | null
  matched_by: "isin" | "name" | "none"
}

export interface OverlapCell {
  i: number
  j: number
  overlap_pct: number
  shared_count: number
}

export interface SharedStock {
  name: string
  isin: string | null
  weight_a: number
  weight_b: number
  min: number
}

export interface OverlapResponse {
  funds: OverlapFund[]
  matrix: OverlapCell[][]
  shared_stocks_index: Record<string, SharedStock[]>
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message)
  }
}

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

/** Long-running endpoints (e.g., the Sonnet agent) bypass the Next.js dev proxy
 * (which times out around 30s and returns ECONNRESET) by hitting the backend directly. */
const DIRECT_BACKEND =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

async function _postJson<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    let detail: unknown = null
    try {
      const data = await r.json()
      detail = data.detail
      throw new ApiError(r.status, data.detail?.error || `HTTP ${r.status}`, detail)
    } catch (e) {
      if (e instanceof ApiError) throw e
      throw new ApiError(r.status, `HTTP ${r.status}`)
    }
  }
  return r.json() as Promise<T>
}

export function fetchMarketSnapshot(
  holdings: NormalizedHoldings,
  opts: { refresh?: boolean } = {},
): Promise<MarketSnapshot> {
  return _postJson<MarketSnapshot>("/api/market", { holdings, refresh: opts.refresh ?? false })
}

export function runRebalance(
  holdings: NormalizedHoldings,
): Promise<RebalanceResult> {
  return _postJson<RebalanceResult>(`${DIRECT_BACKEND}/api/rebalance`, { holdings })
}

export function fetchHoldingsPerFund(
  holdings: NormalizedHoldings,
): Promise<HoldingsResponse> {
  return _postJson<HoldingsResponse>("/api/holdings/per-fund", { holdings })
}

export function fetchOverlap(
  holdings: NormalizedHoldings,
): Promise<OverlapResponse> {
  return _postJson<OverlapResponse>("/api/holdings/overlap", { holdings })
}
