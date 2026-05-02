interface CategoryCardProps {
  category: string
  pnlInr: string
  cagrPct: string | null
  isPositive: boolean
}

export function CategoryCard({ category, pnlInr, cagrPct, isPositive }: CategoryCardProps) {
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
    </div>
  )
}
