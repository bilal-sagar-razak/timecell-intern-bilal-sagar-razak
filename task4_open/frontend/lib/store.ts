import { useEffect, useState } from "react"
import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"
import type { MarketSnapshot, ParseAndComputeResponse, RebalanceResult } from "./api"

interface PortfolioState {
  data: ParseAndComputeResponse | null
  lastFile: File | null
  marketSnapshot: MarketSnapshot | null
  rebalanceResult: RebalanceResult | null
  setData: (d: ParseAndComputeResponse | null) => void
  setLastFile: (f: File | null) => void
  setMarketSnapshot: (s: MarketSnapshot | null) => void
  setRebalanceResult: (r: RebalanceResult | null) => void
  clear: () => void
}

export const usePortfolio = create<PortfolioState>()(
  persist(
    (set) => ({
      data: null,
      lastFile: null,
      marketSnapshot: null,
      rebalanceResult: null,
      setData: (d) => set({ data: d }),
      setLastFile: (f) => set({ lastFile: f }),
      setMarketSnapshot: (s) => set({ marketSnapshot: s }),
      setRebalanceResult: (r) => set({ rebalanceResult: r }),
      clear: () => {
        set({
          data: null,
          lastFile: null,
          marketSnapshot: null,
          rebalanceResult: null,
        })
        if (typeof window !== "undefined") {
          localStorage.removeItem("timecell-portfolio-v1")
        }
      },
    }),
    {
      name: "timecell-portfolio-v1",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ data: s.data }),
    },
  ),
)

/** True once Zustand finishes reading localStorage. Component-safe. */
export function useHasHydrated(): boolean {
  const [hydrated, setHydrated] = useState(false)
  useEffect(() => {
    setHydrated(usePortfolio.persist.hasHydrated())
    const unsub = usePortfolio.persist.onFinishHydration(() => setHydrated(true))
    return unsub
  }, [])
  return hydrated
}
