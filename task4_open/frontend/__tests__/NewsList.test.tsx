import { describe, expect, test } from "vitest"
import { render, screen } from "@testing-library/react"
import { NewsList } from "@/components/NewsList"

const sampleHeadlines = [
  {
    title: "Reliance hits new high",
    publisher: "Moneycontrol",
    url: "https://example.com/1",
    published_at: "2026-01-02T10:00:00Z",
    snippet: "Stock rallies on Q3 outlook.",
  },
  {
    title: "Nifty closes flat",
    publisher: "ET",
    url: "https://example.com/2",
    published_at: "2026-01-02T09:00:00Z",
    snippet: null,
  },
]

describe("NewsList", () => {
  test("renders each headline with title and publisher", () => {
    render(<NewsList headlines={sampleHeadlines} fallbackUsed={false} />)
    expect(screen.getByText("Reliance hits new high")).toBeInTheDocument()
    expect(screen.getByText("Nifty closes flat")).toBeInTheDocument()
    expect(screen.getByText("Moneycontrol")).toBeInTheDocument()
  })

  test("shows fallback banner when fallbackUsed is true", () => {
    render(<NewsList headlines={sampleHeadlines} fallbackUsed={true} />)
    expect(
      screen.getByText(/no headlines matched your holdings/i),
    ).toBeInTheDocument()
  })

  test("shows empty state when headlines is empty", () => {
    render(<NewsList headlines={[]} fallbackUsed={false} />)
    expect(screen.getByText(/couldn't load news right now/i)).toBeInTheDocument()
  })
})
