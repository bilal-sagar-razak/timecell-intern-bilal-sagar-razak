import Image from "next/image"
import { FileUpload } from "@/components/FileUpload"

export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl px-6 pt-20 pb-16">
      <div className="mb-12 flex items-center gap-3">
        <Image src="/timecell-logo.png" alt="TimeCell" width={28} height={28} className="opacity-90" />
        <span className="font-mono text-xs uppercase tracking-[0.22em] text-brass">TimeCell</span>
      </div>
      <h1 className="font-serif text-4xl leading-tight text-fg">
        Portfolio Intelligence Dashboard
      </h1>
      <p className="mt-3 font-serif text-lg text-fg-soft">
        Upload your holdings statement — any format, any broker. Claude reads it,
        normalizes it, and renders the picture.
      </p>
      <div className="mt-12">
        <FileUpload />
      </div>
    </main>
  )
}
