/**
 * KPICards 组件 - 情报总控台 KPI 概览卡片
 * 展示：总频道数 / 总视频数 / 今日新增 / 监控状态
 * 配合趋势指示器（升/降）
 */

"use client"

import {
  Tv,
  PlayCircle,
  PlusCircle,
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react"
import { cn, formatNumber } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { StatSkeleton } from "@/components/ui/skeleton"
import type { DashboardKPI } from "@/lib/store"

interface KPICardsProps {
  data?: DashboardKPI | null
  loading?: boolean
}

/** KPI 配置 */
const kpiConfig = [
  {
    key: "totalChannels" as const,
    label: "监控频道",
    icon: Tv,
    color: "text-blue-400",
    bgColor: "bg-blue-400/10",
  },
  {
    key: "totalVideos" as const,
    label: "总视频数",
    icon: PlayCircle,
    color: "text-emerald-400",
    bgColor: "bg-emerald-400/10",
  },
  {
    key: "todayNewVideos" as const,
    label: "今日新增",
    icon: PlusCircle,
    color: "text-violet-400",
    bgColor: "bg-violet-400/10",
  },
  {
    key: "monitoringStatus" as const,
    label: "监控状态",
    icon: Activity,
    color: "text-amber-400",
    bgColor: "bg-amber-400/10",
  },
]

/** 状态映射 */
const statusMap: Record<string, { text: string; color: string }> = {
  normal: { text: "正常", color: "text-emerald-400" },
  warning: { text: "警告", color: "text-amber-400" },
  error: { text: "异常", color: "text-red-400" },
}

export function KPICards({ data, loading = false }: KPICardsProps) {
  if (loading || !data) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatSkeleton key={i} />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpiConfig.map((kpi) => {
        const Icon = kpi.icon
        let value: string | number = data[kpi.key]

        // 特殊处理监控状态
        if (kpi.key === "monitoringStatus") {
          const status = statusMap[value as string] || statusMap.normal
          value = status.text
          kpi.color = status.color
        } else {
          value = formatNumber(value as number)
        }

        return (
          <Card
            key={kpi.key}
            className="relative overflow-hidden group hover:shadow-lg transition-all"
          >
            {/* 背景装饰 */}
            <div
              className={cn(
                "absolute -right-4 -top-4 h-24 w-24 rounded-full opacity-10",
                kpi.bgColor
              )}
            />

            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground">{kpi.label}</p>
                  <p className="text-2xl font-bold tracking-tight">{value}</p>
                  {/* 趋势 */}
                  {kpi.key !== "monitoringStatus" && (
                    <div className="flex items-center gap-1 text-xs">
                      {data.avgGrowthRate > 0 ? (
                        <>
                          <TrendingUp className="h-3 w-3 text-emerald-400" />
                          <span className="text-emerald-400">
                            +{data.avgGrowthRate}%
                          </span>
                        </>
                      ) : data.avgGrowthRate < 0 ? (
                        <>
                          <TrendingDown className="h-3 w-3 text-red-400" />
                          <span className="text-red-400">
                            {data.avgGrowthRate}%
                          </span>
                        </>
                      ) : (
                        <>
                          <Minus className="h-3 w-3 text-muted-foreground" />
                          <span className="text-muted-foreground">持平</span>
                        </>
                      )}
                      <span className="text-muted-foreground ml-1">
                        平均增长
                      </span>
                    </div>
                  )}
                </div>

                <div
                  className={cn(
                    "h-10 w-10 rounded-lg flex items-center justify-center",
                    kpi.bgColor
                  )}
                >
                  <Icon className={cn("h-5 w-5", kpi.color)} />
                </div>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}