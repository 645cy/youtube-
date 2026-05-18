"use client"

import { KeyValue } from "./KeyValue"

export function ViralDetail({ result }: { result: Record<string, unknown> }) {
  const r = result as any
  return (
    <div className="space-y-2 text-sm">
      <KeyValue label="病毒传播评分" value={r?.viral_score ?? "-"} />
      <KeyValue label="VRI 指数" value={r?.vri ?? "-"} />
      <KeyValue label="传播速度指数" value={r?.velocity_index ?? "-"} />
      <KeyValue label="预估峰值播放" value={r?.estimated_peak_views ?? "-"} />
      <KeyValue label="推荐动作" value={r?.recommendation ?? "-"} />
    </div>
  )
}
