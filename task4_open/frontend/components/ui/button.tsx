import * as React from "react"
import { cn } from "@/lib/utils"

type Variant = "default" | "outline" | "ghost"
type Size = "default" | "sm" | "lg"

const variantClass: Record<Variant, string> = {
  default: "bg-brass text-bg hover:bg-brass-bright",
  outline: "border border-rule text-fg hover:border-brass hover:text-brass",
  ghost: "text-fg hover:text-brass",
}
const sizeClass: Record<Size, string> = {
  default: "h-10 px-4 text-sm",
  sm: "h-8 px-3 text-xs",
  lg: "h-12 px-6 text-base",
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 font-mono uppercase tracking-wide-uppercase transition-colors disabled:opacity-50 disabled:pointer-events-none focus-visible:outline focus-visible:outline-1 focus-visible:outline-brass",
        variantClass[variant],
        sizeClass[size],
        className,
      )}
      {...props}
    />
  ),
)
Button.displayName = "Button"
