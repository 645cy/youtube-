/**
 * 前端 API 客户端 v2
 * 与后端 FastAPI 端点完全对齐
 * 前缀统一: /api/v1
 */

import { APP_DEFAULTS } from "./defaults"
import { requestWithRetry } from "./api/request"
import type { PaginatedResponse } from "./api/types"

// CRG: Keep the legacy public barrel stable while shared API primitives move out.
export { ApiError, TimeoutError } from "./api/types"
export { channelApi } from "./api/channels"
export type { ChannelList, ChannelRead } from "./api/channels"
export type { HttpMethod, PaginatedResponse, RequestConfig } from "./api/types"

// =============================================================================
// 类型定义（与后端 Pydantic Schema 对齐）
// =============================================================================

export interface VideoCreate {
  youtube_id: string
  channel_id: number
  title: string
  description?: string | null
  published_at?: string | null
  duration?: number | null
  view_count?: number | null
  like_count?: number | null
  comment_count?: number | null
  thumbnail_url?: string | null
  tags?: string[] | null
  category_id?: string | null
  language?: string | null
  is_short?: boolean
}

export interface VideoRead {
  id: number
  youtube_id: string
  channel_id: number
  title: string
  description: string | null
  published_at: string | null
  duration: number | null
  view_count: number | null
  like_count: number | null
  comment_count: number | null
  thumbnail_url: string | null
  /** 后端存储为 JSON 字符串，需用 toStringArray 解析 */
  tags: string | null
  category_id: string | null
  language: string | null
  is_short: boolean
  created_at: string
}

export interface VideoList extends PaginatedResponse<VideoRead> {}

export interface MonitorJobRead {
  id: number
  channel_id: number
  job_type: string
  frequency: string
  status: string
  config_json: string | null
  last_run_at: string | null
  next_run_at: string | null
  created_at: string
}

export interface MonitorWithChannel {
  id: number
  channel_id: number
  channel_name: string
  channel_thumbnail: string
  subscriber_count: number
  job_type: string
  frequency: string
  status: string
  last_run_at: string | null
  next_run_at: string | null
  created_at: string
}

export interface AnalysisDashboardKPI {
  total_channels: number
  total_videos: number
  total_views: number
  total_subscribers: number
  active_monitors: number
  recent_analyses: number
  viral_videos_count: number
  evergreen_videos_count: number
  avg_sentiment_score: number
  top_performing_channel: string | null
  monetization_coverage_pct: number
}

export interface BackendAnalysisResult {
  analysis_type: string
  target_id: string
  target_type: string
  status: string
  result: Record<string, unknown>
  score?: number | null
  processing_time_ms?: number | null
}

export interface YouTubeDiagnostics {
  configured: boolean
  key_length: number
  extractor_ready: boolean
  quota: { units_consumed?: number; units_remaining?: number; usage_pct?: number; calls_total?: number }
  live_check: string
  status: string
  next_action: string
  error?: string
}

export interface LabPathResponse {
  path_id: number
  path_name: string
  path_name_en?: string
  category?: string
  description?: string
  match_score?: number
  match_reasons?: string[]
  difficulty?: string
  estimated_startup_cost?: number
  estimated_startup_cost_usd?: number
  estimated_monthly_income_low?: number
  estimated_monthly_income_high?: number
  estimated_monthly_income_low_usd?: number
  estimated_monthly_income_high_usd?: number
  time_to_first_income_months?: number
  required_tools?: string[]
  workflow_steps?: string[]
  pros?: string[]
  cons?: string[]
}

export interface PathRecommendation {
  id: string
  name: string
  description: string
  match_score: number
  estimated_revenue: { min: number; max: number; currency: string }
  timeline: string
  steps: WorkflowStep[]
}

export interface WorkflowStep {
  id: string
  order: number
  title: string
  description: string
  status: "pending" | "active" | "completed"
  substeps: SubStep[]
  tools: string[]
  deliverables: string[]
}

export interface SubStep {
  id: string
  title: string
  detail: string
  estimated_hours: number
}

export interface TopicItem {
  id: string
  title: string
  description: string
  search_volume: string
  competition: string
  score: number
}

export interface ScriptSegment {
  id: string
  type: "hook" | "pain" | "solution" | "demo" | "cta"
  content: string
  speaker_note?: string
}

export interface StoryboardItem {
  id: string
  timestamp: string
  scene: string
  shot: string
  source: string
}

export interface BackendUserProfile {
  skills: Array<{ name: string; level: number }>
  has_camera: boolean
  has_mic: boolean
  editing_experience: number
  weekly_hours: number
  preferred_video_length: string
  can_show_face: boolean
  monthly_budget_usd: number
  willing_to_invest: boolean
  interests: string[]
  native_language: string
  target_audience: string
  has_computer: boolean
  computer_os: string
  has_smartphone: boolean
}

export interface TagItem {
  name: string
  count: number
  trend: "up" | "down" | "stable"
}

export interface GrowthDataPoint {
  date: string
  subscribers: number
  views: number
  videos: number
  [key: string]: string | number
}

// =============================================================================
// 业务 API 封装（与后端端点一一对应）
// =============================================================================

/** 视频 API */
export const videoApi = {
  list: (params?: {
    offset?: number
    limit?: number
    channel_id?: number
    is_short?: boolean
    min_views?: number
  }) => requestWithRetry<VideoList>("/api/v1/videos", params ? { params } : {}),

  get: (id: number) =>
    requestWithRetry<VideoRead>(`/api/v1/videos/${id}`),

  /** 创建视频 */
  create: (data: VideoCreate) =>
    requestWithRetry<VideoRead>("/api/v1/videos", {
      method: "POST",
      body: data,
    }),

  importBatch: (channelId: number, youtubeIds: string[]) =>
    requestWithRetry<{ imported: number; skipped: number; total: number; source: string }>(
      "/api/v1/videos/import-batch",
      { method: "POST", params: { channel_id: channelId }, body: youtubeIds }
    ),

  delete: (id: number) =>
    requestWithRetry<void>(`/api/v1/videos/${id}`, { method: "DELETE" }),
}

/** 分析 API */
export const analysisApi = {
  /** 获取 Dashboard KPI */
  getDashboardKPI: () =>
    requestWithRetry<AnalysisDashboardKPI>("/api/v1/analysis/dashboard"),

  /** 爆款检测 (传入 YouTube 视频 ID，非数据库自增 ID) */
  viralDetection: (youtubeId: string) =>
    requestWithRetry("/api/v1/analysis/viral-detection", {
      method: "POST",
      body: { target_type: "video", target_id: youtubeId, analysis_types: ["viral_detection"] },
    }),

  /** 长尾 Evergreen 检测 */
  evergreenDetection: (youtubeId: string) =>
    requestWithRetry("/api/v1/analysis/evergreen", {
      method: "POST",
      body: { target_type: "video", target_id: youtubeId, analysis_types: ["evergreen"] },
    }),

  /** 评论情感分析 */
  sentimentAnalysis: (youtubeId: string) =>
    requestWithRetry("/api/v1/analysis/sentiment", {
      method: "POST",
      body: { target_type: "video", target_id: youtubeId, analysis_types: ["sentiment"] },
    }),

  /** 变现信号检测 */
  monetizationDetection: (youtubeId: string) =>
    requestWithRetry<BackendAnalysisResult>("/api/v1/analysis/monetization", {
      method: "POST",
      body: { target_type: "video", target_id: youtubeId, analysis_types: ["monetization"] },
    }),

  /** Niche 评分 */
  nicheScoring: (targetId: string, targetType: "niche" | "video" = "niche") =>
    requestWithRetry<BackendAnalysisResult>("/api/v1/analysis/niche-score", {
      method: "POST",
      body: { target_type: targetType, target_id: targetId, analysis_types: ["niche_score"] },
    }), // CRG: Expose the backend niche-score capability that previously had no web API entry.

  /** 全套分析 */
  fullAnalysis: (youtubeId: string) =>
    requestWithRetry("/api/v1/analysis/full-analysis", {
      method: "POST",
      body: {
        target_type: "video",
        target_id: youtubeId,
        analysis_types: ["viral_detection", "evergreen", "sentiment", "monetization"],
      },
    }),

  /** 分析历史 */
  getHistory: (params?: { limit?: number; video_id?: number; analysis_type?: string }) =>
    requestWithRetry<Array<{ id: number; video_id: number | null; analysis_type: string; score: number | null; created_at: string }>>("/api/v1/analysis/history", params ? { params } : {}),

  /** 增长趋势数据 */
  getGrowth: (params?: { days?: number }) =>
    requestWithRetry<GrowthDataPoint[]>("/api/v1/analysis/growth", params ? { params } : {}),

  /** Shorts vs Long-form 爆款系数 */
  formatCoefficient: (videoId: string) =>
    requestWithRetry<{
      viral_coefficient: number
      format: string
      recommendation: string
    }>("/api/v1/analysis/format-coefficient", {
      method: "POST",
      params: { video_id: videoId },
    }),

  /** 缩略图 CTR 估算 */
  thumbnailCTR: (videoId: string, hasFace = true, hasText = true) =>
    requestWithRetry<{
      estimated_ctr: number
      confidence: string
      suggestions: string[]
    }>("/api/v1/analysis/thumbnail-ctr", {
      method: "POST",
      params: { video_id: videoId, has_face: hasFace, has_text: hasText },
    }),
}

/** 竞品雷达 API */
export const radarApi = {
  listMonitors: () =>
    requestWithRetry<MonitorWithChannel[]>("/api/v1/radar/monitors"),

  createMonitor: (data: {
    channel_id: number
    job_type: string
    frequency?: string
  }) =>
    requestWithRetry<MonitorJobRead>("/api/v1/radar/monitors", {
      method: "POST",
      body: data,
    }),

  getMonitor: (id: number) =>
    requestWithRetry<MonitorJobRead>(`/api/v1/radar/monitors/${id}`),

  updateMonitor: (id: number, data: Partial<MonitorJobRead>) =>
    requestWithRetry<MonitorJobRead>(`/api/v1/radar/monitors/${id}`, {
      method: "PUT",
      body: data,
    }),

  deleteMonitor: (id: number) =>
    requestWithRetry<void>(`/api/v1/radar/monitors/${id}`, {
      method: "DELETE",
    }),

  triggerMonitor: (id: number) =>
    requestWithRetry<{ job_id: number; new_videos_found: number; message: string; next_run_at: string | null }>(`/api/v1/radar/monitors/${id}/trigger`, {
      method: "POST",
    }),

  compareChannels: (channelIds: number[]) =>
    requestWithRetry<unknown>("/api/v1/radar/compare", {
      params: { channel_ids: channelIds },
    }),

  /** 获取监控任务执行日志 */
  getMonitorLogs: (id: number, limit?: number) =>
    requestWithRetry<Array<{ id: number; analysis_type: string; score: number | null; created_at: string }>>(
      `/api/v1/radar/monitors/${id}/logs`,
      limit ? { params: { limit } } : {}
    ),
}

/** OCP 实验室 API */
export const labApi = {
  /** 获取所有变现路径 */
  listPaths: () =>
    requestWithRetry<LabPathResponse[]>("/api/v1/lab/paths"),

  /** 获取单条路径详情（含工作流步骤） */
  getPath: (id: number | string) =>
    requestWithRetry<LabPathResponse>(`/api/v1/lab/paths/${id}`),

  /** 提交用户画像，获取推荐 */
  recommend: (profile: BackendUserProfile) =>
    requestWithRetry<{ recommendations: LabPathResponse[]; user_profile_summary: Record<string, unknown>; top_path?: LabPathResponse }>(
      "/api/v1/lab/recommend",
      { method: "POST", body: profile }
    ),

  /** 提交用户画像 */
  createProfile: (profile: BackendUserProfile) =>
    requestWithRetry<{ profile_id: string; status: string }>("/api/v1/lab/profile", {
      method: "POST",
      body: profile,
    }),

  /** 快速匹配 */
  quickMatch: (profile: BackendUserProfile) =>
    requestWithRetry<unknown>("/api/v1/lab/quick-match", {
      method: "POST",
      params: profile as unknown as Record<string, unknown>,
    }),
}

/** 内容工厂 API */
export const factoryApi = {
  /** 选题发现 */
  topicDiscovery: (params?: { niche?: string; channel_id?: number }) =>
    requestWithRetry<Record<string, unknown>>("/api/v1/content-factory/topic-discovery", params ? {
      params: {
        niche: params.niche || "",
        channel_id: params.channel_id,
      },
    } : {}),

  /** 获取脚本模板列表 */
  listScriptTemplates: () =>
    requestWithRetry<Record<string, unknown>[]>("/api/v1/content-factory/script-templates"),

  /** 获取脚本模板详情 */
  getScriptTemplate: (id: string) =>
    requestWithRetry<Record<string, unknown>>(
      `/api/v1/content-factory/script-templates/${id}`
    ),

  /** 生成分镜拍摄清单 */
  generateShotList: (data: {
    template_id?: string
    video_duration_minutes?: number
    camera_count?: number
    has_b_roll?: boolean
  }) =>
    requestWithRetry<{
      template_id: string
      template_name: string
      video_duration_minutes: number
      total_shots: number
      estimated_setup_time_minutes: number
      camera_count: number
      has_b_roll: boolean
      shot_list: Array<{
        section: string
        purpose: string
        allocated_duration_sec: number
        tips: string
        shots: Array<{ shot: string; duration: string; note: string }>
        camera_angles: string[]
      }>
      equipment_checklist: string[]
    }>("/api/v1/content-factory/shot-list", {
      method: "POST",
      params: {
        template_id: data.template_id || "tutorial",
        video_duration_minutes: data.video_duration_minutes || 10,
        camera_count: data.camera_count || 1,
        has_b_roll: data.has_b_roll ?? true,
      },
    }),

  /** 标题优化 + CTR 估算 */
  optimizeTitle: (data: { title: string; niche?: string }) =>
    requestWithRetry<Record<string, unknown>>("/api/v1/content-factory/title-optimization", {
      method: "POST",
      params: {
        title: data.title,
        target_audience: data.niche || "general",
        has_face_in_thumbnail: true,
        has_text_overlay: true,
      },
    }),

  /** SEO 关键词建议 */
  getSEOKeywords: (params?: { niche?: string; count?: number }) =>
    requestWithRetry<{ keywords: string[] }>("/api/v1/content-factory/seo-keywords", params ? {
      params: {
        topic: params.niche || "",
        limit: params.count || 10,
      },
    } : {}),

  /** AI 生成脚本内容 */
  aiScriptGenerate: (data: {
    niche: string
    template_id?: string
    topic?: string
  }) =>
    requestWithRetry<{
      template_id: string
      template_name: string
      segments: Array<{
        id: string
        type: string
        title: string
        content: string
        duration: number
        purpose?: string
        tips?: string
      }>
    }>("/api/v1/content-factory/ai-script", {
      method: "POST",
      params: {
        niche: data.niche,
        template_id: data.template_id || "tutorial",
        topic: data.topic || data.niche,
      },
    }),

  /** 缩略图创意和 CTR 检查 */
  thumbnailSuggestions: (data: {
    title: string
    niche?: string
    has_face?: boolean
    has_text?: boolean
  }) =>
    requestWithRetry<Record<string, unknown>>("/api/v1/content-factory/thumbnail-suggestions", {
      method: "POST",
      params: {
        title: data.title,
        niche: data.niche || "general",
        has_face: data.has_face ?? true,
        has_text: data.has_text ?? true,
      },
    }),

  /** 发布时间优化 */
  publishTimeOptimization: (data: {
    niche?: string
    target_region?: string
    video_length_minutes?: number
  }) =>
    requestWithRetry<Record<string, unknown>>("/api/v1/content-factory/publish-time-optimization", {
      method: "POST",
      params: {
        niche: data.niche || "general",
        target_region: data.target_region || APP_DEFAULTS.targetRegion,
        video_length_minutes: data.video_length_minutes || 10,
      },
    }),

  /** Human review and evidence checklist from the KimiAgent blueprint */
  humanReviewChecklist: (params?: { niche?: string; video_type?: string }) =>
    requestWithRetry<Record<string, unknown>>("/api/v1/content-factory/human-review-checklist", {
      params: {
        niche: params?.niche || APP_DEFAULTS.niche,
        video_type: params?.video_type || APP_DEFAULTS.videoType,
      },
    }),
}

/** 标签 API */
export const tagApi = {
  /** 获取热门标签（从频道 niche 聚合） */
  list: () => requestWithRetry<TagItem[]>("/api/v1/channels/tags"),
}

/** 健康检查 */
export const healthApi = {
  check: () =>
    requestWithRetry<{
      status: string
      env: string
      database: string
      youtube_api: boolean
      quota: Record<string, unknown>
    }>("/health"),
  youtubeDiagnostics: (liveCheck = false) =>
    requestWithRetry<YouTubeDiagnostics>("/api/v1/integrations/youtube/diagnostics", {
      params: { live_check: liveCheck },
    }), // CRG: Route integrations through the shared API client for retry, timeout, and toast consistency.
}

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

  /** 发现结果列表 */
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

  /** 发现统计 */
  discoveryStats: () =>
    requestWithRetry<{
      total_discovered_channels: number
      avg_score: number
      high_potential_count: number
      top_keywords: Array<{ keyword: string; count: number }>
      channels_by_age_range: Record<string, number>
    }>("/api/v1/crawler/discovery/stats"),

  /** 智能分析面板 */
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

// =============================================================================
// 内容项目 API — 串联 Crawler → Factory → Lab 工作流
// =============================================================================

export interface ContentProject {
  id: number
  title: string
  description: string | null
  status: "draft" | "active" | "archived"
  source_crawler_task_id: number | null
  source_run_id: number | null
  script_json: string | null
  storyboard_json: string | null
  analysis_json: string | null
  monetization_path_id: number | null
  created_at: string
  updated_at: string
  source_task_name?: string | null
  source_run_status?: string | null
}

export interface ContentProjectList {
  items: ContentProject[]
  total: number
}

export const projectApi = {
  list: (params?: { status?: string; limit?: number; offset?: number }) =>
    requestWithRetry<ContentProjectList>("/api/v1/projects", {
      params: {
        status: params?.status,
        limit: params?.limit ?? 50,
        offset: params?.offset ?? 0,
      },
    }),

  create: (data: {
    title: string
    description?: string
    source_crawler_task_id?: number
    source_run_id?: number
  }) =>
    requestWithRetry<ContentProject>("/api/v1/projects", {
      method: "POST",
      body: data,
    }),

  get: (projectId: number) =>
    requestWithRetry<ContentProject>(`/api/v1/projects/${projectId}`),

  update: (projectId: number, data: {
    title?: string
    description?: string
    status?: "draft" | "active" | "archived"
    script_json?: string
    storyboard_json?: string
    analysis_json?: string
    monetization_path_id?: number
  }) =>
    requestWithRetry<ContentProject>(`/api/v1/projects/${projectId}`, {
      method: "PUT",
      body: data,
    }),

  delete: (projectId: number) =>
    requestWithRetry<void>(`/api/v1/projects/${projectId}`, {
      method: "DELETE",
    }),
}
