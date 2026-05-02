import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { XirrBarChart } from "@/components/XirrBarChart"

describe("XirrBarChart", () => {
  test("renders header", () => {
    render(<XirrBarChart entries={[{ name: "PPFCF", xirr_pct: 10.22, color: "positive" }]} />)
    expect(screen.getByText("Return by Fund")).toBeInTheDocument()
  })
  test("includes each fund name", () => {
    render(
      <XirrBarChart
        entries={[
          { name: "Top Fund", xirr_pct: 10, color: "positive" },
          { name: "Bottom Fund", xirr_pct: -5, color: "negative" },
        ]}
      />,
    )
    expect(screen.getByText("Top Fund")).toBeInTheDocument()
    expect(screen.getByText("Bottom Fund")).toBeInTheDocument()
  })
})
