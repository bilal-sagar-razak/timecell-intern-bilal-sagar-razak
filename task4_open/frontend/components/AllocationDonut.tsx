"use client"
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts"
import { colors, donutPalette } from "@/lib/theme"
import { formatINR } from "@/lib/format"

interface AllocationDonutProps {
  slices: { label: string; value_inr: number; pct: number }[]
  totalInr: number
}

export function AllocationDonut({ slices, totalInr }: AllocationDonutProps) {
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
            >
              {slices.map((_, i) => (
                <Cell key={i} fill={donutPalette[i % donutPalette.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <div className="font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep">Total</div>
          <div className="font-mono text-lg text-fg tabular-nums">₹{formatINR(totalInr)}</div>
        </div>
      </div>
      <ul className="mt-4 space-y-1 font-mono text-xs">
        {slices.map((s, i) => (
          <li key={s.label} className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-fg-soft">
              <span
                className="inline-block h-2.5 w-2.5"
                style={{ background: donutPalette[i % donutPalette.length] }}
              />
              {s.label}
            </span>
            <span className="tabular-nums text-muted">{s.pct.toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
