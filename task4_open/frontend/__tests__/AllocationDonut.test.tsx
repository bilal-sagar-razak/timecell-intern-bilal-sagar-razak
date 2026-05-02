import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { AllocationDonut } from "@/components/AllocationDonut"

describe("AllocationDonut", () => {
  test("renders header and total", () => {
    render(
      <AllocationDonut
        slices={[
          { label: "Flexi Cap", value_inr: 1000000, pct: 60 },
          { label: "Gilt", value_inr: 666666, pct: 40 },
        ]}
        totalInr={1666666}
      />,
    )
    expect(screen.getByText("Allocation")).toBeInTheDocument()
    expect(screen.getByText("₹16,66,666")).toBeInTheDocument()
  })
  test("lists each slice in the legend", () => {
    render(
      <AllocationDonut
        slices={[
          { label: "Flexi Cap", value_inr: 100, pct: 50 },
          { label: "Gilt", value_inr: 100, pct: 50 },
        ]}
        totalInr={200}
      />,
    )
    expect(screen.getByText("Flexi Cap")).toBeInTheDocument()
    expect(screen.getByText("Gilt")).toBeInTheDocument()
  })
})
