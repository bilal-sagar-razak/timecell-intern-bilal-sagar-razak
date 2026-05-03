"use client"
import type { OverlapResponse } from "@/lib/api"

interface Props {
  data: OverlapResponse
  onSelect: (i: number, j: number) => void
  selected?: { i: number; j: number } | null
}

function shadeFor(pct: number): string {
  const opacity = Math.max(0.05, Math.min(1, pct / 100))
  return `rgba(176, 141, 87, ${opacity.toFixed(3)})`
}

export function OverlapHeatmap({ data, onSelect, selected }: Props) {
  const n = data.funds.length
  if (n < 2) {
    return (
      <div className="border border-rule bg-rule-soft/30 px-5 py-8 text-center font-mono text-xs text-muted-deep">
        Need at least 2 matched funds to compute overlap.
      </div>
    )
  }
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        Fund overlap
      </div>
      <div
        className="grid gap-1"
        style={{ gridTemplateColumns: `8rem repeat(${n}, minmax(2.5rem, 1fr))` }}
      >
        <div></div>
        {data.funds.map((f, j) => (
          <div key={`col-${j}`} className="group relative">
            <div className="cursor-help overflow-hidden text-ellipsis whitespace-nowrap font-mono text-[0.6rem] uppercase tracking-[0.18em] text-muted-deep">
              {f.asset_name}
            </div>
            <div className="pointer-events-none invisible absolute bottom-full left-1/2 z-20 mb-1 -translate-x-1/2 whitespace-nowrap border border-rule bg-bg px-2 py-1 font-serif text-xs text-fg shadow-lg group-hover:visible">
              {f.asset_name}
            </div>
          </div>
        ))}
        {data.funds.map((rowFund, i) => (
          <div key={`row-${i}`} className="contents">
            <div className="group relative self-center">
              <div className="cursor-help overflow-hidden text-ellipsis whitespace-nowrap font-mono text-[0.65rem] uppercase tracking-[0.18em] text-muted-deep">
                {rowFund.asset_name}
              </div>
              <div className="pointer-events-none invisible absolute left-0 top-full z-20 mt-1 whitespace-nowrap border border-rule bg-bg px-2 py-1 font-serif text-xs text-fg shadow-lg group-hover:visible">
                {rowFund.asset_name}
              </div>
            </div>
            {data.funds.map((_, j) => {
              const cell = data.matrix[i][j]
              const isDiag = i === j
              const isUpper = j > i
              const isSel = selected && selected.i === Math.min(i, j) && selected.j === Math.max(i, j)
              if (!isUpper) {
                return (
                  <div key={`c-${i}-${j}`} className="h-8" aria-hidden="true">
                    {isDiag && (
                      <div className="h-full w-full bg-rule/30 text-center text-[0.55rem] leading-8 text-muted-deep">·</div>
                    )}
                  </div>
                )
              }
              return (
                <button
                  key={`c-${i}-${j}`}
                  data-cell-pair={`${i}_${j}`}
                  onClick={() => onSelect(i, j)}
                  className={`h-8 transition-opacity hover:ring-1 hover:ring-brass-bright ${isSel ? "ring-2 ring-brass-bright" : ""}`}
                  style={{ backgroundColor: shadeFor(cell.overlap_pct) }}
                  title={`${rowFund.asset_name} ↔ ${data.funds[j].asset_name}: ${cell.overlap_pct.toFixed(1)}%`}
                >
                  <span className="font-mono text-[0.6rem] tabular-nums text-fg">
                    {cell.overlap_pct >= 5 ? cell.overlap_pct.toFixed(0) : ""}
                  </span>
                </button>
              )
            })}
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-3 font-mono text-[0.6rem] uppercase tracking-[0.18em] text-muted-deep">
        <span>Match: <span style={{ background: shadeFor(5) }} className="ml-1 inline-block h-3 w-3 align-middle"></span> &lt;10%</span>
        <span><span style={{ background: shadeFor(20) }} className="inline-block h-3 w-3 align-middle"></span> 10-30%</span>
        <span><span style={{ background: shadeFor(50) }} className="inline-block h-3 w-3 align-middle"></span> 30%+</span>
      </div>
    </div>
  )
}
