"use client"

import {
  Tv,
  PlayCircle,
  Eye,
  PlusCircle,
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react"
import { cn, formatNumber } from "@/lib/utils"
import { StatSkeleton } from "@/components/ui/skeleton"
import { useGSAPCounter } from "@/hooks/useGSAPReveal"
import type { DashboardKPI } from "@/lib/store"

interface KPICardsProps {
  data?: DashboardKPI | null
  loading?: boolean
}

const kpiConfig = [
  {
    key: "totalChannels" as const,
    label: "监控频道",
    icon: Tv,
    color: "text-primary",
    accent: "border-primary/20",
    sparkline: [12, 19, 15, 25, 22, 30, 28],
  },
  {
    key: "totalVideos" as const,
    label: "总视频数",
    icon: PlayCircle,
    color: "text-emerald-600 dark:text-emerald-400",
    accent: "border-emerald-500/20",
    sparkline: [45, 52, 48, 60, 55, 68, 72],
  },
  {
    key: "totalViews" as const,
    label: "总播放",
    icon: Eye,
    color: "text-amber-600 dark:text-amber-400",
    accent: "border-amber-500/20",
    sparkline: [120, 135, 128, 150, 145, 168, 175],
  },
  {
    key: "todayNewVideos" as const,
    label: "今日新增",
    icon: PlusCircle,
    color: "text-violet-600 dark:text-violet-400",
    accent: "border-violet-500/20",
    sparkline: [2, 5, 3, 8, 6, 10, 7],
  },
  {
    key: "monitoringStatus" as const,
    label: "监控状态",
    icon: Activity,
    color: "text-primary",
    accent: "border-primary/20",
    sparkline: null,
  },
]

const statusMap: Record<string, { text: string; color: string }> = {
  normal: { text: "正常", color: "text-emerald-600 dark:text-emerald-400" },
  warning: { text: "警告", color: "text-amber-600 dark:text-amber-400" },
  error: { text: "异常", color: "text-red-500 dark:text-red-400" },
}

/** 迷你 Sparkline SVG */
function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const width = 48
  const height = 20
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - ((v - min) / range) * (height - 4) - 2
    return `${x},${y}`
  })

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="opacity-40">
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={color}
      />
      {/* 终点小圆点 */}
      <circle
        cx={points[points.length - 1].split(",")[0]}
        cy={points[points.length - 1].split(",")[1]}
        r="1.5"
        className={color}
        fill="currentColor"
      />
    </svg>
  )
}

function CounterNumber({ value }: { value: number }) {
  const ref = useGSAPCounter(value, { duration: 1.5, ease: "power2.out" })
  return <span ref={ref} className="tabular-nums">{value.toLocaleString()}</span>
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
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {kpiConfig.map((kpi) => {
        const Icon = kpi.icon
        const rawValue: unknown = data[kpi.key]
        let displayValue: string | number
        let numericValue = 0
        let iconColor = kpi.color

        if (kpi.key === "monitoringStatus") {
          const status = statusMap[String(rawValue)] || statusMap.normal
          displayValue = status.text
          iconColor = status.color
        } else {
          numericValue = typeof rawValue === "number" && Number.isFinite(rawValue) ? rawValue : 0
          displayValue = formatNumber(numericValue)
        }

        const isStatus = kpi.key === "monitoringStatus"
        const growthValue = data.avgGrowthRate ?? 0

        return (
          <div
            key={kpi.key}
            className={cn(
              "relative overflow-hidden paper-card page-corner depth-hover p-5 min-h-[170px]",
              kpi.accent
            )}
          >
            <div className="absolute inset-x-0 top-0 h-px bg-primary/10" />
            <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-primary/5" />
            <div className="absolute bottom-0 left-0 right-0 h-10 bg-[linear-gradient(180deg,transparent,rgba(255,255,255,0.03))] dark:bg-[linear-gradient(180deg,transparent,rgba(255,255,255,0.01))]" />

            <div className="relative z-10 flex h-full flex-col justify-between gap-4">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1 flex-1 min-w-0">
                  <p className="text-[10px] text-muted-foreground font-serif tracking-[0.18em] uppercase">{kpi.label}</p>
                  <p className="text-[12px] text-muted-foreground/70 font-serif tracking-[0.12em] uppercase">{kpi.key === "monitoringStatus" ? "系统状态" : "核心指标"}</p>
                </div>
                <div
                  className={cn(
                    "h-10 w-10 rounded-lg flex items-center justify-center shrink-0 border bg-background/70",
                    kpi.accent
                  )}
                >
                  <Icon className={cn("h-5 w-5", iconColor)} />
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-3xl font-bold tracking-tight font-serif text-foreground tabular-nums leading-tight">
                  {isStatus ? displayValue : <CounterNumber value={numericValue} />}
                </p>
                <div className="kpi-divider" />
                <div className="flex items-end justify-between gap-3">
                  {!isStatus && (
                    <div className="flex items-center gap-1 text-xs min-w-0">
                      {growthValue > 0 ? (
                        <>
                          <TrendingUp className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
                          <span className="text-emerald-600 dark:text-emerald-400 font-medium">+{growthValue}%</span>
                        </>
                      ) : growthValue < 0 ? (
                        <>
                          <TrendingDown className="h-3 w-3 text-red-500 dark:text-red-400" />
                          <span className="text-red-500 dark:text-red-400 font-medium">{growthValue}%</span>
                        </>
                      ) : (
                        <>
                          <Minus className="h-3 w-3 text-muted-foreground" />
                          <span className="text-muted-foreground">持平</span>
                        </>
                      )}
                      <span className="text-muted-foreground/60 ml-1 truncate">平均增长</span>
                    </div>
                  )}

                  {kpi.sparkline && !isStatus && (
                    <MiniSparkline data={kpi.sparkline} color={iconColor} />
                  )}
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
