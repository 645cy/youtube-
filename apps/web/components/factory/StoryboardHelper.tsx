/**
 * StoryboardHelper 组件 - 内容工厂 Tab 3: 分镜辅助
 * 时间码/画面/素材来源 三列表格
 */

"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import {
  Clock,
  Image,
  Film,
  Plus,
  Trash2,
  Sparkles,
  Loader2,
  Video,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

/** 分镜项 */
export interface StoryboardItem {
  id: string
  timestamp: string    // 时间码 00:00-00:05
  scene: string        // 画面描述
  shot: string         // 镜头描述
  source: string       // 素材来源
  type?: "实拍" | "屏幕录制" | "素材库" | "AI生成" | "动画"
}

/** 素材来源类型颜色 */
const sourceTypeColors: Record<string, string> = {
  实拍: "bg-blue-500/20 text-blue-400",
  屏幕录制: "bg-emerald-500/20 text-emerald-400",
  素材库: "bg-amber-500/20 text-amber-400",
  "AI生成": "bg-violet-500/20 text-violet-400",
  动画: "bg-pink-500/20 text-pink-400",
}

interface StoryboardHelperProps {
  items: StoryboardItem[]
  onUpdate: (items: StoryboardItem[]) => void
  onGenerate?: () => void
  isGenerating?: boolean
  className?: string
}

export function StoryboardHelper({
  items,
  onUpdate,
  onGenerate,
  isGenerating = false,
  className,
}: StoryboardHelperProps) {
  const [editingId, setEditingId] = useState<string | null>(null)

  const addItem = () => {
    const lastItem = items[items.length - 1]
    let startTime = 0
    if (lastItem) {
      const match = lastItem.timestamp.match(/(\d+):(\d+)$/)
      if (match) {
        startTime = parseInt(match[1]) * 60 + parseInt(match[2])
      }
    }
    const endTime = startTime + 5
    const formatTime = (s: number) =>
      `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`

    const newItem: StoryboardItem = {
      id: `sb-${Date.now()}`,
      timestamp: `${formatTime(startTime)}-${formatTime(endTime)}`,
      scene: "",
      shot: "",
      source: "实拍",
      type: "实拍",
    }
    onUpdate([...items, newItem])
    setEditingId(newItem.id)
  }

  const updateItem = (id: string, updates: Partial<StoryboardItem>) => {
    onUpdate(items.map((item) => (item.id === id ? { ...item, ...updates } : item)))
  }

  const removeItem = (id: string) => {
    onUpdate(items.filter((item) => item.id !== id))
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* 头部操作 */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-sm">分镜表</h3>
          <span className="text-xs text-muted-foreground">
            {items.length} 个镜头
          </span>
        </div>
        <div className="flex gap-2">
          {onGenerate && (
            <Button
              size="sm"
              variant="outline"
              onClick={onGenerate}
              disabled={isGenerating}
            >
              {isGenerating ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : (
                <Sparkles className="h-4 w-4 mr-1" />
              )}
              AI 生成
            </Button>
          )}
          <Button size="sm" onClick={addItem}>
            <Plus className="h-4 w-4 mr-1" />
            添加镜头
          </Button>
        </div>
      </div>

      {/* 表格头部 */}
      {items.length > 0 && (
        <div className="hidden sm:grid grid-cols-12 gap-2 px-3 text-xs font-semibold text-muted-foreground uppercase">
          <div className="col-span-2 flex items-center gap-1">
            <Clock className="h-3 w-3" />
            时间码
          </div>
          <div className="col-span-3 flex items-center gap-1">
            <Image className="h-3 w-3" />
            画面
          </div>
          <div className="col-span-3 flex items-center gap-1">
            <Video className="h-3 w-3" />
            镜头
          </div>
          <div className="col-span-2 flex items-center gap-1">
            <Film className="h-3 w-3" />
            素材来源
          </div>
          <div className="col-span-2" />
        </div>
      )}

      {/* 分镜列表 */}
      <div className="space-y-2">
        {items.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.03 }}
          >
            <StoryboardRow
              item={item}
              index={index}
              isEditing={editingId === item.id}
              onEdit={() => setEditingId(editingId === item.id ? null : item.id)}
              onUpdate={(updates) => updateItem(item.id, updates)}
              onRemove={() => removeItem(item.id)}
            />
          </motion.div>
        ))}
      </div>

      {/* 空状态 */}
      {items.length === 0 && (
        <div className="text-center py-8 text-muted-foreground border rounded-lg border-dashed">
          <Film className="h-10 w-10 mx-auto mb-2 opacity-50" />
          <p className="text-sm">暂无分镜数据</p>
          <p className="text-xs mt-1">点击"添加镜头"开始编写分镜表</p>
        </div>
      )}
    </div>
  )
}

/** 单行分镜 */
function StoryboardRow({
  item,
  index,
  isEditing,
  onEdit,
  onUpdate,
  onRemove,
}: {
  item: StoryboardItem
  index: number
  isEditing: boolean
  onEdit: () => void
  onUpdate: (updates: Partial<StoryboardItem>) => void
  onRemove: () => void
}) {
  const sourceColor = sourceTypeColors[item.type || "实拍"] || "bg-muted"

  if (isEditing) {
    return (
      <Card className="border-primary/30 ring-1 ring-primary/20">
        <CardContent className="p-3 space-y-3">
          <div className="text-xs font-medium text-muted-foreground mb-2">
            镜头 #{index + 1}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                时间码
              </label>
              <Input
                value={item.timestamp}
                onChange={(e) => onUpdate({ timestamp: e.target.value })}
                placeholder="00:00-00:05"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                类型
              </label>
              <select
                value={item.type || "实拍"}
                onChange={(e) => {
                  const val = e.target.value as NonNullable<StoryboardItem["type"]>
                  onUpdate({ type: val, source: val })
                }}
                className="w-full h-9 rounded-md border bg-background px-2 text-sm"
              >
                <option value="实拍">实拍</option>
                <option value="屏幕录制">屏幕录制</option>
                <option value="素材库">素材库</option>
                <option value="AI生成">AI生成</option>
                <option value="动画">动画</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">
              画面描述
            </label>
            <Input
              value={item.scene}
              onChange={(e) => onUpdate({ scene: e.target.value })}
              placeholder="描述画面内容..."
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">
              镜头描述
            </label>
            <Input
              value={item.shot}
              onChange={(e) => onUpdate({ shot: e.target.value })}
              placeholder="景别、角度、运动..."
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">
              素材来源
            </label>
            <Input
              value={item.source}
              onChange={(e) => onUpdate({ source: e.target.value })}
              placeholder="具体素材来源..."
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="ghost" onClick={onEdit}>
              完成
            </Button>
            <Button size="sm" variant="ghost" onClick={onRemove}>
              <Trash2 className="h-3.5 w-3.5 text-red-400" />
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card
      className="cursor-pointer hover:bg-accent/30 transition-colors group"
      onClick={onEdit}
    >
      <CardContent className="p-3">
        {/* 桌面布局 */}
        <div className="hidden sm:grid grid-cols-12 gap-2 items-center">
          <div className="col-span-2">
            <code className="text-xs font-mono bg-muted px-2 py-1 rounded">
              {item.timestamp}
            </code>
          </div>
          <div className="col-span-3 text-sm truncate">{item.scene || "-"}</div>
          <div className="col-span-3 text-sm text-muted-foreground truncate">
            {item.shot || "-"}
          </div>
          <div className="col-span-2">
            <Badge variant="outline" className={cn("text-[10px]", sourceColor)}>
              {item.source}
            </Badge>
          </div>
          <div className="col-span-2 flex justify-end">
            <Button
              variant="ghost"
              size="icon-sm"
              className="h-7 w-7 opacity-0 group-hover:opacity-100"
              onClick={(e) => {
                e.stopPropagation()
                onRemove()
              }}
            >
              <Trash2 className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
          </div>
        </div>

        {/* 移动端布局 */}
        <div className="sm:hidden space-y-2">
          <div className="flex items-center justify-between">
            <code className="text-xs font-mono bg-muted px-2 py-1 rounded">
              {item.timestamp}
            </code>
            <Badge
              variant="outline"
              className={cn("text-[10px]", sourceColor)}
            >
              {item.source}
            </Badge>
          </div>
          <p className="text-sm">{item.scene || "-"}</p>
          <p className="text-xs text-muted-foreground">{item.shot || "-"}</p>
        </div>
      </CardContent>
    </Card>
  )
}