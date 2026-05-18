"use client"

import { cn } from "@/lib/utils"

interface DetailSectionProps {
  icon: React.ComponentType<any>
  title: string
  color: string
  children: React.ReactNode
}

export function DetailSection({ icon: Icon, title, color, children }: DetailSectionProps) {
  return (
    <div className="rounded-lg border p-4 space-y-3 paper-card">
      <div className="flex items-center gap-2">
        <Icon className={cn("h-4 w-4", color)} />
        <span className="text-sm font-semibold font-serif tracking-wide">{title}</span>
      </div>
      <div className="gold-rule" />
      {children}
    </div>
  )
}
