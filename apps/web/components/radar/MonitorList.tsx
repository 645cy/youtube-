/**
 * MonitorList 组件 - 竞品雷达
 * 功能：
 * - 监控频道列表（头像/名称/订阅数/新视频Badge）
 * - 添加监控频道表单
 * - 新视频检测提示
 */

"use client"

import { useState } from "react"
import Image from "next/image"
import { motion, AnimatePresence } from "framer-motion"
import {
  Users,
  Video,
  TrendingUp,
  Plus,
  Bell,
  Trash2,
  Search,
  Loader2,
  RefreshCw,
} from "lucide-react"
import { cn, formatCompactNumber } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useGSAPReveal } from "@/hooks/useGSAPReveal"

/** 监控频道数据 */
interface MonitoredChannel {
  id: string
  monitorJobId?: number
  name: string
  avatarUrl: string
  subscriberCount: number
  newVideoCount: number
  growthRate: number
  lastChecked: string
}

interface MonitorListProps {
  channels: MonitoredChannel[]
  loading?: boolean
  onAddChannel?: (url: string) => void
  onRemoveChannel?: (id: string) => void
  onTriggerChannel?: (id: string) => void | Promise<void>
  onSelectChannel?: (id: string) => void
  selectedId?: string | null
  className?: string
}

export function MonitorList({
  channels,
  loading = false,
  onAddChannel,
  onRemoveChannel,
  onTriggerChannel,
  onSelectChannel,
  selectedId,
  className,
}: MonitorListProps) {
  const [showAddForm, setShowAddForm] = useState(false)
  const [newUrl, setNewUrl] = useState("")
  const [adding, setAdding] = useState(false)
  const [triggeringId, setTriggeringId] = useState<string | null>(null)

  const listRef = useGSAPReveal<HTMLDivElement>({ y: 20, opacity: 0, duration: 0.5, stagger: 0.08, ease: "power3.out" })
  const formRef = useGSAPReveal<HTMLDivElement>({ y: 20, opacity: 0, duration: 0.5, ease: "power3.out" })

  const handleAdd = async () => {
    if (!newUrl.trim() || !onAddChannel) return
    setAdding(true)
    try {
      await onAddChannel(newUrl)
      setNewUrl("")
      setShowAddForm(false)
    } finally {
      setAdding(false)
    }
  }

  if (loading) {
    return (
      <div className={cn("space-y-3", className)}>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-3 rounded-lg border paper-card depth-hover">
            <Skeleton className="h-10 w-10 rounded-full shrink-0" />
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-3 w-1/3" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1">
          <p className="page-kicker">监控册</p>
          <h3 className="font-semibold font-serif tracking-wide text-foreground">监控频道</h3>
        </div>
        <Badge variant="outline" className="text-xs font-serif tracking-wider bg-background/70">
          {channels.length}
        </Badge>
      </div>

      <Button
        size="sm"
        variant="outline"
        onClick={() => setShowAddForm(!showAddForm)}
        className="btn-ripple font-serif tracking-wider w-full justify-center border-primary/15 bg-background/70"
      >
        <Plus className="h-4 w-4 mr-1" />
        添加频道
      </Button>

      <AnimatePresence>
        {showAddForm && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div ref={formRef} className="p-4 space-y-3 paper-card depth-hover bg-background/80">
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4 text-muted-foreground shrink-0" />
                <Input
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  placeholder="输入 YouTube 频道链接或 @用户名..."
                  className="h-9 text-sm input-glow font-serif tracking-wide"
                  onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowAddForm(false)}
                  className="font-serif tracking-wider"
                >
                  取消
                </Button>
                <Button
                  size="sm"
                  onClick={handleAdd}
                  disabled={!newUrl.trim() || adding}
                  className="btn-ripple font-serif tracking-wider"
                >
                  {adding ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1" />
                  ) : (
                    <Plus className="h-4 w-4 mr-1" />
                  )}
                  添加监控
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {channels.some((c) => c.newVideoCount > 0) && (
        <div className="flex items-center gap-2 p-3 paper-card page-corner bg-amber-500/10 border border-amber-500/20 text-amber-500 text-sm">
          <Bell className="h-4 w-4 shrink-0 animate-candle-pulse" />
          <span className="font-serif tracking-wide">
            {channels.reduce((sum, c) => sum + c.newVideoCount, 0)} 个新视频待查看
          </span>
        </div>
      )}

      <div ref={listRef} className="space-y-2">
        <AnimatePresence>
          {channels.map((channel) => (
            <motion.div
              key={channel.id}
              layout
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
            >
              <Card
                className={cn(
                  "cursor-pointer transition-all group paper-card page-corner paper-hover-lift depth-hover bg-background/80",
                  selectedId === channel.id ? "ring-1 ring-primary shadow-md" : ""
                )}
                onClick={() => onSelectChannel?.(channel.id)}
              >
                <CardContent className="p-3.5">
                  <div className="flex items-center gap-3">
                    <div className="relative shrink-0">
                      <div className="h-10 w-10 rounded-full overflow-hidden bg-muted flex items-center justify-center border border-border">
                        {channel.avatarUrl ? (
                          <Image
                            src={channel.avatarUrl}
                            alt={channel.name}
                            width={40}
                            height={40}
                            className="object-cover"
                            onError={(e) => {
                              const target = e.currentTarget as HTMLImageElement
                              target.style.display = "none"
                            }}
                          />
                        ) : null}
                        <span className="text-xs font-semibold text-foreground/70 absolute inset-0 flex items-center justify-center pointer-events-none font-serif">
                          {(channel.name || "?").trim().charAt(0).toUpperCase()}
                        </span>
                      </div>
                      {channel.newVideoCount > 0 && (
                        <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-white text-[9px] flex items-center justify-center font-bold tabular-nums animate-candle-pulse">
                          {channel.newVideoCount > 9 ? "9+" : channel.newVideoCount}
                        </span>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-medium truncate font-serif tracking-wide text-foreground">
                          {channel.name}
                        </h4>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                        <span className="flex items-center gap-1 tabular-nums tracking-wide">
                          <Users className="h-3 w-3" />
                          {formatCompactNumber(channel.subscriberCount)}
                        </span>
                        <span className={cn("flex items-center gap-1 tabular-nums tracking-wide", channel.growthRate > 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-500 dark:text-red-400") }>
                          <TrendingUp className="h-3 w-3" />
                          {channel.growthRate > 0 ? "+" : ""}{channel.growthRate}%
                        </span>
                      </div>
                    </div>

                    {onTriggerChannel && channel.monitorJobId && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="h-7 w-7 opacity-100 sm:opacity-70 sm:group-hover:opacity-100 transition-opacity btn-ripple"
                        onClick={async (e) => {
                          e.stopPropagation()
                          setTriggeringId(channel.id)
                          try {
                            await onTriggerChannel(channel.id)
                          } finally {
                            setTriggeringId(null)
                          }
                        }}
                        title="立即检查"
                        disabled={triggeringId === channel.id}
                      >
                        <RefreshCw className={cn("h-3.5 w-3.5 text-muted-foreground hover:text-primary", triggeringId === channel.id && "animate-spin")} />
                      </Button>
                    )}

                    {onRemoveChannel && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="h-7 w-7 opacity-100 sm:opacity-70 sm:group-hover:opacity-100 transition-opacity btn-ripple"
                        onClick={(e) => {
                          e.stopPropagation()
                          onRemoveChannel(channel.id)
                        }}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-red-400" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {channels.length === 0 && (
        <div className="text-center py-8 text-muted-foreground paper-card page-corner depth-hover bg-background/70">
          <Video className="h-10 w-10 mx-auto mb-2 opacity-50" />
          <p className="text-sm font-serif tracking-wide">暂无监控频道</p>
          <p className="text-xs mt-1 tracking-wide leading-relaxed">点击上方按钮添加</p>
        </div>
      )}
    </div>
  )
}
