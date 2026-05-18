import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  // CRG: Badges use label typography so status chips feel deliberate rather than default small text.
  "lux-badge-type inline-flex max-w-full items-center rounded-full border px-2.5 py-1 text-[11px] leading-none transition-colors",
  {
    variants: {
      variant: {
        // CRG: Status variants keep API compatibility while improving contrast in both themes.
        default: "border-border/70 bg-secondary/80 text-secondary-foreground",
        primary: "border-primary/24 bg-primary/12 text-primary",
        outline: "border-border/80 bg-transparent text-foreground",
        success: "border-emerald-500/24 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300",
        warning: "border-amber-500/28 bg-amber-500/12 text-amber-700 dark:text-amber-300",
        danger: "border-red-500/24 bg-red-500/10 text-red-600 dark:text-red-300",
        info: "border-sky-500/24 bg-sky-500/10 text-sky-700 dark:text-sky-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
