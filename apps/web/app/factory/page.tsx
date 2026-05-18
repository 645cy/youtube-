/**
 * 内容工厂页面 - /factory
 * 三 Tab 布局：
 * - Tab 1: 选题生成器（niche 输入 → AI 选题建议）
 * - Tab 2: 脚本编辑器（Hook/痛点/方案/演示/CTA 分段编辑）
 * - Tab 3: 分镜辅助（时间码/画面/素材来源 三列表格）
 */

"use client"

import { useMemo, useState } from "react"
import { ArrowRight, BadgeCheck, Globe2, Layers3, Palette, Sparkles, Star, TrendingUp, Users } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const highlights = [
  {
    title: "品牌感首页",
    desc: "大标题、强对比、视觉冲击，一眼记住你是谁。",
  },
  {
    title: "交互式内容区",
    desc: "卡片切换、数据展示、渐变玻璃质感，适合展示作品和能力。",
  },
  {
    title: "立刻可用",
    desc: "页面已写好，打开就能看，之后你只要改文案即可。",
  },
]

const stats = [
  { label: "体验升级", value: "3x" },
  { label: "转化目标", value: "1" },
  { label: "关键模块", value: "5" },
  { label: "交互亮点", value: "12" },
]

const projects = [
  { name: "产品落地页", tag: "转化", meta: "主视觉 + CTA + 社会证明" },
  { name: "作品集展示", tag: "个人品牌", meta: "项目卡片 + 能力标签 + 联系方式" },
  { name: "活动发布页", tag: "运营", meta: "日程 + 嘉宾 + 报名入口" },
]

export default function FactoryPage() {
  const [activeCard, setActiveCard] = useState(0)

  const activeProject = useMemo(() => projects[activeCard], [activeCard])

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.22),transparent_30%),linear-gradient(135deg,#0f172a_0%,#111827_45%,#030712_100%)] text-white">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between gap-4 rounded-3xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-xl shadow-2xl shadow-black/20">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-fuchsia-500 via-violet-500 to-cyan-400 shadow-lg shadow-fuchsia-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-white/50">Instant Website</p>
              <h1 className="text-lg font-semibold tracking-tight">随便先做一个很能打的首页</h1>
            </div>
          </div>
          <Button className="rounded-full bg-white text-slate-950 hover:bg-white/90">
            立即开始
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </header>

        <section className="grid flex-1 gap-6 py-6 lg:grid-cols-[1.2fr_0.8fr] lg:py-10">
          <div className="flex flex-col justify-between rounded-[2rem] border border-white/10 bg-white/6 p-6 shadow-2xl shadow-black/30 backdrop-blur-2xl sm:p-8 lg:p-10">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-fuchsia-400/30 bg-fuchsia-400/10 px-3 py-1 text-xs font-medium text-fuchsia-200">
                <Star className="h-3.5 w-3.5" />
                现代 · 强视觉 · 互动感
              </div>
              <div className="space-y-4">
                <p className="text-sm uppercase tracking-[0.35em] text-white/45">Your Next Website</p>
                <h2 className="max-w-3xl text-5xl font-black leading-[0.92] tracking-tight sm:text-6xl lg:text-7xl">
                  把网站做成
                  <span className="block bg-gradient-to-r from-cyan-300 via-fuchsia-300 to-yellow-200 bg-clip-text text-transparent">
                    一次漂亮的发布
                  </span>
                </h2>
                <p className="max-w-2xl text-base leading-8 text-white/70 sm:text-lg">
                  这是一个可以直接打开的全新首页：深色科技风、品牌感标题、交互卡片、数据模块、项目展示和清晰 CTA。
                </p>
              </div>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {stats.map((item) => (
                <div key={item.label} className="rounded-2xl border border-white/10 bg-black/20 p-4 backdrop-blur-md">
                  <p className="text-xs uppercase tracking-[0.25em] text-white/45">{item.label}</p>
                  <p className="mt-2 text-2xl font-black text-white">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          <aside className="grid gap-4">
            <div className="rounded-[2rem] border border-white/10 bg-white/8 p-5 backdrop-blur-2xl">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-white/50">互动模块</h3>
                <Palette className="h-4 w-4 text-cyan-300" />
              </div>
              <div className="mt-4 space-y-3">
                {highlights.map((item, index) => (
                  <button
                    key={item.title}
                    onClick={() => setActiveCard(index)}
                    className={cn(
                      "w-full rounded-2xl border p-4 text-left transition-all duration-300",
                      activeCard === index
                        ? "border-cyan-400/50 bg-cyan-400/10 shadow-lg shadow-cyan-500/10"
                        : "border-white/10 bg-white/5 hover:bg-white/10"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10">
                        <BadgeCheck className="h-4 w-4 text-cyan-300" />
                      </div>
                      <div>
                        <p className="font-semibold">{item.title}</p>
                        <p className="mt-1 text-sm leading-6 text-white/60">{item.desc}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded-[2rem] border border-white/10 bg-gradient-to-br from-violet-500/20 via-fuchsia-500/10 to-cyan-500/20 p-5 backdrop-blur-2xl">
              <p className="text-sm uppercase tracking-[0.22em] text-white/50">当前展示</p>
              <h3 className="mt-2 text-2xl font-bold">{activeProject.name}</h3>
              <p className="mt-2 text-sm text-white/70">{activeProject.meta}</p>
              <div className="mt-5 flex flex-wrap gap-2">
                <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/80">{activeProject.tag}</span>
                <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/80">高对比</span>
                <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/80">可扩展</span>
              </div>
            </div>
          </aside>
        </section>

        <section className="grid gap-4 pb-6 lg:grid-cols-3">
          {projects.map((project, index) => (
            <button
              key={project.name}
              onClick={() => setActiveCard(index)}
              className={cn(
                "group rounded-3xl border p-5 text-left transition-all duration-300 backdrop-blur-xl",
                activeCard === index
                  ? "border-fuchsia-400/40 bg-white/12 shadow-2xl shadow-fuchsia-500/10"
                  : "border-white/10 bg-white/6 hover:-translate-y-1 hover:bg-white/10"
              )}
            >
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em] text-white/70">{project.tag}</span>
                <Layers3 className="h-4 w-4 text-white/50 transition-transform group-hover:rotate-12" />
              </div>
              <h3 className="mt-4 text-xl font-bold">{project.name}</h3>
              <p className="mt-2 text-sm leading-7 text-white/65">{project.meta}</p>
            </button>
          ))}
        </section>

        <footer className="grid gap-4 border-t border-white/10 pt-6 pb-2 text-sm text-white/55 lg:grid-cols-[1fr_auto] lg:items-center">
          <p>如果你愿意，我下一步可以继续把这个首页改成“个人主页 / 作品集 / 企业官网 / 产品落地页”中的任意一种。</p>
          <div className="flex flex-wrap gap-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1">
              <Globe2 className="h-4 w-4" />
              即开即用
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1">
              <Users className="h-4 w-4" />
              面向用户
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1">
              <TrendingUp className="h-4 w-4" />
              强转化
            </span>
          </div>
        </footer>
      </div>
    </main>
  )
}
