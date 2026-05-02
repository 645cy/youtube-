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

// =============================================================================
// 页面组件
// =============================================================================

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
    if (currentScore > existingScore) {
      byChannel.set(monitor.channel_id, monitor)
    }
  }
  return Array.from(byChannel.values())
}

export default function RadarPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [initialLoading, setInitialLoading] = useState(true)

  const {
    monitoredChannels,
    growthData,
    setMonitoredChannels,
    setGrowthData,
    selectChannel,
  } = useRadarStore()

  // 初始化：加载监控任务列表（含关联频道信息）
  useEffect(() => {
    const load = async () => {
      try {
        const monitors = await radarApi.listMonitors()
        const converted = normalizeMonitors(monitors).map(mapMonitorToRadarChannel)
        setMonitoredChannels(converted)
      } catch (e) {
        setMonitoredChannels([])
        setGrowthData([])
      } finally {
        setInitialLoading(false)
      }
    }
    load()
  }, [setMonitoredChannels, setGrowthData])

  const handleSelectChannel = useCallback(
    (id: string) => {
      setSelectedId(id)
      selectChannel(id)
    },
    [selectChannel]
  )

  const handleAddChannel = useCallback(
    async (url: string) => {
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
    },
    [setMonitoredChannels]
  )

  const handleRemoveChannel = useCallback(
    async (id: string) => {
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
    },
    [monitoredChannels, selectedId, setMonitoredChannels]
  )

  const handleTriggerChannel = useCallback(
    async (id: string) => {
      const channel = monitoredChannels.find((c) => c.id === id)
      if (!channel?.monitorJobId) return
      try {
        const res = await radarApi.triggerMonitor(channel.monitorJobId) as any
        const count = Number(res?.new_videos_found || 0)
        const message = res?.source_status === "api_error"
          ? "远程检查失败，已刷新本地监控时间"
          : `检查完成，发现 ${count} 个新视频`
        toastInfo(message)
        setMonitoredChannels(monitoredChannels.map((c) =>
          c.id === id
            ? { ...c, newVideoCount: count, lastChecked: new Date().toISOString() }
            : c
        ))
      } catch (e: any) {
        toastError("触发监控失败: " + (e.message || "未知错误"))
      }
    },
    [monitoredChannels, setMonitoredChannels]
  )

  const newVideoTotal = monitoredChannels.reduce(
    (sum, c) => sum + c.newVideoCount,
    0
  )

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Radar className="h-6 w-6 text-primary" />
            竞品雷达
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            追踪竞品频道动态，发现增长机会
          </p>
        </div>
        {newVideoTotal > 0 && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
            <Bell className="h-4 w-4" />
            {newVideoTotal} 个新视频
          </div>
        )}
      </div>

      {/* 两栏布局 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧：监控列表 */}
        <div className="lg:col-span-1">
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

        {/* 右侧：增长图表 */}
        <div className="lg:col-span-2">
          <RadarGrowthChart
            data={growthData}
            series={[]}
            loading={false}
          />
        </div>
      </div>
    </div>
  )
}
