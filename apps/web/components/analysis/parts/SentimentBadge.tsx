"use client"

import { cn } from "@/lib/utils"

interface SentimentBadgeProps {
  label: string
  value?: number | null
  color: string
}

export function SentimentBadge({ label, value, color }: SentimentBadgeProps) {
  const numeric = typeof value === "number" ? value : 0
  const pct = Math.round(numeric > 1 ? numeric : numeric * 100)
  return (
    <div className={cn("rounded px-2 py-1.5 text-center", color)}>
      <div className="text-xs font-bold tabular-nums">{pct}%</div>
      <div className="text-[10px] opacity-80 font-serif tracking-wider">{label}</div>
    </div>
  )
}
