/**
 * GrowthChart 组件 - 情报总控台增长趋势图
 * 基于 Recharts AreaChart，展示订阅/观看/视频增长趋势
 * 自动适配暗色主题
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
 * 自定义 Tooltip
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
    <div className="rounded-xl border bg-background/95 backdrop-blur-sm p-3 shadow-xl">
      <p className="text-xs text-muted-foreground mb-2">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 text-sm py-0.5">
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-medium">{formatCompactNumber(entry.value)}</span>
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

  // 轴线颜色
  const axisColor = isDark ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.4)"
  const gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)"

  if (loading) {
    return (
      <Card className={cn(className)}>
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
      <Card className={cn(className)}>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            增长趋势
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">
            暂无数据
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn(className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          增长趋势
          <span className="text-xs font-normal text-muted-foreground ml-2">
            (近30天)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              {/* 订阅数渐变 */}
              <linearGradient id="gradientSubs" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(217, 91%, 60%)" stopOpacity={0} />
              </linearGradient>
              {/* 观看数渐变 */}
              <linearGradient id="gradientViews" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(174, 72%, 56%)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(174, 72%, 56%)" stopOpacity={0} />
              </linearGradient>
              {/* 视频数渐变 */}
              <linearGradient id="gradientVideos" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(280, 65%, 60%)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(280, 65%, 60%)" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
            <XAxis
              dataKey="date"
              stroke={axisColor}
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value: string) => {
                const date = new Date(value)
                return `${date.getMonth() + 1}/${date.getDate()}`
              }}
            />
            <YAxis
              stroke={axisColor}
              fontSize={12}
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
              stroke="hsl(217, 91%, 60%)"
              strokeWidth={2}
              fill="url(#gradientSubs)"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="views"
              name="观看数"
              stroke="hsl(174, 72%, 56%)"
              strokeWidth={2}
              fill="url(#gradientViews)"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="videos"
              name="视频数"
              stroke="hsl(280, 65%, 60%)"
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