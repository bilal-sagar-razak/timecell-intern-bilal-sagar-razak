import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { OverlapDrilldown } from "@/components/OverlapDrilldown"

const sampleShared = [
  { name: "HDFC Bank", isin: "INE040A01034", weight_a: 8.42, weight_b: 5.10, min: 5.10 },
  { name: "Reliance Industries", isin: "INE002A01018", weight_a: 6.0, weight_b: 4.2, min: 4.2 },
]

describe("OverlapDrilldown", () => {
  test("empty state when no pair selected", () => {
    render(<OverlapDrilldown selected={null} />)
    expect(screen.getByText(/click a cell to see shared stocks/i)).toBeInTheDocument()
  })

  test("populated state shows shared stocks sorted by min weight", () => {
    render(<OverlapDrilldown selected={{ fundA: "Fund A", fundB: "Fund B", shared: sampleShared }} />)
    const rows = document.querySelectorAll(".shared-stock-row")
    expect(rows[0].textContent).toContain("HDFC Bank")
    expect(rows[1].textContent).toContain("Reliance Industries")
  })
})
