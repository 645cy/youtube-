"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  Loader2,
  Play,
  Plus,
  RefreshCw,
  ShieldAlert,
  Trash2,
  Sparkles,
  ExternalLink,
  BarChart3,
  TrendingUp,
  Target,
  Activity,
  Zap,
  Search,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { crawlerApi, projectApi, type CrawlerTask, type CrawlerTaskRun } from "@/lib/api"
import { APP_DEFAULTS, CRAWLER_FREQUENCIES, CRAWLER_TASK_TYPES } from "@/lib/defaults"
import { toastError, toastInfo } from "@/lib/toast"
import { useGSAPReveal } from "@/hooks/useGSAPReveal"
import { SectionHeading } from "@/components/SectionHeading"
import { HeroFooter } from "@/components/HeroFooter"

function statusTone(status?: string | null) {
  if (status === "success") return "border-emerald-500/30 text-emerald-400"
  if (status === "error") return "border-red-500/30 text-red-400"
  if (status === "running") return "border-primary/30 text-amber-400"
  return "border-muted-foreground/30 text-muted-foreground"
}

function formatTime(value?: string | null) {
  if (!value) return "未运行"
  return new Date(value).toLocaleString("zh-CN", { hour12: false })
}

export default function CrawlerPage() {
  const [tasks, setTasks] = useState<CrawlerTask[]>([])
  const [runs, setRuns] = useState<CrawlerTaskRun[]>([])
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [triggeringId, setTriggeringId] = useState<number | null>(null)
  const [form, setForm] = useState({
    name: "",
    task_type: APP_DEFAULTS.crawlerTaskType,
    target: "",
    frequency: APP_DEFAULTS.crawlerFrequency,
    config: {
      keywords: [] as string[],
      max_results_per_keyword: 25,
      min_avg_views: 100000,
      max_channel_age_months: 6,
      max_video_count: 20,
    },
  })
  const [activeTab, setActiveTab] = useState<"tasks" | "analytics">("tasks")

  const titleRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, ease: "power3.out" })
  const formRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, delay: 0.1, ease: "power3.out" })
  const taskListRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, stagger: 0.08, delay: 0.15, ease: "power3.out" })
  const logsRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, stagger: 0.08, delay: 0.2, ease: "power3.out" })
  const [analytics, setAnalytics] = useState<any>(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const selectedTaskIdRef = useRef(selectedTaskId)
  selectedTaskIdRef.current = selectedTaskId

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) || tasks[0] || null,
    [tasks, selectedTaskId]
  )

  const loadTasks = useCallback(async () => {
    setLoading(true)
    try {
      const data = await crawlerApi.listTasks()
      setTasks(data)
      if (!selectedTaskIdRef.current && data[0]) setSelectedTaskId(data[0].id)
    } catch (e: any) {
      toastError("加载爬虫任务失败: " + (e.message || "未知错误"))
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [])

  const loadRuns = useCallback(async (taskId: number | null) => {
    if (!taskId) {
      setRuns([])
      return
    }
    try {
      setRuns(await crawlerApi.listRuns(taskId))
    } catch (e: any) {
      toastError("加载执行日志失败: " + (e.message || "未知错误"))
      setRuns([])
    }
  }, [])

  const loadAnalytics = useCallback(async () => {
    setAnalyticsLoading(true)
    try {
      const data = await crawlerApi.analytics(14)
      setAnalytics(data)
    } catch (e: any) {
      toastError("加载分析数据失败: " + (e.message || "未知错误"))
    } finally {
      setAnalyticsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  useEffect(() => {
    loadRuns(selectedTask?.id || null)
  }, [selectedTask?.id, loadRuns])

  useEffect(() => {
    if (activeTab === "analytics") {
      loadAnalytics()
    }
  }, [activeTab, loadAnalytics])

  const isDiscovery = form.task_type === "channel_discovery"

  const createTask = async () => {
    if (!form.name.trim()) {
      toastError("请填写任务名称")
      return
    }
    if (isDiscovery) {
      if (form.config.keywords.length === 0 && !form.target.trim()) {
        toastError("请至少输入一个关键词")
        return
      }
    } else {
      if (!form.target.trim()) {
        toastError("请填写任务目标")
        return
      }
    }

    setCreating(true)
    try {
      const payload: Record<string, unknown> = {
        name: form.name,
        task_type: form.task_type,
        target: form.target,
        frequency: form.frequency,
      }
      if (isDiscovery) {
        const keywords = form.config.keywords.length > 0
          ? form.config.keywords
          : form.target.split(",").map((k) => k.trim()).filter(Boolean)
        payload.config = {
          keywords,
          max_results_per_keyword: form.config.max_results_per_keyword,
          min_avg_views: form.config.min_avg_views,
          max_channel_age_months: form.config.max_channel_age_months,
          max_video_count: form.config.max_video_count,
        }
        if (!form.target.trim()) {
          payload.target = keywords.join(", ")
        }
      }

      const task = await crawlerApi.createTask(payload as any)
      setTasks((prev) => [task, ...prev])
      setSelectedTaskId(task.id)
      setForm({
        name: "",
        task_type: APP_DEFAULTS.crawlerTaskType,
        target: "",
        frequency: APP_DEFAULTS.crawlerFrequency,
        config: {
          keywords: [],
          max_results_per_keyword: 25,
          min_avg_views: 100000,
          max_channel_age_months: 6,
          max_video_count: 20,
        },
      })
      toastInfo("爬虫任务已创建")
    } catch (e: any) {
      toastError("创建任务失败: " + (e.message || "未知错误"))
    } finally {
      setCreating(false)
    }
  }

  const triggerTask = async (task: CrawlerTask) => {
    setTriggeringId(task.id)
    try {
      const run = await crawlerApi.triggerTask(task.id)
      toastInfo("任务已加入队列，后台执行中...")
      // 轮询状态
      const poll = setInterval(async () => {
        try {
          const latestRuns = await crawlerApi.listRuns(task.id)
          const latest = latestRuns.find((r) => r.id === run.id)
          if (latest && latest.status !== "running") {
            clearInterval(poll)
            setRuns(latestRuns)
            await loadTasks()
            if (latest.status === "success") {
              toastInfo(`任务执行完成，发现 ${latest.items_found} 条结果`)
              if (latest.items_found > 0) {
                const createProject = confirm(
                  `任务「${task.name}」发现 ${latest.items_found} 条结果。\n是否基于此创建内容项目？`
                )
                if (createProject) {
                  try {
                    await projectApi.create({
                      title: `${task.name} — ${new Date().toLocaleDateString("zh-CN")}`,
                      description: `从爬虫任务「${task.name}」创建，发现 ${latest.items_found} 条结果`,
                      source_crawler_task_id: task.id,
                      source_run_id: latest.id,
                    })
                    toastInfo("内容项目已创建，可在工作台查看")
                  } catch (e: any) {
                    toastError("创建项目失败: " + (e.message || "未知错误"))
                  }
                }
              }
            } else {
              toastError("任务执行失败: " + (latest.message || "未知错误"))
            }
          }
        } catch {
          // 忽略轮询错误
        }
      }, 2000)

      // 30秒后停止轮询（兜底）
      setTimeout(() => clearInterval(poll), 300000)

      // 立即刷新一次
      await loadTasks()
      setRuns((prev) => [run, ...prev])
    } catch (e: any) {
      toastError("触发任务失败: " + (e.message || "未知错误"))
    } finally {
      setTriggeringId(null)
    }
  }

  const deleteTask = async (task: CrawlerTask) => {
    try {
      await crawlerApi.deleteTask(task.id)
      setTasks((prev) => prev.filter((item) => item.id !== task.id))
      if (selectedTaskId === task.id) setSelectedTaskId(null)
      toastInfo("任务已删除")
    } catch (e: any) {
      toastError("删除任务失败: " + (e.message || "未知错误"))
    }
  }

  const addKeyword = (kw: string) => {
    const trimmed = kw.trim()
    if (!trimmed) return
    if (form.config.keywords.includes(trimmed)) return
    setForm((prev) => ({
      ...prev,
      config: { ...prev.config, keywords: [...prev.config.keywords, trimmed] },
    }))
  }

  const removeKeyword = (kw: string) => {
    setForm((prev) => ({
      ...prev,
      config: { ...prev.config, keywords: prev.config.keywords.filter((k) => k !== kw) },
    }))
  }

  return (
    <div className="space-y-10 max-w-6xl mx-auto">
      <div ref={titleRef} className="pt-2 pb-2">
        <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr] items-stretch">
          <div className="relative overflow-hidden border paper-card page-corner p-6 md:p-8 min-h-[220px] flex flex-col justify-between">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.14),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.42),rgba(255,255,255,0.02))] dark:bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.16),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.05),rgba(255,255,255,0.01))]" />
            <div className="relative z-10 space-y-3">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">爬虫任务</span>
                <span className="text-xs text-muted-foreground">创建 · 执行 · 日志 · 分析</span>
              </div>
              <h1 className="hero-title max-w-xl flex items-center gap-3">
                <Loader2 className="h-7 w-7 md:h-8 md:w-8 text-primary shrink-0" />
                爬虫任务中心
              </h1>
              <p className="page-body mt-2 max-w-lg">
                统一管理抓取任务、触发执行并查看运行日志与趋势分析。
              </p>
            </div>
            <HeroFooter segment="爬虫任务" />
          </div>

          <div className="grid gap-4">
            <div className="p-5 border paper-card page-corner bg-background/80 flex items-center justify-between gap-3">
              <div>
                <p className="page-meta">发现结果</p>
                <p className="stat-value mt-2 text-lg">跳转到结果页</p>
              </div>
              <Button variant="outline" asChild className="border-primary/15 hover:bg-primary hover:text-primary-foreground">
                <a href="/discovery">
                  <Sparkles className="h-4 w-4 mr-1" />
                  进入
                </a>
              </Button>
            </div>
            <div className="p-5 border paper-card page-corner bg-muted/20">
              <p className="page-meta">执行状态</p>
              <p className="stat-value mt-2 text-lg leading-none">{selectedTask ? selectedTask.status : "未选择"}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1 mt-4">
          <button type="button" onClick={() => setActiveTab("tasks")} className={`px-4 py-1.5 text-sm rounded-md transition-colors font-sans tracking-wide ${activeTab === "tasks" ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-primary"}`}>
            任务中心
          </button>
          <button type="button" onClick={() => setActiveTab("analytics")} className={`px-4 py-1.5 text-sm rounded-md transition-colors font-sans tracking-wide ${activeTab === "analytics" ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-primary"}`}>
            智能分析
          </button>
        </div>
      </div>

      {activeTab === "analytics" ? (
        <AnalyticsPanel analytics={analytics} loading={analyticsLoading} onRefresh={loadAnalytics} />
      ) : (
      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-4">
          <SectionHeading label="新建任务" />
          <div ref={formRef} className="p-5 paper-card page-corner paper-hover-lift depth-hover space-y-4 bg-background/80">
            <Input
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="任务名称，例如：AI 工具潜力号挖掘"
              className="input-glow font-serif tracking-wide"
            />
            <select
              value={form.task_type}
              onChange={(e) => setForm((prev) => ({ ...prev, task_type: e.target.value }))}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm input-glow font-serif tracking-wide"
            >
              {CRAWLER_TASK_TYPES.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>

            {/* Discovery 专属配置 */}
            {isDiscovery && (
              <div className="space-y-3 border-t border-dashed border-primary/15 pt-3">
                <div className="text-xs text-muted-foreground font-medium font-serif tracking-wider">关键词列表</div>
                <div className="flex flex-wrap gap-1.5">
                  {form.config.keywords.map((kw) => (
                    <Badge key={kw} variant="default" className="cursor-pointer hover:bg-red-100 font-serif text-[10px] tracking-wider" onClick={() => removeKeyword(kw)}>
                      {kw} ×
                    </Badge>
                  ))}
                </div>
                <Input
                  placeholder="输入关键词后回车添加"
                  className="input-glow font-serif tracking-wide"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault()
                      addKeyword((e.target as HTMLInputElement).value)
                      ;(e.target as HTMLInputElement).value = ""
                    }
                  }}
                />
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-muted-foreground font-serif tracking-wider">每词视频数</label>
                    <select
                      value={form.config.max_results_per_keyword}
                      onChange={(e) => setForm((prev) => ({
                        ...prev,
                        config: { ...prev.config, max_results_per_keyword: Number(e.target.value) },
                      }))}
                      className="h-8 w-full rounded border bg-background px-2 text-xs input-glow font-serif tracking-wide"
                    >
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-muted-foreground font-serif tracking-wider">最小平均播放</label>
                    <Input
                      type="number"
                      value={form.config.min_avg_views}
                      onChange={(e) => setForm((prev) => ({
                        ...prev,
                        config: { ...prev.config, min_avg_views: Number(e.target.value) },
                      }))}
                      className="h-8 text-xs input-glow font-serif tracking-wide"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-muted-foreground font-serif tracking-wider">最大频道年龄(月)</label>
                    <Input
                      type="number"
                      value={form.config.max_channel_age_months}
                      onChange={(e) => setForm((prev) => ({
                        ...prev,
                        config: { ...prev.config, max_channel_age_months: Number(e.target.value) },
                      }))}
                      className="h-8 text-xs input-glow font-serif tracking-wide"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-muted-foreground font-serif tracking-wider">最大视频数</label>
                    <Input
                      type="number"
                      value={form.config.max_video_count}
                      onChange={(e) => setForm((prev) => ({
                        ...prev,
                        config: { ...prev.config, max_video_count: Number(e.target.value) },
                      }))}
                      className="h-8 text-xs input-glow"
                    />
                  </div>
                </div>
              </div>
            )}

            {!isDiscovery && (
              <Input
                value={form.target}
                maxLength={200}
                onChange={(e) => setForm((prev) => ({ ...prev, target: e.target.value }))}
                placeholder={isDiscovery ? "目标描述（可选）" : "目标：频道ID、本地频道名或关键词"}
                className="input-glow font-serif tracking-wide"
              />
            )}

            <select
              value={form.frequency}
              onChange={(e) => setForm((prev) => ({ ...prev, frequency: e.target.value }))}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm input-glow font-serif tracking-wide"
            >
              {CRAWLER_FREQUENCIES.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
            <Button className="w-full font-serif tracking-wide" onClick={createTask} disabled={creating}>
              {creating ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
              创建任务
            </Button>
            <div className="p-3 border border-primary/15 bg-primary/[0.03] text-xs text-muted-foreground rounded-md tracking-wide leading-relaxed">
              <ShieldAlert className="h-4 w-4 text-primary/60 mb-2" />
              频道发现任务会在后台异步执行，执行完成后自动更新发现结果页面。
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <SectionHeading label="任务列表" />
          <div className="paper-card page-corner paper-hover-lift depth-hover p-4 bg-background/80">
              {loading ? (
                <div className="py-8 text-center text-sm text-muted-foreground font-serif tracking-wide">正在加载任务...</div>
              ) : tasks.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground font-serif tracking-wide">暂无任务，先从左侧创建一个。</div>
              ) : (
                <div ref={taskListRef} className="space-y-2">
                  {tasks.map((task) => (
                    <div key={task.id} className={`rounded-lg border p-3 transition-colors cursor-pointer paper-card page-corner paper-hover-lift depth-hover ${selectedTask?.id === task.id ? "bg-primary/5 border-primary/30" : ""}`} onClick={() => setSelectedTaskId(task.id)}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <div className="font-medium truncate font-serif tracking-wide">{task.name}</div>
                            <Badge variant="outline" className="font-serif text-[10px] tracking-wider">{CRAWLER_TASK_TYPES.find((t) => t.value === task.task_type)?.label || task.task_type}</Badge>
                            <Badge variant="outline" className={`font-serif text-[10px] tracking-wider ${statusTone(task.latest_run_status)}`}>
                              {task.latest_run_status || "未运行"}
                            </Badge>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1 truncate tracking-wide">目标: {task.target} · 最近运行: {formatTime(task.last_run_at)}</div>
                          {task.latest_run_message && <div className="text-xs text-muted-foreground mt-1 truncate tracking-wide">{task.latest_run_message}</div>}
                        </div>
                        <div className="flex items-center gap-2">
                          <Button size="sm" onClick={(e) => { e.stopPropagation(); triggerTask(task) }} disabled={triggeringId === task.id} className="font-serif tracking-wide">
                            {triggeringId === task.id ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Play className="h-4 w-4 mr-1" />}
                            执行
                          </Button>
                          <Button size="icon-sm" variant="ghost" onClick={(e) => { e.stopPropagation(); deleteTask(task) }} title="删除任务">
                            <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-red-400" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          <SectionHeading label="执行日志" />
          <div className="paper-card page-corner paper-hover-lift depth-hover p-5 bg-background/80">
              {!selectedTask ? (
                <div className="py-6 text-center text-sm text-muted-foreground font-serif tracking-wide">请选择任务。</div>
              ) : runs.length === 0 ? (
                <div className="py-6 text-center text-sm text-muted-foreground font-serif tracking-wide">该任务还没有执行记录。</div>
              ) : (
                <div ref={logsRef} className="space-y-2">
                  {runs.map((run) => (
                    <div key={run.id} className="rounded-lg border bg-muted/20 p-3 paper-card page-corner paper-hover-lift depth-hover">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className={`font-serif text-[10px] tracking-wider ${statusTone(run.status)}`}>{run.status}</Badge>
                          <span className="text-xs text-muted-foreground tracking-wide">{run.source_status || "unknown"}</span>
                        </div>
                        <span className="text-xs text-muted-foreground tracking-wide">{formatTime(run.started_at)}</span>
                      </div>
                      {run.status === "running" && <div className="flex items-center gap-2 mt-2"><span className="relative flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/80 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span></span><span className="text-xs text-primary font-serif tracking-wide">执行中...</span></div>}
                      <div className="text-sm mt-2 tracking-wide">{run.message || "无消息"}</div>
                      <div className="text-xs text-muted-foreground mt-1 tracking-wide">结果数量: {run.items_found}</div>
                      {run.status === "success" && run.result_json && (
                        <div className="mt-2">
                          <Button size="sm" variant="outline" asChild className="text-xs h-7 font-serif tracking-wide">
                            <a href={`/discovery?task=${run.task_id}`}>
                              <ExternalLink className="h-3 w-3 mr-1" />
                              查看发现结果
                            </a>
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
          </div>
        </div>
      </div>
      )}
    </div>
  )
}

// =============================================================================
// AnalyticsPanel 组件
// =============================================================================

function AnalyticsPanel({
  analytics,
  loading,
  onRefresh,
}: {
  analytics: any
  loading: boolean
  onRefresh: () => void
}) {
  const kpiRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, stagger: 0.06, ease: "power3.out" })
  const trendRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, delay: 0.15, ease: "power3.out" })
  const bottomRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, delay: 0.2, ease: "power3.out" })
  if (loading) {
    return (
      <div className="py-20 text-center text-sm text-muted-foreground font-serif tracking-wide">
        <Loader2 className="h-6 w-6 animate-spin mx-auto mb-3 text-primary" />
        正在加载分析数据...
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="py-20 text-center text-sm text-muted-foreground font-serif tracking-wide">
        暂无分析数据
      </div>
    )
  }

  const maxRunCount = Math.max(
    1,
    ...analytics.run_trend.map((d: any) => d.success + d.error)
  )
  const maxDiscCount = Math.max(1, ...analytics.discovery_trend.map((d: any) => d.count))
  const totalScore = Object.values(analytics.score_distribution as Record<string, number>).reduce(
    (a, b) => a + b, 0
  )

  return (
    <div className="space-y-8">
      {/* 刷新按钮 */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">近 {analytics.days} 天数据概览</span>
        <Button variant="outline" size="sm" onClick={onRefresh} className="border-primary/15 hover:bg-primary hover:text-primary-foreground text-xs">
          <RefreshCw className="h-3 w-3 mr-1" />
          刷新
        </Button>
      </div>

      {/* KPI 卡片 */}
      <div ref={kpiRef} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={<Target className="h-5 w-5 text-primary" />} label="任务总数" value={analytics.task_count} />
        <KpiCard
          icon={<Activity className="h-5 w-5 text-emerald-400" />}
          label="成功率"
          value={`${Math.round(analytics.success_rate * 100)}%`}
          sub={`${analytics.success_runs}/${analytics.total_runs} 次成功`}
        />
        <KpiCard icon={<Search className="h-5 w-5 text-sky-400" />} label="总发现数" value={analytics.total_discovered} />
        <KpiCard
          icon={<Zap className="h-5 w-5 text-amber-400" />}
          label="高潜频道"
          value={analytics.high_potential_count}
          sub={`均分 ${analytics.avg_score}`}
        />
      </div>

      {/* 趋势图 */}
      <div ref={trendRef} className="grid gap-6 lg:grid-cols-2">
        {/* 运行趋势 */}
        <div className="paper-card page-corner paper-hover-lift depth-hover p-5 space-y-4">
          <SectionHeading label="运行趋势" icon={BarChart3} className="mb-4" />
          {analytics.run_trend.length === 0 ? (
            <div className="text-xs text-muted-foreground py-4 font-serif tracking-wide">暂无运行记录</div>
          ) : (
            <div className="space-y-2">
              {analytics.run_trend.map((d: any) => (
                <div key={d.date} className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted-foreground tracking-wide">
                    <span>{d.date.slice(5)}</span>
                    <span className="text-emerald-400 tabular-nums">{d.success}</span>
                    <span className="text-red-400 tabular-nums">{d.error}</span>
                  </div>
                  <div className="flex h-2 rounded-full overflow-hidden bg-muted/30">
                    <div
                      className="bg-emerald-500/60"
                      style={{ width: `${((d.success / maxRunCount) * 100).toFixed(1)}%` }}
                    />
                    <div
                      className="bg-red-500/60"
                      style={{ width: `${((d.error / maxRunCount) * 100).toFixed(1)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 发现趋势 */}
        <div className="paper-card page-corner paper-hover-lift depth-hover p-5 space-y-4">
          <SectionHeading label="发现趋势" icon={TrendingUp} className="mb-4" />
          {analytics.discovery_trend.length === 0 ? (
            <div className="text-xs text-muted-foreground py-4 font-serif tracking-wide">暂无发现记录</div>
          ) : (
            <div className="space-y-2">
              {analytics.discovery_trend.map((d: any) => (
                <div key={d.date} className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted-foreground tracking-wide">
                    <span>{d.date.slice(5)}</span>
                    <span className="text-primary tabular-nums">{d.count} 个</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted/30 overflow-hidden">
                    <div
                      className="h-full bg-primary/60 rounded-full transition-all"
                      style={{ width: `${((d.count / maxDiscCount) * 100).toFixed(1)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 评分分布 + 关键词 */}
      <div ref={bottomRef} className="grid gap-6 lg:grid-cols-2">
        <div className="paper-card page-corner paper-hover-lift depth-hover p-5 space-y-4">
          <SectionHeading label="评分分布" icon={BarChart3} className="mb-4" />
          {totalScore === 0 ? (
            <div className="text-xs text-muted-foreground py-4 font-serif tracking-wide">暂无评分数据</div>
          ) : (
            <div className="space-y-2">
              {Object.entries(analytics.score_distribution as Record<string, number>).map(([range, count]) => (
                <div key={range} className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted-foreground tracking-wide">
                    <span>{range} 分</span>
                    <span className="tabular-nums">{count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted/30 overflow-hidden">
                    <div
                      className="h-full bg-primary/50 rounded-full transition-all"
                      style={{ width: `${((count / totalScore) * 100).toFixed(1)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="paper-card page-corner paper-hover-lift depth-hover p-5 space-y-4">
          <SectionHeading label="Top 关键词" icon={Search} className="mb-4" />
          {analytics.top_keywords.length === 0 ? (
            <div className="text-xs text-muted-foreground py-4 font-serif tracking-wide">暂无关键词数据</div>
          ) : (
            <div className="space-y-2">
              {analytics.top_keywords.map((kw: any, idx: number) => (
                <div key={kw.keyword} className="flex items-center justify-between py-1.5 border-b border-primary/5 last:border-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground w-4 tabular-nums">{idx + 1}</span>
                    <span className="text-sm font-serif tracking-wide">{kw.keyword}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground tracking-wide">
                    <span className="tabular-nums">{kw.count} 个</span>
                    <span className="text-primary tabular-nums">均分 {kw.avg_score}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function KpiCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
}) {
  return (
    <div className="paper-card page-corner paper-hover-lift depth-hover p-4 space-y-2">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-xs text-muted-foreground font-serif tracking-wider">{label}</span>
      </div>
      <div className="text-2xl font-serif font-semibold tracking-tight tabular-nums">{value}</div>
      {sub && <div className="text-[10px] text-muted-foreground font-serif tracking-wider">{sub}</div>}
    </div>
  )
}
