"use client"
import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"
import { ApiError, fetchMarketSnapshot } from "@/lib/api"
import { usePortfolio } from "@/lib/store"
import { NiftyChart } from "@/components/NiftyChart"
import { NewsList } from "@/components/NewsList"

export default function MarketPage() {
  const data = usePortfolio((s) => s.data)
  const snapshot = usePortfolio((s) => s.marketSnapshot)
  const setSnapshot = usePortfolio((s) => s.setMarketSnapshot)
  const [loading, setLoading] = useState(false)

  const load = useCallback(
    async (refresh: boolean) => {
      if (!data) return
      setLoading(true)
      try {
        const fresh = await fetchMarketSnapshot(data.normalized, { refresh })
        setSnapshot(fresh)
      } catch (e) {
        const msg = e instanceof ApiError
          ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
          : (e as Error).message
        toast.error(msg)
      } finally {
        setLoading(false)
      }
    },
    [data, setSnapshot],
  )

  useEffect(() => {
    if (data && !snapshot) {
      void load(false)
    }
  }, [data, snapshot, load])

  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-xl text-fg">Market</h2>
        <button
          onClick={() => void load(true)}
          disabled={loading}
          className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass disabled:opacity-50"
        >
          {loading ? "Refreshing…" : "↻ Refresh market"}
        </button>
      </div>
      {snapshot ? (
        <>
          <NiftyChart trend={snapshot.nifty_trend} />
          <NewsList headlines={snapshot.news} fallbackUsed={snapshot.news_fallback_used} />
        </>
      ) : (
        <div className="flex min-h-[40vh] items-center justify-center">
          <span className="font-mono text-sm text-muted-deep">Loading market data…</span>
        </div>
      )}
    </div>
  )
}
