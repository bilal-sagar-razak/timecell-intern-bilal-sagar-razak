import type { Headline } from "@/lib/api"

interface NewsListProps {
  headlines: Headline[]
  fallbackUsed: boolean
}

function relativeTime(iso: string): string {
  const t = new Date(iso).getTime()
  const diff = Date.now() - t
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

export function NewsList({ headlines, fallbackUsed }: NewsListProps) {
  if (headlines.length === 0) {
    return (
      <div className="border border-rule bg-rule-soft/30 px-5 py-8 text-center font-mono text-xs text-muted-deep">
        Couldn't load news right now
      </div>
    )
  }
  return (
    <div className="border border-rule bg-rule-soft/30 p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-mono text-[0.7rem] uppercase tracking-[0.22em] text-muted-deep">
          Headlines
        </span>
        <span className="font-mono text-[0.65rem] uppercase tracking-[0.22em] text-muted-deep">
          {headlines.length}
        </span>
      </div>
      {fallbackUsed && (
        <div className="mb-3 border-l-2 border-brass bg-brass/5 px-3 py-2 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-brass-bright">
          No headlines matched your holdings — showing top general market news
        </div>
      )}
      <ul className="divide-y divide-rule">
        {headlines.map((h) => (
          <li key={h.url} className="py-3">
            <a
              href={h.url}
              target="_blank"
              rel="noreferrer"
              className="block font-serif text-sm text-fg hover:text-brass"
            >
              {h.title}
            </a>
            <div className="mt-1 flex gap-2 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-muted-deep">
              <span>{h.publisher}</span>
              <span>·</span>
              <span>{relativeTime(h.published_at)}</span>
            </div>
            {h.snippet && (
              <p className="mt-1 line-clamp-2 font-serif text-xs text-fg-soft">
                {h.snippet}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
