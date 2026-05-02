"use client"
import { useEffect, useState } from "react"

const PHASES = [
  "Reading portfolio…",
  "Checking Nifty trend…",
  "Pulling news for your holdings…",
  "Stress-testing scenarios…",
]

export function AgentRunningIndicator() {
  const [phaseIdx, setPhaseIdx] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setPhaseIdx((i) => (i + 1) % PHASES.length)
    }, 3000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-6">
      <div className="flex gap-1.5">
        <span className="h-2 w-2 animate-pulse rounded-full bg-brass [animation-delay:0ms]" />
        <span className="h-2 w-2 animate-pulse rounded-full bg-brass [animation-delay:200ms]" />
        <span className="h-2 w-2 animate-pulse rounded-full bg-brass [animation-delay:400ms]" />
      </div>
      <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted-deep">
        {PHASES[phaseIdx]}
      </p>
    </div>
  )
}
