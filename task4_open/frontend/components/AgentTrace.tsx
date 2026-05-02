"use client"
import { useState } from "react"
import type { ToolCall } from "@/lib/api"

interface AgentTraceProps {
  trace: ToolCall[]
}

function summarize(input: Record<string, unknown>): string {
  const parts = Object.entries(input).map(([k, v]) => `${k}=${JSON.stringify(v)}`)
  const joined = parts.join(", ")
  return joined.length > 60 ? joined.slice(0, 60) + "…" : joined
}

function relativeStart(trace: ToolCall[], idx: number): string {
  if (idx === 0 || trace.length === 0) return "+0.0s"
  const t0 = new Date(trace[0].ts).getTime()
  const ti = new Date(trace[idx].ts).getTime()
  return `+${((ti - t0) / 1000).toFixed(1)}s`
}

export function AgentTrace({ trace }: AgentTraceProps) {
  const [openIdx, setOpenIdx] = useState<number | null>(null)
  return (
    <details className="border border-rule bg-rule-soft/30 p-5">
      <summary className="cursor-pointer font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass">
        Agent thought process — {trace.length} tool call{trace.length === 1 ? "" : "s"}
      </summary>
      {trace.length === 0 ? (
        <p className="mt-3 font-mono text-xs text-muted-deep">
          (No tool calls were made.)
        </p>
      ) : (
        <ol className="mt-3 space-y-2">
          {trace.map((call, idx) => (
            <li key={idx} className="border-l border-rule pl-3">
              <button
                type="button"
                onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                className="block w-full text-left font-mono text-xs text-fg hover:text-brass"
              >
                <span className="text-muted-deep">{relativeStart(trace, idx)}</span>{" "}
                <span>
                  {call.tool_name}({summarize(call.input_json)})
                </span>
              </button>
              {openIdx === idx && (
                <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-all border border-rule bg-bg-deep p-2 font-mono text-[0.65rem] text-fg-soft">
                  {JSON.stringify({ input: call.input_json, output: call.output_json }, null, 2)}
                </pre>
              )}
            </li>
          ))}
        </ol>
      )}
    </details>
  )
}
