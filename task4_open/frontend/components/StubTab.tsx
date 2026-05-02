import { Lock } from "lucide-react"

interface StubTabProps {
  task: "4b" | "4c"
  description: string
}

export function StubTab({ task, description }: StubTabProps) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="max-w-md border border-rule bg-rule-soft/30 px-8 py-10 text-center">
        <Lock className="mx-auto h-8 w-8 text-muted-deep" />
        <div className="mt-4 font-mono text-xs uppercase tracking-[0.22em] text-brass">
          Coming in Task {task}
        </div>
        <p className="mt-3 font-serif text-sm leading-relaxed text-fg-soft">
          {description}
        </p>
      </div>
    </div>
  )
}
