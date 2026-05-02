interface KpiCardProps {
  label: string
  value: string
  subline?: string
}

export function KpiCard({ label, value, subline }: KpiCardProps) {
  return (
    <div className="border border-rule bg-rule-soft/30 px-5 py-4">
      <div className="font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
        {label}
      </div>
      <div className="mt-2 font-mono text-2xl text-fg tabular-nums">
        {value}
      </div>
      {subline && (
        <div className="mt-1 font-mono text-xs text-fg-soft tabular-nums">
          {subline}
        </div>
      )}
    </div>
  )
}
