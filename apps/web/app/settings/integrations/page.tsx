"use client"

import { useEffect, useState } from "react"
import { Activity, KeyRound, RefreshCw, Wifi } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { channelApi, healthApi, type YouTubeDiagnostics } from "@/lib/api"
import { toastError, toastInfo } from "@/lib/toast"
import { useGSAPReveal } from "@/hooks/useGSAPReveal"
import { HeroFooter } from "@/components/HeroFooter"

export default function IntegrationsPage() {
  const [data, setData] = useState<YouTubeDiagnostics | null>(null)
  const [loading, setLoading] = useState(false)
  const [maintenance, setMaintenance] = useState<"backfill" | "repair" | null>(null)
  const [error, setError] = useState<string | null>(null)

  const titleRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, ease: "power3.out" })
  const statusRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, stagger: 0.08, delay: 0.1, ease: "power3.out" })
  const diagRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, delay: 0.2, ease: "power3.out" })

  const refresh = async (live = false) => {
    setLoading(true)
    setError(null)
    try {
      setData(await healthApi.youtubeDiagnostics(live))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh(false)
  }, [])

  const runThumbnailMaintenance = async (kind: "backfill" | "repair") => {
    setMaintenance(kind)
    try {
      const result = kind === "backfill"
        ? await channelApi.backfillThumbnails(100)
        : await channelApi.repairThumbnails(200)
      toastInfo(`头像维护完成，更新 ${result.updated} 个，失败 ${result.failed ?? 0} 个`)
    } catch (err) {
      toastError(err instanceof Error ? err.message : "头像维护失败")
    } finally {
      setMaintenance(null)
    }
  }

  return (
    <div className="space-y-10 max-w-6xl mx-auto">
      <div ref={titleRef} className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr] items-stretch">
        <div className="relative overflow-hidden border paper-card page-corner p-6 md:p-8 min-h-[220px] flex flex-col justify-between">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.14),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.42),rgba(255,255,255,0.02))] dark:bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.16),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.05),rgba(255,255,255,0.01))]" />
          <div className="relative z-10 space-y-3">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">接入诊断</span>
              <span className="text-xs text-muted-foreground">密钥 · 配额 · 连通性</span>
            </div>
            <h1 className="hero-title max-w-xl flex items-center gap-3">
              <KeyRound className="h-6 w-6 md:h-7 md:w-7 text-primary shrink-0" />
              接入诊断
            </h1>
            <p className="page-body max-w-lg">检查 YouTube API Key、后端初始化、配额和实时连接状态。</p>
          </div>
          <HeroFooter segment="接入诊断" />
        </div>

        <div className="flex flex-col justify-between gap-4 p-5 border paper-card page-corner paper-hover-lift depth-hover bg-muted/20">
          <div className="space-y-2">
            <p className="page-meta">运行操作</p>
            <p className="page-body text-sm">快速检查当前接入状态，必要时进行实时探测。</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refresh(false)} disabled={loading}><RefreshCw className="mr-2 h-4 w-4" />刷新</Button>
            <Button onClick={() => refresh(true)} disabled={loading}><Wifi className="mr-2 h-4 w-4" />实时探测</Button>
          </div>
        </div>
      </div>

      {error ? <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</div> : null}

      <div ref={statusRef} className="grid gap-4 md:grid-cols-3">
        <StatusCard icon={KeyRound} label="API Key" value={data?.configured ? `已配置 (${data.key_length} 位)` : "未配置"} ok={Boolean(data?.configured)} />
        <StatusCard icon={Activity} label="后端 extractor" value={data?.extractor_ready ? "已初始化" : "未初始化"} ok={Boolean(data?.extractor_ready)} />
        <StatusCard icon={Wifi} label="实时连接" value={data?.live_check || "skipped"} ok={data?.live_check === "passed"} />
      </div>

      <section ref={diagRef} className="paper-card page-corner paper-hover-lift depth-hover bg-background/80">
        <div className="border-b px-5 py-3 text-sm font-semibold font-sans">诊断结果</div>
        <div className="grid gap-3 p-5 text-sm md:grid-cols-2">
          <Row label="状态" value={data?.status || "loading"} />
          <Row label="下一步" value={data?.next_action || "读取中"} />
          <Row label="已用配额" value={String(data?.quota.units_consumed ?? 0)} />
          <Row label="剩余配额" value={String(data?.quota.units_remaining ?? 0)} />
          <Row label="调用次数" value={String(data?.quota.calls_total ?? 0)} />
          <Row label="错误" value={data?.error || "-"} />
        </div>
      </section>

      <section className="paper-card page-corner paper-hover-lift depth-hover bg-background/80">
        <div className="border-b px-5 py-3 font-serif font-semibold tracking-wide">数据维护</div>
        <div className="grid gap-3 p-5 text-sm md:grid-cols-[1fr_auto_auto] md:items-center">
          <div className="text-muted-foreground leading-relaxed tracking-wide">频道头像缺失时，可以从 YouTube 回填缩略图，修复历史空头像记录。</div>
          <Button variant="outline" onClick={() => runThumbnailMaintenance("backfill")} disabled={maintenance !== null} className="font-serif tracking-wide">{maintenance === "backfill" ? "处理中..." : "回填头像"}</Button>
          <Button onClick={() => runThumbnailMaintenance("repair")} disabled={maintenance !== null} className="font-serif tracking-wide">{maintenance === "repair" ? "处理中..." : "修复头像"}</Button>
        </div>
      </section>
    </div>
  )
}

function StatusCard({ icon: Icon, label, value, ok }: { icon: typeof KeyRound; label: string; value: string; ok: boolean }) {
  return (
    <div className="paper-card page-corner paper-hover-lift depth-hover p-4 bg-background/80">
      <div className="flex items-center justify-between">
        <Icon className="h-5 w-5 text-primary" />
        <Badge variant={ok ? "default" : "outline"} className="font-serif text-[10px] tracking-wider">{ok ? "OK" : "CHECK"}</Badge>
      </div>
      <div className="mt-4 text-sm text-muted-foreground font-serif tracking-wide">{label}</div>
      <div className="mt-1 font-semibold font-serif tracking-wide tabular-nums">{value}</div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-background/50 p-3 paper-hover-lift depth-hover">
      <div className="text-xs text-muted-foreground font-serif tracking-wider">{label}</div>
      <div className="mt-1 break-words font-medium font-serif tracking-wide tabular-nums">{value}</div>
    </div>
  )
}
