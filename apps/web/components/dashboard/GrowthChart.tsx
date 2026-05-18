/**
 * GrowthChart 组件 - Phase 3
 * 暗色模式使用暖色调（金色/琥珀色系），Tooltip 精致化
 */

"use client"

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { useTheme } from "next-themes"
import { TrendingUp } from "lucide-react"
import { cn, formatCompactNumber } from "@/lib/utils"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { GrowthDataPoint } from "@/lib/store"

interface GrowthChartProps {
  data: GrowthDataPoint[]
  loading?: boolean
  className?: string
}

/**
 * 自定义 Tooltip - Phase 3 精致化
 */
function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ name: string; value: number; color: string }>
  label?: string
}) {
  if (!active || !payload?.length) return null

  return (
    <div className="rounded-xl border bg-background/95 backdrop-blur-sm p-3 shadow-xl paper-card page-corner">
      <p className="text-xs text-muted-foreground mb-2 tracking-wide font-serif">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 text-sm py-0.5 tracking-wide">
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-medium tabular-nums">{formatCompactNumber(entry.value)}</span>
        </div>
      ))}
    </div>
  )
}

export function GrowthChart({
  data,
  loading = false,
  className,
}: GrowthChartProps) {
  const { theme } = useTheme()
  const isDark = theme === "dark"

  const axisColor = isDark ? "rgba(255,255,255,0.35)" : "rgba(0,0,0,0.35)"
  const gridColor = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)"

  // 暗色模式使用暖色调，明亮模式使用原色调
  const colors = isDark
    ? {
        subs: { stroke: "hsl(38, 50%, 55%)", fill: "hsl(38, 50%, 55%)" },
        views: { stroke: "hsl(30, 45%, 50%)", fill: "hsl(30, 45%, 50%)" },
        videos: { stroke: "hsl(45, 40%, 48%)", fill: "hsl(45, 40%, 48%)" },
      }
    : {
        subs: { stroke: "hsl(217, 91%, 60%)", fill: "hsl(217, 91%, 60%)" },
        views: { stroke: "hsl(174, 72%, 56%)", fill: "hsl(174, 72%, 56%)" },
        videos: { stroke: "hsl(280, 65%, 60%)", fill: "hsl(280, 65%, 60%)" },
      }

  if (loading) {
    return (
      <Card className={cn("paper-card page-corner", className)}>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  if (data.length === 0) {
    return (
      <Card className={cn("paper-card page-corner", className)}>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2 font-serif tracking-wide">
            <TrendingUp className="h-4 w-4 text-primary" />
            增长趋势
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex flex-col items-center justify-center text-muted-foreground">
            <TrendingUp className="h-10 w-10 mb-3 opacity-30" />
            <p className="text-sm font-serif tracking-wide">暂无数据</p>
            <p className="text-xs text-muted-foreground/70 mt-1 tracking-wide">运行爬虫任务后将显示增长趋势</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn("paper-card page-corner", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2 font-serif tracking-wide">
          <TrendingUp className="h-4 w-4 text-primary" />
          增长趋势
          <span className="text-xs font-normal text-muted-foreground ml-2 tracking-wide">
            (近30天)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="gradientSubs" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors.subs.fill} stopOpacity={0.25} />
                <stop offset="95%" stopColor={colors.subs.fill} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradientViews" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors.views.fill} stopOpacity={0.25} />
                <stop offset="95%" stopColor={colors.views.fill} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradientVideos" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors.videos.fill} stopOpacity={0.25} />
                <stop offset="95%" stopColor={colors.videos.fill} stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
            <XAxis
              dataKey="date"
              stroke={axisColor}
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value: string) => {
                const date = new Date(value)
                return `${date.getMonth() + 1}/${date.getDate()}`
              }}
            />
            <YAxis
              stroke={axisColor}
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => formatCompactNumber(v)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }}
            />

            <Area
              type="monotone"
              dataKey="subscribers"
              name="订阅数"
              stroke={colors.subs.stroke}
              strokeWidth={2}
              fill="url(#gradientSubs)"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="views"
              name="观看数"
              stroke={colors.views.stroke}
              strokeWidth={2}
              fill="url(#gradientViews)"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="videos"
              name="视频数"
              stroke={colors.videos.stroke}
              strokeWidth={2}
              fill="url(#gradientVideos)"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
