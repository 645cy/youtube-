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
  status: "success" | "error"
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

    const run = async () => {
      setLoading(true)
      setResults([])
      try {
        const res = await analysisApi.fullAnalysis(youtubeId)
        setResults(Array.isArray(res) ? res : [res])
      } catch (e: any) {
        toastError("分析请求失败: " + (e.message || "未知错误"))
      } finally {
        setLoading(false)
      }
    }
    run()
  }, [isOpen, youtubeId])

  const viralResult = results.find((r) => r.analysis_type === "viral_detection")
  const evergreenResult = results.find((r) => r.analysis_type === "evergreen")
  const sentimentResult = results.find((r) => r.analysis_type === "sentiment")
  const monetizationResult = results.find((r) => r.analysis_type === "monetization")

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
            className="fixed inset-x-4 top-[5vh] bottom-[5vh] md:inset-x-auto md:left-1/2 md:-translate-x-1/2 md:w-[640px] z-50 bg-card border rounded-xl shadow-2xl flex flex-col overflow-hidden"
          >
            {/* 头部 */}
            <div className="flex items-center justify-between px-5 py-4 border-b shrink-0">
              <div className="min-w-0">
                <h3 className="font-semibold text-base truncate">
                  视频分析报告
                </h3>
                {videoTitle && (
                  <p className="text-xs text-muted-foreground truncate max-w-[400px]">
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
                  <Loader2 className="h-8 w-8 animate-spin mb-3" />
                  <p className="text-sm">正在分析视频数据...</p>
                  <p className="text-xs mt-1">这可能需要几秒钟</p>
                </div>
              ) : results.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mb-3 opacity-50" />
                  <p className="text-sm">暂无分析数据</p>
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
                  <p className="text-[10px] text-muted-foreground text-center">
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
    <div className={cn("rounded-lg border p-3", bg)}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className={cn("h-4 w-4", color)} />
        <span className="text-xs font-medium">{label}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className={cn("text-2xl font-bold", color)}>{score}</span>
        <span className="text-[10px] text-muted-foreground mb-1">/100</span>
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
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Icon className={cn("h-4 w-4", color)} />
        <span className="text-sm font-semibold">{title}</span>
      </div>
      {children}
    </div>
  )
}

function ViralDetail({ result }: { result: Record<string, unknown> }) {
  const r = result as any
  return (
    <div className="space-y-2 text-sm">
      <KeyValue label="病毒传播评分" value={r?.viral_score ?? "-"} />
      <KeyValue label="VRI 指数" value={r?.vri ?? "-"} />
      <KeyValue label="预计传播速度" value={r?.spread_speed ?? "-"} />
      <KeyValue label="推荐动作" value={r?.recommendation ?? "-"} />
    </div>
  )
}

function EvergreenDetail({ result }: { result: Record<string, unknown> }) {
  const r = result as any
  return (
    <div className="space-y-2 text-sm">
      <KeyValue label="Evergreen 评分" value={r?.evergreen_score ?? "-"} />
      <KeyValue label="搜索需求稳定性" value={r?.search_stability ?? "-"} />
      <KeyValue label="内容持久度" value={r?.content_longevity ?? "-"} />
      <KeyValue label="推荐动作" value={r?.recommendation ?? "-"} />
    </div>
  )
}

function SentimentDetail({ result }: { result: Record<string, unknown> }) {
  const agg = (result as any)?.aggregation || {}
  const samples = ((result as any)?.sample_results || []) as any[]
  return (
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-3 gap-2">
        <SentimentBadge
          label="正面"
          value={agg?.positive_ratio}
          color="bg-emerald-500/20 text-emerald-400"
        />
        <SentimentBadge
          label="中性"
          value={agg?.neutral_ratio}
          color="bg-blue-500/20 text-blue-400"
        />
        <SentimentBadge
          label="负面"
          value={agg?.negative_ratio}
          color="bg-red-500/20 text-red-400"
        />
      </div>
      {samples.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-xs text-muted-foreground">样本评论:</span>
          {samples.slice(0, 3).map((s, i) => (
            <div
              key={i}
              className="text-xs bg-muted/50 rounded px-2 py-1.5 line-clamp-2"
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
  const signals = r?.signals || []
  return (
    <div className="space-y-2 text-sm">
      <KeyValue label="变现评分" value={r?.monetization_score ?? "-"} />
      <KeyValue label="预估 RPM" value={r?.estimated_rpm ?? "-"} />
      {signals.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {signals.map((s: string, i: number) => (
            <Badge key={i} variant="outline" className="text-[10px]">
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
  value?: number
  color: string
}) {
  const pct = value !== undefined ? Math.round((value as number) * 100) : 0
  return (
    <div className={cn("rounded px-2 py-1.5 text-center", color)}>
      <div className="text-xs font-bold">{pct}%</div>
      <div className="text-[10px] opacity-80">{label}</div>
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
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-xs font-medium">{value ?? "-"}</span>
    </div>
  )
}
