/**
 * OCP变现实验室页面 - /lab
 * 三步交互流程：
 * - Step 1: 用户画像表单（技能/时间/资金/兴趣/设备）
 * - Step 2: 推荐结果卡片（最多20条路径匹配排序）
 * - Step 3: 工作流展开（7步执行指南 + AI工具栈）
 */

"use client"

import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FlaskConical,
  ChevronRight,
  ArrowLeft,
  Target,
} from "lucide-react"
import { UserProfileForm, type UserProfileFormData } from "@/components/lab/UserProfileForm"
import { PathRecommendation } from "@/components/lab/PathRecommendation"
import { WorkflowDetail } from "@/components/lab/WorkflowDetail"
import { useOCPStore, type OCPPath } from "@/lib/store"
import { labApi } from "@/lib/api"
import { mapPathToOCPPath } from "@/lib/mappers"
import { toastInfo, toastError } from "@/lib/toast"

// =============================================================================
// 步骤枚举
// =============================================================================

type Step = 1 | 2 | 3

export default function LabPage() {
  const [currentStep, setCurrentStep] = useState<Step>(1)
  const [generating, setGenerating] = useState(false)
  const [allPathsLoading, setAllPathsLoading] = useState(false)

  const {
    recommendedPaths,
    selectedPathId,
    setUserProfile,
    setRecommendedPaths,
    selectPath,
  } = useOCPStore()

  const updateSelectedPathSteps = useCallback((steps: typeof recommendedPaths[number]["steps"]) => {
    if (!selectedPathId) return
    const nextPaths = recommendedPaths.map((path) =>
      path.id === selectedPathId ? { ...path, steps } : path
    )
    setRecommendedPaths(nextPaths)
    if (typeof window !== "undefined") {
      window.localStorage.setItem(`tubefactory:workflow:${selectedPathId}`, JSON.stringify(steps))
    }
  }, [recommendedPaths, selectedPathId, setRecommendedPaths])

  // Step 1: 提交画像
  const handleProfileSubmit = useCallback(
    async (data: UserProfileFormData) => {
      setUserProfile(data as never)
      setGenerating(true)

      try {
        // 将前端表单数据映射到后端 UserProfile schema
        const experienceMap: Record<string, number> = {
          beginner: 2,
          intermediate: 5,
          advanced: 8,
          expert: 10,
        }
        const equipment = data.equipment || []
        const res = await labApi.recommend({
          skills: (data.skills || []).map((name: string) => ({ name, level: 5 })),
          has_camera: equipment.some((e: string) => e.includes("相机")),
          has_mic: equipment.some((e: string) => e.includes("麦克风")),
          editing_experience: experienceMap[data.experience || "beginner"] || 2,
          weekly_hours: data.availableTime || 10,
          preferred_video_length: "medium",
          can_show_face: true,
          monthly_budget_usd: data.budget || 0,
          willing_to_invest: (data.budget || 0) > 0,
          interests: data.interests || [],
          native_language: "zh",
          target_audience: "global",
          has_computer: equipment.some((e: string) => e.includes("电脑")),
          computer_os: equipment.find((e: string) => e.includes("Mac")) ? "mac" : "windows",
          has_smartphone: equipment.some((e: string) => e.includes("手机")),
        })

        const items = res?.recommendations || []
        setRecommendedPaths(items.map(mapPathToOCPPath))
        if (items.length === 0) {
          toastInfo("暂未匹配到推荐路径，请调整画像或浏览全部路径")
        }
      } catch (e) {
        setRecommendedPaths([])
      } finally {
        setGenerating(false)
        setCurrentStep(2)
      }
    },
    [setUserProfile, setRecommendedPaths]
  )

  // Step 2: 选择路径
  const handleSelectPath = useCallback(
    (pathId: string) => {
      const path = recommendedPaths.find((item) => item.id === pathId)
      if (path && typeof window !== "undefined") {
        const saved = window.localStorage.getItem(`tubefactory:workflow:${pathId}`)
        if (saved) {
          try {
            const steps = JSON.parse(saved)
            setRecommendedPaths(recommendedPaths.map((item) => item.id === pathId ? { ...item, steps } : item))
          } catch {
            window.localStorage.removeItem(`tubefactory:workflow:${pathId}`)
          }
        }
      }
      selectPath(pathId)
      setCurrentStep(3)
    },
    [selectPath, recommendedPaths, setRecommendedPaths]
  )

  // 加载全部变现路径
  const handleLoadAllPaths = useCallback(async () => {
    setAllPathsLoading(true)
    try {
      const paths = await labApi.listPaths()
      const converted: OCPPath[] = (paths || []).map(mapPathToOCPPath)
      setRecommendedPaths(converted)
    } catch (e) {
      toastError("加载变现路径失败")
    } finally {
      setAllPathsLoading(false)
    }
  }, [setRecommendedPaths])

  // Step 3: 返回
  const handleBack = useCallback(() => {
    if (currentStep === 3) {
      setCurrentStep(2)
      selectPath(null)
    } else if (currentStep === 2) {
      setCurrentStep(1)
    }
  }, [currentStep, selectPath])

  const selectedPath = recommendedPaths.find((p) => p.id === selectedPathId)

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* 页面标题 */}
      <div className="flex items-center gap-4">
        {currentStep > 1 && (
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            返回
          </Button>
        )}
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <FlaskConical className="h-6 w-6 text-primary" />
            OCP 变现实验室
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            基于 AI 分析，为你规划最佳的内容变现路径
          </p>
        </div>
      </div>

      {/* 步骤指示器 */}
      <div className="flex items-center gap-4 px-4 py-3 rounded-lg bg-card border">
        <StepIndicator step={1} current={currentStep} label="填写画像" />
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
        <StepIndicator step={2} current={currentStep} label="查看推荐" />
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
        <StepIndicator step={3} current={currentStep} label="执行工作流" />
      </div>

      {/* 内容区 */}
      <AnimatePresence mode="wait">
        {currentStep === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            <Card className="p-6">
              <div className="mb-6">
                <h2 className="text-lg font-semibold mb-2">
                  让我们了解你
                </h2>
                <p className="text-sm text-muted-foreground">
                  填写以下信息，AI 将为你匹配最适合的变现路径
                </p>
              </div>
              <UserProfileForm
                onSubmit={handleProfileSubmit}
                isLoading={generating}
              />
            </Card>
          </motion.div>
        )}

        {currentStep === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center gap-2 mb-4">
              <Button
                variant="outline"
                size="sm"
                onClick={handleLoadAllPaths}
                disabled={allPathsLoading}
              >
                {allPathsLoading ? "加载中..." : "浏览全部路径"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentStep(1)}
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                重新填写画像
              </Button>
            </div>
            {recommendedPaths.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Target className="h-12 w-12 mx-auto text-muted-foreground/50 mb-3" />
                <p className="text-muted-foreground">未生成推荐方案</p>
                <p className="text-xs mt-1">请检查网络连接后重试，或浏览全部路径</p>
              </div>
            ) : (
              <PathRecommendation
                paths={recommendedPaths}
                onSelectPath={handleSelectPath}
              />
            )}
          </motion.div>
        )}

        {currentStep === 3 && selectedPath && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            <WorkflowDetail
              steps={selectedPath.steps}
              pathName={selectedPath.name}
              onStepsChange={updateSelectedPathSteps}
              onExport={() => {
                if (!selectedPath) return
                const stepLines = (selectedPath.steps || [])
                  .map((step) => {
                    const substeps = (step.substeps || [])
                      .map((substep) => `   - ${substep.title}: ${substep.detail}（约 ${substep.estimatedHours} 小时）`)
                      .join("\n")
                    const tools = step.tools?.length ? `\n   工具: ${step.tools.join("、")}` : ""
                    const deliverables = step.deliverables?.length
                      ? `\n   交付物: ${step.deliverables.join("、")}`
                      : ""
                    return `${step.order}. ${step.title}\n   ${step.description}${tools}${deliverables}${substeps ? `\n${substeps}` : ""}`
                  })
                  .join("\n\n")

                const content = `# ${selectedPath.name} - 变现路径方案

## 匹配分数
${selectedPath.matchScore}/100

## 路径说明
${selectedPath.description || "暂无说明"}

## 预估数据
- 月收入区间: ${selectedPath.estimatedRevenue || "未知"}
- 执行周期: ${selectedPath.timeline || "未知"}
- 难度: ${selectedPath.difficulty || "未知"}

## 推荐原因
${(selectedPath.matchReasons?.length ? selectedPath.matchReasons : ["该路径与当前画像匹配度较高"]).map((reason) => `- ${reason}`).join("\n")}

## 执行步骤
${stepLines || "暂无执行步骤"}

## 推荐工具
${(selectedPath.tools || []).map((tool) => `- ${tool}`).join("\n") || "暂无推荐工具"}

## 优缺点
优势:
${(selectedPath.pros || []).map((p: string) => `- ${p}`).join("\n") || "- 暂无"}

劣势:
${(selectedPath.cons || []).map((c: string) => `- ${c}`).join("\n") || "- 暂无"}

---
生成时间: ${new Date().toLocaleString()}
TubeFactory OCP Lab
`
                const blob = new Blob([content], { type: "text/markdown" })
                const url = URL.createObjectURL(blob)
                const a = document.createElement("a")
                a.href = url
                a.download = `${selectedPath.name.replace(/\s+/g, "_")}_方案.md`
                a.click()
                URL.revokeObjectURL(url)
                toastInfo("方案已导出为 Markdown 文件")
              }}
              onStartExecution={() => {
                const nextSteps = selectedPath.steps.map((step, index) => ({
                  ...step,
                  status: index === 0 ? "active" as const : "pending" as const,
                }))
                updateSelectedPathSteps(nextSteps)
                toastInfo("已进入执行模式，点击步骤图标可标记完成，进度会保存在本机")
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/** 步骤指示器 */
function StepIndicator({
  step,
  current,
  label,
}: {
  step: number
  current: number
  label: string
}) {
  const isActive = step === current
  const isCompleted = step < current

  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors",
          isActive && "bg-primary text-primary-foreground",
          isCompleted && "bg-emerald-500 text-white",
          !isActive && !isCompleted && "bg-muted text-muted-foreground"
        )}
      >
        {isCompleted ? "✓" : step}
      </span>
      <span
        className={cn(
          "text-sm transition-colors",
          isActive ? "text-foreground font-medium" : "text-muted-foreground"
        )}
      >
        {label}
      </span>
    </div>
  )
}

// 需要引入的组件和类型
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"