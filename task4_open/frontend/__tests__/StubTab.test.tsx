import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { StubTab } from "@/components/StubTab"

describe("StubTab", () => {
  test("shows the task label and description", () => {
    render(<StubTab task="4b" description="Nifty trend + market news will land here." />)
    expect(screen.getByText(/Coming in Task 4b/)).toBeInTheDocument()
    expect(screen.getByText(/Nifty trend/)).toBeInTheDocument()
  })
})
