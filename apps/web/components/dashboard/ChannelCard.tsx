/**
 * ChannelCard 组件 - 情报总控台频道卡片
 * 展示频道缩略图、名称、关键指标（订阅数/视频数/增长率）
 * 点击展开 VideoDrawer
 */

"use client"

import Image from "next/image"
import { Users, PlayCircle, TrendingUp } from "lucide-react"
import { cn, formatCompactNumber } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { IntelChannel } from "@/lib/store"

interface ChannelCardProps {
  channel: IntelChannel
  onClick?: (channel: IntelChannel) => void
  className?: string
}

/** 状态颜色映射 */
const statusColorMap = {
  active: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  paused: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  error: "bg-red-500/20 text-red-400 border-red-500/30",
}

/** 来源图标映射 */
const sourceIconMap = {
  youtube: "YT",
  twitter: "TW",
  rss: "RSS",
  custom: "CU",
}

export function ChannelCard({ channel, onClick, className }: ChannelCardProps) {
  const { name, description, coverUrl, subscriberCount, status, tags, metrics } =
    channel

  return (
    <Card
      className={cn(
        "group cursor-pointer overflow-hidden transition-all duration-300",
        "hover:shadow-lg hover:shadow-primary/5 hover:ring-1 hover:ring-primary/30",
        "active:scale-[0.98]",
        className
      )}
      onClick={() => onClick?.(channel)}
    >
      {/* 缩略图区域 */}
      <div className="relative aspect-video overflow-hidden">
        <Image
          src={coverUrl || "/images/placeholder-channel.svg"}
          alt={name}
          fill
          className="object-cover transition-transform duration-500 group-hover:scale-105"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
        />
        {/* 渐变遮罩 */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

        {/* 状态 Badge */}
        <div className="absolute top-2 right-2">
          <Badge variant="outline" className={cn("text-[10px]", statusColorMap[status])}>
            {status === "active" ? "监控中" : status === "paused" ? "已暂停" : "异常"}
          </Badge>
        </div>

        {/* 来源标识 */}
        <div className="absolute top-2 left-2">
          <span className="bg-black/50 backdrop-blur text-white text-[10px] font-bold px-2 py-0.5 rounded">
            {sourceIconMap[channel.sourceType]}
          </span>
        </div>

        {/* 底部信息 */}
        <div className="absolute bottom-2 left-2 right-2">
          <h3 className="text-white font-semibold text-sm truncate drop-shadow">
            {name}
          </h3>
        </div>
      </div>

      {/* 指标区域 */}
      <CardContent className="p-3 space-y-2">
        {/* 描述 */}
        <p className="text-xs text-muted-foreground line-clamp-2">
          {description}
        </p>

        {/* 关键指标 */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1 text-muted-foreground">
            <Users className="h-3 w-3" />
            <span>{formatCompactNumber(subscriberCount)}</span>
          </div>
          <div className="flex items-center gap-1 text-muted-foreground">
            <PlayCircle className="h-3 w-3" />
            <span>{metrics.totalVideos}</span>
          </div>
          <div className={cn(
            "flex items-center gap-1 font-medium",
            metrics.growthRate > 0 ? "text-emerald-400" : "text-red-400"
          )}>
            <TrendingUp className="h-3 w-3" />
            <span>{metrics.growthRate > 0 ? "+" : ""}{metrics.growthRate}%</span>
          </div>
        </div>

        {/* 标签 */}
        <div className="flex flex-wrap gap-1">
          {tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="text-[10px] bg-muted text-muted-foreground px-1.5 py-0.5 rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
