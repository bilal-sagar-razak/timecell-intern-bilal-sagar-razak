"use client"
import { useState } from "react"
import type { AmfiScheme } from "@/lib/api"
import { formatINR } from "@/lib/format"

interface Props {
  scheme: AmfiScheme
}

export function HoldingExpandedRow({ scheme }: Props) {
  const [showAll, setShowAll] = useState(false)
  const sorted = [...scheme.holdings].sort((a, b) => b.weight_pct - a.weight_pct)
  const visible = showAll ? sorted : sorted.slice(0, 10)
  const remaining = sorted.length - visible.length

  return (
    <div className="border-l-2 border-brass/40 bg-rule-soft/20 px-5 py-3">
      <div className="mb-2 flex items-baseline justify-between">
        <span className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
          Top holdings (snapshot {scheme.as_of_date})
        </span>
        <span className="font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep">
          AMC: {scheme.amc}
        </span>
      </div>
      <table className="w-full">
        <tbody>
          {visible.map((h) => (
            <tr key={h.isin || h.name} className="border-b border-rule/30">
              <td className="py-1 font-serif text-sm text-fg">{h.name}</td>
              <td className="py-1 text-right font-mono text-xs tabular-nums text-fg">
                {h.weight_pct.toFixed(2)}%
              </td>
              <td className="py-1 text-right font-mono text-xs tabular-nums text-fg-soft">
                ₹{formatINR(h.value_inr)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {remaining > 0 && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-2 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass"
        >
          show all {sorted.length}
        </button>
      )}
      <div className="mt-2 font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
        Cash &amp; equivalents: {scheme.cash_pct.toFixed(2)}%
      </div>
    </div>
  )
}
