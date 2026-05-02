"use client"
import { AllocationDonut } from "@/components/AllocationDonut"
import { CategoryCard } from "@/components/CategoryCard"
import { KpiCard } from "@/components/KpiCard"
import { XirrBarChart } from "@/components/XirrBarChart"
import { formatINR, formatPct } from "@/lib/format"
import { usePortfolio } from "@/lib/store"

export default function OverviewPage() {
  const data = usePortfolio((s) => s.data)
  if (!data) return null

  const { kpis, allocation, xirr_by_fund, category_performance } = data
  const equityValue = kpis.current_inr * (kpis.equity_pct / 100)
  const debtValue = kpis.current_inr * (kpis.debt_pct / 100)

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Invested"
          value={`₹${formatINR(kpis.invested_inr)}`}
          subline={`${kpis.asset_count} ${kpis.asset_count === 1 ? "scheme" : "schemes"}`}
        />
        <KpiCard
          label="Current"
          value={`₹${formatINR(kpis.current_inr)}`}
          subline={kpis.overall_xirr_pct !== null ? `XIRR ${formatPct(kpis.overall_xirr_pct)}` : undefined}
        />
        <KpiCard
          label="Equity"
          value={`${kpis.equity_pct.toFixed(1)}%`}
          subline={`₹${formatINR(equityValue)}`}
        />
        <KpiCard
          label="Debt"
          value={`${kpis.debt_pct.toFixed(1)}%`}
          subline={`₹${formatINR(debtValue)}`}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <AllocationDonut slices={allocation} totalInr={kpis.current_inr} />
        </div>
        <div className="lg:col-span-2">
          <XirrBarChart entries={xirr_by_fund} />
        </div>
      </div>

      {category_performance.length > 0 ? (
        <div>
          <h2 className="mb-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
            Category Performance
          </h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {category_performance.map((c) => (
              <CategoryCard
                key={c.category}
                category={c.category}
                pnlInr={`${c.pnl_inr >= 0 ? "+" : ""}₹${formatINR(Math.abs(c.pnl_inr))}`}
                cagrPct={c.cagr_pct !== null ? formatPct(c.cagr_pct, true) : null}
                isPositive={c.pnl_inr >= 0}
                subBreakdowns={c.sub_breakdowns.map((b) => ({
                  label: b.label,
                  pnlInr: `${b.pnl_inr >= 0 ? "+" : ""}₹${formatINR(Math.abs(b.pnl_inr))}`,
                  cagrPct: b.cagr_pct !== null ? formatPct(b.cagr_pct, true) : null,
                  isPositive: b.pnl_inr >= 0,
                }))}
              />
            ))}
          </div>
        </div>
      ) : null}

      {data.normalized.parser_warnings.length > 0 && (
        <details className="border border-rule bg-rule-soft/30 p-4">
          <summary className="cursor-pointer font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
            Parser notes ({data.normalized.parser_warnings.length})
          </summary>
          <ul className="mt-3 space-y-1 font-mono text-xs text-fg-soft">
            {data.normalized.parser_warnings.map((w, i) => (
              <li key={i}>• {w}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
