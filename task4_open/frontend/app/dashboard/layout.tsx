"use client"
import { useEffect } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { TabNav } from "@/components/TabNav"
import { usePortfolio } from "@/lib/store"
import { formatINR, formatPct } from "@/lib/format"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const data = usePortfolio((s) => s.data)

  useEffect(() => {
    if (!data) router.replace("/")
  }, [data, router])

  if (!data) return null

  const { normalized, kpis } = data
  const totalPnl = normalized.summary.total_pnl_inr
  const totalPnlPct = normalized.summary.total_pnl_pct

  return (
    <div>
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <Image src="/timecell-logo.png" alt="TimeCell" width={22} height={22} className="opacity-90" />
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-brass">TimeCell</span>
          </div>
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
        </div>
      </header>
      <TabNav />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  )
}
