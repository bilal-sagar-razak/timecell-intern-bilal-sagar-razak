import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { CategoryCard } from "@/components/CategoryCard"

describe("CategoryCard", () => {
  test("renders positive category with brass accent", () => {
    const { container } = render(
      <CategoryCard category="Flexi Cap" pnlInr="+₹1,77,213" cagrPct="+6.64%" isPositive />,
    )
    expect(screen.getByText("Flexi Cap")).toBeInTheDocument()
    expect(screen.getByText("+₹1,77,213")).toBeInTheDocument()
    expect(container.querySelector(".border-l-brass")).toBeTruthy()
  })
  test("renders negative category with oxblood accent", () => {
    const { container } = render(
      <CategoryCard category="Mid Cap" pnlInr="-₹3,888" cagrPct="-0.68%" isPositive={false} />,
    )
    expect(container.querySelector(".border-l-oxblood")).toBeTruthy()
  })
  test("hides CAGR row when null", () => {
    render(<CategoryCard category="X" pnlInr="₹0" cagrPct={null} isPositive />)
    expect(screen.queryByText(/CAGR/)).not.toBeInTheDocument()
  })
  test("renders sub-category breakdowns when provided", () => {
    render(
      <CategoryCard
        category="Equity"
        pnlInr="+₹1,20,000"
        cagrPct="+9.00%"
        isPositive
        subBreakdowns={[
          { label: "Flexi Cap", pnlInr: "+₹1,00,000", cagrPct: "+10.00%", isPositive: true },
          { label: "Mid Cap", pnlInr: "-₹10,000", cagrPct: "-2.00%", isPositive: false },
        ]}
      />,
    )
    expect(screen.getByText("Flexi Cap")).toBeInTheDocument()
    expect(screen.getByText("+₹1,00,000")).toBeInTheDocument()
    expect(screen.getByText("Mid Cap")).toBeInTheDocument()
    expect(screen.getByText("-₹10,000")).toBeInTheDocument()
  })
})
