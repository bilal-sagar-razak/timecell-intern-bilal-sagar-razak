"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"

const TABS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/holdings", label: "Holdings" },
  { href: "/dashboard/market", label: "Market" },
  { href: "/dashboard/rebalance", label: "Rebalance" },
]

export function TabNav() {
  const pathname = usePathname()
  return (
    <nav className="border-b border-rule">
      <div className="mx-auto flex max-w-6xl gap-8 px-6">
        {TABS.map((t) => {
          const active = pathname === t.href
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`relative py-4 font-mono text-xs uppercase tracking-[0.22em] transition-colors ${
                active ? "text-brass" : "text-muted-deep hover:text-fg-soft"
              }`}
            >
              {t.label}
              {active && <span className="absolute bottom-[-1px] left-0 right-0 h-px bg-brass" />}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
