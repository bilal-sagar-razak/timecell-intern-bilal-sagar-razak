type Match = "isin" | "name" | "none"

const STYLES: Record<Match, string> = {
  isin: "border-brass text-brass-bright",
  name: "border-brass/50 text-brass",
  none: "border-oxblood text-oxblood",
}

const LABEL: Record<Match, string> = {
  isin: "ISIN",
  name: "name",
  none: "none",
}

export function MatchBadge({ matchedBy }: { matchedBy: Match }) {
  return (
    <span
      className={`inline-block border px-1.5 py-0.5 font-mono text-[0.55rem] uppercase tracking-[0.18em] ${STYLES[matchedBy]}`}
    >
      {LABEL[matchedBy]}
    </span>
  )
}
