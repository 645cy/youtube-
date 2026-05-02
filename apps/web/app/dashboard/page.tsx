/**
 * 情报总控台页面 - /dashboard
 * 功能：
 * - 搜索栏（频道搜索）
 * - KPI 概览卡片（总频道数/总视频数/今日新增/监控状态）
 * - 频道卡片网格（缩略图+关键指标）
 * - 视频展开 Drawer（点击频道展开视频列表）
 * - 标签云（niche 分类筛选）
 * - AreaChart 增长趋势
 */

"use client"

import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import {
  LayoutDashboard,
  Tag,
  RefreshCw,
  Tv,
  Search,
  Sparkles,
  X,
  Radar,
  DatabaseZap,
  Factory,
  FlaskConical,
  ArrowRight,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { SearchBox } from "@/components/dashboard/SearchBox"
import { ChannelCard } from "@/components/dashboard/ChannelCard"
import { VideoDrawer } from "@/components/dashboard/VideoDrawer"
import { KPICards } from "@/components/dashboard/KPICards"
import { GrowthChart } from "@/components/dashboard/GrowthChart"
import { VideoAnalysisPanel } from "@/components/analysis/VideoAnalysisPanel"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  useIntelStore,
  type IntelChannel,
  type VideoItem,
  type DashboardKPI,
  type TagItem,
} from "@/lib/store"
import { channelApi, videoApi, analysisApi, tagApi } from "@/lib/api"
import { mapChannelToIntelChannel, mapVideoToVideoItem } from "@/lib/mappers"
import { toastError, toastInfo } from "@/lib/toast"

// CRG: Surface the operating path on the default landing page without changing routes.
const WORKFLOW_ACTIONS = [
  { href: "/radar", label: "竞品雷达", detail: "添加频道", icon: Radar },
  { href: "/crawler", label: "任务中心", detail: "抓取数据", icon: DatabaseZap },
  { href: "/factory", label: "内容工厂", detail: "生成方案", icon: Factory },
  { href: "/lab", label: "OCP 实验室", detail: "规划变现", icon: FlaskConical },
]

// =============================================================================
// 页面组件
// =============================================================================

export default function DashboardPage() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] = useState<IntelChannel | null>(
    null
  )
  const [videos, setVideos] = useState<VideoItem[]>([])
  const [videosLoading, setVideosLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const [discovering, setDiscovering] = useState(false)
  const [showDiscoverInput, setShowDiscoverInput] = useState(false)
  const [discoverKeywords, setDiscoverKeywords] = useState("AI make money, passive income, ChatGPT business")
  const [analysisOpen, setAnalysisOpen] = useState(false)
  const [analysisVideoId, setAnalysisVideoId] = useState<string>("")
  const [analysisVideoTitle, setAnalysisVideoTitle] = useState<string>("")
  const [channelStats, setChannelStats] = useState<{
    video_count: number
    total_views: number
    avg_views_per_video: number
    subscriber_count: number | null
  } | null>(null)

  const {
    tags,
    kpis,
    growthData,
    selectedTags,
    setChannels,
    setTags,
    setKPIs,
    setGrowthData,
    toggleTag,
    filteredChannels,
  } = useIntelStore()

  // 加载真实数据
  const loadDashboardData = useCallback(async () => {
    try {
      setRefreshing(true)
      // 并行加载频道、标签、KPI、增长数据
      const [channelsRes, tagsRes, kpiRes] = await Promise.allSettled([
        channelApi.list({ limit: 50 }),
        tagApi.list(),
        analysisApi.getDashboardKPI(),
      ])

      // 频道数据转换
      if (channelsRes.status === "fulfilled" && channelsRes.value?.items) {
        const items = channelsRes.value.items
        const converted: IntelChannel[] = items.map(mapChannelToIntelChannel)
        if (converted.length > 0) setChannels(converted)
      }

      // 标签数据
      if (tagsRes.status === "fulfilled" && Array.isArray(tagsRes.value)) {
        const convertedTags: TagItem[] = tagsRes.value.map((t: any) => ({
          name: t.name || "未分类",
          count: t.count || 0,
          trend: (t.trend as any) || "stable",
        }))
        if (convertedTags.length > 0) setTags(convertedTags)
      }

      // KPI 数据
      if (kpiRes.status === "fulfilled" && kpiRes.value) {
        const k = kpiRes.value
        const convertedKPI: DashboardKPI = {
          totalChannels: k.total_channels ?? 0,
          totalVideos: k.total_videos ?? 0,
          todayNewVideos: 0,
          monitoringStatus: (k.active_monitors ?? 0) > 0 ? "normal" : "warning",
          avgGrowthRate: 0,
        }
        setKPIs(convertedKPI)
      }

      // 增长数据
      try {
        const growthRes = await analysisApi.getGrowth({ days: 30 })
        if (growthRes && growthRes.length > 0) {
          setGrowthData(growthRes)
        }
      } catch {
        // growth 数据非关键，失败静默
      }
    } catch (e) {
      toastError("加载仪表盘数据失败，请刷新重试")
    } finally {
      setRefreshing(false)
      setInitialLoading(false)
    }
  }, [setChannels, setTags, setKPIs, setGrowthData])

  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  // 处理频道点击 - 展开 VideoDrawer
  const handleChannelClick = useCallback(
    async (channel: IntelChannel) => {
      setSelectedChannel(channel)
      setDrawerOpen(true)
      setVideosLoading(true)
      setChannelStats(null)

      try {
        const channelIdNum = parseInt(channel.id, 10)
        const [videoRes, statsRes] = await Promise.allSettled([
          videoApi.list({ channel_id: channelIdNum, limit: 20 }),
          channelApi.getStats(channelIdNum),
        ])

        // 视频列表
        if (videoRes.status === "fulfilled") {
          const items = videoRes.value?.items || []
          const converted: VideoItem[] = items.map(mapVideoToVideoItem)
          setVideos(converted)
        } else {
          setVideos([])
        }

        // 频道统计
        if (statsRes.status === "fulfilled" && statsRes.value) {
          setChannelStats(statsRes.value)
        }
      } catch (e) {
        toastError("加载频道视频失败，请稍后重试")
        setVideos([])
      } finally {
        setVideosLoading(false)
      }
    },
    []
  )

  // 批量发现
  const handleBulkDiscover = useCallback(async () => {
    const keywords = discoverKeywords
      .split(",")
      .map((k) => k.trim())
      .filter((k) => k.length > 0)
    if (keywords.length === 0) {
      toastError("请输入至少一个关键词")
      return
    }
    setDiscovering(true)
    try {
      const res = await channelApi.bulkDiscover(keywords)
      toastInfo(`批量发现完成: 导入 ${res.imported} 个频道`)
      await loadDashboardData()
      setShowDiscoverInput(false)
    } catch (e: any) {
      toastError("批量发现失败: " + (e.message || "未知错误"))
    } finally {
      setDiscovering(false)
    }
  }, [discoverKeywords, loadDashboardData])

  // 过滤后的频道列表
  const displayChannels = filteredChannels()

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <LayoutDashboard className="h-6 w-6 text-primary" />
            情报总控台
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            实时监控频道动态，洞察内容趋势
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadDashboardData} disabled={refreshing}>
            <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
            {refreshing ? "刷新中..." : "刷新数据"}
          </Button>
          {showDiscoverInput ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={discoverKeywords}
                onChange={(e) => setDiscoverKeywords(e.target.value)}
                placeholder="输入关键词，用逗号分隔"
                className="h-9 rounded-md border bg-background px-3 text-sm w-64"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleBulkDiscover()
                  }
                }}
              />
              <Button
                variant="secondary"
                size="sm"
                onClick={handleBulkDiscover}
                disabled={discovering}
              >
                <Sparkles className={cn("h-4 w-4 mr-1", discovering && "animate-spin")} />
                {discovering ? "发现中..." : "开始"}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setShowDiscoverInput(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowDiscoverInput(true)}
            >
              <Search className="h-4 w-4 mr-2" />
              批量发现
            </Button>
          )}
        </div>
      </div>

      {/* CRG: Put the main operating flow before secondary dashboard widgets. */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {WORKFLOW_ACTIONS.map((action) => {
          const Icon = action.icon
          return (
            <Link
              key={action.href}
              href={action.href}
              className="group flex min-h-20 items-center justify-between rounded-lg border bg-card px-4 py-3 transition hover:border-primary/50 hover:bg-accent"
            >
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{action.label}</div>
                  <div className="truncate text-xs text-muted-foreground">{action.detail}</div>
                </div>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground transition group-hover:translate-x-0.5 group-hover:text-primary" />
            </Link>
          )
        })}
      </div>

      {/* KPI 概览 */}
      <KPICards data={kpis} loading={!kpis} />

      {/* 搜索栏 */}
      <SearchBox />

      {/* 标签云 */}
      <div className="flex items-center gap-2 flex-wrap">
        <Tag className="h-4 w-4 text-muted-foreground shrink-0" />
        {tags.map((tag) => (
          <Badge
            key={tag.name}
            variant={selectedTags.includes(tag.name) ? "default" : "outline"}
            className="cursor-pointer transition-all text-xs"
            onClick={() => toggleTag(tag.name)}
          >
            {tag.name}
            <span className="ml-1 opacity-60">{tag.count}</span>
          </Badge>
        ))}
      </div>

      {/* 频道卡片网格 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Tv className="h-5 w-5 text-primary" />
            监控频道
          </h2>
          <span className="text-sm text-muted-foreground">
            共 {displayChannels.length} 个频道
          </span>
        </div>

        {initialLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="h-44 rounded-lg border bg-muted/20 animate-pulse" />
            ))}
          </div>
        ) : (
          <motion.div
            layout
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
          >
            {displayChannels.map((channel, index) => (
              <motion.div
                key={channel.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
              >
                <ChannelCard
                  channel={channel}
                  onClick={handleChannelClick}
                />
              </motion.div>
            ))}
          </motion.div>
        )}

        {!initialLoading && displayChannels.length === 0 && (
          <div className="text-center py-12 text-muted-foreground border rounded-lg border-dashed">
            <Tv className="h-10 w-10 mx-auto mb-2 opacity-50" />
            <p className="text-sm">没有找到匹配的频道</p>
            <p className="text-xs mt-1">尝试调整搜索条件或筛选标签</p>
          </div>
        )}
      </div>

      {/* 增长趋势图 */}
      <GrowthChart data={growthData} loading={false} />

      {/* Video Drawer */}
      <VideoDrawer
        channelId={selectedChannel?.id ?? ""}
        channelName={selectedChannel?.name ?? ""}
        isOpen={drawerOpen}
        onClose={() => {
          setDrawerOpen(false)
          setSelectedChannel(null)
          setChannelStats(null)
        }}
        videos={videos}
        loading={videosLoading}
        stats={channelStats}
        onAnalyzeVideo={(video) => {
          if (video.youtubeId) {
            setAnalysisVideoId(video.youtubeId)
            setAnalysisVideoTitle(video.title)
            setAnalysisOpen(true)
          }
        }}
      />

      <VideoAnalysisPanel
        youtubeId={analysisVideoId}
        videoTitle={analysisVideoTitle}
        isOpen={analysisOpen}
        onClose={() => {
          setAnalysisOpen(false)
          setAnalysisVideoId("")
          setAnalysisVideoTitle("")
        }}
      />
    </div>
  )
}
