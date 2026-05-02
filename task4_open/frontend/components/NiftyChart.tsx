"use client"
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import type { NiftyTrend } from "@/lib/api"

interface NiftyChartProps {
  trend: NiftyTrend
}

export function NiftyChart({ trend }: NiftyChartProps) {
  const positive = trend.pct_change_period >= 0
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
          NIFTY 50
        </span>
        <span className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
          {trend.period_days}d
        </span>
      </div>
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-2xl tabular-nums text-fg">
          {trend.current.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
        </span>
        <span
          className={`font-mono text-sm tabular-nums ${
            positive ? "text-brass-bright" : "text-oxblood"
          }`}
        >
          {positive ? "+" : ""}
          {trend.pct_change_period.toFixed(2)}%
        </span>
      </div>
      <div className="mt-4 h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trend.points} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
            <XAxis dataKey="date" hide />
            <YAxis domain={["auto", "auto"]} hide />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(20,16,10,0.92)",
                border: "1px solid var(--color-rule)",
                borderRadius: 0,
                fontFamily: "var(--font-mono)",
                fontSize: "0.7rem",
              }}
              formatter={(v: number) =>
                v.toLocaleString("en-IN", { maximumFractionDigits: 0 })
              }
            />
            <Line
              type="monotone"
              dataKey="close"
              stroke={positive ? "var(--color-brass-bright)" : "var(--color-oxblood)"}
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
