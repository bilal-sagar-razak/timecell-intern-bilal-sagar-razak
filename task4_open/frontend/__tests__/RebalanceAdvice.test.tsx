import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { RebalanceAdvice } from "@/components/RebalanceAdvice"

describe("RebalanceAdvice", () => {
  test("renders numbered items", () => {
    const md = "1. Trim Reliance — Evidence: foo.\n2. Hold Gilt Fund — Evidence: bar."
    render(<RebalanceAdvice markdown={md} />)
    expect(screen.getByText(/Trim Reliance/)).toBeInTheDocument()
    expect(screen.getByText(/Hold Gilt Fund/)).toBeInTheDocument()
  })

  test("parses bold markdown into <strong>", () => {
    const md = "1. **Trim Reliance** by 10%."
    const { container } = render(<RebalanceAdvice markdown={md} />)
    const strong = container.querySelector("strong")
    expect(strong).not.toBeNull()
    expect(strong?.textContent).toBe("Trim Reliance")
  })
})
