"use client"

import { KeyValue } from "./KeyValue"

export function EvergreenDetail({ result }: { result: Record<string, unknown> }) {
  const r = result as any
  return (
    <div className="space-y-2 text-sm">
      <KeyValue label="Evergreen 评分" value={r?.evergreen_score ?? "-"} />
      <KeyValue label="搜索稳定指数" value={r?.search_stability_index ?? "-"} />
      <KeyValue label="竞争比" value={r?.competition_ratio ?? "-"} />
      <KeyValue label="流量类型" value={r?.traffic_type ?? "-"} />
      <KeyValue label="推荐动作" value={r?.recommendation ?? "-"} />
    </div>
  )
}
