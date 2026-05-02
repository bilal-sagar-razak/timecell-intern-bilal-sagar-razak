import { afterEach, beforeEach, expect, test } from "vitest"
import { usePortfolio } from "@/lib/store"
import type { ParseAndComputeResponse } from "@/lib/api"

const STORAGE_KEY = "timecell-portfolio-v1"

function fakeResponse(): ParseAndComputeResponse {
  return {
    normalized: {
      holder_name: "Alice",
      source_format: "test",
      summary: {
        total_invested_inr: 100,
        total_current_inr: 110,
        total_pnl_inr: 10,
        total_pnl_pct: 10,
        overall_xirr_pct: null,
        asset_count: 0,
        statement_date: null,
      },
      assets: [],
      parser_warnings: [],
    },
    kpis: { invested_inr: 100, current_inr: 110, equity_pct: 0, debt_pct: 0, overall_xirr_pct: null, asset_count: 0 },
    allocation: [],
    xirr_by_fund: [],
    category_performance: [],
    cached: false,
  }
}

beforeEach(() => {
  localStorage.clear()
  usePortfolio.setState({ data: null, lastFile: null })
})

afterEach(() => {
  localStorage.clear()
})


test("persist round-trip: setData writes to localStorage", () => {
  const r = fakeResponse()
  usePortfolio.getState().setData(r)
  const raw = localStorage.getItem(STORAGE_KEY)
  expect(raw).not.toBeNull()
  const parsed = JSON.parse(raw!)
  expect(parsed.state.data.normalized.holder_name).toBe("Alice")
})


test("clear empties both store state and localStorage", () => {
  usePortfolio.getState().setData(fakeResponse())
  expect(localStorage.getItem(STORAGE_KEY)).not.toBeNull()
  usePortfolio.getState().clear()
  expect(usePortfolio.getState().data).toBeNull()
  expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
})


test("lastFile is held in memory but excluded from persisted state", () => {
  const file = new File(["bytes"], "test.xlsx")
  usePortfolio.getState().setData(fakeResponse())
  usePortfolio.getState().setLastFile(file)
  expect(usePortfolio.getState().lastFile).toBe(file)
  const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY)!)
  expect(parsed.state.lastFile).toBeUndefined()
})
