/**
 * TopicGenerator 组件 - 内容工厂 Tab 1: 选题生成器
 * niche 输入 → AI 选题建议
 * 显示搜索量/竞争度/评分
 */

"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Sparkles,
  Search,
  TrendingUp,
  BarChart3,
  Star,
  Loader2,
  Lightbulb,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

/** 选题项 */
export interface TopicItem {
  id: string
  title: string
  description: string
  searchVolume: string
  competition: string
  score: number
  tags?: string[]
}

interface TopicGeneratorProps {
  onGenerate: (niche: string) => void
  topics: TopicItem[]
  selectedTopicId?: string | null
  onSelectTopic?: (topic: TopicItem) => void
  isLoading?: boolean
  className?: string
}

export function TopicGenerator({
  onGenerate,
  topics,
  selectedTopicId,
  onSelectTopic,
  isLoading = false,
  className,
}: TopicGeneratorProps) {
  const [niche, setNiche] = useState("")

  const handleGenerate = () => {
    if (!niche.trim()) return
    onGenerate(niche)
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* 输入区域 */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            placeholder="输入你的 niche（如：iPhone技巧、健身教程...）"
            className="pl-10 h-11"
            onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
          />
        </div>
        <Button
          onClick={handleGenerate}
          disabled={!niche.trim() || isLoading}
          className="h-11 px-6"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Sparkles className="h-4 w-4 mr-2" />
          )}
          {isLoading ? "生成中..." : "AI 选题"}
        </Button>
      </div>

      {/* 热门 niche 快速选择 */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-muted-foreground">热门:</span>
        {[
          "科技数码",
          "美食烹饪",
          "健身运动",
          "旅行Vlog",
          "知识科普",
          "游戏电竞",
          "财经投资",
        ].map((tag) => (
          <Badge
            key={tag}
            variant="outline"
            className="cursor-pointer text-xs hover:bg-accent transition-colors"
            onClick={() => {
              setNiche(tag)
              onGenerate(tag)
            }}
          >
            {tag}
          </Badge>
        ))}
      </div>

      {/* 选题结果 */}
      <div className="grid grid-cols-1 gap-3">
        <AnimatePresence>
          {isLoading
            ? Array.from({ length: 5 }).map((_, i) => (
                <TopicSkeleton key={i} />
              ))
            : topics.map((topic, index) => (
                <motion.div
                  key={topic.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <TopicCard
                    topic={topic}
                    selected={selectedTopicId === topic.id}
                    onSelect={() => onSelectTopic?.(topic)}
                  />
                </motion.div>
              ))}
        </AnimatePresence>
      </div>

      {/* 空状态 */}
      {!isLoading && topics.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <Lightbulb className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">输入 niche 开始 AI 选题</p>
          <p className="text-xs mt-1">我们将为你生成高潜力的视频选题建议</p>
        </div>
      )}
    </div>
  )
}

/** 选题卡片 */
function TopicCard({
  topic,
  selected = false,
  onSelect,
}: {
  topic: TopicItem
  selected?: boolean
  onSelect?: () => void
}) {
  return (
    <Card
      className={cn(
        "group hover:shadow-md transition-all cursor-pointer",
        selected && "ring-1 ring-primary bg-primary/5"
      )}
      onClick={onSelect}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-medium text-sm">{topic.title}</h4>
            </div>
            <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
              {topic.description}
            </p>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                搜索量: {topic.searchVolume}
              </span>
              <span className="flex items-center gap-1">
                <BarChart3 className="h-3 w-3" />
                竞争度: {topic.competition}
              </span>
            </div>
            {topic.tags && (
              <div className="flex flex-wrap gap-1 mt-2">
                {topic.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
          {/* 评分 */}
          <div className="flex flex-col items-center shrink-0">
            <div
              className={cn(
                "h-10 w-10 rounded-full flex items-center justify-center text-sm font-bold",
                topic.score >= 80
                  ? "bg-emerald-500/20 text-emerald-400"
                  : topic.score >= 60
                    ? "bg-blue-500/20 text-blue-400"
                    : "bg-amber-500/20 text-amber-400"
              )}
            >
              {topic.score}
            </div>
            <span className="text-[10px] text-muted-foreground mt-1 flex items-center gap-0.5">
              <Star className="h-2.5 w-2.5" />
              评分
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/** 骨架屏 */
function TopicSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex gap-3">
          <div className="space-y-2 flex-1">
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-10 w-10 rounded-full shrink-0" />
        </div>
      </CardContent>
    </Card>
  )
}