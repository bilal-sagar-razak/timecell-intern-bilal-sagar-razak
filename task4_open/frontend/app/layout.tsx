import type { Metadata } from "next"
import { Fraunces, Geist_Mono } from "next/font/google"
import { Toaster } from "sonner"
import "./globals.css"

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-fraunces",
})

const geistMono = Geist_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-geist-mono",
})

export const metadata: Metadata = {
  title: "TimeCell — Portfolio Intelligence Dashboard",
  description: "AI-powered portfolio analysis with cross-vendor critique.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${geistMono.variable}`}>
      <body>
        {children}
        <Toaster position="top-right" theme="dark" />
      </body>
    </html>
  )
}
