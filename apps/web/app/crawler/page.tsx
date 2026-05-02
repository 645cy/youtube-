"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  DatabaseZap,
  Loader2,
  Play,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  Trash2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { crawlerApi, type CrawlerTask, type CrawlerTaskRun } from "@/lib/api"
import { APP_DEFAULTS, CRAWLER_FREQUENCIES, CRAWLER_TASK_TYPES } from "@/lib/defaults"
import { toastError, toastInfo } from "@/lib/toast"

function statusTone(status?: string | null) {
  if (status === "success") return "border-emerald-500/30 text-emerald-400"
  if (status === "error") return "border-red-500/30 text-red-400"
  if (status === "running") return "border-amber-500/30 text-amber-400"
  return "border-muted-foreground/30 text-muted-foreground"
}

function formatTime(value?: string | null) {
  if (!value) return "未运行"
  return new Date(value).toLocaleString("zh-CN", { hour12: false })
}

export default function CrawlerPage() {
  const [tasks, setTasks] = useState<CrawlerTask[]>([])
  const [runs, setRuns] = useState<CrawlerTaskRun[]>([])
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [triggeringId, setTriggeringId] = useState<number | null>(null)
  const [form, setForm] = useState({
    name: "",
    task_type: APP_DEFAULTS.crawlerTaskType,
    target: "",
    frequency: APP_DEFAULTS.crawlerFrequency,
  })

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) || tasks[0] || null,
    [tasks, selectedTaskId]
  )

  const loadTasks = useCallback(async () => {
    setLoading(true)
    try {
      const data = await crawlerApi.listTasks()
      setTasks(data)
      if (!selectedTaskId && data[0]) setSelectedTaskId(data[0].id)
    } catch (e: any) {
      toastError("加载爬虫任务失败: " + (e.message || "未知错误"))
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [selectedTaskId])

  const loadRuns = useCallback(async (taskId: number | null) => {
    if (!taskId) {
      setRuns([])
      return
    }
    try {
      setRuns(await crawlerApi.listRuns(taskId))
    } catch {
      setRuns([])
    }
  }, [])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  useEffect(() => {
    loadRuns(selectedTask?.id || null)
  }, [selectedTask?.id, loadRuns])

  const createTask = async () => {
    if (!form.name.trim() || !form.target.trim()) {
      toastError("请填写任务名称和目标")
      return
    }
    setCreating(true)
    try {
      const task = await crawlerApi.createTask(form)
      setTasks((prev) => [task, ...prev])
      setSelectedTaskId(task.id)
      setForm({
        name: "",
        task_type: APP_DEFAULTS.crawlerTaskType,
        target: "",
        frequency: APP_DEFAULTS.crawlerFrequency,
      })
      toastInfo("爬虫任务已创建")
    } catch (e: any) {
      toastError("创建任务失败: " + (e.message || "未知错误"))
    } finally {
      setCreating(false)
    }
  }

  const triggerTask = async (task: CrawlerTask) => {
    setTriggeringId(task.id)
    try {
      const run = await crawlerApi.triggerTask(task.id)
      toastInfo(`执行完成，发现 ${run.items_found} 条结果`)
      await loadTasks()
      await loadRuns(task.id)
    } catch (e: any) {
      toastError("执行任务失败: " + (e.message || "未知错误"))
    } finally {
      setTriggeringId(null)
    }
  }

  const deleteTask = async (task: CrawlerTask) => {
    try {
      await crawlerApi.deleteTask(task.id)
      setTasks((prev) => prev.filter((item) => item.id !== task.id))
      if (selectedTaskId === task.id) setSelectedTaskId(null)
      toastInfo("任务已删除")
    } catch (e: any) {
      toastError("删除任务失败: " + (e.message || "未知错误"))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <DatabaseZap className="h-6 w-6 text-primary" />
            爬虫任务中心
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            从 KimiAgent 原始爬虫蓝图迁移来的任务、触发和执行日志工作台
          </p>
        </div>
        <Button variant="outline" onClick={loadTasks} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <RefreshCw className="h-4 w-4 mr-1" />}
          刷新
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Plus className="h-4 w-4" />
              新建任务
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="任务名称，例如：监控 AI 工具频道"
            />
            <select
              value={form.task_type}
              onChange={(e) => setForm((prev) => ({ ...prev, task_type: e.target.value }))}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            >
              {CRAWLER_TASK_TYPES.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
            <Input
              value={form.target}
              onChange={(e) => setForm((prev) => ({ ...prev, target: e.target.value }))}
              placeholder="目标：频道ID、本地频道名或关键词"
            />
            <select
              value={form.frequency}
              onChange={(e) => setForm((prev) => ({ ...prev, frequency: e.target.value }))}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            >
              {CRAWLER_FREQUENCIES.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
            <Button className="w-full" onClick={createTask} disabled={creating}>
              {creating ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
              创建任务
            </Button>
            <div className="rounded-md border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-muted-foreground">
              <ShieldAlert className="h-4 w-4 text-amber-400 mb-2" />
              当前是本地任务中心版本；定时调度和自动重试会在下一步接入。
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Search className="h-4 w-4" />
                任务列表
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="py-8 text-center text-sm text-muted-foreground">正在加载任务...</div>
              ) : tasks.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">暂无任务，先从左侧创建一个。</div>
              ) : (
                <div className="space-y-2">
                  {tasks.map((task) => (
                    <div
                      key={task.id}
                      className={`rounded-lg border p-3 transition-colors cursor-pointer ${selectedTask?.id === task.id ? "bg-primary/5 border-primary/30" : "hover:bg-muted/30"}`}
                      onClick={() => setSelectedTaskId(task.id)}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <div className="font-medium truncate">{task.name}</div>
                            <Badge variant="outline">{CRAWLER_TASK_TYPES.find((t) => t.value === task.task_type)?.label || task.task_type}</Badge>
                            <Badge variant="outline" className={statusTone(task.latest_run_status)}>
                              {task.latest_run_status || "未运行"}
                            </Badge>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1 truncate">
                            目标: {task.target} · 最近运行: {formatTime(task.last_run_at)}
                          </div>
                          {task.latest_run_message && (
                            <div className="text-xs text-muted-foreground mt-1 truncate">{task.latest_run_message}</div>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              triggerTask(task)
                            }}
                            disabled={triggeringId === task.id}
                          >
                            {triggeringId === task.id ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Play className="h-4 w-4 mr-1" />}
                            执行
                          </Button>
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteTask(task)
                            }}
                            title="删除任务"
                          >
                            <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-red-400" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">执行日志</CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedTask ? (
                <div className="py-6 text-center text-sm text-muted-foreground">请选择任务。</div>
              ) : runs.length === 0 ? (
                <div className="py-6 text-center text-sm text-muted-foreground">该任务还没有执行记录。</div>
              ) : (
                <div className="space-y-2">
                  {runs.map((run) => (
                    <div key={run.id} className="rounded-lg border bg-muted/20 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className={statusTone(run.status)}>{run.status}</Badge>
                          <span className="text-xs text-muted-foreground">{run.source_status || "unknown"}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">{formatTime(run.started_at)}</span>
                      </div>
                      <div className="text-sm mt-2">{run.message || "无消息"}</div>
                      <div className="text-xs text-muted-foreground mt-1">结果数量: {run.items_found}</div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
