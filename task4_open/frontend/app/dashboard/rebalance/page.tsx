"use client"
import { useCallback, useState } from "react"
import { toast } from "sonner"
import { ApiError, runRebalance } from "@/lib/api"
import { usePortfolio } from "@/lib/store"
import { RebalanceAdvice } from "@/components/RebalanceAdvice"
import { AgentTrace } from "@/components/AgentTrace"
import { AgentRunningIndicator } from "@/components/AgentRunningIndicator"

export default function RebalancePage() {
  const data = usePortfolio((s) => s.data)
  const result = usePortfolio((s) => s.rebalanceResult)
  const setResult = usePortfolio((s) => s.setRebalanceResult)
  const [busy, setBusy] = useState(false)

  const run = useCallback(async () => {
    if (!data || busy) return
    setBusy(true)
    try {
      const r = await runRebalance(data.normalized)
      setResult(r)
    } catch (e) {
      const msg = e instanceof ApiError
        ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
        : (e as Error).message
      toast.error(msg)
    } finally {
      setBusy(false)
    }
  }, [data, busy, setResult])

  if (!data) return null
  if (busy) return <AgentRunningIndicator />

  if (!result) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-6">
        <p className="max-w-md text-center font-serif text-base text-fg-soft">
          Generate a rebalance plan tailored to your holdings, market conditions, and risk band.
          The Anthropic Sonnet agent runs 4 tools and produces 2–3 actionable suggestions.
        </p>
        <button
          onClick={run}
          disabled={busy}
          className="border border-brass px-6 py-2 font-mono text-xs uppercase tracking-[0.22em] text-brass-bright hover:bg-brass/10 disabled:opacity-50"
        >
          Generate rebalance plan
        </button>
        <p className="font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted-deep">
          ~$0.05 per run
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="font-serif text-xl text-fg">Rebalance plan</h2>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
            ${result.cost_usd.toFixed(4)} · {result.iterations} iter
          </span>
          <button
            onClick={run}
            disabled={busy}
            className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep hover:text-brass disabled:opacity-50"
          >
            ↻ Re-run
          </button>
        </div>
      </div>
      {result.truncated && (
        <div
          role="status"
          className="border-l-2 border-oxblood bg-oxblood/5 px-4 py-2 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-oxblood"
        >
          Agent didn&apos;t finalise within 8 iterations — partial advice below.
        </div>
      )}
      <RebalanceAdvice markdown={result.advice_markdown} />
      <AgentTrace trace={result.trace} />
    </div>
  )
}
