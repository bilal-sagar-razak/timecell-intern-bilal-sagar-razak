import { describe, expect, test, vi } from "vitest"
import { render, fireEvent } from "@testing-library/react"
import { OverlapHeatmap } from "@/components/OverlapHeatmap"

const sample = {
  funds: [
    { asset_name: "PPFAS Flexi Cap", scheme_name: "Parag Parikh Flexi Cap Fund", matched_by: "isin" as const },
    { asset_name: "HDFC Flexi Cap", scheme_name: "HDFC Flexi Cap Fund", matched_by: "isin" as const },
    { asset_name: "Quant Active", scheme_name: "Quant Active Fund", matched_by: "isin" as const },
  ],
  matrix: [
    [
      { i: 0, j: 0, overlap_pct: 95.8, shared_count: 2 },
      { i: 0, j: 1, overlap_pct: 25.5, shared_count: 1 },
      { i: 0, j: 2, overlap_pct: 12.3, shared_count: 1 },
    ],
    [
      { i: 1, j: 0, overlap_pct: 25.5, shared_count: 1 },
      { i: 1, j: 1, overlap_pct: 96.9, shared_count: 2 },
      { i: 1, j: 2, overlap_pct: 8.0, shared_count: 1 },
    ],
    [
      { i: 2, j: 0, overlap_pct: 12.3, shared_count: 1 },
      { i: 2, j: 1, overlap_pct: 8.0, shared_count: 1 },
      { i: 2, j: 2, overlap_pct: 97.9, shared_count: 2 },
    ],
  ],
  shared_stocks_index: {},
}

describe("OverlapHeatmap", () => {
  test("renders one cell per upper-triangle pair", () => {
    render(<OverlapHeatmap data={sample} onSelect={() => {}} />)
    const cells = document.querySelectorAll("[data-cell-pair]")
    expect(cells.length).toBe(3)
  })

  test("clicking a cell fires onSelect with i, j", () => {
    const onSelect = vi.fn()
    render(<OverlapHeatmap data={sample} onSelect={onSelect} />)
    const cell = document.querySelector('[data-cell-pair="0_1"]')
    fireEvent.click(cell!)
    expect(onSelect).toHaveBeenCalledWith(0, 1)
  })
})
