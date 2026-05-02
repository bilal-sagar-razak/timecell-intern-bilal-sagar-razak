interface SubBreakdown {
  label: string
  pnlInr: string
  cagrPct: string | null
  isPositive: boolean
}

interface CategoryCardProps {
  category: string
  pnlInr: string
  cagrPct: string | null
  isPositive: boolean
  subBreakdowns?: SubBreakdown[]
}

export function CategoryCard({ category, pnlInr, cagrPct, isPositive, subBreakdowns }: CategoryCardProps) {
  const accent = isPositive ? "border-l-brass" : "border-l-oxblood"
  const valueColor = isPositive ? "text-brass-bright" : "text-oxblood"
  return (
    <div className={`border border-rule border-l-2 ${accent} bg-rule-soft/30 px-5 py-4`}>
      <div className="font-serif text-base text-fg">{category}</div>
      <div className="mt-3 flex justify-between font-mono text-sm">
        <span className="text-muted-deep">P&amp;L</span>
        <span className={`tabular-nums ${valueColor}`}>{pnlInr}</span>
      </div>
      {cagrPct !== null && (
        <div className="mt-1 flex justify-between font-mono text-sm">
          <span className="text-muted-deep">CAGR</span>
          <span className={`tabular-nums ${valueColor}`}>{cagrPct}</span>
        </div>
      )}
      {subBreakdowns && subBreakdowns.length > 0 && (
        <ul className="mt-4 space-y-1.5 border-t border-rule pt-3 font-mono text-xs">
          {subBreakdowns.map((s) => (
            <li key={s.label} className="flex items-center justify-between gap-3">
              <span className="truncate text-fg-soft">{s.label}</span>
              <span className="flex shrink-0 items-baseline gap-2 tabular-nums">
                <span className={s.isPositive ? "text-brass-bright" : "text-oxblood"}>
                  {s.pnlInr}
                </span>
                {s.cagrPct !== null && (
                  <span className={`text-[0.65rem] ${s.isPositive ? "text-brass" : "text-oxblood"}`}>
                    {s.cagrPct}
                  </span>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
