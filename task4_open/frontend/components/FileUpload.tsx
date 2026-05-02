"use client"
import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Upload } from "lucide-react"
import { ApiError, parseAndCompute } from "@/lib/api"
import { usePortfolio } from "@/lib/store"

const PHASES = [
  "Reading statement...",
  "Analysing with Claude...",
  "Computing metrics...",
]

export function FileUpload() {
  const router = useRouter()
  const setData = usePortfolio((s) => s.setData)
  const [busy, setBusy] = useState(false)
  const [phase, setPhase] = useState<string>("")

  const onDrop = useCallback(async (files: File[]) => {
    if (files.length === 0) return
    const file = files[0]
    setBusy(true)
    let phaseIdx = 0
    setPhase(PHASES[0])
    const phaseTimer = setInterval(() => {
      phaseIdx = Math.min(phaseIdx + 1, PHASES.length - 1)
      setPhase(PHASES[phaseIdx])
    }, 1500)

    try {
      const data = await parseAndCompute(file)
      setData(data)
      router.push("/dashboard")
    } catch (e) {
      const message = e instanceof ApiError
        ? `${e.message}${e.status ? ` (HTTP ${e.status})` : ""}`
        : (e as Error).message
      toast.error(message)
    } finally {
      clearInterval(phaseTimer)
      setBusy(false)
      setPhase("")
    }
  }, [router, setData])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "application/pdf": [".pdf"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
    disabled: busy,
  })

  return (
    <div
      {...getRootProps()}
      className={`flex min-h-[280px] cursor-pointer flex-col items-center justify-center border-2 border-dashed border-rule bg-rule-soft/20 px-10 py-12 transition-colors ${
        isDragActive ? "border-brass" : "hover:border-brass-bright"
      } ${busy ? "cursor-wait opacity-60" : ""}`}
    >
      <input {...getInputProps()} />
      <Upload className="h-10 w-10 text-brass" />
      {busy ? (
        <p className="mt-6 font-mono text-sm text-fg-soft">{phase}</p>
      ) : (
        <>
          <p className="mt-6 font-serif text-lg text-fg">
            {isDragActive ? "Drop your statement..." : "Drop your holdings statement"}
          </p>
          <p className="mt-2 font-mono text-xs uppercase tracking-[0.22em] text-muted-deep">
            xlsx · xls · pdf · png · jpg
          </p>
        </>
      )}
    </div>
  )
}
