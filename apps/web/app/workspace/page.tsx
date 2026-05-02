"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { ArrowRight, Compass, DatabaseZap, Factory, FlaskConical, Radar } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { analysisApi, channelApi, crawlerApi } from "@/lib/api"

const t = {
  title: "\u5de5\u4f5c\u53f0",
  subtitle: "\u628a\u7ade\u54c1\u53d1\u73b0\u3001\u6570\u636e\u6293\u53d6\u3001\u5185\u5bb9\u751f\u4ea7\u548c\u53d8\u73b0\u5224\u65ad\u653e\u5230\u4e00\u6761\u4e3b\u6d41\u7a0b\u91cc\u3002",
  live: "\u5b9e\u65f6\u72b6\u6001",
  risks: "\u5f85\u5f3a\u5316\u95ee\u9898",
}

const flow = [
  { step: "1", title: "\u627e\u9891\u9053", href: "/radar", icon: Radar, goal: "\u52a0\u5165\u7ade\u54c1\u9891\u9053", result: "\u5f62\u6210\u76d1\u63a7\u6c60" },
  { step: "2", title: "\u6293\u6570\u636e", href: "/crawler", icon: DatabaseZap, goal: "\u521b\u5efa\u6216\u89e6\u53d1\u4efb\u52a1", result: "\u83b7\u5f97\u9891\u9053\u4e0e\u89c6\u9891\u6570\u636e" },
  { step: "3", title: "\u505a\u5185\u5bb9", href: "/factory", icon: Factory, goal: "\u751f\u6210\u9009\u9898\u3001\u811a\u672c\u3001\u6807\u9898", result: "\u5f97\u5230\u53ef\u6267\u884c\u65b9\u6848" },
  { step: "4", title: "\u5b9a\u53d8\u73b0", href: "/lab", icon: FlaskConical, goal: "\u5339\u914d\u53d8\u73b0\u8def\u5f84", result: "\u9009\u62e9\u5e7f\u544a\u3001\u8054\u76df\u6216\u670d\u52a1" },
]

const risks = [
  ["\u9879\u76ee\u6c89\u6dc0", "\u9ad8", "\u8fd8\u9700\u8981\u5185\u5bb9\u9879\u76ee\u6a21\u578b\uff0c\u4fdd\u5b58\u9009\u9898\u3001\u811a\u672c\u3001\u5206\u6790\u548c\u53d8\u73b0\u8def\u5f84"],
  ["\u6293\u53d6\u81ea\u52a8\u5316", "\u4e2d", "\u4efb\u52a1\u80fd\u624b\u52a8\u89e6\u53d1\uff0c\u4f46\u8c03\u5ea6\u3001\u91cd\u8bd5\u548c\u7ed3\u679c\u5f52\u6863\u8fd8\u8981\u52a0\u5f3a"],
  ["\u7ed3\u679c\u8054\u52a8", "\u4e2d", "Factory\u3001Lab\u3001Crawler\u7684\u7ed3\u679c\u8fd8\u6ca1\u6709\u8054\u52a8\u5230\u540c\u4e00\u4e2a\u5de5\u4f5c\u6d41"],
]

export default function WorkspacePage() {
  const [channels, setChannels] = useState<number | null>(null)
  const [tasks, setTasks] = useState<number | null>(null)
  const [videos, setVideos] = useState<number | null>(null)
  const [views, setViews] = useState<number | null>(null)

  useEffect(() => {
    Promise.allSettled([
      channelApi.list({ limit: 1 }),
      crawlerApi.listTasks(),
      analysisApi.getDashboardKPI(),
    ]).then(([channelRes, taskRes, kpiRes]) => {
      if (channelRes.status === "fulfilled") setChannels(channelRes.value.total)
      if (taskRes.status === "fulfilled") setTasks(taskRes.value.length)
      if (kpiRes.status === "fulfilled") {
        setVideos(kpiRes.value.total_videos)
        setViews(kpiRes.value.total_views)
      }
    })
  }, [])

  const status = useMemo(() => [
    ["\u9891\u9053\u6c60", channels === null ? "\u8bfb\u53d6\u4e2d" : `${channels}`, "\u7528\u4e8e\u7ade\u54c1\u5206\u6790\u548c\u5185\u5bb9\u5bf9\u6807"],
    ["\u722c\u866b\u4efb\u52a1", tasks === null ? "\u8bfb\u53d6\u4e2d" : `${tasks}`, "\u7528\u4e8e\u6293\u53d6\u9891\u9053\u3001\u5173\u952e\u8bcd\u548c\u7edf\u8ba1\u6570\u636e"],
    ["\u89c6\u9891\u6570", videos === null ? "\u8bfb\u53d6\u4e2d" : `${videos}`, "\u5206\u6790\u548c\u9009\u9898\u7684\u57fa\u7840\u6837\u672c"],
    ["\u603b\u64ad\u653e", views === null ? "\u8bfb\u53d6\u4e2d" : `${views}`, "\u7528\u4e8e\u5224\u65ad\u9891\u9053\u91cf\u7ea7\u548c\u673a\u4f1a"],
  ], [channels, tasks, videos, views])

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold"><Compass className="h-6 w-6 text-primary" />TubeFactory {t.title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t.subtitle}</p>
        </div>
        <Badge variant="outline">Live</Badge>
      </div>
      <div className="grid gap-3 md:grid-cols-4">{flow.map((item) => <FlowCard key={item.href} item={item} />)}</div>
      <ReportTable title={t.live} columns={["\u6307\u6807", "\u5f53\u524d", "\u7528\u9014"]} rows={status} />
      <ReportTable title={t.risks} columns={["\u95ee\u9898", "\u7b49\u7ea7", "\u5904\u7406\u65b9\u5411"]} rows={risks} />
    </div>
  )
}

function FlowCard({ item }: { item: (typeof flow)[number] }) {
  const Icon = item.icon
  return <Link href={item.href} className="group rounded-lg border bg-card p-4 transition hover:border-primary/50 hover:bg-accent"><div className="mb-3 flex items-center justify-between"><Icon className="h-5 w-5 text-primary" /><ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary" /></div><div className="text-xs text-muted-foreground">Step {item.step}</div><div className="mt-1 font-semibold">{item.title}</div><div className="mt-2 text-xs text-muted-foreground">{item.goal}</div><div className="mt-3 text-xs">{item.result}</div></Link>
}

function ReportTable({ title, columns, rows }: { title: string; columns: string[]; rows: string[][] }) {
  return <section className="rounded-lg border bg-card"><div className="border-b px-4 py-3 font-semibold">{title}</div><div className="overflow-x-auto"><table className="w-full text-sm"><thead className="bg-muted/40 text-left"><tr>{columns.map((c) => <th key={c} className="px-4 py-2 font-medium">{c}</th>)}</tr></thead><tbody>{rows.map((r) => <tr key={r.join("-")} className="border-t">{r.map((c, i) => <td key={i} className="px-4 py-2">{i === 1 ? <Badge variant="outline">{c}</Badge> : c}</td>)}</tr>)}</tbody></table></div></section>
}
