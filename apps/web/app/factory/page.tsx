/**
 * 内容工厂页面 - /factory
 * 三 Tab 布局：
 * - Tab 1: 选题生成器（niche 输入 → AI 选题建议）
 * - Tab 2: 脚本编辑器（Hook/痛点/方案/演示/CTA 分段编辑）
 * - Tab 3: 分镜辅助（时间码/画面/素材来源 三列表格）
 */

"use client"

import { useState, useCallback } from "react"
import {
  Factory,
  Sparkles,
  PenTool,
  Film,
  Search,
  Lightbulb,
  Loader2,
  ImageIcon,
  Clock3,
  ShieldCheck,
} from "lucide-react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { TopicGenerator } from "@/components/factory/TopicGenerator"
import { ScriptEditor } from "@/components/factory/ScriptEditor"
import { StoryboardHelper } from "@/components/factory/StoryboardHelper"
import type { TopicItem } from "@/components/factory/TopicGenerator"
import type { ScriptSegment } from "@/components/factory/ScriptEditor"
import type { StoryboardItem } from "@/components/factory/StoryboardHelper"
import { factoryApi } from "@/lib/api"
import { APP_DEFAULTS } from "@/lib/defaults"
import { toastError, toastInfo } from "@/lib/toast"

// =============================================================================
// 页面组件
// =============================================================================

export default function FactoryPage() {
  const [activeTab, setActiveTab] = useState("topics")
  const [topics, setTopics] = useState<TopicItem[]>([])
  const [scriptSegments, setScriptSegments] =
    useState<ScriptSegment[]>([])
  const [storyboardItems, setStoryboardItems] =
    useState<StoryboardItem[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [seoKeywords, setSeoKeywords] = useState<string[]>([])
  const [seoLoading, setSeoLoading] = useState(false)
  const [optimizedTitle, setOptimizedTitle] = useState("")
  const [titleLoading, setTitleLoading] = useState(false)
  const [titleInput, setTitleInput] = useState("")
  const [selectedTopic, setSelectedTopic] = useState<TopicItem | null>(null)
  const [thumbnailResult, setThumbnailResult] = useState<Record<string, unknown> | null>(null)
  const [publishResult, setPublishResult] = useState<Record<string, unknown> | null>(null)
  const [reviewResult, setReviewResult] = useState<Record<string, unknown> | null>(null)
  const [thumbnailLoading, setThumbnailLoading] = useState(false)
  const [publishLoading, setPublishLoading] = useState(false)
  const [reviewLoading, setReviewLoading] = useState(false)

  // 选题生成
  const handleGenerateTopics = useCallback(
    async (niche: string) => {
      setIsGenerating(true)
      setSeoLoading(true)
      try {
        const [topicRes, seoRes] = await Promise.allSettled([
          factoryApi.topicDiscovery({ niche }),
          factoryApi.getSEOKeywords({ niche, count: 10 }),
        ])

        // 选题结果
        if (topicRes.status === "fulfilled") {
          const suggestions = (topicRes.value as any)?.topic_suggestions || []
          const converted = suggestions.map((t: any, i: number) => ({
            id: String(t.topic_id || i + 1),
            title: t.suggested_title || t.keyword || "未命名选题",
            description: `关键词: ${t.keyword || "未知"} | 模板: ${t.template_category || "general"}`,
            searchVolume: t.estimated_monthly_searches ? String(t.estimated_monthly_searches) : "未知",
            competition: t.competition || "中",
            score: t.estimated_ctr_boost === "high" ? 85 : t.estimated_ctr_boost === "medium" ? 65 : 50,
            tags: [t.template_category || niche || "general"],
          }))
          setTopics(converted.length > 0 ? converted : [])
          setSelectedTopic(converted[0] || null)
        } else {
          setTopics([])
          toastError("选题生成失败")
        }

        // SEO 关键词
        if (seoRes.status === "fulfilled") {
          setSeoKeywords((seoRes.value as any)?.keywords?.map((k: any) => k.keyword || k) || [])
        } else {
          setSeoKeywords([])
        }
      } catch (e) {
        toastError("选题生成失败")
        setTopics([])
        setSeoKeywords([])
      } finally {
        setIsGenerating(false)
        setSeoLoading(false)
      }
    },
    []
  )

  // 脚本生成：AI 生成带内容的脚本
  const handleGenerateScript = useCallback(async () => {
    setIsGenerating(true)
    try {
      const topic = selectedTopic?.title || (topics.length > 0 ? topics[0].title : "视频内容")
      const niche = selectedTopic?.tags?.[0] || (topics.length > 0 && topics[0].tags?.[0] ? topics[0].tags[0] : "general")
      const res = await factoryApi.aiScriptGenerate({
        niche,
        topic,
        template_id: "tutorial",
      })
      if (res?.segments && res.segments.length > 0) {
        const typeMap: Record<string, ScriptSegment["type"]> = {
          hook: "hook", pain: "pain", solution: "solution", demo: "demo", cta: "cta",
        }
        const segments: ScriptSegment[] = res.segments.map((s: any) => ({
          id: s.id || `seg-${Date.now()}`,
          type: typeMap[s.type] || "solution",
          title: s.title || "未命名段落",
          content: s.content || "",
          duration: s.duration || 30,
        }))
        setScriptSegments(segments)
        toastInfo(`已生成「${res.template_name || "脚本"}」共 ${segments.length} 段`)
      } else {
        setScriptSegments([])
        toastError("AI 生成返回空内容")
      }
    } catch (e: any) {
      toastError("AI 脚本生成失败: " + (e.message || "未知错误"))
      setScriptSegments([])
    } finally {
      setIsGenerating(false)
    }
  }, [topics, selectedTopic])

  // 标题优化
  const handleOptimizeTitle = useCallback(async () => {
    if (!titleInput.trim()) return
    setTitleLoading(true)
    try {
      const res = await factoryApi.optimizeTitle({ title: titleInput })
      const suggestions = (res as any)?.improved_title_suggestions || []
      setOptimizedTitle(suggestions[0] || titleInput)
      const ctr = (res as any)?.ctr_analysis?.estimated_ctr ?? (res as any)?.ctr_estimate ?? 0
      toastInfo(`CTR 预估: ${Math.round(ctr * 100)}% · ${suggestions.length || 1} 条建议`)
    } catch (e: any) {
      toastError("标题优化失败: " + (e.message || "未知错误"))
    } finally {
      setTitleLoading(false)
    }
  }, [titleInput])

  const handleThumbnailSuggestions = useCallback(async () => {
    const title = titleInput.trim() || selectedTopic?.title || topics[0]?.title || ""
    if (!title) {
      toastError("请先输入标题或选择一个选题")
      return
    }
    setThumbnailLoading(true)
    try {
      const res = await factoryApi.thumbnailSuggestions({
        title,
        niche: selectedTopic?.tags?.[0] || topics[0]?.tags?.[0] || "general",
      })
      setThumbnailResult(res)
      toastInfo("缩略图建议已生成")
    } catch (e: any) {
      toastError("缩略图建议生成失败: " + (e.message || "未知错误"))
    } finally {
      setThumbnailLoading(false)
    }
  }, [titleInput, selectedTopic, topics])

  const handlePublishTime = useCallback(async () => {
    setPublishLoading(true)
    try {
      const minutes = Math.max(3, Math.ceil(scriptSegments.reduce((sum, segment) => sum + (segment.duration || 0), 0) / 60) || 10)
      const res = await factoryApi.publishTimeOptimization({
        niche: selectedTopic?.tags?.[0] || topics[0]?.tags?.[0] || "general",
        target_region: APP_DEFAULTS.targetRegion,
        video_length_minutes: minutes,
      })
      setPublishResult(res)
      toastInfo("发布时间建议已生成")
    } catch (e: any) {
      toastError("发布时间建议生成失败: " + (e.message || "未知错误"))
    } finally {
      setPublishLoading(false)
    }
  }, [scriptSegments, selectedTopic, topics])

  const handleHumanReview = useCallback(async () => {
    setReviewLoading(true)
    try {
      const res = await factoryApi.humanReviewChecklist({
        niche: selectedTopic?.tags?.[0] || topics[0]?.tags?.[0] || APP_DEFAULTS.niche,
        video_type: APP_DEFAULTS.videoType,
      })
      setReviewResult(res)
      toastInfo("人审与证据链清单已生成")
    } catch (e: any) {
      toastError("人审清单生成失败: " + (e.message || "未知错误"))
    } finally {
      setReviewLoading(false)
    }
  }, [selectedTopic, topics])

  // 分镜生成
  const handleGenerateStoryboard = useCallback(async () => {
    setIsGenerating(true)
    try {
      const res = await factoryApi.generateShotList({
        video_duration_minutes: Math.max(3, Math.ceil(scriptSegments.reduce((sum, segment) => sum + (segment.duration || 0), 0) / 60) || 10),
      })
      const items = res?.shot_list || []
      let currentTime = 0
      const converted: StoryboardItem[] = items.flatMap((section: any, secIdx: number) => {
        const secDuration = section.allocated_duration_sec || 30
        const shots = section.shots || []
        const shotDuration = shots.length > 0 ? Math.floor(secDuration / shots.length) : secDuration
        return shots.map((shot: any, i: number) => {
          const start = currentTime + i * shotDuration
          const end = start + shotDuration
          const formatTime = (s: number) =>
            `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`
          const item: StoryboardItem = {
            id: `sb-${secIdx}-${i}-${Date.now()}`,
            timestamp: `${formatTime(start)}-${formatTime(end)}`,
            scene: section.purpose || "",
            shot: shot.shot || "",
            source: shot.note || section.tips || "实拍",
            type: "实拍",
          }
          return item
        })
      })
      setStoryboardItems(converted.length > 0 ? converted : [])
    } catch (e) {
      toastError("分镜生成失败，请检查网络连接后重试")
      setStoryboardItems([])
    } finally {
      setIsGenerating(false)
    }
  }, [scriptSegments])

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Factory className="h-6 w-6 text-primary" />
          内容工厂
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          AI 辅助内容生产，从选题到分镜一站式完成
        </p>
      </div>

      {/* Tab 切换 */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="w-full sm:w-auto">
          <TabsTrigger value="topics" className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            <span className="hidden sm:inline">选题生成</span>
          </TabsTrigger>
          <TabsTrigger value="script" className="flex items-center gap-2">
            <PenTool className="h-4 w-4" />
            <span className="hidden sm:inline">脚本编辑</span>
          </TabsTrigger>
          <TabsTrigger value="storyboard" className="flex items-center gap-2">
            <Film className="h-4 w-4" />
            <span className="hidden sm:inline">分镜辅助</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="topics" className="mt-6 space-y-6">
          <TopicGenerator
            topics={topics}
            onGenerate={handleGenerateTopics}
            selectedTopicId={selectedTopic?.id || null}
            onSelectTopic={(topic) => {
              setSelectedTopic(topic)
              setTitleInput(topic.title)
              toastInfo(`已选择选题：${topic.title}`)
            }}
            isLoading={isGenerating}
          />
          {/* SEO 关键词 */}
          {(seoKeywords.length > 0 || seoLoading) && (
            <div className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-semibold">SEO 关键词建议</span>
                {seoLoading && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
              </div>
              <div className="flex flex-wrap gap-2">
                {seoKeywords.map((kw, i) => (
                  <span
                    key={i}
                    className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded-full"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="script" className="mt-6 space-y-6">
          {/* 标题优化 */}
          <div className="rounded-lg border p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-semibold">标题优化 + CTR 估算</span>
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                placeholder="输入你的视频标题..."
                className="flex-1 h-9 rounded-md border bg-background px-3 text-sm"
                onKeyDown={(e) => e.key === "Enter" && handleOptimizeTitle()}
              />
              <Button
                size="sm"
                onClick={handleOptimizeTitle}
                disabled={!titleInput.trim() || titleLoading}
              >
                {titleLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : (
                  <Sparkles className="h-4 w-4 mr-1" />
                )}
                优化
              </Button>
            </div>
            {optimizedTitle && (
              <div className="text-sm bg-muted/50 rounded px-3 py-2">
                <span className="text-muted-foreground text-xs">优化建议:</span>
                <p className="font-medium mt-1">{optimizedTitle}</p>
              </div>
            )}
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <ImageIcon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-semibold">缩略图建议</span>
                </div>
                <Button size="sm" variant="outline" onClick={handleThumbnailSuggestions} disabled={thumbnailLoading}>
                  {thumbnailLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
                  生成
                </Button>
              </div>
              {thumbnailResult ? (
                <div className="space-y-2 text-sm">
                  {Array.isArray((thumbnailResult as any).concepts) && (thumbnailResult as any).concepts.slice(0, 2).map((item: any, index: number) => (
                    <div key={index} className="rounded-md bg-muted/40 px-3 py-2">
                      <div className="font-medium">{item.name}</div>
                      <div className="text-xs text-muted-foreground mt-1">{item.layout}</div>
                      <div className="text-xs mt-1">封面字: {item.text_overlay}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">根据标题生成封面构图、文字和 CTR 检查清单。</p>
              )}
            </div>

            <div className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Clock3 className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-semibold">发布时间优化</span>
                </div>
                <Button size="sm" variant="outline" onClick={handlePublishTime} disabled={publishLoading}>
                  {publishLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
                  计算
                </Button>
              </div>
              {publishResult ? (
                <div className="space-y-2 text-sm">
                  <div className="text-xs text-muted-foreground">
                    推荐日期: {Array.isArray((publishResult as any).recommended_days) ? (publishResult as any).recommended_days.join(", ") : "N/A"}
                  </div>
                  {Array.isArray((publishResult as any).time_windows) && (publishResult as any).time_windows.map((item: any, index: number) => (
                    <div key={index} className="rounded-md bg-muted/40 px-3 py-2">
                      <div className="font-medium">{item.window}</div>
                      <div className="text-xs text-muted-foreground mt-1">{item.reason}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">根据领域、视频长度和目标区域给出发布窗口与复盘节奏。</p>
              )}
            </div>

            <div className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-semibold">人审与证据链</span>
                </div>
                <Button size="sm" variant="outline" onClick={handleHumanReview} disabled={reviewLoading}>
                  {reviewLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
                  生成
                </Button>
              </div>
              {reviewResult ? (
                <div className="space-y-2 text-sm">
                  {Array.isArray((reviewResult as any).checklist) && (reviewResult as any).checklist.slice(0, 4).map((item: any, index: number) => (
                    <div key={index} className="rounded-md bg-muted/40 px-3 py-2">
                      <div className="font-medium">{item.stage} · {item.title}</div>
                      <div className="text-xs text-muted-foreground mt-1">{item.evidence}</div>
                    </div>
                  ))}
                  <div className="text-xs text-muted-foreground">
                    证据目录: {(reviewResult as any).recommended_folder || "data/evidence/{video_slug}/"}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">按 KimiAgent 原始蓝图补齐人类决策、素材来源、脚本修订、版权和发布复盘记录。</p>
              )}
            </div>
          </div>
          {selectedTopic && (
            <div className="rounded-lg border bg-primary/5 border-primary/20 px-4 py-3 text-sm">
              <span className="text-muted-foreground">当前选题：</span>
              <span className="font-medium">{selectedTopic.title}</span>
            </div>
          )}
          <ScriptEditor
            segments={scriptSegments}
            onUpdate={setScriptSegments}
            onGenerate={handleGenerateScript}
            isGenerating={isGenerating}
          />
        </TabsContent>

        <TabsContent value="storyboard" className="mt-6">
          <StoryboardHelper
            items={storyboardItems}
            onUpdate={setStoryboardItems}
            onGenerate={handleGenerateStoryboard}
            isGenerating={isGenerating}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
