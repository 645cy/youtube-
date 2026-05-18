"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface PageHeaderProps {
  chapter: string
  title: string
  subtitle?: string
  action?: React.ReactNode
  className?: string
}

export default function PageHeader({ chapter, title, subtitle, action, className }: PageHeaderProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.42, ease: [0.22, 0.61, 0.36, 1] }}
      className={cn("pb-7", className)}
    >
      {/* CRG: Header becomes a compact command surface so first screen remains operational, not a landing hero. */}
      <div className="lux-card relative overflow-hidden p-5 sm:p-6 lg:p-7">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_85%_20%,hsl(var(--primary)/0.18),transparent_28rem),radial-gradient(circle_at_12%_90%,hsl(var(--accent)/0.10),transparent_24rem)]" />
        <div className="relative z-10 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <span className="lux-page-eyebrow inline-flex items-center rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-[11px] uppercase text-primary">
              {chapter}
            </span>
            <div className="space-y-2">
              {/* CRG: Shared page headers now use the refined Chinese heading role. */}
              <h1 className="lux-page-title text-3xl leading-tight text-foreground sm:text-4xl lg:text-5xl">
                {title}
              </h1>
              {subtitle ? <p className="lux-page-copy max-w-2xl text-muted-foreground">{subtitle}</p> : null}
            </div>
          </div>
          {action ? <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div> : null}
        </div>
      </div>
    </motion.section>
  )
}
