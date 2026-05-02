/** Indian-grouping INR formatter. 10000000 → "1,00,00,000". */
export function formatINR(amount: number): string {
  const n = Math.round(amount)
  const sign = n < 0 ? "-" : ""
  const s = String(Math.abs(n))
  if (s.length <= 3) return `${sign}${s}`
  let head = s.slice(0, -3)
  const tail = s.slice(-3)
  const groups: string[] = []
  while (head.length > 2) {
    groups.unshift(head.slice(-2))
    head = head.slice(0, -2)
  }
  if (head) groups.unshift(head)
  return `${sign}${groups.join(",")},${tail}`
}

/** Format a percentage with sign and 2 decimal places. */
export function formatPct(pct: number, withSign = false): string {
  const sign = withSign && pct > 0 ? "+" : ""
  return `${sign}${pct.toFixed(2)}%`
}
