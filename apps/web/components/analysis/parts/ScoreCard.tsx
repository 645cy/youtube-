"use client"

import { cn } from "@/lib/utils"
import { Progress } from "@/components/ui/progress"

interface ScoreCardProps {
  icon: React.ComponentType<any>
  label: string
  score: number
  color: string
  bg: string
}

export function ScoreCard({ icon: Icon, label, score, color, bg }: ScoreCardProps) {
  return (
    <div className={cn("rounded-lg border p-3 paper-hover-lift", bg)}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className={cn("h-4 w-4", color)} />
        <span className="text-xs font-medium font-serif tracking-wider">{label}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className={cn("text-2xl font-bold tabular-nums", color)}>{score}</span>
        <span className="text-[10px] text-muted-foreground mb-1 tracking-wide">/100</span>
      </div>
      <Progress value={score} className="h-1.5 mt-2" />
    </div>
  )
}
