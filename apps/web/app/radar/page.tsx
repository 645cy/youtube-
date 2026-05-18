/**
 * 竞品雷达页面 - /radar
 * 功能：
 * - 监控频道列表（头像/名称/订阅数/新视频Badge）
 * - 增长曲线图表（Recharts LineChart）
 * - 新视频检测提示
 * - 添加监控频道表单
 */

"use client"

import { useState, useEffect, useCallback } from "react"
import { Radar, Bell } from "lucide-react"
import { MonitorList } from "@/components/radar/MonitorList"
import { RadarGrowthChart } from "@/components/radar/GrowthChart"
import { useRadarStore } from "@/lib/store"
import { channelApi, radarApi } from "@/lib/api"
import { APP_DEFAULTS } from "@/lib/defaults"
import { mapMonitorToRadarChannel } from "@/lib/mappers"
import { toastError, toastInfo } from "@/lib/toast"
import { useGSAPReveal } from "@/hooks/useGSAPReveal"
import { HeroFooter } from "@/components/HeroFooter"

function normalizeMonitors(monitors: any[]) {
  const byChannel = new Map<number, any>()
  for (const monitor of monitors || []) {
    const existing = byChannel.get(monitor.channel_id)
    if (!existing) {
      byChannel.set(monitor.channel_id, monitor)
      continue
    }
    const existingScore = existing.job_type === "new_videos" ? 1 : 0
    const currentScore = monitor.job_type === "new_videos" ? 1 : 0
    if (currentScore > existingScore) byChannel.set(monitor.channel_id, monitor)
  }
  return Array.from(byChannel.values())
}

export default function RadarPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [initialLoading, setInitialLoading] = useState(true)

  const titleRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, ease: "power3.out" })
  const chartRef = useGSAPReveal<HTMLDivElement>({ y: 24, opacity: 0, duration: 0.5, delay: 0.15, ease: "power3.out" })

  const { monitoredChannels, growthData, setMonitoredChannels, setGrowthData, selectChannel } = useRadarStore()

  useEffect(() => {
    const load = async () => {
      try {
        const monitors = await radarApi.listMonitors()
        const converted = normalizeMonitors(monitors).map(mapMonitorToRadarChannel)
        setMonitoredChannels(converted)
      } catch {
        setMonitoredChannels([])
        setGrowthData([])
      } finally {
        setInitialLoading(false)
      }
    }
    load()
  }, [setMonitoredChannels, setGrowthData])

  const handleSelectChannel = useCallback((id: string) => {
    setSelectedId(id)
    selectChannel(id)

    const channel = monitoredChannels.find((c) => c.id === id)
    if (channel) {
      const days = 30
      const now = new Date()
      const data: Array<{ date: string; [key: string]: string | number }> = []
      const dailyRate = channel.growthRate / 100 / days
      const currentSubs = channel.subscriberCount || 0
      const denominator = 1 + dailyRate * days
      const baseSubs = denominator === 0 ? currentSubs : Math.max(1, Math.round(currentSubs / denominator))

      for (let i = 0; i < days; i++) {
        const d = new Date(now)
        d.setDate(d.getDate() - (days - 1 - i))
        const factor = 1 + dailyRate * i
        data.push({
          date: d.toISOString().split("T")[0],
          [channel.name]: Math.round(baseSubs * factor),
        })
      }
      setGrowthData(data)
    }
  }, [monitoredChannels, selectChannel, setGrowthData])

  const handleAddChannel = useCallback(async (url: string) => {
    if (!url || typeof url !== "string") {
      toastError("请输入有效的 YouTube 链接")
      return
    }
    try {
      const channelIdMatch = url.match(/youtube\.com\/channel\/(UC[\w-]+)/)
      const handleMatch = url.match(/(?:youtube\.com\/)?@([\w.-]+)/)
      const importedChannel = channelIdMatch
        ? await channelApi.importYoutube(channelIdMatch[1])
        : await channelApi.search(handleMatch ? `@${handleMatch[1]}` : url)

      const existingMonitors = await radarApi.listMonitors()
      const hasMonitor = existingMonitors.some((monitor) => monitor.channel_id === importedChannel.id)
      if (!hasMonitor) {
        await radarApi.createMonitor({
          channel_id: importedChannel.id,
          job_type: "new_videos",
          frequency: APP_DEFAULTS.monitorFrequency,
        })
      }

      const monitors = await radarApi.listMonitors()
      const converted = normalizeMonitors(monitors).map(mapMonitorToRadarChannel)
      setMonitoredChannels(converted)
    } catch (e: any) {
      toastError("添加频道失败: " + (e.message || "请检查 URL 或网络连接"))
    }
  }, [setMonitoredChannels])

  const handleRemoveChannel = useCallback(async (id: string) => {
    const channel = monitoredChannels.find((c) => c.id === id)
    if (channel?.monitorJobId) {
      try {
        await radarApi.deleteMonitor(channel.monitorJobId)
      } catch (e: any) {
        toastError("删除监控失败: " + (e.message || "未知错误"))
        return
      }
    }
    setMonitoredChannels(monitoredChannels.filter((c) => c.id !== id))
    if (selectedId === id) setSelectedId(null)
  }, [monitoredChannels, selectedId, setMonitoredChannels])

  const handleTriggerChannel = useCallback(async (id: string) => {
    const channel = monitoredChannels.find((c) => c.id === id)
    if (!channel?.monitorJobId) return
    try {
      const res = await radarApi.triggerMonitor(channel.monitorJobId) as any
      const count = Number(res?.new_videos_found || 0)
      const message = res?.source_status === "api_error"
        ? "远程检查失败，已刷新本地监控时间"
        : `检查完成，发现 ${count} 个新视频`
      toastInfo(message)
      setMonitoredChannels(monitoredChannels.map((c) => c.id === id ? { ...c, newVideoCount: count, lastChecked: new Date().toISOString() } : c))
    } catch (e: any) {
      toastError("触发监控失败: " + (e.message || "未知错误"))
    }
  }, [monitoredChannels, setMonitoredChannels])

  const newVideoTotal = monitoredChannels.reduce((sum, c) => sum + c.newVideoCount, 0)

  const quickSignals = [
    { label: "监控频道", value: String(monitoredChannels.length) },
    { label: "新视频", value: String(newVideoTotal) },
    { label: "趋势图", value: selectedId ? "已激活" : "待选择" },
  ]

  return (
    <div className="space-y-10 max-w-6xl mx-auto">
      <div ref={titleRef} className="pt-2 pb-2">
        <div className="grid gap-6 lg:grid-cols-[1.35fr_0.65fr] items-stretch">
          <div className="relative overflow-hidden border paper-card page-corner p-6 md:p-8 min-h-[240px] flex flex-col justify-between">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.16),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.45),rgba(255,255,255,0.02))] dark:bg-[radial-gradient(circle_at_top_left,rgba(184,151,92,0.18),transparent_35%),linear-gradient(135deg,rgba(255,255,255,0.05),rgba(255,255,255,0.01))]" />
            <div className="relative z-10 space-y-3">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[11px] font-semibold text-primary">竞品雷达</span>
                <span className="text-xs text-muted-foreground">监控 · 增长 · 告警</span>
              </div>
              <h1 className="hero-title max-w-xl flex items-center gap-3">
                <Radar className="h-7 w-7 md:h-8 md:w-8 text-primary shrink-0" />
                竞品雷达
              </h1>
              <p className="page-body max-w-lg">
                追踪竞品频道动态与新视频告警，把监控任务和增长趋势放在同一视图里复盘。
              </p>
            </div>
            <HeroFooter segment="竞品雷达" />
          </div>

          <div className="grid gap-4">
            <div className="p-5 border paper-card page-corner bg-background/80 flex items-center justify-between gap-3">
              <div>
                <p className="page-meta">新视频告警</p>
                <p className="stat-value mt-2 text-lg">{newVideoTotal > 0 ? `${newVideoTotal} 条待查看` : "暂无新视频"}</p>
              </div>
              <Bell className="h-5 w-5 text-primary/80" />
            </div>
            {quickSignals.map((item, idx) => (
              <div key={item.label} className={idx % 2 === 0 ? "p-5 border paper-card page-corner bg-muted/20" : "p-5 border paper-card page-corner bg-background/75"}>
                <p className="page-meta">{item.label}</p>
                <p className="stat-value mt-2 text-lg leading-none">{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[0.92fr_1.08fr] gap-6 items-start">
        <div className="paper-card page-corner paper-hover-lift depth-hover p-4">
          <MonitorList
            channels={monitoredChannels}
            loading={initialLoading}
            selectedId={selectedId}
            onSelectChannel={handleSelectChannel}
            onAddChannel={handleAddChannel}
            onRemoveChannel={handleRemoveChannel}
            onTriggerChannel={handleTriggerChannel}
          />
        </div>

        <div ref={chartRef} className="paper-card page-corner paper-hover-lift depth-hover p-4">
          <RadarGrowthChart
            data={growthData}
            series={selectedId ? monitoredChannels.filter((c) => c.id === selectedId).map((c) => ({ key: c.name, name: c.name, color: "#B8860B" })) : []}
            loading={false}
          />
        </div>
      </div>
    </div>
  )
}
