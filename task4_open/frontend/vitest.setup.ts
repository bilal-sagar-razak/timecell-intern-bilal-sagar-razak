import "@testing-library/jest-dom/vitest"
import { vi } from "vitest"
import * as React from "react"

class ResizeObserverPolyfill {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = globalThis.ResizeObserver || (ResizeObserverPolyfill as unknown as typeof ResizeObserver)

vi.mock("recharts", async () => {
  const actual = await vi.importActual<typeof import("recharts")>("recharts")
  const Mock = ({ children }: { children: React.ReactElement }) => {
    const child = React.Children.only(children)
    return React.cloneElement(child, { width: 600, height: 400 } as Record<string, number>)
  }
  return { ...actual, ResponsiveContainer: Mock }
})
