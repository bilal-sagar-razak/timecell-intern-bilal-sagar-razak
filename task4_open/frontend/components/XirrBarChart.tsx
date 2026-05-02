"use client"
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts"
import { colors } from "@/lib/theme"

interface XirrBarChartProps {
  entries: { name: string; xirr_pct: number; color: "positive" | "negative" }[]
}

export function XirrBarChart({ entries }: XirrBarChartProps) {
  const height = Math.max(280, entries.length * 28)
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        Return by Fund
      </div>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={entries} layout="vertical" margin={{ left: 10, right: 40, top: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="name"
              width={170}
              tick={{ fill: colors.fgSoft, fontSize: 12, fontFamily: "var(--font-fraunces)" }}
              axisLine={false}
              tickLine={false}
            />
            <Bar
              dataKey="xirr_pct"
              radius={[0, 2, 2, 0]}
              label={{
                position: "right",
                fill: colors.fg,
                fontSize: 11,
                fontFamily: "var(--font-geist-mono)",
                formatter: (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`,
              }}
            >
              {entries.map((e, i) => (
                <Cell key={i} fill={e.color === "positive" ? colors.brass : colors.oxblood} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
