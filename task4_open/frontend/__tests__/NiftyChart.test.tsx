import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { NiftyChart } from "@/components/NiftyChart"

const sample = {
  points: [
    { date: "2026-01-01", close: 22000 },
    { date: "2026-01-02", close: 22100 },
    { date: "2026-01-03", close: 22200 },
  ],
  pct_change_period: 0.91,
  current: 22200,
  period_days: 3,
}

describe("NiftyChart", () => {
  test("renders header label, current value, and period change", () => {
    render(<NiftyChart trend={sample} />)
    expect(screen.getByText("NIFTY 50")).toBeInTheDocument()
    expect(screen.getByText("22,200")).toBeInTheDocument()
    expect(screen.getByText(/\+0\.91%/)).toBeInTheDocument()
  })

  test("renders the chart SVG when there are points", () => {
    const { container } = render(<NiftyChart trend={sample} />)
    expect(container.querySelector("svg")).toBeTruthy()
  })
})
