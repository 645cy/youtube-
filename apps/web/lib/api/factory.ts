import { APP_DEFAULTS } from "../defaults"
import { requestWithRetry } from "./request"

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

export const factoryApi = {
  topicDiscovery: (params?: { niche?: string; channel_id?: number }) =>
    requestWithRetry<Record<string, unknown>>("/api/v1/content-factory/topic-discovery", params ? {
      params: {
        niche: params.niche || "",
        channel_id: params.channel_id,
      },
    } : {}),

  listScriptTemplates: () =>
    requestWithRetry<Record<string, unknown>[]>('/api/v1/content-factory/script-templates'),

  getScriptTemplate: (id: string) =>
    requestWithRetry<Record<string, unknown>>(
      `/api/v1/content-factory/script-templates/${id}`
    ),

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

  getSEOKeywords: (params?: { niche?: string; count?: number }) =>
    requestWithRetry<{ keywords: string[] }>("/api/v1/content-factory/seo-keywords", params ? {
      params: {
        topic: params.niche || "",
        limit: params.count || 10,
      },
    } : {}),

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

  humanReviewChecklist: (params?: { niche?: string; video_type?: string }) =>
    requestWithRetry<Record<string, unknown>>("/api/v1/content-factory/human-review-checklist", {
      params: {
        niche: params?.niche || APP_DEFAULTS.niche,
        video_type: params?.video_type || APP_DEFAULTS.videoType,
      },
    }),
}
