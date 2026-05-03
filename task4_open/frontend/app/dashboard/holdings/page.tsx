"use client"
import { useCallback, useEffect, useMemo, useState } from "react"
import { toast } from "sonner"
import {
  ApiError, fetchHoldingsPerFund, fetchOverlap,
} from "@/lib/api"
import { usePortfolio } from "@/lib/store"
import { HoldingsTable } from "@/components/HoldingsTable"
import { OverlapHeatmap } from "@/components/OverlapHeatmap"
import { OverlapDrilldown } from "@/components/OverlapDrilldown"

export default function HoldingsPage() {
  const data = usePortfolio((s) => s.data)
  const holdings = usePortfolio((s) => s.holdingsData)
  const overlap = usePortfolio((s) => s.overlapData)
  const setHoldings = usePortfolio((s) => s.setHoldingsData)
  const setOverlap = usePortfolio((s) => s.setOverlapData)
  const [loading, setLoading] = useState(false)
  const [selectedPair, setSelectedPair] = useState<{ i: number; j: number } | null>(null)

  const load = useCallback(async () => {
    if (!data) return
    setLoading(true)
    try {
      const [h, o] = await Promise.all([
        fetchHoldingsPerFund(data.normalized),
        fetchOverlap(data.normalized),
      ])
      setHoldings(h)
      setOverlap(o)
    } catch (e) {
      const msg = e instanceof ApiError
        ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
        : (e as Error).message
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }, [data, setHoldings, setOverlap])

  useEffect(() => {
    if (data && (!holdings || !overlap)) {
      void load()
    }
  }, [data, holdings, overlap, load])

  const drilldown = useMemo(() => {
    if (!overlap || !selectedPair) return null
    const i = Math.min(selectedPair.i, selectedPair.j)
    const j = Math.max(selectedPair.i, selectedPair.j)
    const key = `${i}_${j}`
    return {
      fundA: overlap.funds[i].asset_name,
      fundB: overlap.funds[j].asset_name,
      shared: overlap.shared_stocks_index[key] || [],
    }
  }, [overlap, selectedPair])

  if (!data) return null

  const unmatched = holdings?.matches.filter((m) => !m.matched) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-xl text-fg">Fund overlap</h2>
        <button
          onClick={() => void load()}
          disabled={loading}
          className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass disabled:opacity-50"
        >
          {loading ? "Loading…" : "↻ Reload data"}
        </button>
      </div>

      {overlap && overlap.funds.length >= 2 ? (
        <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
          <OverlapHeatmap data={overlap} onSelect={(i, j) => setSelectedPair({ i, j })} selected={selectedPair} />
          <OverlapDrilldown selected={drilldown} />
        </div>
      ) : overlap ? (
        <div className="border border-rule bg-rule-soft/30 px-5 py-8 text-center font-mono text-xs text-muted-deep">
          Need at least 2 matched funds to compute overlap.
        </div>
      ) : (
        <div className="flex min-h-[20vh] items-center justify-center">
          <span className="font-mono text-sm text-muted-deep">Loading overlap…</span>
        </div>
      )}

      <hr className="border-rule" />

      <h2 className="font-serif text-xl text-fg">Your funds</h2>
      {holdings ? (
        <HoldingsTable assets={data.normalized.assets} matches={holdings.matches} />
      ) : (
        <div className="flex min-h-[20vh] items-center justify-center">
          <span className="font-mono text-sm text-muted-deep">Loading per-fund data…</span>
        </div>
      )}

      {unmatched.length > 0 && (
        <details className="border border-rule bg-rule-soft/20 p-4">
          <summary className="cursor-pointer font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">
            {unmatched.length} fund{unmatched.length === 1 ? "" : "s"} excluded from matrix (no AMFI match)
          </summary>
          <ul className="mt-2 space-y-1 font-serif text-sm text-fg-soft">
            {unmatched.map((m) => <li key={m.asset_name}>• {m.asset_name}</li>)}
          </ul>
        </details>
      )}
    </div>
  )
}
