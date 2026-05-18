"use client"

import { SentimentBadge } from "./SentimentBadge"

export function SentimentDetail({ result }: { result: Record<string, unknown> }) {
  const agg = (result as any)?.aggregation || {}
  const samples = ((result as any)?.sample_results || []) as any[]
  return (
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-3 gap-2">
        <SentimentBadge label="正面" value={agg?.positive_pct} color="bg-emerald-500/20 text-emerald-400" />
        <SentimentBadge label="中性" value={agg?.neutral_pct} color="bg-blue-500/20 text-blue-400" />
        <SentimentBadge label="负面" value={agg?.negative_pct} color="bg-red-500/20 text-red-400" />
      </div>
      {samples.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-xs text-muted-foreground font-serif tracking-wider">样本评论:</span>
          {samples.slice(0, 3).map((s, i) => (
            <div
              key={i}
              className="text-xs bg-muted/50 rounded px-2 py-1.5 line-clamp-2 border border-border/50 tracking-wide leading-relaxed"
            >
              {s?.text || s?.comment || "..."}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
