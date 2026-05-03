import type { SharedStock } from "@/lib/api"

interface Props {
  selected: { fundA: string; fundB: string; shared: SharedStock[] } | null
}

export function OverlapDrilldown({ selected }: Props) {
  if (selected === null) {
    return (
      <div className="border border-rule bg-rule-soft/20 px-5 py-8 text-center font-mono text-xs uppercase tracking-[0.18em] text-muted-deep">
        Click a cell to see shared stocks
      </div>
    )
  }
  const sorted = [...selected.shared].sort((a, b) => b.min - a.min)
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-2 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        Shared stocks
      </div>
      <div className="mb-3 font-serif text-sm text-fg">
        {selected.fundA} ↔ {selected.fundB}
      </div>
      {sorted.length === 0 ? (
        <div className="font-mono text-xs text-muted-deep">No shared stocks.</div>
      ) : (
        <ul className="divide-y divide-rule/40">
          {sorted.map((s) => (
            <li key={s.isin || s.name} className="shared-stock-row py-2">
              <div className="font-serif text-sm text-fg">{s.name}</div>
              <div className="mt-0.5 flex gap-4 font-mono text-[0.65rem] tabular-nums text-fg-soft">
                <span>{selected.fundA}: {s.weight_a.toFixed(2)}%</span>
                <span>{selected.fundB}: {s.weight_b.toFixed(2)}%</span>
                <span className="text-brass-bright">min {s.min.toFixed(2)}%</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
