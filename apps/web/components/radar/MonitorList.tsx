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
          <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
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
      {/* 头部操作区 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold">监控频道</h3>
          <Badge variant="outline" className="text-xs">
            {channels.length}
          </Badge>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          <Plus className="h-4 w-4 mr-1" />
          添加
        </Button>
      </div>

      {/* 添加频道表单 */}
      <AnimatePresence>
        {showAddForm && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-3 rounded-lg border bg-accent/30 space-y-3">
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4 text-muted-foreground shrink-0" />
                <Input
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  placeholder="输入 YouTube 频道链接或 @用户名..."
                  className="h-9 text-sm"
                  onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setShowAddForm(false)}
                >
                  取消
                </Button>
                <Button
                  size="sm"
                  onClick={handleAdd}
                  disabled={!newUrl.trim() || adding}
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

      {/* 新视频提示 */}
      {channels.some((c) => c.newVideoCount > 0) && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
          <Bell className="h-4 w-4 shrink-0" />
          <span>
            {channels.reduce((sum, c) => sum + c.newVideoCount, 0)} 个新视频待查看
          </span>
        </div>
      )}

      {/* 频道列表 */}
      <div className="space-y-2">
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
                  "cursor-pointer transition-all group",
                  selectedId === channel.id
                    ? "ring-1 ring-primary shadow-md"
                    : "hover:bg-accent/50"
                )}
                onClick={() => onSelectChannel?.(channel.id)}
              >
                <CardContent className="p-3">
                  <div className="flex items-center gap-3">
                    {/* 头像 */}
                    <div className="relative shrink-0">
                      <div className="h-10 w-10 rounded-full overflow-hidden bg-muted flex items-center justify-center">
                        {channel.avatarUrl ? (
                          <Image
                            src={channel.avatarUrl}
                            alt={channel.name}
                            width={40}
                            height={40}
                            className="object-cover"
                          />
                        ) : (
                          <span className="text-xs font-semibold text-foreground/70">
                            {(channel.name || "?").trim().charAt(0).toUpperCase()}
                          </span>
                        )}
                      </div>
                      {/* 新视频红点 */}
                      {channel.newVideoCount > 0 && (
                        <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-white text-[9px] flex items-center justify-center font-bold">
                          {channel.newVideoCount > 9
                            ? "9+"
                            : channel.newVideoCount}
                        </span>
                      )}
                    </div>

                    {/* 信息 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-medium truncate">
                          {channel.name}
                        </h4>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                        <span className="flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          {formatCompactNumber(channel.subscriberCount)}
                        </span>
                        <span
                          className={cn(
                            "flex items-center gap-1",
                            channel.growthRate > 0
                              ? "text-emerald-400"
                              : "text-red-400"
                          )}
                        >
                          <TrendingUp className="h-3 w-3" />
                          {channel.growthRate > 0 ? "+" : ""}
                          {channel.growthRate}%
                        </span>
                      </div>
                    </div>

                    {onTriggerChannel && channel.monitorJobId && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="h-7 w-7 opacity-100 sm:opacity-70 sm:group-hover:opacity-100 transition-opacity"
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

                    {/* 删除按钮 */}
                    {onRemoveChannel && (
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="h-7 w-7 opacity-100 sm:opacity-70 sm:group-hover:opacity-100 transition-opacity"
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

      {/* 空状态 */}
      {channels.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <Video className="h-10 w-10 mx-auto mb-2 opacity-50" />
          <p className="text-sm">暂无监控频道</p>
          <p className="text-xs mt-1">点击上方按钮添加</p>
        </div>
      )}
    </div>
  )
}
