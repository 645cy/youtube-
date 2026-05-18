"use client"

import { useState, useEffect, useCallback, useRef, Suspense, lazy } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import gsap from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import { ChannelGrid } from "./components/ChannelGrid"
import {
  RefreshCw,
  Tv,
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
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { SectionHeading } from "@/components/SectionHeading"
import { HeroFooter } from "@/components/HeroFooter"
import {
  useIntelStore,
  type IntelChannel,
  type VideoItem,
  type DashboardKPI,
  type TagItem,
} from "@/lib/store"
import { channelApi, videoApi, analysisApi, tagApi } from "@/lib/api"
import { mapChannelToIntelChannel, mapVideoToVideoItem } from "@/lib/mappers"
import { toastError } from "@/lib/toast"

const VideoAnalysisPanel = lazy(() =>
  import("@/components/analysis/VideoAnalysisPanel").then((mod) => ({
    default: mod.VideoAnalysisPanel,
  }))
)

const CHANNEL_GRID_BATCH_SIZE = 12

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger)
}

const WORKFLOW_ACTIONS = [
  { href: "/radar", label: "竞品雷达", detail: "添加频道", icon: Radar, color: "#C7A15A" },
  { href: "/crawler", label: "任务中心", detail: "抓取数据", icon: DatabaseZap, color: "#5E86B6" },
  { href: "/factory", label: "内容工厂", detail: "生成方案", icon: Factory, color: "#3D9B7A" },
  { href: "/lab", label: "OCP 实验室", detail: "规划变现", icon: FlaskConical, color: "#A077D2" },
]

export default function DashboardPage() {
  const router = useRouter()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedChannel, setSelectedChannel] = useState<IntelChannel | null>(null)
  const [videos, setVideos] = useState<VideoItem[]>([])
  const [videosLoading, setVideosLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const [analysisOpen, setAnalysisOpen] = useState(false)
  const [analysisVideoId, setAnalysisVideoId] = useState<string>("")
  const [analysisVideoTitle, setAnalysisVideoTitle] = useState<string>("")
  const [growthSource, setGrowthSource] = useState<"unknown" | "estimated" | "metric_history">("unknown")
  const [channelStats, setChannelStats] = useState<{
    video_count: number
    total_views: number
    avg_views_per_video: number
    subscriber_count: number | null
  } | null>(null)

  const cancelChannelLoadRef = useRef<(() => void) | null>(null)
  const workflowRef = useRef<HTMLDivElement>(null)
  const searchSectionRef = useRef<HTMLDivElement>(null)
  const tagSectionRef = useRef<HTMLDivElement>(null)
  const growthChartRef = useRef<HTMLDivElement>(null)
  const guidanceRef = useRef<HTMLDivElement>(null)
  const kpiSectionRef = useRef<HTMLDivElement>(null)

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

  const loadDashboardData = useCallback(async () => {
    try {
      setRefreshing(true)
      const [channelsRes, tagsRes, kpiRes] = await Promise.allSettled([
        channelApi.list({ limit: 50 }),
        tagApi.list(),
        analysisApi.getDashboardKPI(),
      ])

      if (channelsRes.status === "fulfilled" && channelsRes.value?.items) {
        const converted = channelsRes.value.items.map(mapChannelToIntelChannel)
        if (converted.length > 0) setChannels(converted)
      }

      if (tagsRes.status === "fulfilled" && Array.isArray(tagsRes.value)) {
        const convertedTags: TagItem[] = tagsRes.value.map((t: any) => ({
          name: t.name || "未分类",
          count: t.count || 0,
          trend: (t.trend as any) || "stable",
        }))
        if (convertedTags.length > 0) setTags(convertedTags)
      }

      if (kpiRes.status === "fulfilled" && kpiRes.value) {
        const k = kpiRes.value
        const convertedKPI: DashboardKPI = {
          totalChannels: k.total_channels ?? 0,
          totalVideos: k.total_videos ?? 0,
          totalViews: k.total_views ?? 0,
          todayNewVideos: 0,
          monitoringStatus: (k.active_monitors ?? 0) > 0 ? "normal" : "warning",
          avgGrowthRate: 0,
        }
        setKPIs(convertedKPI)
      }

      try {
        const growthRes = await analysisApi.getGrowth({ days: 30 })
        if (growthRes && growthRes.length > 0) {
          setGrowthData(growthRes)
          setGrowthSource(growthRes.some((point) => point.source === "metric_history") ? "metric_history" : "estimated")
        }
      } catch {
      }
    } catch {
      toastError("加载仪表盘数据失败，请刷新重试")
    } finally {
      setRefreshing(false)
      setInitialLoading(false)
    }
  }, [setChannels, setTags, setKPIs, setGrowthData])

  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  useEffect(() => {
    const ctx = gsap.context(() => {
      const reveal = (ref: React.RefObject<HTMLElement>, y = 20, duration = 0.55) => {
        if (!ref.current) return
        gsap.set(ref.current, { y, opacity: 0 })
        gsap.to(ref.current, {
          y: 0,
          opacity: 1,
          duration,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ref.current,
            start: "top 88%",
            toggleActions: "play none none none",
          },
        })
      }

      reveal(kpiSectionRef)
      reveal(guidanceRef)
      reveal(searchSectionRef, 24)
      reveal(growthChartRef, 28, 0.65)

      if (workflowRef.current) {
        const items = workflowRef.current.children
        gsap.set(items, { y: 24, opacity: 0 })
        gsap.to(items, {
          y: 0,
          opacity: 1,
          duration: 0.5,
          ease: "power3.out",
          stagger: 0.08,
          scrollTrigger: {
            trigger: workflowRef.current,
            start: "top 88%",
            toggleActions: "play none none none",
          },
        })
      }

      if (tagSectionRef.current) {
        const badges = tagSectionRef.current.querySelectorAll("[data-tag-badge]")
        gsap.set(badges, { scale: 0.92, opacity: 0 })
        gsap.to(badges, {
          scale: 1,
          opacity: 1,
          duration: 0.4,
          ease: "back.out(1.4)",
          stagger: 0.03,
          scrollTrigger: {
            trigger: tagSectionRef.current,
            start: "top 88%",
            toggleActions: "play none none none",
          },
        })
      }
    })

    return () => ctx.revert()
  }, [tags.length])

  const handleChannelClick = useCallback(async (channel: IntelChannel) => {
    if (cancelChannelLoadRef.current) cancelChannelLoadRef.current()
    let cancelled = false
    cancelChannelLoadRef.current = () => {
      cancelled = true
    }

    setSelectedChannel(channel)
    setDrawerOpen(true)
    setVideosLoading(true)
    setChannelStats(null)

    try {
      const channelIdNum = parseInt(channel.id, 10)
      if (Number.isNaN(channelIdNum)) {
        toastError("频道 ID 格式错误")
        setVideosLoading(false)
        return
      }
      const [videoRes, statsRes] = await Promise.allSettled([
        videoApi.list({ channel_id: channelIdNum, limit: 20 }),
        channelApi.getStats(channelIdNum),
      ])

      if (cancelled) return

      if (videoRes.status === "fulfilled") {
        const items = videoRes.value?.items || []
        setVideos(items.map(mapVideoToVideoItem))
      } else {
        setVideos([])
      }

      if (statsRes.status === "fulfilled" && statsRes.value) {
        setChannelStats(statsRes.value)
      }
    } catch {
      if (!cancelled) {
        toastError("加载频道视频失败，请稍后重试")
        setVideos([])
      }
    } finally {
      if (!cancelled) setVideosLoading(false)
    }
  }, [])

  const displayChannels = filteredChannels()
  const dashboardGuidance = (() => {
    if (initialLoading || !kpis) return { label: "正在诊断", title: "正在读取工作区数据", body: "加载完成后会给出下一步操作。", href: "/settings/integrations", action: "检查集成", variant: "info" as const }
    if (kpis.totalChannels === 0) return { label: "缺少频道", title: "先建立竞品样本池", body: "添加或批量发现频道后，后续分析和内容工厂才有可靠输入。", href: "/radar", action: "添加频道", variant: "warning" as const }
    if (growthSource === "estimated") return { label: "趋势为估算", title: "需要抓取真实历史快照", body: "当前增长曲线来自估算，运行任务中心或开启监控后会沉淀 metric_history。", href: "/crawler", action: "抓取数据", variant: "warning" as const }
    if (kpis.monitoringStatus !== "normal") return { label: "监控未闭环", title: "把重点频道加入雷达", body: "持续监控能把新视频、增长趋势和分析日志串起来。", href: "/radar", action: "配置雷达", variant: "info" as const }
    return { label: "可进入生产", title: "数据已可支撑内容决策", body: "选择高价值频道或视频后，进入内容工厂生成选题、脚本和分镜。", href: "/factory", action: "生成方案", variant: "success" as const }
  })()

  return (
    <div className="mx-auto w-full max-w-7xl min-w-0 space-y-10">
      <section className="grid gap-5 xl:grid-cols-[1.35fr_0.75fr] xl:items-stretch">
        <div className="lux-hero-panel relative flex min-h-[300px] min-w-0 flex-col justify-between overflow-hidden border paper-card bg-background/85 p-6 md:p-8">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.16),transparent_34%),radial-gradient(circle_at_80%_10%,rgba(255,255,255,0.32),transparent_18%),linear-gradient(135deg,rgba(255,255,255,0.42),rgba(255,255,255,0.02))] dark:bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.18),transparent_34%),radial-gradient(circle_at_80%_10%,rgba(255,255,255,0.06),transparent_18%),linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01))]" />
          <div className="relative z-10 space-y-4 min-w-0">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary shrink-0">情报总览</span>
              <span className="text-xs text-muted-foreground min-w-0">监控 · 趋势 · 频道</span>
            </div>
            <h1 className="lux-title-stack break-words">
              <span className="lux-title-en">Creator Intelligence</span>
              <span className="lux-title-cn">情报总览控制台</span>
            </h1>
            <p className="lux-page-copy page-body max-w-lg">实时监控频道动态，洞察内容趋势，把数据流转成可执行的内容决策。</p>
          </div>
          <HeroFooter segment="情报总览" />
        </div>

        <div className="grid grid-cols-2 gap-3 sm:gap-4 min-w-0">
          <div className="lux-metric-tile border paper-card bg-background/80 p-5">
            <p className="page-meta">当前动作</p>
            <p className="lux-stat-value mt-3 text-lg">{dashboardGuidance.action}</p>
            <p className="mt-2 page-body text-xs">{dashboardGuidance.label}</p>
          </div>
          <div className="lux-metric-tile border paper-card bg-muted/20 p-5">
            <p className="page-meta">增长曲线</p>
            <p className="lux-stat-value mt-3 text-lg leading-snug">{growthSource === "metric_history" ? "真实历史" : growthSource === "estimated" ? "估算曲线" : "待生成"}</p>
            <p className="mt-2 page-body text-xs leading-relaxed">趋势来源会影响你对频道状态的判断。</p>
          </div>
          <div className="lux-metric-tile border paper-card bg-muted/15 p-5">
            <p className="page-meta">频道册</p>
            <p className="lux-stat-value mt-3 leading-none">{displayChannels.length}</p>
            <p className="mt-2 page-body text-xs">当前可审阅的频道数量</p>
          </div>
          <div className="lux-metric-tile flex items-end justify-between gap-3 border paper-card bg-background/70 p-5">
            <div>
              <p className="page-meta">刷新</p>
              <p className="lux-stat-value mt-3 text-lg">{refreshing ? "同步中" : "就绪"}</p>
            </div>
            <Button variant="outline" size="sm" onClick={loadDashboardData} disabled={refreshing} className="border-border/60 bg-background/80">
              <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
              {refreshing ? "刷新中" : "刷新数据"}
            </Button>
          </div>
        </div>
      </section>

      <div ref={workflowRef} className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {WORKFLOW_ACTIONS.map((action) => {
          const Icon = action.icon
          return (
            <Link key={action.href} href={action.href} className="lux-workflow-card group flex items-center justify-between border paper-card p-4 paper-hover-lift">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" style={{ backgroundColor: `${action.color}18`, color: action.color }}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <div className="lux-card-title truncate text-sm">{action.label}</div>
                  <div className="truncate text-xs text-muted-foreground">{action.detail}</div>
                </div>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground/70 transition group-hover:translate-x-0.5 group-hover:text-muted-foreground" />
            </Link>
          )
        })}
      </div>

      <div ref={guidanceRef} className="flex min-w-0 flex-col gap-4 border paper-card bg-background/80 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 space-y-1.5">
          <Badge variant={dashboardGuidance.variant} className="text-[10px]">{dashboardGuidance.label}</Badge>
          <h2 className="lux-card-title text-base text-foreground leading-snug">{dashboardGuidance.title}</h2>
          <p className="lux-card-copy max-w-2xl text-xs text-muted-foreground">{dashboardGuidance.body}</p>
        </div>
        <Button size="sm" variant="outline" className="shrink-0 border-primary/15 hover:bg-primary hover:text-primary-foreground w-full sm:w-auto" onClick={() => router.push(dashboardGuidance.href)}>
          {dashboardGuidance.action}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div ref={kpiSectionRef} className="space-y-4">
          <SectionHeading label="关键指标" />
          <KPICards data={kpis} loading={!kpis} />
        </div>

        <div ref={searchSectionRef} className="space-y-4">
          <SectionHeading label="搜索" />
          <SearchBox />
        </div>
      </div>

      <div ref={tagSectionRef} className="space-y-4">
        <SectionHeading label="标签筛选" />
        <div className="flex flex-wrap items-center gap-2 border paper-card bg-muted/15 p-4">
          {tags.map((tag) => (
            <Badge key={tag.name} data-tag-badge variant={selectedTags.includes(tag.name) ? "default" : "outline"} className="cursor-pointer transition-all text-xs border-primary/15 paper-hover-lift" onClick={() => toggleTag(tag.name)}>
              {tag.name}
              <span className="ml-1 opacity-60">{tag.count}</span>
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <SectionHeading label={`频道列表（${displayChannels.length}）`} className="mb-0 w-full" />
        </div>

        <div className="border paper-card bg-background/80 p-5">
          {initialLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: CHANNEL_GRID_BATCH_SIZE }).map((_, index) => (
                <div key={index} className="h-48 rounded-lg border bg-muted/20 paper-card page-corner overflow-hidden">
                  <div className="h-28 bg-muted/40 animate-pulse" />
                  <div className="p-3 space-y-2">
                    <div className="h-3 w-3/4 max-w-[85%] bg-muted/50 animate-pulse rounded" />
                    <div className="flex gap-2">
                      <div className="h-2.5 w-12 bg-muted/40 animate-pulse rounded" />
                      <div className="h-2.5 w-12 bg-muted/40 animate-pulse rounded" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <ChannelGrid channels={displayChannels} onChannelClick={handleChannelClick} />
          )}

          {!initialLoading && displayChannels.length === 0 && (
            <div className="text-center py-16 text-muted-foreground border rounded-lg border-dashed border-border/60 paper-card page-corner">
              <Tv className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p className="page-body text-sm text-foreground">没有找到匹配的频道</p>
              <p className="text-xs mt-2 page-body">尝试调整搜索条件或筛选标签</p>
            </div>
          )}
        </div>
      </div>

      <div ref={growthChartRef}>
        <GrowthChart data={growthData} loading={false} />
      </div>

      <Suspense fallback={null}>
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
      </Suspense>

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
    </div>
  )
}


