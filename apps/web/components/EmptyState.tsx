"use client"

import { motion } from "framer-motion"
import { Inbox } from "lucide-react"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
  variant?: "default" | "compact"
}

export default function EmptyState({ icon, title, description, action, className, variant = "default" }: EmptyStateProps) {
  if (variant === "compact") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn("lux-card flex items-center gap-3 px-4 py-3 text-muted-foreground", className)}
      >
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-secondary text-primary">
          {icon ?? <Inbox className="h-4 w-4" />}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-foreground">{title}</p>
          {description ? <p className="truncate text-xs text-muted-foreground">{description}</p> : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("lux-card flex flex-col items-center justify-center px-6 py-14 text-center", className)}
    >
      {/* CRG: Empty states now reinforce the operational product tone instead of the old paper motif. */}
      <div className="mb-4 grid h-14 w-14 place-items-center rounded-2xl border border-primary/20 bg-primary/10 text-primary">
        {icon ?? <Inbox className="h-6 w-6" />}
      </div>
      <p className="text-sm font-bold text-foreground">{title}</p>
      {description ? <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </motion.div>
  )
}
