"use client"

import { useCallback, useEffect, useState } from "react"
import {
  Loader2,
  RefreshCw,
  TrendingUp,
  Users,
  Video,
  Eye,
  Calendar,
  Search,
  Trophy,
  Zap,
  ArrowLeft,
  ExternalLink,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { crawlerApi } from "@/lib/api"
import { toastError } from "@/lib/toast"
import { useGSAPReveal } from "@/hooks/useGSAPReveal"
import { HeroFooter } from "@/components/HeroFooter"
import { SectionHeading } from "@/components/SectionHeading"

interface DiscoveryChannel {
  id: number
  youtube_id: string
  title: string
  thumbnail_url: string | null
  subscriber_count: number | null
  video_count: number | null
  view_count: number | null
  avg_views_per_video: number | null
  discovery_score: number | null
  discovery_keyword: string | null
  channel_age_months: number | null
  discovered_at: string | null
}

interface DiscoveryStats {
  total_discovered_channels: number
  avg_score: number
  high_potential_count: number
  top_keywords: Array<{ keyword: string; count: number }>
  channels_by_age_range: Record<string, number>
}

function scoreColor(score: number | null): string {
  if (score === null) return "text-muted-foreground/70"
  if (score >= 80) return "text-amber-500"
  if (score >= 60) return "text-orange-500"
  if (score >= 40) return "text-blue-500"
  return "text-muted-foreground/70"
}

function formatNumber(n: number | null): string {
  if (n === null) return "—"
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M"
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K"
  return n.toString()
}

export default function DiscoveryPage() {
  const [channels, setChannels] = useState<DiscoveryChannel[]>([])
  const [stats, setStats] = useState<DiscoveryStats | null>(null)
  const [loading, setLoading] = useState(true)

  const titleRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, ease: "power3.out" })
  const statsRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, stagger: 0.08, delay: 0.1, ease: "power3.out" })
  const filterRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, delay: 0.15, ease: "power3.out" })
  const listRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, stagger: 0.06, delay: 0.2, ease: "power3.out" })
  const [filters, setFilters] = useState({
    keyword: "",
    min_score: "",
    max_age_months: "",
    max_videos: "",
    sort_by: "score" as "score" | "views" | "subscribers" | "recent",
  })

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { sort_by: filters.sort_by, limit: 100 }
      if (filters.keyword) params.keyword = filters.keyword
      if (filters.min_score) params.min_score = Number(filters.min_score)
      if (filters.max_age_months) params.max_age_months = Number(filters.max_age_months)
      if (filters.max_videos) params.max_videos = Number(filters.max_videos)

      const [results, statData] = await Promise.all([
        crawlerApi.discoveryResults(params as any),
        crawlerApi.discoveryStats(),
      ])
      setChannels(results)
      setStats(statData)
    } catch (e: any) {
      toastError("加载发现结果失败: " + (e.message || "未知错误"))
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    loadData()
  }, [loadData])

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div ref={titleRef} className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr] items-stretch">
        <div className="relative overflow-hidden border paper-card page-corner p-6 md:p-8 min-h-[220px] flex flex-col justify-between">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.14),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.42),rgba(255,255,255,0.02))] dark:bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.16),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.05),rgba(255,255,255,0.01))]" />
          <div className="relative z-10 space-y-3">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">频道发现</span>
              <span className="text-xs text-muted-foreground">筛选 · 排名 · 导出</span>
            </div>
            <h1 className="hero-title max-w-xl flex items-center gap-3">
              <Search className="h-6 w-6 md:h-7 md:w-7 text-primary shrink-0" />
              潜力频道发现
            </h1>
            <p className="page-body max-w-lg">自动挖掘建号短、视频少、但已有爆款流量的潜力新号。</p>
          </div>
          <HeroFooter segment="频道发现" />
        </div>

        <div className="flex flex-col justify-between gap-4 p-5 border paper-card page-corner paper-hover-lift depth-hover bg-muted/20">
          <div className="space-y-2">
            <p className="page-meta">返回入口</p>
            <Button variant="ghost" size="sm" asChild className="px-0 w-fit text-muted-foreground"><a href="/crawler"><ArrowLeft className="h-4 w-4 mr-1" />返回任务中心</a></Button>
            <p className="page-body text-sm">从爬虫任务中心进入，筛选并查看潜力频道排行。</p>
          </div>
          <Button variant="outline" onClick={loadData} disabled={loading} className="w-fit">{loading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <RefreshCw className="h-4 w-4 mr-1" />}刷新</Button>
        </div>
      </div>

      {stats && (
        <div ref={statsRef} className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 border paper-card page-corner depth-hover bg-background/80"><div className="flex items-center gap-2 text-xs text-muted-foreground mb-1"><Search className="h-3.5 w-3.5" />总发现频道</div><div className="stat-value text-2xl">{stats.total_discovered_channels}</div></div>
          <div className="p-4 border paper-card page-corner depth-hover bg-background/80"><div className="flex items-center gap-2 text-xs text-muted-foreground mb-1"><TrendingUp className="h-3.5 w-3.5" />平均评分</div><div className="stat-value text-2xl">{stats.avg_score}</div></div>
          <div className="p-4 border paper-card page-corner depth-hover bg-background/80"><div className="flex items-center gap-2 text-xs text-muted-foreground mb-1"><Trophy className="h-3.5 w-3.5" />高潜频道 (≥70)</div><div className="stat-value text-2xl text-primary">{stats.high_potential_count}</div></div>
          <div className="p-4 border paper-card page-corner depth-hover bg-background/80"><div className="flex items-center gap-2 text-xs text-muted-foreground mb-1"><Zap className="h-3.5 w-3.5" />热门关键词</div><div className="flex flex-wrap gap-1 mt-1">{stats.top_keywords.slice(0, 3).map((kw) => (<Badge key={kw.keyword} variant="outline" className="text-[10px] font-sans">{kw.keyword}</Badge>))}</div></div>
        </div>
      )}

      <div ref={filterRef} className="p-4 border paper-card page-corner depth-hover space-y-3 bg-background/80">
        <SectionHeading label="筛选条件" className="mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Input placeholder="关键词" value={filters.keyword} onChange={(e) => setFilters((p) => ({ ...p, keyword: e.target.value }))} className="h-9 text-sm input-glow" />
          <Input placeholder="最小评分" type="number" value={filters.min_score} onChange={(e) => setFilters((p) => ({ ...p, min_score: e.target.value }))} className="h-9 text-sm input-glow" />
          <Input placeholder="最大年龄(月)" type="number" value={filters.max_age_months} onChange={(e) => setFilters((p) => ({ ...p, max_age_months: e.target.value }))} className="h-9 text-sm input-glow" />
          <Input placeholder="最大视频数" type="number" value={filters.max_videos} onChange={(e) => setFilters((p) => ({ ...p, max_videos: e.target.value }))} className="h-9 text-sm input-glow" />
          <select value={filters.sort_by} onChange={(e) => setFilters((p) => ({ ...p, sort_by: e.target.value as any }))} className="h-9 rounded-md border bg-background px-2 text-sm input-glow"><option value="score">按潜力评分</option><option value="views">按总播放量</option><option value="subscribers">按订阅数</option><option value="recent">按发现时间</option></select>
        </div>
      </div>

      <div className="space-y-3">
        <SectionHeading label={`潜力排行榜（${channels.length}）`} className="mb-4" />

        {loading && channels.length === 0 ? (
          <div className="py-12 text-center text-sm text-muted-foreground paper-card page-corner depth-hover bg-background/80"><Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" /><p className="font-sans">加载发现结果...</p></div>
        ) : channels.length === 0 ? (
          <div className="py-12 text-center text-sm text-muted-foreground border paper-card page-corner depth-hover bg-background/80"><Search className="h-8 w-8 mx-auto mb-3 text-muted-foreground/70" /><p className="font-sans font-medium text-foreground">暂无发现结果</p><p className="text-xs mt-1 leading-relaxed">在爬虫任务中心创建一个「频道发现」任务来开始挖掘潜力新号</p><Button className="mt-4" size="sm" asChild><a href="/crawler">去创建任务</a></Button></div>
        ) : (
          <div ref={listRef} className="grid gap-3">
            {channels.map((ch, idx) => (
              <div key={ch.id} className={`p-4 transition-all page-corner paper-hover-lift depth-hover border paper-card bg-background/80`}>
                <div className="flex items-start gap-4">
                  <div className="flex flex-col items-center justify-center w-10 shrink-0"><span className={`text-lg font-semibold font-sans tabular-nums ${scoreColor(ch.discovery_score)}`}>{idx + 1}</span>{idx < 3 && <Trophy className="h-3.5 w-3.5 text-primary/60" />}</div>
                  <div className="w-12 h-12 rounded-full bg-muted overflow-hidden shrink-0 border border-border">{ch.thumbnail_url ? (<img src={ch.thumbnail_url} alt={ch.title} className="w-full h-full object-cover" />) : (<div className="w-full h-full flex items-center justify-center text-xs text-muted-foreground font-sans">{ch.title?.[0] || "?"}</div>)}</div>
                  <div className="flex-1 min-w-0"><div className="flex items-center gap-2 flex-wrap"><h3 className="font-medium text-foreground truncate font-sans">{ch.title}</h3><Badge variant="outline" className={`text-xs font-sans ${scoreColor(ch.discovery_score)}`}>{ch.discovery_score?.toFixed(1) || "—"} 分</Badge>{ch.discovery_keyword && (<Badge variant="default" className="text-[10px] font-sans">{ch.discovery_keyword}</Badge>)}</div><div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-muted-foreground"><span className="flex items-center gap-1 tabular-nums"><Users className="h-3 w-3" />{formatNumber(ch.subscriber_count)} 订阅</span><span className="flex items-center gap-1 tabular-nums"><Video className="h-3 w-3" />{formatNumber(ch.video_count)} 视频</span><span className="flex items-center gap-1 tabular-nums"><Eye className="h-3 w-3" />{formatNumber(ch.avg_views_per_video)} 均播</span><span className="flex items-center gap-1 tabular-nums"><Calendar className="h-3 w-3" />{ch.channel_age_months ? `${ch.channel_age_months} 个月` : "—"}</span></div></div>
                  <div className="shrink-0"><Button size="sm" variant="outline" asChild className="text-xs h-8 btn-ripple"><a href={`https://www.youtube.com/channel/${ch.youtube_id}`} target="_blank" rel="noopener noreferrer"><ExternalLink className="h-3 w-3 mr-1" />查看</a></Button></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
