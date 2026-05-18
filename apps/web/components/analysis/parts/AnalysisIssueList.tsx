"use client"

import { Badge } from "@/components/ui/badge"
import { AlertCircle } from "lucide-react"
import type { AnalysisResult } from "../VideoAnalysisPanel"

export { AnalysisResult }

function analysisLabel(type: string): string {
  return ({ viral_detection: "爆款检测", evergreen: "长尾价值", sentiment: "评论情感", monetization: "变现信号" } as Record<string, string>)[type] || type
}

function analysisAction(result: AnalysisResult): string {
  const error = typeof result.result?.error === "string" ? result.result.error : ""
  if (result.analysis_type === "sentiment" || error.toLowerCase().includes("comment")) {
    return "评论不可用：到 Settings > Integrations 检查 YouTube API，或在后续导入真实评论后重跑。"
  }
  if (error) return error
  return "检查视频是否已导入、频道数据是否完整，然后重新运行分析。"
}

export function AnalysisIssueList({ results }: { results: AnalysisResult[] }) {
  return (
    <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 space-y-2">
      <div className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4 text-amber-400" />
        <span className="text-sm font-semibold font-serif tracking-wide">需要补齐的数据</span>
      </div>
      {results.map((result) => (
        <div key={result.analysis_type} className="flex items-start justify-between gap-3 rounded-md bg-background/60 px-3 py-2 border border-amber-500/10">
          <div className="min-w-0">
            <div className="text-xs font-medium font-serif tracking-wide">{analysisLabel(result.analysis_type)}</div>
            <div className="mt-1 text-xs text-muted-foreground tracking-wide leading-relaxed">{analysisAction(result)}</div>
          </div>
          <Badge variant={result.status === "skipped" ? "warning" : "danger"} className="shrink-0 font-serif tracking-wider">
            {result.status === "skipped" ? "已跳过" : "失败"}
          </Badge>
        </div>
      ))}
    </div>
  )
}
