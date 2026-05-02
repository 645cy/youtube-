/**
 * WorkflowDetail 组件 - OCP变现实验室 Step 3
 * 工作流展开：7步执行指南 + AI工具栈
 * Accordion 手风琴展开，显示子步骤/工具/交付物
 */

"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  ChevronDown,
  CheckCircle2,
  Circle,
  Clock,
  Wrench,
  FileText,
  Download,
  Play,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import type { WorkflowStep } from "@/lib/store"

interface WorkflowDetailProps {
  steps: WorkflowStep[]
  pathName: string
  onStepsChange?: (steps: WorkflowStep[]) => void
  onExport?: () => void
  onStartExecution?: () => void
}

/** 步骤状态图标 */
function StepStatusIcon({ status }: { status: WorkflowStep["status"] }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
    case "active":
      return (
        <Circle className="h-5 w-5 text-primary shrink-0 animate-pulse" />
      )
    default:
      return <Circle className="h-5 w-5 text-muted-foreground shrink-0" />
  }
}

export function WorkflowDetail({
  steps,
  pathName,
  onStepsChange,
  onExport,
  onStartExecution,
}: WorkflowDetailProps) {
  const [openSteps, setOpenSteps] = useState<string[]>(
    steps.length > 0 ? [steps[0].id] : []
  )

  const completedCount = steps.filter((s) => s.status === "completed").length
  const progress = steps.length > 0 ? (completedCount / steps.length) * 100 : 0

  const toggleStep = (stepId: string) => {
    setOpenSteps((prev) =>
      prev.includes(stepId)
        ? prev.filter((id) => id !== stepId)
        : [...prev, stepId]
    )
  }

  const toggleStepStatus = (stepId: string) => {
    const nextSteps = steps.map((step) => {
      if (step.id !== stepId) return step
      const nextStatus: WorkflowStep["status"] = step.status === "completed" ? "active" : "completed"
      return { ...step, status: nextStatus }
    })
    onStepsChange?.(nextSteps)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card>
        {/* 头部 */}
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                <span className="bg-primary text-primary-foreground w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold">
                  3
                </span>
                <span>执行工作流</span>
              </div>
              <CardTitle className="text-lg">{pathName}</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              {onExport && (
                <Button variant="outline" size="sm" onClick={onExport}>
                  <Download className="h-4 w-4 mr-1" />
                  导出PDF
                </Button>
              )}
              {onStartExecution && (
                <Button size="sm" onClick={onStartExecution}>
                  <Play className="h-4 w-4 mr-1" />
                  开始执行
                </Button>
              )}
            </div>
          </div>

          {/* 总进度 */}
          <div className="mt-4 space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>总进度</span>
              <span>
                {completedCount}/{steps.length} 步骤完成
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        </CardHeader>

        <CardContent className="space-y-2">
          {steps.map((step) => {
            const isOpen = openSteps.includes(step.id)

            return (
              <div
                key={step.id}
                className={cn(
                  "rounded-lg border transition-all",
                  step.status === "active" && "ring-1 ring-primary/30",
                  step.status === "completed" && "bg-emerald-500/5"
                )}
              >
                {/* 步骤头部（可点击展开） */}
                <button
                  onClick={() => toggleStep(step.id)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-accent/50 transition-colors rounded-lg"
                >
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation()
                      toggleStepStatus(step.id)
                    }}
                    className="rounded-full hover:scale-105 transition-transform"
                    title={step.status === "completed" ? "标记为进行中" : "标记为已完成"}
                  >
                    <StepStatusIcon status={step.status} />
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        {step.order}. {step.title}
                      </span>
                      {step.status === "completed" && (
                        <Badge
                          variant="outline"
                          className="text-[10px] bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        >
                          已完成
                        </Badge>
                      )}
                      {step.status === "active" && (
                        <Badge
                          variant="outline"
                          className="text-[10px] bg-primary/10 text-primary border-primary/20"
                        >
                          进行中
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {step.substeps.length} 个子步骤 ·
                      {step.substeps.reduce((sum, s) => sum + s.estimatedHours, 0)}
                      小时
                    </span>
                  </div>
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 text-muted-foreground transition-transform shrink-0",
                      isOpen && "rotate-180"
                    )}
                  />
                </button>

                {/* 展开内容 */}
                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 pl-12 space-y-4">
                        {/* 描述 */}
                        <p className="text-sm text-muted-foreground">
                          {step.description}
                        </p>

                        {/* 子步骤 */}
                        <div className="space-y-2">
                          <h5 className="text-xs font-semibold uppercase text-muted-foreground flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            详细步骤
                          </h5>
                          {step.substeps.map((sub, si) => (
                            <div
                              key={sub.id}
                              className="flex items-start gap-2 rounded-md bg-accent/50 p-2.5"
                            >
                              <span className="text-xs font-mono text-muted-foreground shrink-0 w-5">
                                {step.order}.{si + 1}
                              </span>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm">{sub.title}</p>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  {sub.detail}
                                </p>
                              </div>
                              <span className="text-xs text-muted-foreground flex items-center gap-1 shrink-0">
                                <Clock className="h-3 w-3" />
                                {sub.estimatedHours}h
                              </span>
                            </div>
                          ))}
                        </div>

                        {/* 工具 */}
                        {step.tools.length > 0 && (
                          <div>
                            <h5 className="text-xs font-semibold uppercase text-muted-foreground mb-2 flex items-center gap-1">
                              <Wrench className="h-3 w-3" />
                              推荐工具
                            </h5>
                            <div className="flex flex-wrap gap-1.5">
                              {step.tools.map((tool) => (
                                <Badge
                                  key={tool}
                                  variant="outline"
                                  className="text-xs"
                                >
                                  {tool}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* 交付物 */}
                        {step.deliverables.length > 0 && (
                          <div>
                            <h5 className="text-xs font-semibold uppercase text-muted-foreground mb-2 flex items-center gap-1">
                              <CheckCircle2 className="h-3 w-3" />
                              交付物
                            </h5>
                            <div className="flex flex-wrap gap-1.5">
                              {step.deliverables.map((d) => (
                                <Badge
                                  key={d}
                                  variant="outline"
                                  className="text-xs"
                                >
                                  {d}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
        </CardContent>
      </Card>
    </motion.div>
  )
}