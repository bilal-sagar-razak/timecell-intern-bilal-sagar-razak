import { Fragment } from "react"

interface RebalanceAdviceProps {
  markdown: string
}

const NUM_ITEM_RE = /^\s*(\d+)\.\s+(.*)$/
const SEPARATOR_RE = /^\s*-{3,}\s*$/
const BOLD_RE = /\*\*([^*]+)\*\*/g
const CODE_RE = /`([^`]+)`/g

function renderInline(text: string): React.ReactNode[] {
  const tokens: { type: "text" | "bold" | "code"; value: string }[] = []
  let cursor = 0
  type Match = { index: number; length: number; type: "bold" | "code"; value: string }
  const matches: Match[] = []
  for (const m of text.matchAll(BOLD_RE)) {
    if (m.index !== undefined) matches.push({ index: m.index, length: m[0].length, type: "bold", value: m[1] })
  }
  for (const m of text.matchAll(CODE_RE)) {
    if (m.index !== undefined) matches.push({ index: m.index, length: m[0].length, type: "code", value: m[1] })
  }
  matches.sort((a, b) => a.index - b.index)
  for (const m of matches) {
    if (m.index < cursor) continue
    if (m.index > cursor) tokens.push({ type: "text", value: text.slice(cursor, m.index) })
    tokens.push({ type: m.type, value: m.value })
    cursor = m.index + m.length
  }
  if (cursor < text.length) tokens.push({ type: "text", value: text.slice(cursor) })
  return tokens.map((t, i) => {
    if (t.type === "bold") return <strong key={i}>{t.value}</strong>
    if (t.type === "code") return <code key={i} className="font-mono text-[0.85em] text-brass-bright">{t.value}</code>
    return <Fragment key={i}>{t.value}</Fragment>
  })
}

function renderParagraphs(text: string): React.ReactNode[] {
  const paras = text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean)
  return paras.map((p, i) => (
    <p key={i} className="font-serif text-sm leading-relaxed text-fg-soft">
      {renderInline(p.replace(/\n/g, " "))}
    </p>
  ))
}

interface Section {
  preamble: string
  items: { number: string; body: string }[]
  trailer: string
}

function parse(markdown: string): Section {
  const lines = markdown.split("\n")
  const preambleLines: string[] = []
  const trailerLines: string[] = []
  const items: { number: string; body: string }[] = []
  let current: { number: string; body: string } | null = null
  let phase: "pre" | "items" | "post" = "pre"

  for (const line of lines) {
    const m = NUM_ITEM_RE.exec(line)
    if (m) {
      if (current) items.push(current)
      current = { number: m[1], body: m[2] }
      phase = "items"
      continue
    }
    if (SEPARATOR_RE.test(line)) {
      if (current) {
        items.push(current)
        current = null
        phase = "post"
      }
      continue
    }
    if (phase === "pre") {
      preambleLines.push(line)
    } else if (current) {
      if (line.trim()) current.body += " " + line.trim()
    } else {
      trailerLines.push(line)
    }
  }
  if (current) items.push(current)

  return {
    preamble: preambleLines.join("\n").trim(),
    items,
    trailer: trailerLines.join("\n").trim(),
  }
}

export function RebalanceAdvice({ markdown }: RebalanceAdviceProps) {
  const { preamble, items, trailer } = parse(markdown)
  if (items.length === 0) {
    return (
      <div className="border border-rule bg-rule-soft/30 p-5 font-serif text-sm text-fg">
        {renderParagraphs(markdown)}
      </div>
    )
  }
  return (
    <div className="space-y-4">
      {preamble && (
        <div className="space-y-2">
          {renderParagraphs(preamble)}
        </div>
      )}
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
      {trailer && (
        <div className="border-l-2 border-rule bg-rule-soft/20 px-4 py-3 space-y-2">
          {renderParagraphs(trailer.replace(/^>\s?/gm, ""))}
        </div>
      )}
    </div>
  )
}
