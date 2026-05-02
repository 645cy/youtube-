/**
 * VideoDrawer 组件 - 视频展开面板
 * 点击频道后从右侧滑出，展示视频列表
 * 基于 Radix Sheet（Drawer）
 */

"use client"

import Image from "next/image"
import { Eye, Calendar, FileText, BarChart3, ExternalLink, TrendingUp, Users, PlayCircle } from "lucide-react"
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
      <SheetContent className="w-full sm:max-w-xl overflow-hidden p-0 flex flex-col">
        {/* 头部 */}
        <SheetHeader className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <div>
              <SheetTitle className="text-lg">{channelName}</SheetTitle>
              <SheetDescription>
                共 {videos.length} 个视频
              </SheetDescription>
            </div>
          </div>
          {stats && (
            <div className="flex items-center gap-4 mt-3 text-xs">
              <div className="flex items-center gap-1 text-muted-foreground">
                <Users className="h-3 w-3" />
                <span>{(stats.subscriber_count ?? 0).toLocaleString()} 订阅</span>
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <PlayCircle className="h-3 w-3" />
                <span>{stats.video_count} 视频</span>
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <Eye className="h-3 w-3" />
                <span>{(stats.total_views ?? 0).toLocaleString()} 总观看</span>
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <TrendingUp className="h-3 w-3" />
                <span>均播 {Math.round(stats.avg_views_per_video).toLocaleString()}</span>
              </div>
            </div>
          )}
        </SheetHeader>

        {/* 视频列表 */}
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-3">
            {loading ? (
              // 骨架屏
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex gap-3 p-3 rounded-lg border">
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
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mb-3 opacity-50" />
                <p className="text-sm">暂无视频数据</p>
              </div>
            ) : (
              videos.map((video) => (
                <VideoListItem
                  key={video.id}
                  video={video}
                  onAnalyze={onAnalyzeVideo}
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
}: {
  video: VideoItem
  onAnalyze?: ((video: VideoItem) => void) | undefined
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
      className="group flex gap-3 rounded-lg border p-3 hover:bg-accent transition-all"
    >
      {/* 缩略图 */}
      <div className="relative aspect-video w-32 flex-shrink-0 overflow-hidden rounded-md bg-muted">
        <Image
          src={video.thumbnailUrl || "/images/placeholder-video.svg"}
          alt={video.title}
          fill
          className="object-cover transition-transform group-hover:scale-105"
          sizes="128px"
        />
        {/* 悬停操作 */}
        <div className="absolute inset-0 flex items-center justify-center gap-2 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleOpenYoutube}
            className="p-2 rounded-full bg-white/20 hover:bg-white/40 text-white transition-colors"
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
        {/* 时长 */}
        <div className="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1 rounded">
          {video.duration}
        </div>
      </div>

      {/* 信息 */}
      <div className="flex flex-1 flex-col justify-between min-w-0">
        <h4 className="text-sm font-medium line-clamp-2 group-hover:text-primary transition-colors">
          {video.title}
        </h4>

        <div className="flex items-center gap-3 text-xs text-muted-foreground mt-2">
          <span className="flex items-center gap-1">
            <Eye className="h-3 w-3" />
            {formatNumber(video.viewCount)}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatDate(video.publishDate)}
          </span>
        </div>

        {/* AI 摘要（如果有） */}
        {video.summary && (
          <p className="text-[11px] text-muted-foreground line-clamp-1 mt-1">
            {video.summary}
          </p>
        )}
      </div>
    </div>
  )
}