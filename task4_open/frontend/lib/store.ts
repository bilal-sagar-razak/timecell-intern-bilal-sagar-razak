import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"
import type { ParseAndComputeResponse } from "./api"

interface PortfolioState {
  data: ParseAndComputeResponse | null
  lastFile: File | null
  hasHydrated: boolean
  setData: (d: ParseAndComputeResponse | null) => void
  setLastFile: (f: File | null) => void
  clear: () => void
}

export const usePortfolio = create<PortfolioState>()(
  persist(
    (set) => ({
      data: null,
      lastFile: null,
      hasHydrated: false,
      setData: (d) => set({ data: d }),
      setLastFile: (f) => set({ lastFile: f }),
      clear: () => {
        set({ data: null, lastFile: null })
        if (typeof window !== "undefined") {
          localStorage.removeItem("timecell-portfolio-v1")
        }
      },
    }),
    {
      name: "timecell-portfolio-v1",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ data: s.data }),
      onRehydrateStorage: () => () => {
        usePortfolio.setState({ hasHydrated: true })
      },
    },
  ),
)
