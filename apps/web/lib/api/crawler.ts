import { APP_DEFAULTS } from "../defaults"
import { requestWithRetry } from "./request"

export interface CrawlerTask {
  id: number
  name: string
  task_type: string
  target: string
  frequency: string
  status: string
  config_json?: string | null
  last_run_at?: string | null
  next_run_at?: string | null
  created_at: string
  updated_at: string
  latest_run_status?: string | null
  latest_run_message?: string | null
  latest_items_found: number
}

export interface CrawlerTaskRun {
  id: number
  task_id: number
  status: string
  source_status?: string | null
  message?: string | null
  items_found: number
  result_json?: string | null
  started_at: string
  finished_at?: string | null
}

export const crawlerApi = {
  listTasks: () =>
    requestWithRetry<CrawlerTask[]>("/api/v1/crawler/tasks"),

  createTask: (data: {
    name: string
    task_type: string
    target: string
    frequency?: string
    config?: Record<string, unknown>
  }) =>
    requestWithRetry<CrawlerTask>("/api/v1/crawler/tasks", {
      method: "POST",
      body: {
        name: data.name,
        task_type: data.task_type,
        target: data.target,
        frequency: data.frequency || APP_DEFAULTS.crawlerFrequency,
        config: data.config || {},
      },
    }),

  getTask: (taskId: number) =>
    requestWithRetry<CrawlerTask>(`/api/v1/crawler/tasks/${taskId}`),

  triggerTask: (taskId: number) =>
    requestWithRetry<CrawlerTaskRun>(`/api/v1/crawler/tasks/${taskId}/trigger`, {
      method: "POST",
      timeout: 30000,
      retries: 0,
    }),

  listRuns: (taskId: number) =>
    requestWithRetry<CrawlerTaskRun[]>(`/api/v1/crawler/tasks/${taskId}/runs`),

  deleteTask: (taskId: number) =>
    requestWithRetry<void>(`/api/v1/crawler/tasks/${taskId}`, {
      method: "DELETE",
    }),

  discoveryResults: (params?: {
    keyword?: string | undefined
    min_score?: number | undefined
    max_age_months?: number | undefined
    max_videos?: number | undefined
    sort_by?: "score" | "views" | "subscribers" | "recent" | undefined
    limit?: number | undefined
  }) =>
    requestWithRetry<Array<{
      id: number
      youtube_id: string
      title: string
      thumbnail_url: string | null
      subscriber_count: number | null
      video_count: number | null
      view_count: number | null
      avg_views_per_video: number | null
      discovery_score: number | null
      discovery_keyword: string | null
      channel_age_months: number | null
      discovered_at: string | null
    }>>("/api/v1/crawler/discovery/results", params ? { params } : {}),

  discoveryStats: () =>
    requestWithRetry<{
      total_discovered_channels: number
      avg_score: number
      high_potential_count: number
      top_keywords: Array<{ keyword: string; count: number }>
      channels_by_age_range: Record<string, number>
    }>("/api/v1/crawler/discovery/stats"),

  analytics: (days?: number) =>
    requestWithRetry<{
      days: number
      task_count: number
      total_runs: number
      success_runs: number
      success_rate: number
      total_discovered: number
      avg_score: number
      high_potential_count: number
      run_trend: Array<{ date: string; success: number; error: number }>
      discovery_trend: Array<{ date: string; count: number }>
      score_distribution: Record<string, number>
      top_keywords: Array<{ keyword: string; count: number; avg_score: number }>
    }>(`/api/v1/crawler/analytics?days=${days || 14}`),
}
