import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { KpiCard } from "@/components/KpiCard"

describe("KpiCard", () => {
  test("renders label and value", () => {
    render(<KpiCard label="INVESTED" value="₹41,49,792" />)
    expect(screen.getByText("INVESTED")).toBeInTheDocument()
    expect(screen.getByText("₹41,49,792")).toBeInTheDocument()
  })
  test("renders subline when provided", () => {
    render(<KpiCard label="CURRENT" value="₹44,81,647" subline="XIRR 4.71%" />)
    expect(screen.getByText("XIRR 4.71%")).toBeInTheDocument()
  })
  test("does not render subline when omitted", () => {
    render(<KpiCard label="EQUITY" value="64.2%" />)
    expect(screen.queryByText(/XIRR/)).not.toBeInTheDocument()
  })
})
