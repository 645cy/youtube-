import type { ReactNode } from "react"
import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface SectionHeadingProps {
  label: string
  icon?: LucideIcon
  className?: string
  children?: ReactNode
}

export function SectionHeading({ label, icon: Icon, className, children }: SectionHeadingProps) {
  return (
    <div className={cn("mb-4 flex min-w-0 items-center gap-3", className)}>
      {Icon ? (
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl border border-primary/20 bg-primary/10 text-primary">
          <Icon className="h-4 w-4" aria-hidden />
        </span>
      ) : null}
      {/* CRG: Section headings use a small editorial title style, not generic bold UI text. */}
      <h2 className="lux-section-title min-w-0 shrink-0 truncate text-sm text-foreground">{label}</h2>
      <div className="h-px flex-1 bg-gradient-to-r from-border to-transparent" aria-hidden />
      {children ? <div className="flex shrink-0 items-center gap-2">{children}</div> : null}
    </div>
  )
}
