"use client"
import { Fragment, useMemo, useState } from "react"
import type { Asset, FundMatch } from "@/lib/api"
import { formatINR } from "@/lib/format"
import { MatchBadge } from "./MatchBadge"
import { HoldingExpandedRow } from "./HoldingExpandedRow"

interface Props {
  assets: Asset[]
  matches: FundMatch[]
}

type SortKey = "value" | "pct" | "return" | "match" | null

export function HoldingsTable({ assets, matches }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>(null)

  const totalValue = assets.reduce((s, a) => s + a.current_value_inr, 0) || 1
  const matchByName = useMemo(
    () => new Map(matches.map((m) => [m.asset_name, m])),
    [matches],
  )

  const rows = useMemo(() => {
    const out = assets.map((a) => ({
      asset: a,
      pctOfPortfolio: (a.current_value_inr / totalValue) * 100,
      returnPct: a.xirr_pct ?? a.pnl_pct,
      match: matchByName.get(a.name),
    }))
    if (sortKey === "value") out.sort((a, b) => b.asset.current_value_inr - a.asset.current_value_inr)
    else if (sortKey === "pct") out.sort((a, b) => b.pctOfPortfolio - a.pctOfPortfolio)
    else if (sortKey === "return") out.sort((a, b) => (b.returnPct ?? -Infinity) - (a.returnPct ?? -Infinity))
    else if (sortKey === "match") out.sort((a, b) => {
      const order: Record<string, number> = {isin: 0, name: 1, none: 2}
      return (order[a.match?.matched_by || "none"] ?? 3) - (order[b.match?.matched_by || "none"] ?? 3)
    })
    return out
  }, [assets, matchByName, sortKey, totalValue])

  return (
    <div className="border border-rule bg-rule-soft/30">
      <table className="w-full">
        <thead>
          <tr className="border-b border-rule">
            <th className="px-4 py-2 text-left font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">Fund</th>
            <th className="px-4 py-2 text-left font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">Cat</th>
            <th onClick={() => setSortKey("value")} className="cursor-pointer px-4 py-2 text-right font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">Value</th>
            <th onClick={() => setSortKey("pct")} className="cursor-pointer px-4 py-2 text-right font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">%</th>
            <th onClick={() => setSortKey("return")} className="cursor-pointer px-4 py-2 text-right font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">Return</th>
            <th onClick={() => setSortKey("match")} className="cursor-pointer px-4 py-2 text-center font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">Match</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({asset, pctOfPortfolio, returnPct, match}) => {
            const isOpen = expanded === asset.name
            const canExpand = match?.matched && match.scheme
            return (
              <Fragment key={asset.name}>
                <tr
                  className={`fund-row border-b border-rule/40 ${canExpand ? "cursor-pointer hover:bg-brass/5" : "opacity-70"}`}
                  onClick={() => canExpand && setExpanded(isOpen ? null : asset.name)}
                >
                  <td className="px-4 py-2 font-serif text-sm text-fg">
                    <span className="mr-2 font-mono text-xs text-muted-deep">{canExpand ? (isOpen ? "▼" : "▶") : " "}</span>
                    {asset.name}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs uppercase tracking-[0.18em] text-muted-deep">
                    {asset.category || "—"}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-sm tabular-nums text-fg">
                    ₹{formatINR(asset.current_value_inr)}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-xs tabular-nums text-fg-soft">
                    {pctOfPortfolio.toFixed(1)}%
                  </td>
                  <td className={`px-4 py-2 text-right font-mono text-xs tabular-nums ${returnPct >= 0 ? "text-brass-bright" : "text-oxblood"}`}>
                    {returnPct >= 0 ? "+" : ""}{returnPct.toFixed(2)}%
                  </td>
                  <td className="px-4 py-2 text-center">
                    <MatchBadge matchedBy={match?.matched_by || "none"} />
                  </td>
                </tr>
                {isOpen && match?.scheme && (
                  <tr>
                    <td colSpan={6} className="p-0">
                      <HoldingExpandedRow scheme={match.scheme} />
                    </td>
                  </tr>
                )}
              </Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
