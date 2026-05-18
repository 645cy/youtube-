/**
 * VideoAnalysisPanel - 视频分析结果展示面板
 * 展示 viral / evergreen / sentiment / monetization 四合一分析结果
 */

"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  X,
  TrendingUp,
  Leaf,
  MessageCircle,
  DollarSign,
  Zap,
  AlertCircle,
  Loader2,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { analysisApi } from "@/lib/api"
import { toastError } from "@/lib/toast"

interface AnalysisResult {
  analysis_type: string
  target_id: string
  target_type: string
  status: "success" | "error" | "skipped" // CRG: Backend sentiment can return skipped when real comments are unavailable.
  result?: Record<string, unknown>
  score?: number
  processing_time_ms?: number
}

interface VideoAnalysisPanelProps {
  youtubeId: string
  videoTitle?: string
  isOpen: boolean
  onClose: () => void
}

export function VideoAnalysisPanel({
  youtubeId,
  videoTitle,
  isOpen,
  onClose,
}: VideoAnalysisPanelProps) {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<AnalysisResult[]>([])

  useEffect(() => {
    if (!isOpen || !youtubeId) return

    let cancelled = false
    const run = async () => {
      setLoading(true)
      setResults([])
      try {
        const res = await analysisApi.fullAnalysis(youtubeId)
        if (!cancelled) setResults(Array.isArray(res) ? res : [res])
      } catch (e: any) {
        if (!cancelled) toastError("分析请求失败: " + (e.message || "未知错误"))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [isOpen, youtubeId])

  const viralResult = results.find((r) => r.analysis_type === "viral_detection")
  const evergreenResult = results.find((r) => r.analysis_type === "evergreen")
  const sentimentResult = results.find((r) => r.analysis_type === "sentiment")
  const monetizationResult = results.find((r) => r.analysis_type === "monetization")
  const issueResults = results.filter((r) => r.status !== "success")

  const getScore = (r?: AnalysisResult) =>
    r?.status === "success" ? Math.round(r?.score || 0) : 0

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 z-50"
            onClick={onClose}
          />
          {/* 面板 */}
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-x-4 top-[5vh] bottom-[5vh] md:inset-x-auto md:left-1/2 md:-translate-x-1/2 md:w-[640px] z-50 paper-card page-corner flex flex-col overflow-hidden"
          >
            {/* 头部 */}
            <div className="flex items-center justify-between px-5 py-4 border-b shrink-0">
              <div className="min-w-0">
                <h3 className="font-serif tracking-wide font-semibold text-base truncate">
                  视频分析报告
                </h3>
                {videoTitle && (
                  <p className="text-xs text-muted-foreground truncate max-w-[400px] tracking-wide leading-relaxed">
                    {videoTitle}
                  </p>
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="shrink-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* 内容 */}
            <div className="flex-1 overflow-auto p-5 space-y-5">
              {loading ? (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <Loader2 className="h-8 w-8 animate-spin mb-3 text-primary/60" />
                  <p className="text-sm font-serif tracking-wide">正在分析视频数据...</p>
                  <p className="text-xs mt-1 tracking-wide leading-relaxed">这可能需要几秒钟</p>
                </div>
              ) : results.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mb-3 opacity-50" />
                  <p className="text-sm font-serif tracking-wide">暂无分析数据</p>
                </div>
              ) : (
                <>
                  {/* 概览分数卡片 */}
                  <div className="grid grid-cols-2 gap-3">
                    <ScoreCard
                      icon={Zap}
                      label="爆款潜力"
                      score={getScore(viralResult)}
                      color="text-amber-400"
                      bg="bg-amber-500/10"
                    />
                    <ScoreCard
                      icon={Leaf}
                      label="长尾价值"
                      score={getScore(evergreenResult)}
                      color="text-emerald-400"
                      bg="bg-emerald-500/10"
                    />
                    <ScoreCard
                      icon={MessageCircle}
                      label="情感得分"
                      score={getScore(sentimentResult)}
                      color="text-blue-400"
                      bg="bg-blue-500/10"
                    />
                    <ScoreCard
                      icon={DollarSign}
                      label="变现指数"
                      score={getScore(monetizationResult)}
                      color="text-violet-400"
                      bg="bg-violet-500/10"
                    />
                  </div>

                  {/* CRG: Explain partial analysis failures as operator actions instead of silent zero scores. */}
                  {issueResults.length > 0 && (
                    <AnalysisIssueList results={issueResults} />
                  )}

                  {/* 详细结果 */}
                  {viralResult?.status === "success" && viralResult.result && (
                    <DetailSection
                      icon={TrendingUp}
                      title="爆款检测"
                      color="text-amber-400"
                    >
                      <ViralDetail result={viralResult.result} />
                    </DetailSection>
                  )}

                  {evergreenResult?.status === "success" && evergreenResult.result && (
                    <DetailSection
                      icon={Leaf}
                      title="长尾 Evergreen"
                      color="text-emerald-400"
                    >
                      <EvergreenDetail result={evergreenResult.result} />
                    </DetailSection>
                  )}

                  {sentimentResult?.status === "success" && sentimentResult.result && (
                    <DetailSection
                      icon={MessageCircle}
                      title="评论情感"
                      color="text-blue-400"
                    >
                      <SentimentDetail result={sentimentResult.result} />
                    </DetailSection>
                  )}

                  {monetizationResult?.status === "success" && monetizationResult.result && (
                    <DetailSection
                      icon={DollarSign}
                      title="变现信号"
                      color="text-violet-400"
                    >
                      <MonetizationDetail result={monetizationResult.result} />
                    </DetailSection>
                  )}

                  {/* 处理时间 */}
                  <p className="text-[10px] text-muted-foreground text-center tabular-nums tracking-wide">
                    处理耗时 {results[0]?.processing_time_ms || 0}ms
                  </p>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

/* ── 子组件 ── */

function ScoreCard({
  icon: Icon,
  label,
  score,
  color,
  bg,
}: {
  icon: typeof Zap
  label: string
  score: number
  color: string
  bg: string
}) {
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

function DetailSection({
  icon: Icon,
  title,
  color,
  children,
}: {
  icon: typeof Zap
  title: string
  color: string
  children: React.ReactNode
}) {
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

function AnalysisIssueList({ results }: { results: AnalysisResult[] }) {
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

function analysisLabel(type: string): string {
  // CRG: Keep backend analysis_type values readable without changing the API contract.
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

function ViralDetail({ result }: { result: Record<string, unknown> }) {
  const r = result as any
  // CRG: Match backend ViralDetectionResult field names from apps/api/schemas/analysis.py.
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

function EvergreenDetail({ result }: { result: Record<string, unknown> }) {
  const r = result as any
  // CRG: Match backend EvergreenResult keys instead of stale UI-only names.
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

function SentimentDetail({ result }: { result: Record<string, unknown> }) {
  const agg = (result as any)?.aggregation || {}
  const samples = ((result as any)?.sample_results || []) as any[]
  // CRG: Backend sentiment aggregation exposes positive_pct/neutral_pct/negative_pct.
  return (
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-3 gap-2">
        <SentimentBadge
          label="正面"
          value={agg?.positive_pct}
          color="bg-emerald-500/20 text-emerald-400"
        />
        <SentimentBadge
          label="中性"
          value={agg?.neutral_pct}
          color="bg-blue-500/20 text-blue-400"
        />
        <SentimentBadge
          label="负面"
          value={agg?.negative_pct}
          color="bg-red-500/20 text-red-400"
        />
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

function MonetizationDetail({ result }: { result: Record<string, unknown> }) {
  const r = result as any
  // CRG: Backend MonetizationResult exposes monetization_types/coupons, not a signals array.
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

function SentimentBadge({
  label,
  value,
  color,
}: {
  label: string
  value?: number | null
  color: string
}) {
  // CRG: Backend returns *_pct as 0-100 while older UI callers used 0-1 ratios.
  const numeric = typeof value === "number" ? value : 0
  const pct = Math.round(numeric > 1 ? numeric : numeric * 100)
  return (
    <div className={cn("rounded px-2 py-1.5 text-center", color)}>
      <div className="text-xs font-bold tabular-nums">{pct}%</div>
      <div className="text-[10px] opacity-80 font-serif tracking-wider">{label}</div>
    </div>
  )
}

function KeyValue({
  label,
  value,
}: {
  label: string
  value?: string | number
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted-foreground tracking-wide">{label}</span>
      <span className="text-xs font-medium tabular-nums">{value ?? "-"}</span>
    </div>
  )
}
