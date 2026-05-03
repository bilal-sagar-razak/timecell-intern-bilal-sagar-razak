import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { MatchBadge } from "@/components/MatchBadge"

describe("MatchBadge", () => {
  test("renders label for each match type", () => {
    const { rerender } = render(<MatchBadge matchedBy="isin" />)
    expect(screen.getByText("ISIN")).toBeInTheDocument()
    rerender(<MatchBadge matchedBy="name" />)
    expect(screen.getByText("name")).toBeInTheDocument()
    rerender(<MatchBadge matchedBy="none" />)
    expect(screen.getByText("none")).toBeInTheDocument()
  })
})
