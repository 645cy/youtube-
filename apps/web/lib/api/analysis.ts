import { requestWithRetry } from "./request"

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

export interface GrowthDataPoint {
  date: string
  subscribers: number
  views: number
  videos: number
  [key: string]: string | number
}

export const analysisApi = {
  getDashboardKPI: () =>
    requestWithRetry<AnalysisDashboardKPI>("/api/v1/analysis/dashboard"),

  viralDetection: (youtubeId: string) =>
    requestWithRetry("/api/v1/analysis/viral-detection", {
      method: "POST",
      body: { target_type: "video", target_id: youtubeId, analysis_types: ["viral_detection"] },
    }),

  evergreenDetection: (youtubeId: string) =>
    requestWithRetry("/api/v1/analysis/evergreen", {
      method: "POST",
      body: { target_type: "video", target_id: youtubeId, analysis_types: ["evergreen"] },
    }),

  sentimentAnalysis: (youtubeId: string) =>
    requestWithRetry("/api/v1/analysis/sentiment", {
      method: "POST",
      body: { target_type: "video", target_id: youtubeId, analysis_types: ["sentiment"] },
    }),

  monetizationDetection: (youtubeId: string) =>
    requestWithRetry<BackendAnalysisResult>("/api/v1/analysis/monetization", {
      method: "POST",
      body: { target_type: "video", target_id: youtubeId, analysis_types: ["monetization"] },
    }),

  nicheScoring: (targetId: string, targetType: "niche" | "video" = "niche") =>
    requestWithRetry<BackendAnalysisResult>("/api/v1/analysis/niche-score", {
      method: "POST",
      body: { target_type: targetType, target_id: targetId, analysis_types: ["niche_score"] },
    }),

  fullAnalysis: (youtubeId: string) =>
    requestWithRetry("/api/v1/analysis/full-analysis", {
      method: "POST",
      body: {
        target_type: "video",
        target_id: youtubeId,
        analysis_types: ["viral_detection", "evergreen", "sentiment", "monetization"],
      },
    }),

  getHistory: (params?: { limit?: number; video_id?: number; analysis_type?: string }) =>
    requestWithRetry<Array<{ id: number; video_id: number | null; analysis_type: string; score: number | null; created_at: string }>>("/api/v1/analysis/history", params ? { params } : {}),

  getGrowth: (params?: { days?: number }) =>
    requestWithRetry<GrowthDataPoint[]>("/api/v1/analysis/growth", params ? { params } : {}),

  formatCoefficient: (videoId: string) =>
    requestWithRetry<{
      viral_coefficient: number
      format: string
      recommendation: string
    }>("/api/v1/analysis/format-coefficient", {
      method: "POST",
      params: { video_id: videoId },
    }),

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
