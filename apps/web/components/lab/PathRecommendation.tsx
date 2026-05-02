/**
 * PathRecommendation 组件 - OCP变现实验室 Step 2
 * 推荐结果卡片（最多20条路径匹配排序）
 * 显示匹配度/预估收益/时间线
 */

"use client"

import { motion, AnimatePresence } from "framer-motion"
import {
  Zap,
  TrendingUp,
  Clock,
  ChevronRight,
  Target,
  BarChart3,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

import { Skeleton } from "@/components/ui/skeleton"
import type { OCPPath } from "@/lib/store"

interface PathRecommendationProps {
  paths: OCPPath[]
  isLoading?: boolean
  onSelectPath: (pathId: string) => void
  className?: string
}

/** 匹配度颜色 */
function getMatchColor(score: number): string {
  if (score >= 85) return "text-emerald-400 bg-emerald-400/10 border-emerald-400/30"
  if (score >= 70) return "text-blue-400 bg-blue-400/10 border-blue-400/30"
  if (score >= 55) return "text-amber-400 bg-amber-400/10 border-amber-400/30"
  return "text-muted-foreground bg-muted border-muted"
}

/** 匹配度标签 */
function getMatchLabel(score: number): string {
  if (score >= 85) return "高度匹配"
  if (score >= 70) return "推荐"
  if (score >= 55) return "可行"
  return "一般"
}

export function PathRecommendation({
  paths,
  isLoading = false,
  onSelectPath,
  className,
}: PathRecommendationProps) {
  if (isLoading) {
    return (
      <div className={cn("space-y-4", className)}>
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
          <Skeleton className="h-5 w-5 rounded-full" />
          <Skeleton className="h-4 w-32" />
        </div>
        {Array.from({ length: 3 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (paths.length === 0) {
    return (
      <div className={cn("text-center py-12", className)}>
        <Target className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
        <p className="text-muted-foreground">请先填写画像并生成方案</p>
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="bg-primary text-primary-foreground w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold">
            2
          </span>
          <span>推荐路径</span>
          <span className="text-muted-foreground/60">
            (找到 {paths.length} 条匹配路径)
          </span>
        </div>
        <Badge variant="outline" className="text-xs">
          <BarChart3 className="h-3 w-3 mr-1" />
          AI 匹配
        </Badge>
      </div>

      {/* 路径卡片列表 */}
      <div className="grid grid-cols-1 gap-3">
        <AnimatePresence>
          {paths.map((path, index) => (
            <motion.div
              key={path.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <Card
                className="group cursor-pointer transition-all hover:shadow-lg hover:ring-1 hover:ring-primary/30"
                onClick={() => onSelectPath(path.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    {/* 左侧：序号 + 信息 */}
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      {/* 排名序号 */}
                      <div
                        className={cn(
                          "w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm shrink-0",
                          index < 3
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        {index + 1}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold truncate">
                            {path.name}
                          </h4>
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-[10px] shrink-0",
                              getMatchColor(path.matchScore)
                            )}
                          >
                            {getMatchLabel(path.matchScore)} {path.matchScore}%
                          </Badge>
                        </div>

                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                          {path.description}
                        </p>

                        {/* 关键指标 */}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3 text-emerald-400" />
                            {path.estimatedRevenue}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-blue-400" />
                            {path.timeline}
                          </span>
                          <span className="flex items-center gap-1">
                            <Zap className="h-3 w-3 text-amber-400" />
                            {path.steps.length} 个步骤
                          </span>
                        </div>

                        {/* 进度条 */}
                        <div className="mt-2">
                          <Progress value={path.matchScore} className="h-1.5" />
                        </div>

                        {/* 工具标签 */}
                        <div className="flex flex-wrap gap-1 mt-2">
                          {path.tools.slice(0, 4).map((tool) => (
                            <span
                              key={tool}
                              className="text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded"
                            >
                              {tool}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* 右侧：箭头 */}
                    <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}

/** 骨架屏卡片 */
function CardSkeleton({ className }: { className?: string }) {
  return (
    <Card className={cn(className)}>
      <CardContent className="p-4">
        <div className="flex gap-3">
          <Skeleton className="h-8 w-8 rounded-lg shrink-0" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}