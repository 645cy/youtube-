"use client"

import { useEffect, useState } from "react"
import { Activity, KeyRound, RefreshCw, Wifi } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

type Diagnostics = {
  configured: boolean
  key_length: number
  extractor_ready: boolean
  quota: { units_consumed?: number; units_remaining?: number; usage_pct?: number; calls_total?: number }
  live_check: string
  status: string
  next_action: string
  error?: string
}

async function loadDiagnostics(live = false): Promise<Diagnostics> {
  const response = await fetch(`/api/v1/integrations/youtube/diagnostics?live_check=${live ? "true" : "false"}`, { cache: "no-store" })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export default function IntegrationsPage() {
  const [data, setData] = useState<Diagnostics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = async (live = false) => {
    setLoading(true)
    setError(null)
    try {
      setData(await loadDiagnostics(live))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh(false)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">接入诊断</h1>
          <p className="mt-1 text-sm text-muted-foreground">检查 YouTube API Key、后端初始化、配额和实时连接状态。</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refresh(false)} disabled={loading}><RefreshCw className="mr-2 h-4 w-4" />刷新</Button>
          <Button onClick={() => refresh(true)} disabled={loading}><Wifi className="mr-2 h-4 w-4" />实时探测</Button>
        </div>
      </div>
      {error ? <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">{error}</div> : null}
      <div className="grid gap-3 md:grid-cols-3">
        <StatusCard icon={KeyRound} label="API Key" value={data?.configured ? `已配置 (${data.key_length} 位)` : "未配置"} ok={Boolean(data?.configured)} />
        <StatusCard icon={Activity} label="后端 extractor" value={data?.extractor_ready ? "已初始化" : "未初始化"} ok={Boolean(data?.extractor_ready)} />
        <StatusCard icon={Wifi} label="实时连接" value={data?.live_check || "skipped"} ok={data?.live_check === "passed"} />
      </div>
      <section className="rounded-lg border bg-card">
        <div className="border-b px-4 py-3 font-semibold">诊断结果</div>
        <div className="grid gap-3 p-4 text-sm md:grid-cols-2">
          <Row label="状态" value={data?.status || "loading"} />
          <Row label="下一步" value={data?.next_action || "读取中"} />
          <Row label="已用配额" value={String(data?.quota.units_consumed ?? 0)} />
          <Row label="剩余配额" value={String(data?.quota.units_remaining ?? 0)} />
          <Row label="调用次数" value={String(data?.quota.calls_total ?? 0)} />
          <Row label="错误" value={data?.error || "-"} />
        </div>
      </section>
    </div>
  )
}

function StatusCard({ icon: Icon, label, value, ok }: { icon: typeof KeyRound; label: string; value: string; ok: boolean }) {
  return <div className="rounded-lg border bg-card p-4"><div className="flex items-center justify-between"><Icon className="h-5 w-5 text-primary" /><Badge variant={ok ? "default" : "outline"}>{ok ? "OK" : "CHECK"}</Badge></div><div className="mt-4 text-sm text-muted-foreground">{label}</div><div className="mt-1 font-semibold">{value}</div></div>
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md border bg-background/50 p-3"><div className="text-xs text-muted-foreground">{label}</div><div className="mt-1 break-words font-medium">{value}</div></div>
}
