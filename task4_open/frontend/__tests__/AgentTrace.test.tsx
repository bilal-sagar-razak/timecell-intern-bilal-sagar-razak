import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { AgentTrace } from "@/components/AgentTrace"

const sampleTrace = [
  {
    tool_name: "compute_concentration",
    input_json: { threshold_pct: 15 },
    output_json: { over_threshold: [{ name: "Reliance", pct: 65 }] },
    ts: "2026-01-02T10:00:00Z",
    duration_ms: 5,
  },
  {
    tool_name: "get_nifty_trend",
    input_json: { period_days: 90 },
    output_json: { current: 22000, period_days: 90 },
    ts: "2026-01-02T10:00:01Z",
    duration_ms: 3,
  },
]

describe("AgentTrace", () => {
  test("renders details summary with tool count", () => {
    render(<AgentTrace trace={sampleTrace} />)
    expect(
      screen.getByText(/Agent thought process — 2 tool calls/i),
    ).toBeInTheDocument()
  })

  test("lists each tool call name in chronological order", () => {
    render(<AgentTrace trace={sampleTrace} />)
    const items = screen.getAllByText(/compute_concentration|get_nifty_trend/)
    expect(items[0].textContent).toContain("compute_concentration")
    expect(items[1].textContent).toContain("get_nifty_trend")
  })
})
