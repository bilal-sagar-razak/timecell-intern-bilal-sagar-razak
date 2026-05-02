import { create } from "zustand"
import type { ParseAndComputeResponse } from "./api"

interface PortfolioState {
  data: ParseAndComputeResponse | null
  setData: (d: ParseAndComputeResponse | null) => void
  clear: () => void
}

export const usePortfolio = create<PortfolioState>((set) => ({
  data: null,
  setData: (d) => set({ data: d }),
  clear: () => set({ data: null }),
}))
