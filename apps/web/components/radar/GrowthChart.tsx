/**
 * GrowthChart 组件 - 竞品雷达增长曲线
 * 基于 Recharts LineChart，展示频道增长趋势
 */

"use client"

import {
  LineChart,
  Line,
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

/** 增长数据点 */
interface GrowthDataPoint {
  date: string
  [key: string]: string | number
}

interface RadarGrowthChartProps {
  data: GrowthDataPoint[]
  series: Array<{
    key: string
    name: string
    color: string
  }>
  loading?: boolean
  className?: string
}

/**
 * 自定义 Tooltip - 精致化
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

export function RadarGrowthChart({
  data,
  series,
  loading = false,
  className,
}: RadarGrowthChartProps) {
  const { theme } = useTheme()
  const isDark = theme === "dark"

  const axisColor = isDark ? "rgba(255,255,255,0.35)" : "rgba(0,0,0,0.35)"
  const gridColor = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)"

  // 暗色模式使用暖色调（金色/琥珀色系），明亮模式使用原色调
  const lineColors = isDark
    ? [
        "hsl(38, 50%, 55%)",
        "hsl(30, 45%, 50%)",
        "hsl(45, 40%, 48%)",
        "hsl(25, 42%, 52%)",
        "hsl(50, 35%, 50%)",
      ]
    : series.map((s) => s.color)

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

  return (
    <Card className={cn("paper-card page-corner bg-background/80", className)}>
      <CardHeader className="pb-2 border-b border-border/40">
        <CardTitle className="text-base flex items-center gap-2 font-serif tracking-wide">
          <TrendingUp className="h-4 w-4 text-primary" />
          增长曲线
          <span className="text-xs font-normal text-muted-foreground ml-2 tracking-wide">
            (订阅数趋势)
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-5">
        {data.length === 0 ? (
          <div className="h-[300px] flex flex-col items-center justify-center text-muted-foreground">
            <TrendingUp className="h-10 w-10 mb-3 opacity-30" />
            <p className="text-sm font-serif tracking-wide">请选择频道查看增长趋势</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={data}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={gridColor}
                vertical={false}
              />
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
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />

              {series.map((s, i) => (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.name}
                  stroke={isDark ? lineColors[i % lineColors.length] : s.color}
                  strokeWidth={2.2}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 2 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
