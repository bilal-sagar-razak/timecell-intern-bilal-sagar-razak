import { useEffect, useState } from "react"
import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"
import type { ParseAndComputeResponse } from "./api"

interface PortfolioState {
  data: ParseAndComputeResponse | null
  lastFile: File | null
  setData: (d: ParseAndComputeResponse | null) => void
  setLastFile: (f: File | null) => void
  clear: () => void
}

export const usePortfolio = create<PortfolioState>()(
  persist(
    (set) => ({
      data: null,
      lastFile: null,
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
