/**
 * VideoDrawer 组件 - Phase 3
 * 视频展开面板精致化：paper-card 风格、书页厚度阴影、水墨动画
 */

"use client"

import Image from "next/image"
import { Eye, Calendar, FileText, BarChart3, ExternalLink } from "lucide-react"
import { formatNumber, formatDate } from "@/lib/utils"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/drawer"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"

import type { VideoItem } from "@/lib/store"

interface VideoDrawerProps {
  channelId: string
  channelName: string
  isOpen: boolean
  onClose: () => void
  videos: VideoItem[]
  loading?: boolean
  stats?: {
    video_count: number
    total_views: number
    avg_views_per_video: number
    subscriber_count: number | null
  } | null
  onAnalyzeVideo?: (video: VideoItem) => void
}

export function VideoDrawer({
  channelName,
  isOpen,
  onClose,
  videos,
  loading = false,
  stats,
  onAnalyzeVideo,
}: VideoDrawerProps) {
  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full sm:max-w-2xl overflow-hidden p-0 flex flex-col bg-background">
        {/* 头部 — 精致书眉 */}
        <SheetHeader className="px-6 py-5 border-b relative bg-background/90">
          <div className="absolute top-0 left-6 right-6 h-px gold-rule" />
          <div className="absolute inset-x-0 bottom-0 h-10 bg-[linear-gradient(180deg,transparent,rgba(255,255,255,0.02))] dark:bg-[linear-gradient(180deg,transparent,rgba(255,255,255,0.01))]" />

          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="page-kicker">视频卷</span>
                <div className="h-px w-8 gold-rule" />
                <span className="page-meta truncate">频道展开</span>
              </div>
              <SheetTitle className="text-xl font-serif tracking-wide text-foreground truncate">{channelName}</SheetTitle>
              <SheetDescription className="text-xs tracking-wide text-muted-foreground">
                共 {videos.length} 个视频
              </SheetDescription>
            </div>
          </div>

          {stats && (
            <div className="mt-5 grid grid-cols-2 gap-3 text-xs md:grid-cols-4">
              <div className="paper-card page-corner p-3 bg-background/70">
                <p className="page-meta">订阅</p>
                <p className="mt-2 text-sm font-serif tabular-nums text-foreground">{(stats.subscriber_count ?? 0).toLocaleString()}</p>
              </div>
              <div className="paper-card page-corner p-3 bg-background/70">
                <p className="page-meta">视频</p>
                <p className="mt-2 text-sm font-serif tabular-nums text-foreground">{stats.video_count}</p>
              </div>
              <div className="paper-card page-corner p-3 bg-background/70">
                <p className="page-meta">总观看</p>
                <p className="mt-2 text-sm font-serif tabular-nums text-foreground">{(stats.total_views ?? 0).toLocaleString()}</p>
              </div>
              <div className="paper-card page-corner p-3 bg-background/70">
                <p className="page-meta">均播</p>
                <p className="mt-2 text-sm font-serif tabular-nums text-foreground">{typeof stats.avg_views_per_video === "number" ? Math.round(stats.avg_views_per_video).toLocaleString() : "-"}</p>
              </div>
            </div>
          )}
        </SheetHeader>

        {/* 视频列表 */}
        <ScrollArea className="flex-1 bg-background/40">
          <div className="p-4 space-y-3">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex gap-3 p-3 rounded-lg border paper-card page-corner bg-background/80">
                  <Skeleton className="h-20 w-32 rounded-md shrink-0" />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-3 w-2/3" />
                    <div className="flex gap-2">
                      <Skeleton className="h-3 w-16" />
                      <Skeleton className="h-3 w-16" />
                    </div>
                  </div>
                </div>
              ))
            ) : videos.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-muted-foreground paper-card page-corner bg-background/60 border-dashed border-border/50">
                <FileText className="h-12 w-12 mb-3 opacity-50" />
                <p className="text-sm font-serif tracking-wide text-foreground">暂无视频数据</p>
                <p className="text-xs text-muted-foreground/70 mt-1 tracking-wide">该频道尚未抓取视频信息</p>
              </div>
            ) : (
              videos.map((video, index) => (
                <VideoListItem
                  key={video.id}
                  video={video}
                  onAnalyze={onAnalyzeVideo}
                  index={index}
                />
              ))
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}

/** 视频列表项 */
function VideoListItem({
  video,
  onAnalyze,
  index,
}: {
  video: VideoItem
  onAnalyze?: ((video: VideoItem) => void) | undefined
  index: number
}) {
  const handleOpenYoutube = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (video.youtubeId) {
      window.open(`https://www.youtube.com/watch?v=${video.youtubeId}`, "_blank")
    }
  }
  const handleAnalyze = (e: React.MouseEvent) => {
    e.stopPropagation()
    onAnalyze?.(video)
  }

  return (
    <div
      className="group flex gap-3 rounded-lg border p-3 hover:bg-accent/40 transition-all duration-300 paper-card page-corner bg-background/80"
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      {/* 缩略图 */}
      <div className="relative aspect-video w-32 flex-shrink-0 overflow-hidden rounded-md bg-muted">
        <Image
          src={video.thumbnailUrl || "/images/placeholder-video.svg"}
          alt={video.title}
          fill
          className="object-cover transition-transform duration-500 group-hover:scale-105"
          sizes="128px"
          onError={(e) => {
            const target = e.currentTarget as HTMLImageElement
            target.style.display = "none"
            target.parentElement?.classList.add("bg-muted", "flex", "items-center", "justify-center")
            const fallback = document.createElement("span")
            fallback.className = "text-[10px] text-muted-foreground font-serif"
            fallback.textContent = "无缩略图"
            target.parentElement?.appendChild(fallback)
          }}
        />
        {/* 悬停操作 */}
        <div className="absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <button
            onClick={handleOpenYoutube}
            className="p-2 rounded-full bg-black/20 hover:bg-black/40 text-white transition-colors"
            title="在 YouTube 打开"
          >
            <ExternalLink className="h-4 w-4" />
          </button>
          {onAnalyze && video.youtubeId && (
            <button
              onClick={handleAnalyze}
              className="p-2 rounded-full bg-primary/80 hover:bg-primary text-white transition-colors"
              title="AI 分析"
            >
              <BarChart3 className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1 rounded font-mono">
          {video.duration}
        </div>
      </div>

      {/* 信息 */}
      <div className="flex flex-1 flex-col justify-between min-w-0">
        <h4 className="text-sm font-medium line-clamp-2 group-hover:text-primary transition-colors duration-300 tracking-wide">
          {video.title}
        </h4>

        <div className="flex items-center gap-3 text-xs text-muted-foreground mt-2 tracking-wide">
          <span className="flex items-center gap-1">
            <Eye className="h-3 w-3" />
            <span className="tabular-nums">{formatNumber(video.viewCount)}</span>
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>{formatDate(video.publishDate)}</span>
          </span>
        </div>

        {video.summary && (
          <p className="text-[11px] text-muted-foreground line-clamp-1 mt-1 tracking-wide leading-relaxed">
            {video.summary}
          </p>
        )}
      </div>
    </div>
  )
}
