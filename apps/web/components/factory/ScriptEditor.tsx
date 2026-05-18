/**
 * ScriptEditor 组件 - 内容工厂 Tab 2: 脚本编辑器
 * Hook/痛点/方案/演示/CTA 分段编辑
 * 支持 AI 生成和手动编辑
 */

"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import {
  GripVertical,
  Mic,
  Flame,
  Lightbulb,
  Monitor,
  Megaphone,
  Sparkles,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/input"

/** 脚本段落类型 */
export interface ScriptSegment {
  id: string
  type: "hook" | "pain" | "solution" | "demo" | "cta"
  title: string
  content: string
  speakerNote?: string
  duration?: number
}

/** 段落类型配置 */
const SEGMENT_TYPES: Record<
  ScriptSegment["type"],
  { label: string; icon: typeof Flame; color: string; bgColor: string }
> = {
  hook: {
    label: "Hook 开场",
    icon: Flame,
    color: "text-red-400",
    bgColor: "bg-red-400/10 border-red-400/20",
  },
  pain: {
    label: "痛点共鸣",
    icon: Mic,
    color: "text-amber-400",
    bgColor: "bg-amber-400/10 border-amber-400/20",
  },
  solution: {
    label: "解决方案",
    icon: Lightbulb,
    color: "text-blue-400",
    bgColor: "bg-blue-400/10 border-blue-400/20",
  },
  demo: {
    label: "演示证明",
    icon: Monitor,
    color: "text-emerald-400",
    bgColor: "bg-emerald-400/10 border-emerald-400/20",
  },
  cta: {
    label: "CTA 行动",
    icon: Megaphone,
    color: "text-violet-400",
    bgColor: "bg-violet-400/10 border-violet-400/20",
  },
}

interface ScriptEditorProps {
  segments: ScriptSegment[]
  onUpdate: (segments: ScriptSegment[]) => void
  onGenerate?: () => void
  isGenerating?: boolean
  className?: string
}

export function ScriptEditor({
  segments,
  onUpdate,
  onGenerate,
  isGenerating = false,
  className,
}: ScriptEditorProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const updateSegment = (id: string, updates: Partial<ScriptSegment>) => {
    onUpdate(
      segments.map((s) => (s.id === id ? { ...s, ...updates } : s))
    )
  }

  const addSegment = (type: ScriptSegment["type"]) => {
    const config = SEGMENT_TYPES[type]
    const newSegment: ScriptSegment = {
      id: `seg-${Date.now()}`,
      type,
      title: config.label,
      content: "",
      duration: 30,
    }
    onUpdate([...segments, newSegment])
    setExpandedId(newSegment.id)
  }

  const removeSegment = (id: string) => {
    onUpdate(segments.filter((s) => s.id !== id))
  }

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="p-4 md:p-5 border paper-card page-corner bg-background/80 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="space-y-1">
            <p className="text-[10px] font-serif tracking-[0.2em] uppercase text-muted-foreground/70">章节页 · 脚本结构</p>
            <h3 className="font-semibold text-sm font-serif tracking-wide">脚本段落</h3>
            <span className="text-xs text-muted-foreground font-serif tracking-wide tabular-nums">{segments.length} 段 · 预计 {segments.reduce((sum, s) => sum + (s.duration || 0), 0)} 秒</span>
          </div>
          {onGenerate && <Button size="sm" onClick={onGenerate} disabled={isGenerating} className="font-serif tracking-wide">{isGenerating ? <Sparkles className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}AI 生成</Button>}
        </div>
      </div>

      <div className="space-y-3">
        {segments.map((segment, index) => {
          const config = SEGMENT_TYPES[segment.type]
          const Icon = config.icon
          const isExpanded = expandedId === segment.id

          return (
            <motion.div key={segment.id} layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}>
              <Card className={cn("border-l-4 paper-card page-corner paper-hover-lift bg-background/80", config.bgColor, isExpanded && "shadow-md")}>
                <div className="flex items-center gap-2 p-3 cursor-pointer hover:bg-accent/30 transition-colors font-serif tracking-wide" onClick={() => toggleExpand(segment.id)}>
                  <GripVertical className="h-4 w-4 text-muted-foreground shrink-0" />
                  <Icon className={cn("h-4 w-4 shrink-0", config.color)} />
                  <span className="font-medium text-sm flex-1 font-serif tracking-wide">{segment.title}</span>
                  {segment.duration && <span className="text-xs text-muted-foreground font-serif tracking-wide tabular-nums">{segment.duration}秒</span>}
                  <Button variant="ghost" size="icon-sm" className="h-7 w-7" onClick={(e) => { e.stopPropagation(); removeSegment(segment.id) }}><Trash2 className="h-3.5 w-3.5 text-muted-foreground" /></Button>
                  {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                </div>

                {isExpanded && (
                  <CardContent className="pt-0 pb-3 px-3 space-y-3">
                    <div className="flex items-center gap-2"><span className="text-xs text-muted-foreground w-16 font-serif tracking-wide">时长(秒)</span><input type="number" min={0} max={3600} value={segment.duration || ""} onChange={(e) => updateSegment(segment.id, { duration: Math.max(0, Math.min(3600, parseInt(e.target.value) || 0)) })} className="w-20 h-8 rounded-md border bg-background px-2 text-sm input-glow font-serif tracking-wide tabular-nums" /></div>
                    <div><span className="text-xs text-muted-foreground mb-1 block font-serif tracking-wide">脚本内容</span><Textarea value={segment.content} onChange={(e) => updateSegment(segment.id, { content: e.target.value })} placeholder={`输入${config.label}内容...`} className="min-h-[100px] input-glow font-serif tracking-wide" /></div>
                    <div><span className="text-xs text-muted-foreground mb-1 block font-serif tracking-wide">口播提示（可选）</span><Textarea value={segment.speakerNote || ""} onChange={(e) => updateSegment(segment.id, { speakerNote: e.target.value })} placeholder="口播时的注意事项、语气、表情提示..." className="min-h-[60px] input-glow font-serif tracking-wide" /></div>
                  </CardContent>
                )}
              </Card>
            </motion.div>
          )
        })}
      </div>

      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-muted-foreground flex items-center font-serif tracking-wide"><Plus className="h-3 w-3 mr-1" />添加段落:</span>
        {(Object.keys(SEGMENT_TYPES) as ScriptSegment["type"][]).map((type) => {
          const config = SEGMENT_TYPES[type]
          const Icon = config.icon
          return <Button key={type} variant="outline" size="sm" className="h-7 text-xs font-serif tracking-wide" onClick={() => addSegment(type)}><Icon className={cn("h-3 w-3 mr-1", config.color)} />{config.label}</Button>
        })}
      </div>

      {segments.length === 0 && (
        <div className="text-center py-8 text-muted-foreground border rounded-lg border-dashed font-serif tracking-wide paper-card page-corner bg-muted/15"><Mic className="h-10 w-10 mx-auto mb-2 opacity-50" /><p className="text-sm">暂无脚本段落</p><p className="text-xs mt-1">点击上方按钮添加段落或使用 AI 生成</p></div>
      )}
    </div>
  )
}