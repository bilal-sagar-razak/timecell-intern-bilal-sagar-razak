import { Fragment } from "react"

interface RebalanceAdviceProps {
  markdown: string
}

const NUM_ITEM_RE = /^\s*(\d+)\.\s+(.*)$/
const BOLD_RE = /\*\*([^*]+)\*\*/g

function renderInline(text: string): React.ReactNode[] {
  const out: React.ReactNode[] = []
  let last = 0
  let key = 0
  for (const m of text.matchAll(BOLD_RE)) {
    if (m.index !== undefined && m.index > last) {
      out.push(<Fragment key={key++}>{text.slice(last, m.index)}</Fragment>)
    }
    out.push(<strong key={key++}>{m[1]}</strong>)
    last = (m.index ?? 0) + m[0].length
  }
  if (last < text.length) {
    out.push(<Fragment key={key++}>{text.slice(last)}</Fragment>)
  }
  return out
}

interface Item {
  number: string
  body: string
}

function parse(markdown: string): Item[] {
  const lines = markdown.split("\n")
  const items: Item[] = []
  let current: Item | null = null
  for (const line of lines) {
    const m = NUM_ITEM_RE.exec(line)
    if (m) {
      if (current) items.push(current)
      current = { number: m[1], body: m[2] }
    } else if (current && line.trim()) {
      current.body += " " + line.trim()
    }
  }
  if (current) items.push(current)
  return items
}

export function RebalanceAdvice({ markdown }: RebalanceAdviceProps) {
  const items = parse(markdown)
  if (items.length === 0) {
    return (
      <div className="border border-rule bg-rule-soft/30 p-5 font-serif text-sm text-fg">
        {renderInline(markdown)}
      </div>
    )
  }
  return (
    <div className="space-y-3">
      {items.map((it) => (
        <div
          key={it.number}
          className="border border-rule border-l-2 border-l-brass bg-rule-soft/30 p-5"
        >
          <div className="mb-2 font-mono text-[0.7rem] uppercase tracking-[0.22em] text-brass">
            Suggestion {it.number}
          </div>
          <p className="font-serif text-sm leading-relaxed text-fg">
            {renderInline(it.body)}
          </p>
        </div>
      ))}
    </div>
  )
}
