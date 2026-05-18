"use client"

import { Badge } from "@/components/ui/badge"
import { KeyValue } from "./KeyValue"

export function MonetizationDetail({ result }: { result: Record<string, unknown> }) {
  const r = result as any
  const signals = [
    ...(Array.isArray(r?.monetization_types) ? r.monetization_types : []),
    ...(r?.affiliate_detected ? ["affiliate"] : []),
    ...(r?.sponsorship_detected ? ["sponsorship"] : []),
    ...(Array.isArray(r?.detected_coupons) ? r.detected_coupons : []),
  ].filter((item): item is string => typeof item === "string" && item.length > 0)
  return (
    <div className="space-y-2 text-sm">
      <KeyValue label="变现评分" value={r?.monetization_score ?? "-"} />
      <KeyValue label="收入层级" value={r?.estimated_monthly_revenue_tier ?? "-"} />
      {signals.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {signals.map((s: string, i: number) => (
            <Badge key={i} variant="outline" className="text-[10px] font-serif tracking-wider">
              {s}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
