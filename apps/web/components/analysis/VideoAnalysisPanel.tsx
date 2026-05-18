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
  Loader2,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { analysisApi } from "@/lib/api"
import { toastError } from "@/lib/toast"
import { ScoreCard } from "./parts/ScoreCard"
import { DetailSection } from "./parts/DetailSection"
import { AnalysisIssueList } from "./parts/AnalysisIssueList"
import { ViralDetail } from "./parts/ViralDetail"
import { EvergreenDetail } from "./parts/EvergreenDetail"
import { SentimentDetail } from "./parts/SentimentDetail"
import { MonetizationDetail } from "./parts/MonetizationDetail"

export interface AnalysisResult {
  analysis_type: string
  target_id: string
  target_type: string
  status: "success" | "error" | "skipped"
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

                  {issueResults.length > 0 && (
                    <AnalysisIssueList results={issueResults} />
                  )}

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
