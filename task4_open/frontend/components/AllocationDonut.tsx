"use client"
import { useState } from "react"
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts"
import { colors, donutPalette } from "@/lib/theme"
import { formatINR } from "@/lib/format"

interface AllocationDonutProps {
  slices: { label: string; value_inr: number; pct: number }[]
  totalInr: number
}

export function AllocationDonut({ slices, totalInr }: AllocationDonutProps) {
  const [activeIdx, setActiveIdx] = useState<number | null>(null)
  const active = activeIdx !== null ? slices[activeIdx] : null
  const centerLabel = active ? active.label : "Total"
  const centerValue = active ? `₹${formatINR(active.value_inr)}` : `₹${formatINR(totalInr)}`
  const centerSub = active ? `${active.pct.toFixed(1)}%` : null

  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        Allocation
      </div>
      <div className="relative h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={slices}
              dataKey="value_inr"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="90%"
              stroke={colors.bg}
              strokeWidth={2}
              onMouseEnter={(_, i) => setActiveIdx(i)}
              onMouseLeave={() => setActiveIdx(null)}
            >
              {slices.map((_, i) => {
                const isActive = activeIdx === i
                const dimmed = activeIdx !== null && !isActive
                return (
                  <Cell
                    key={i}
                    fill={donutPalette[i % donutPalette.length]}
                    fillOpacity={dimmed ? 0.35 : 1}
                    style={{ transition: "fill-opacity 120ms" }}
                  />
                )
              })}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <div className="font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep">
            {centerLabel}
          </div>
          <div className="font-mono text-lg text-fg tabular-nums">{centerValue}</div>
          {centerSub && (
            <div className="font-mono text-[0.65rem] tabular-nums text-brass-bright">{centerSub}</div>
          )}
        </div>
      </div>
      <ul className="mt-4 space-y-1 font-mono text-xs">
        {slices.map((s, i) => {
          const isActive = activeIdx === i
          const dimmed = activeIdx !== null && !isActive
          return (
            <li
              key={s.label}
              onMouseEnter={() => setActiveIdx(i)}
              onMouseLeave={() => setActiveIdx(null)}
              className={`flex cursor-default items-center justify-between transition-opacity ${
                dimmed ? "opacity-40" : "opacity-100"
              }`}
            >
              <span
                className={`flex items-center gap-2 ${isActive ? "text-brass-bright" : "text-fg-soft"}`}
              >
                <span
                  className="inline-block h-2.5 w-2.5"
                  style={{ background: donutPalette[i % donutPalette.length] }}
                />
                {s.label}
              </span>
              <span className={`tabular-nums ${isActive ? "text-brass-bright" : "text-muted"}`}>
                {s.pct.toFixed(1)}%
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
