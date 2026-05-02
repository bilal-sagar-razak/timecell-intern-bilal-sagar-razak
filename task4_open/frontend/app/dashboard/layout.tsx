"use client"
import { useCallback, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { toast } from "sonner"
import { TabNav } from "@/components/TabNav"
import { ApiError, parseAndCompute } from "@/lib/api"
import { usePortfolio } from "@/lib/store"
import { formatINR, formatPct } from "@/lib/format"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const data = usePortfolio((s) => s.data)
  const lastFile = usePortfolio((s) => s.lastFile)
  const hasHydrated = usePortfolio((s) => s.hasHydrated)
  const setData = usePortfolio((s) => s.setData)
  const clear = usePortfolio((s) => s.clear)
  const [reparsing, setReparsing] = useState(false)

  useEffect(() => {
    if (hasHydrated && !data) router.replace("/")
  }, [hasHydrated, data, router])

  const handleReparse = useCallback(async () => {
    if (!lastFile) return
    setReparsing(true)
    try {
      const fresh = await parseAndCompute(lastFile, { force: true })
      setData(fresh)
    } catch (e) {
      const message = e instanceof ApiError
        ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
        : (e as Error).message
      toast.error(message)
    } finally {
      setReparsing(false)
    }
  }, [lastFile, setData])

  const handleUploadAnother = useCallback(() => {
    clear()
    router.push("/")
  }, [clear, router])

  if (!hasHydrated) return null
  if (!data) return null

  const { normalized, kpis } = data
  const totalPnl = normalized.summary.total_pnl_inr
  const totalPnlPct = normalized.summary.total_pnl_pct

  return (
    <div>
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-6xl items-start justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <Image src="/timecell-logo.png" alt="TimeCell" width={22} height={22} className="opacity-90" />
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-brass">TimeCell</span>
          </div>

          <div className="flex flex-col items-end gap-3">
            <div className="text-right">
              <div className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
                Portfolio Intelligence Report
              </div>
              <div className="mt-0.5 font-serif text-base text-fg">
                {normalized.holder_name || "Portfolio"}
              </div>
              <div className="mt-1 font-mono text-sm text-fg tabular-nums">
                ₹{formatINR(kpis.current_inr)}
              </div>
              <div className="mt-1 font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
                Since invested
              </div>
              <div
                className={`font-mono text-xs tabular-nums ${
                  totalPnl >= 0 ? "text-brass-bright" : "text-oxblood"
                }`}
              >
                {totalPnl >= 0 ? "+" : ""}₹{formatINR(Math.abs(totalPnl))} ({formatPct(totalPnlPct, true)})
              </div>
            </div>

            <div className="flex items-center gap-2">
              {data.cached && (
                <span className="border border-brass px-2 py-0.5 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-brass-bright">
                  cached · ₹0.00
                </span>
              )}
              {lastFile && (
                <button
                  onClick={handleReparse}
                  disabled={reparsing}
                  className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass disabled:opacity-50"
                >
                  {reparsing ? "Re-parsing…" : "↻ Re-parse"}
                </button>
              )}
              <button
                onClick={handleUploadAnother}
                className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass"
              >
                ⊕ Upload another
              </button>
            </div>
          </div>
        </div>
      </header>
      <TabNav />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  )
}
