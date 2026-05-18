"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import gsap from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import { ArrowRight, DatabaseZap, Factory, FlaskConical, Radar } from "lucide-react"
import { cn, formatNumber } from "@/lib/utils"
import { analysisApi, channelApi, crawlerApi, projectApi, type ContentProject } from "@/lib/api"
import { SectionHeading } from "@/components/SectionHeading"
import { HeroFooter } from "@/components/HeroFooter"

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger)
}

const t = {
  title: "工作台",
  subtitle: "在频道发现、数据抓取、内容生产和变现规划之间流转。",
  live: "实时状态",
  risks: "待强化问题",
}

const flow = [
  // CRG: Refresh workflow accents from old book tones to premium SaaS control-room colors.
  { step: "01", title: "找频道", href: "/radar", icon: Radar, goal: "加入竞品频道", result: "形成监控池", color: "#C7A15A" },
  { step: "02", title: "抓数据", href: "/crawler", icon: DatabaseZap, goal: "创建或触发任务", result: "获得频道与视频数据", color: "#5E86B6" },
  { step: "03", title: "做内容", href: "/factory", icon: Factory, goal: "生成选题、脚本、标题", result: "得到可执行方案", color: "#3D9B7A" },
  { step: "04", title: "定变现", href: "/lab", icon: FlaskConical, goal: "匹配变现路径", result: "选择广告、联盟或服务", color: "#A077D2" },
]

const risks = [
  ["项目沉淀", "高", "还需要内容项目模型，保存选题、脚本、分析和变现路径"],
  ["抓取自动化", "中", "任务能手动触发，但调度、重试和结果归档还要加强"],
  ["结果联动", "中", "Factory、Lab、Crawler 的结果还没有联动到同一个工作流"],
]

export default function WorkspacePage() {
  const router = useRouter()
  const [channels, setChannels] = useState<number | null>(null)
  const [tasks, setTasks] = useState<number | null>(null)
  const [videos, setVideos] = useState<number | null>(null)
  const [views, setViews] = useState<number | null>(null)
  const [activeMonitors, setActiveMonitors] = useState<number | null>(null)
  const [recentAnalyses, setRecentAnalyses] = useState<number | null>(null)
  const [viralVideos, setViralVideos] = useState<number | null>(null)
  const [evergreenVideos, setEvergreenVideos] = useState<number | null>(null)
  const [monetizationCoverage, setMonetizationCoverage] = useState<number | null>(null)
  const [projects, setProjects] = useState<ContentProject[]>([])
  const [projectsLoading, setProjectsLoading] = useState(true)

  // Refs for GSAP animations
  const flowRef = useRef<HTMLDivElement>(null)
  const statusGridRef = useRef<HTMLDivElement>(null)
  const recommendationRef = useRef<HTMLDivElement>(null)
  const projectGridRef = useRef<HTMLDivElement>(null)
  const riskListRef = useRef<HTMLDivElement>(null)
  const statusNumberRefs = useRef<(HTMLDivElement | null)[]>([])

  useEffect(() => {
    let cancelled = false

    Promise.allSettled([
      channelApi.list({ limit: 1 }),
      crawlerApi.listTasks(),
      analysisApi.getDashboardKPI(),
      projectApi.list({ status: "active", limit: 5 }),
    ]).then(([channelRes, taskRes, kpiRes, projectRes]) => {
      try {
        if (cancelled) return
        if (channelRes.status === "fulfilled") setChannels(channelRes.value?.total ?? 0)
        if (taskRes.status === "fulfilled") setTasks(taskRes.value?.length ?? 0)
        if (kpiRes.status === "fulfilled") {
          setVideos(kpiRes.value?.total_videos ?? 0)
          setViews(kpiRes.value?.total_views ?? 0)
          setActiveMonitors(kpiRes.value?.active_monitors ?? 0)
          setRecentAnalyses(kpiRes.value?.recent_analyses ?? 0)
          setViralVideos(kpiRes.value?.viral_videos_count ?? 0)
          setEvergreenVideos(kpiRes.value?.evergreen_videos_count ?? 0)
          setMonetizationCoverage(kpiRes.value?.monetization_coverage_pct ?? 0)
        }
        if (projectRes.status === "fulfilled") {
          setProjects(projectRes.value?.items ?? [])
        }
      } catch {
        // load failure handled by finally block
      } finally {
        if (!cancelled) setProjectsLoading(false)
      }
    }).catch(() => {
      if (!cancelled) setProjectsLoading(false)
    })

    return () => {
      cancelled = true
    }
  }, [])

  const status = useMemo(() => [
    ["频道池", channels === null ? "—" : formatNumber(channels), channels ?? 0, "用于竞品分析和内容对标"],
    ["爬虫任务", tasks === null ? "—" : formatNumber(tasks), tasks ?? 0, "用于抓取频道、关键词和统计数据"],
    ["视频数", videos === null ? "—" : formatNumber(videos), videos ?? 0, "分析和选题的基础样本"],
    ["总播放", views === null ? "—" : formatNumber(views), views ?? 0, "用于判断频道量级和机会"],
    ["活跃监控", activeMonitors === null ? "—" : formatNumber(activeMonitors), activeMonitors ?? 0, "持续跟踪重点频道更新"],
    ["近期分析", recentAnalyses === null ? "—" : formatNumber(recentAnalyses), recentAnalyses ?? 0, "记录最近生成的分析结论"],
  ], [channels, tasks, videos, views, activeMonitors, recentAnalyses])

  const recommendation = useMemo(() => {
    if (channels === null || tasks === null || videos === null) return { label: "读取中", title: "正在检查工作区", body: "稍后会根据数据状态给出优先动作。", href: "/settings/integrations", action: "查看集成", tone: "info" as const }
    if (channels === 0) return { label: "先补频道", title: "建立竞品样本池", body: "没有频道时，分析、选题和监控都缺少输入。", href: "/radar", action: "添加频道", tone: "warning" as const }
    if (tasks === 0 || videos === 0) return { label: "补齐数据", title: "抓取视频和指标", body: "已有频道但缺少抓取任务或视频样本，优先沉淀可分析数据。", href: "/crawler", action: "创建任务", tone: "warning" as const }
    return { label: "进入生产", title: "从数据转到内容方案", body: "样本已就绪，下一步应生成选题、脚本、缩略图和发布时间。", href: "/factory", action: "打开工厂", tone: "success" as const }
  }, [channels, tasks, videos])

  const dashboardSignals = useMemo(() => [
    { label: "总频道", value: channels === null ? "—" : formatNumber(channels) },
    { label: "总视频", value: videos === null ? "—" : formatNumber(videos) },
    { label: "总播放", value: views === null ? "—" : formatNumber(views) },
    { label: "任务数", value: tasks === null ? "—" : formatNumber(tasks) },
    { label: "活跃监控", value: activeMonitors === null ? "—" : formatNumber(activeMonitors) },
    { label: "近期分析", value: recentAnalyses === null ? "—" : formatNumber(recentAnalyses) },
    { label: "爆款视频", value: viralVideos === null ? "—" : formatNumber(viralVideos) },
    { label: "长尾视频", value: evergreenVideos === null ? "—" : formatNumber(evergreenVideos) },
  ], [channels, videos, views, tasks, activeMonitors, recentAnalyses, viralVideos, evergreenVideos])

  const statusNotes = useMemo(() => [
    { label: "变现覆盖", value: monetizationCoverage === null ? "—" : `${formatNumber(monetizationCoverage)}%`, hint: "广告、联盟与服务信号" },
    { label: "样本完整度", value: channels !== null && videos !== null && channels > 0 && videos > 0 ? "较高" : "待补齐", hint: "频道池与视频池是否足够" },
    { label: "工作流状态", value: recommendation.action, hint: "下一步建议动作" },
  ], [monetizationCoverage, channels, videos, recommendation.action])

  // GSAP ScrollTrigger animations
  useEffect(() => {
    const ctx = gsap.context(() => {
      // Flow cards stagger reveal
      if (flowRef.current) {
        const cards = flowRef.current.children
        gsap.set(cards, { y: 28, opacity: 0 })
        gsap.to(cards, {
          y: 0,
          opacity: 1,
          duration: 0.55,
          ease: "power3.out",
          stagger: 0.1,
          scrollTrigger: {
            trigger: flowRef.current,
            start: "top 88%",
            toggleActions: "play none none none",
          },
        })
      }

      // Status grid stagger reveal
      if (statusGridRef.current) {
        const items = statusGridRef.current.children
        gsap.set(items, { y: 24, opacity: 0 })
        gsap.to(items, {
          y: 0,
          opacity: 1,
          duration: 0.5,
          ease: "power3.out",
          stagger: 0.1,
          scrollTrigger: {
            trigger: statusGridRef.current,
            start: "top 88%",
            toggleActions: "play none none none",
          },
        })
      }

      // Recommendation card reveal from right
      if (recommendationRef.current) {
        gsap.set(recommendationRef.current, { x: 32, opacity: 0 })
        gsap.to(recommendationRef.current, {
          x: 0,
          opacity: 1,
          duration: 0.6,
          ease: "power3.out",
          scrollTrigger: {
            trigger: recommendationRef.current,
            start: "top 88%",
            toggleActions: "play none none none",
          },
        })
      }

      // Status numbers scroll counter
      statusNumberRefs.current.forEach((el) => {
        if (!el) return
        const targetText = el.dataset.value
        if (!targetText || targetText === "—") return
        const target = parseInt(targetText.replace(/,/g, ""), 10)
        if (Number.isNaN(target)) return

        const obj = { val: 0 }
        gsap.to(obj, {
          val: target,
          duration: 1.2,
          ease: "power2.out",
          scrollTrigger: {
            trigger: el,
            start: "top 88%",
            toggleActions: "play none none none",
          },
          onUpdate: () => {
            el.textContent = Math.round(obj.val).toLocaleString()
          },
        })
      })
    })

    return () => ctx.revert()
  }, [status])

  // Project list stagger animation
  useEffect(() => {
    if (projectsLoading) return
    const ctx = gsap.context(() => {
      if (projectGridRef.current) {
        const items = projectGridRef.current.children
        if (items.length === 0) return
        gsap.set(items, { y: 24, opacity: 0 })
        gsap.to(items, {
          y: 0,
          opacity: 1,
          duration: 0.5,
          ease: "power3.out",
          stagger: 0.08,
          scrollTrigger: {
            trigger: projectGridRef.current,
            start: "top 88%",
            toggleActions: "play none none none",
          },
        })
      }
    })
    return () => ctx.revert()
  }, [projectsLoading, projects.length])

  // Risk list stagger animation
  useEffect(() => {
    const ctx = gsap.context(() => {
      if (riskListRef.current) {
        const items = riskListRef.current.children
        gsap.set(items, { x: -20, opacity: 0 })
        gsap.to(items, {
          x: 0,
          opacity: 1,
          duration: 0.5,
          ease: "power3.out",
          stagger: 0.1,
          scrollTrigger: {
            trigger: riskListRef.current,
            start: "top 88%",
            toggleActions: "play none none none",
          },
        })
      }
    })
    return () => ctx.revert()
  }, [])

  return (
    <div className="mx-auto w-full min-w-0 max-w-[calc(100vw-2rem)] space-y-10 xl:max-w-7xl lux-app-content">
      {/* ═══════════════════════════════════════
          卷首语 —— 杂志封面感
         ═══════════════════════════════════════ */}
      <section className="min-w-0 overflow-hidden pt-2">
        <div className="grid min-w-0 items-stretch gap-5 xl:grid-cols-[1.35fr_0.95fr]">
          <div className="lux-hero-panel relative flex min-h-[280px] min-w-0 flex-col justify-between overflow-hidden border paper-card p-5 sm:p-6 md:p-8">
            {/* CRG: Workspace first screen becomes a control deck, while existing data calls remain untouched. */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.14),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.42),rgba(255,255,255,0.02))] dark:bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.16),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.05),rgba(255,255,255,0.01))]" />
            <div className="relative z-10 space-y-5">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">工作台</span>
                <span className="text-xs text-muted-foreground">{t.live}</span>
              </div>
              <h1 className="lux-title-stack">
                {/* CRG: Split Latin brand and Chinese title so each can use the right luxury type role. */}
                <span className="lux-title-en">TubeFactory</span>
                <span className="lux-title-cn">运营控制台</span>
              </h1>
              <p className="lux-page-copy page-body max-w-[18.5rem] break-words sm:max-w-lg">
                {t.subtitle}
              </p>
            </div>
            <HeroFooter segment="工作台" />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4">
            {dashboardSignals.map((item, idx) => (
              <div
                key={item.label}
                className={cn(
                  "lux-metric-tile relative min-w-0 !overflow-visible border paper-card p-5",
                  // CRG: Metric tiles gain consistent height and premium spacing without changing values.
                  idx % 2 === 0 ? "bg-background/80" : "bg-muted/30"
                )}
              >
                <span className="page-meta">{item.label}</span>
                <div className="lux-stat-value mt-3 break-all text-foreground">
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          四步流程 —— 杂志目录感
         ═══════════════════════════════════════ */}
      <section>
        <SectionHeading label="工作流程" className="mb-5" />
        <div ref={flowRef} className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {flow.map((item) => (
            <Link key={item.href} href={item.href} className="group block">
              <div className="lux-workflow-card relative h-full border paper-card p-5 paper-hover-lift">
                {/* CRG: Workflow cards receive richer material depth while keeping the same route targets. */}
                {/* 角落装饰 */}
                <div className="absolute top-0 left-0 w-3 h-px" style={{ backgroundColor: item.color }} />
                <div className="absolute top-0 left-0 h-3 w-px" style={{ backgroundColor: item.color }} />

                <div className="flex items-start justify-between mb-4">
                  <span
                    className="lux-number text-lg font-semibold leading-none"
                    style={{ color: item.color }}
                  >
                    {item.step}
                  </span>
                  <item.icon className="h-4 w-4 text-muted-foreground/70 group-hover:text-muted-foreground transition-colors" />
                </div>

                <h3 className="lux-card-title mb-1 text-base text-foreground">
                  {item.title}
                </h3>
                <p className="page-body text-xs mb-4">{item.goal}</p>

                <div className="flex items-center gap-1.5 text-xs text-muted-foreground/70 group-hover:text-muted-foreground transition-colors">
                  <span className="page-body text-xs">{item.result}</span>
                  <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════
          状态面板 + 推荐 —— 杂志双栏
         ═══════════════════════════════════════ */}
      <section className="grid gap-8 lg:grid-cols-[1.35fr_0.85fr]">
        <div className="space-y-6">
          <SectionHeading label="数据概览" />
          <div ref={statusGridRef} className="grid grid-cols-2 gap-4">
            {status.map(([label, value, numericValue, desc], idx) => (
              <div
                key={label}
                className="border paper-card p-5 paper-hover-lift lux-card"
              >
                <span className="page-meta">
                  {label}
                </span>
                <div
                  ref={(el) => { statusNumberRefs.current[idx] = el }}
                  data-value={String(numericValue)}
                  className="stat-value mt-2 min-w-0 break-words"
                >
                  {value}
                </div>
                <p className="text-[11px] text-muted-foreground mt-2 leading-relaxed">
                  {desc}
                </p>
              </div>
            ))}
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {statusNotes.map((item, idx) => (
              <div
                key={item.label}
                className={cn(
                  "border paper-card p-4",
                  idx === 0 ? "bg-background/80" : idx === 1 ? "bg-muted/25" : "bg-background/60"
                )}
              >
                <p className="page-meta">{item.label}</p>
                <p className="stat-value mt-2 text-base">{item.value}</p>
                <p className="page-body text-[11px] mt-1">{item.hint}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <SectionHeading label="下一步建议" />
          <div
            ref={recommendationRef}
            className={cn(
              "relative flex min-h-[280px] flex-col justify-between overflow-hidden border paper-card p-6",
              recommendation.tone === "warning" && "border-seal/15",
              recommendation.tone === "success" && "border-emerald-800/15",
              recommendation.tone === "info" && "border-primary/15"
            )}
          >
            <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.16),transparent_50%)]" />
            <div className="space-y-4 relative z-10">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    recommendation.tone === "success" && "bg-emerald-600",
                    recommendation.tone === "warning" && "bg-primary",
                    recommendation.tone === "info" && "bg-gold"
                  )}
                />
                <span className="text-xs font-medium text-muted-foreground">
                  {recommendation.label}
                </span>
              </div>
              <h3 className="text-lg font-semibold font-sans text-foreground leading-snug">
                {recommendation.title}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
                {recommendation.body}
              </p>
            </div>
            <button
              className="group relative z-10 mt-6 flex w-full items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
              onClick={() => router.push(recommendation.href)}
            >
              <span>{recommendation.action}</span>
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </button>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          内容项目 —— 工作流核心
         ═══════════════════════════════════════ */}
      <section>
        <SectionHeading label="进行中项目" className="mb-6">
          <Link
            href="/factory"
            className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            查看全部 <ArrowRight className="h-3 w-3" />
          </Link>
        </SectionHeading>
        {projectsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 border paper-card animate-pulse" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="p-8 border paper-card text-center page-corner bg-muted/20">
            <p className="text-sm text-muted-foreground">暂无进行中项目</p>
            <p className="text-xs text-muted-foreground/70 mt-1">从 Crawler 抓取结果创建，或在 Factory 中新建</p>
          </div>
        ) : (
          <div ref={projectGridRef} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project, idx) => (
              <Link
                key={project.id}
                href={`/factory?project=${project.id}`}
                className={cn(
                  "group block p-5 border paper-card page-corner paper-hover-lift relative overflow-hidden",
                  idx % 3 === 0 ? "bg-background/85" : idx % 3 === 1 ? "bg-muted/25" : "bg-background/70"
                )}
              >
                <div className="absolute top-0 right-0 h-16 w-16 bg-[radial-gradient(circle,rgba(184,151,92,0.12),transparent_70%)]" />
                <div className="flex items-start justify-between gap-2 relative z-10">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={cn(
                          "h-1.5 w-1.5 rounded-full",
                          project.status === "active" && "bg-emerald-500",
                          project.status === "draft" && "bg-primary",
                          project.status === "archived" && "bg-muted-foreground/60"
                        )}
                      />
                      <span className="text-sm font-medium font-sans text-foreground truncate">{project.title}</span>
                    </div>
                    {project.description && (
                      <p className="text-xs text-muted-foreground truncate">{project.description}</p>
                    )}
                    {project.source_task_name && (
                      <p className="text-[10px] text-muted-foreground/70 mt-1">
                        来源: {project.source_task_name}
                      </p>
                    )}
                  </div>
                  <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/70 shrink-0 transition-transform group-hover:translate-x-0.5" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* ═══════════════════════════════════════
          风险与问题 —— 杂志勘误栏
         ═══════════════════════════════════════ */}
      <section>
        <SectionHeading label="已知限制与改进方向" className="mb-6" />
        <div ref={riskListRef} className="space-y-3">
          {risks.map(([name, level, desc], idx) => (
            <div
              key={name}
              className={cn(
                "p-4 border paper-card page-corner flex items-start gap-4 group paper-hover-lift relative overflow-hidden",
                idx % 2 === 0 ? "bg-background/85" : "bg-muted/25"
              )}
            >
              <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-transparent via-primary/30 to-transparent opacity-60" />
              <div className="flex flex-col items-center justify-start shrink-0 pt-1">
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    level === "高" ? "bg-primary" : "bg-gold"
                  )}
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium font-sans text-foreground">{name}</span>
                  <span
                    className={cn(
                      "text-[10px] px-1.5 py-0.5 border font-medium font-sans rounded-sm",
                      level === "高"
                        ? "border-seal/20 text-seal"
                        : "border-primary/20 text-primary"
                    )}
                  >
                    {level}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 页脚空白 */}
      <div className="h-8" />
    </div>
  )
}
