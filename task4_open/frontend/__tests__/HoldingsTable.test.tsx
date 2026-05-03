import { describe, expect, test } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { HoldingsTable } from "@/components/HoldingsTable"

const sampleAssets = [
  {
    name: "Parag Parikh Flexi Cap Fund", asset_type: "mutual_fund" as const,
    isin: "INF879O01027", amc: "PPFAS", category: "Equity" as const, sub_category: "Flexi Cap",
    folio: null, units: 100, invested_value_inr: 100000, current_value_inr: 145000,
    xirr_pct: 14.32, pnl_inr: 45000, pnl_pct: 45.0,
  },
  {
    name: "ICICI Pru Gilt Fund", asset_type: "mutual_fund" as const,
    isin: "INF109K01ZF6", amc: "ICICI Pru", category: "Debt" as const, sub_category: "Gilt",
    folio: null, units: 50, invested_value_inr: 50000, current_value_inr: 52000,
    xirr_pct: 4.10, pnl_inr: 2000, pnl_pct: 4.0,
  },
]

const sampleMatches = [
  {
    asset_name: "Parag Parikh Flexi Cap Fund", asset_isin: "INF879O01027",
    matched: true, matched_by: "isin" as const, confidence: 1.0,
    scheme: {
      scheme_name: "Parag Parikh Flexi Cap Fund - Direct Growth",
      isin: "INF879O01027", amc: "PPFAS", scheme_aum_inr: 8.7e10,
      as_of_date: "2026-04-30", cash_pct: 4.2,
      holdings: [{name: "HDFC Bank", isin: "INE040A01034", weight_pct: 8.42, value_inr: 7.3e9, kind: "equity"}],
    },
  },
  {
    asset_name: "ICICI Pru Gilt Fund", asset_isin: "INF109K01ZF6",
    matched: false, matched_by: "none" as const, confidence: 0.0, scheme: null,
  },
]

describe("HoldingsTable", () => {
  test("renders one row per fund", () => {
    render(<HoldingsTable assets={sampleAssets} matches={sampleMatches} />)
    expect(screen.getByText("Parag Parikh Flexi Cap Fund")).toBeInTheDocument()
    expect(screen.getByText("ICICI Pru Gilt Fund")).toBeInTheDocument()
  })

  test("clicking a matched row reveals the expanded panel", () => {
    render(<HoldingsTable assets={sampleAssets} matches={sampleMatches} />)
    fireEvent.click(screen.getByText("Parag Parikh Flexi Cap Fund"))
    expect(screen.getByText(/Top holdings/i)).toBeInTheDocument()
    expect(screen.getByText("HDFC Bank")).toBeInTheDocument()
  })

  test("clicking the Value header sorts descending", () => {
    render(<HoldingsTable assets={sampleAssets} matches={sampleMatches} />)
    const valueHeader = screen.getByText(/Value/i)
    fireEvent.click(valueHeader)
    const rows = document.querySelectorAll("tbody tr.fund-row")
    // first row is the higher-value fund (PPFAS at ₹145000)
    expect(rows[0].textContent).toContain("Parag Parikh Flexi Cap")
  })
})
