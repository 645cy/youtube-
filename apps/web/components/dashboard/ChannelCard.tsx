"use client"

import Image from "next/image"
import { Users, PlayCircle, TrendingUp } from "lucide-react"
import { cn, formatCompactNumber } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import type { IntelChannel } from "@/lib/store"

interface ChannelCardProps {
  channel: IntelChannel
  onClick?: (channel: IntelChannel) => void
  className?: string
}

const statusColorMap = {
  active: "bg-emerald-500/20 text-emerald-600 border-emerald-500/30 dark:text-emerald-400",
  paused: "bg-amber-500/20 text-amber-600 border-amber-500/30 dark:text-amber-400",
  error: "bg-red-500/20 text-red-600 border-red-500/30 dark:text-red-400",
}

const sourceIconMap: Record<string, string> = {
  youtube: "YT",
  twitter: "TW",
  rss: "RSS",
  custom: "CU",
}

/** 分类色标签映射 */
const categoryColorMap: Record<string, { bg: string; text: string; border: string }> = {
  tech: { bg: "bg-blue-500/10", text: "text-blue-600 dark:text-blue-400", border: "border-blue-500/20" },
  business: { bg: "bg-emerald-500/10", text: "text-emerald-600 dark:text-emerald-400", border: "border-emerald-500/20" },
  lifestyle: { bg: "bg-amber-500/10", text: "text-amber-600 dark:text-amber-400", border: "border-amber-500/20" },
  education: { bg: "bg-violet-500/10", text: "text-violet-600 dark:text-violet-400", border: "border-violet-500/20" },
  entertainment: { bg: "bg-rose-500/10", text: "text-rose-600 dark:text-rose-400", border: "border-rose-500/20" },
  default: { bg: "bg-primary/8", text: "text-primary", border: "border-primary/20" },
}

/** SVG 角落花边装饰 */
function LaceCorner({ className }: { className?: string }) {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      className={className}
    >
      <path
        d="M0 0L8 0C8 4.4 11.6 8 16 8C20.4 8 24 4.4 24 0L32 0"
        stroke="currentColor"
        strokeWidth="0.6"
        fill="none"
      />
      <path
        d="M0 0L0 8C4.4 8 8 11.6 8 16C8 20.4 4.4 24 0 24L0 32"
        stroke="currentColor"
        strokeWidth="0.6"
        fill="none"
      />
      <circle cx="4" cy="4" r="1" fill="currentColor" opacity="0.5" />
    </svg>
  )
}

/** 书脊阴影 — 模拟书页厚度 */
function SpineShadow() {
  return (
    <div
      className="absolute top-0 bottom-0 right-0 w-[3px] pointer-events-none z-10"
      style={{
        background: "linear-gradient(90deg, rgba(0,0,0,0.04) 0%, rgba(0,0,0,0.01) 50%, transparent 100%)",
      }}
    />
  )
}

export function ChannelCard({ channel, onClick, className }: ChannelCardProps) {
  const { name, description, coverUrl, subscriberCount, status, tags, metrics } = channel

  // 根据标签推断分类
  const primaryTag = tags[0]?.toLowerCase() || ""
  let category = "default"
  if (primaryTag.includes("tech") || primaryTag.includes("ai") || primaryTag.includes("software")) category = "tech"
  else if (primaryTag.includes("business") || primaryTag.includes("money") || primaryTag.includes("finance")) category = "business"
  else if (primaryTag.includes("life") || primaryTag.includes("health") || primaryTag.includes("travel")) category = "lifestyle"
  else if (primaryTag.includes("edu") || primaryTag.includes("learn") || primaryTag.includes("tutorial")) category = "education"
  else if (primaryTag.includes("entertain") || primaryTag.includes("fun") || primaryTag.includes("game")) category = "entertainment"

  const catStyle = categoryColorMap[category] || categoryColorMap.default

  return (
    <div
      className={cn(
        "group cursor-pointer overflow-hidden paper-card page-corner paper-hover-lift relative",
        className
      )}
      role="button"
      tabIndex={0}
      onClick={() => onClick?.(channel)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onClick?.(channel)
        }
      }}
    >
      <div className="card-lace-corner top-right text-primary/20 dark:text-primary/15">
        <LaceCorner />
      </div>
      <div className="card-lace-corner bottom-left text-primary/20 dark:text-primary/15">
        <LaceCorner />
      </div>

      <SpineShadow />

      <div className="relative aspect-[16/10] overflow-hidden bg-muted/20">
        <Image
          src={coverUrl || "/images/placeholder-channel.svg"}
          alt={name}
          fill
          className="object-cover transition-transform duration-700 group-hover:scale-[1.03]"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
          onError={(e) => {
            const target = e.currentTarget as HTMLImageElement
            target.style.display = "none"
            target.parentElement?.classList.add("bg-muted", "flex", "items-center", "justify-center")
            const fallback = document.createElement("span")
            fallback.className = "text-xs text-muted-foreground font-serif"
            fallback.textContent = "无封面"
            target.parentElement?.appendChild(fallback)
          }}
        />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.06),transparent_22%,rgba(0,0,0,0.32))]" />
        <div className="absolute inset-x-0 top-0 h-px bg-primary/15" />
        <div className="absolute top-2.5 left-2.5 z-10">
          <span className="bg-black/42 backdrop-blur text-white/90 text-[10px] font-bold px-2 py-0.5 rounded font-serif tracking-wider">
            {sourceIconMap[channel.sourceType]}
          </span>
        </div>
        <div className="absolute top-2.5 right-2.5 z-10">
          <Badge variant="outline" className={cn("text-[10px] backdrop-blur-sm bg-black/20", statusColorMap[status])}>
            {status === "active" ? "监控中" : status === "paused" ? "已暂停" : "异常"}
          </Badge>
        </div>
        <div className="absolute bottom-3 left-3 right-3 z-10 flex items-end justify-between gap-2">
          <div className="min-w-0 max-w-[72%]">
            <h3 className="truncate text-sm font-semibold text-white drop-shadow font-serif tracking-wide">
              {name}
            </h3>
            <p className="mt-1 line-clamp-1 text-[10px] text-white/75 font-serif tracking-[0.08em] uppercase">
              {tags[0] || "未分类"}
            </p>
          </div>
          <span className={cn("text-[9px] px-1.5 py-0.5 rounded border font-serif tracking-wide backdrop-blur-sm", catStyle.bg, catStyle.text, catStyle.border)}>
            {tags[0] || "未分类"}
          </span>
        </div>
      </div>

      <div className="p-4 space-y-3">
        <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed tracking-wide min-h-[2.5rem]">
          {description}
        </p>

        <div className="kpi-divider" />

        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="rounded-md border border-border/60 bg-background/60 px-2 py-2">
            <div className="flex items-center gap-1 text-muted-foreground">
              <Users className="h-3 w-3" />
              <span className="text-[10px] font-serif uppercase tracking-[0.14em]">订阅</span>
            </div>
            <div className="mt-1 font-semibold tabular-nums text-foreground">{formatCompactNumber(subscriberCount)}</div>
          </div>
          <div className="rounded-md border border-border/60 bg-background/60 px-2 py-2">
            <div className="flex items-center gap-1 text-muted-foreground">
              <PlayCircle className="h-3 w-3" />
              <span className="text-[10px] font-serif uppercase tracking-[0.14em]">视频</span>
            </div>
            <div className="mt-1 font-semibold tabular-nums text-foreground">{metrics.totalVideos}</div>
          </div>
          <div className="rounded-md border border-border/60 bg-background/60 px-2 py-2">
            <div className="flex items-center gap-1 text-muted-foreground">
              <TrendingUp className="h-3 w-3" />
              <span className="text-[10px] font-serif uppercase tracking-[0.14em]">增长</span>
            </div>
            <div className={cn("mt-1 font-semibold tabular-nums", metrics.growthRate > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-500 dark:text-red-400")}>
              {metrics.growthRate > 0 ? "+" : ""}{metrics.growthRate}%
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {tags.slice(1, 4).map((tag) => (
            <span
              key={tag}
              className="text-[10px] bg-secondary/70 text-muted-foreground px-1.5 py-0.5 rounded font-serif tracking-wide"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
