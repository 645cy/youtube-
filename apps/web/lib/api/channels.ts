import { requestWithRetry } from "./request"
import type { PaginatedResponse } from "./types"
import type { VideoList } from "../api"

export interface ChannelCreate {
  youtube_id: string
  title: string
  description?: string | null
  subscriber_count?: number | null
  video_count?: number | null
  view_count?: number | null
  thumbnail_url?: string | null
  country?: string | null
  language?: string | null
  niche?: string | null
}

export interface ChannelRead {
  id: number
  youtube_id: string
  title: string
  description: string | null
  subscriber_count: number | null
  video_count: number | null
  view_count: number | null
  thumbnail_url: string | null
  country: string | null
  language: string | null
  niche: string | null
  created_at: string
  updated_at: string
}

export interface ChannelList extends PaginatedResponse<ChannelRead> {}

export interface ThumbnailMaintenanceResult {
  scanned?: number
  checked?: number
  updated: number
  skipped?: number
  failed?: number
}

// CRG: Isolate channel endpoints so api.ts can shrink into a compatibility barrel.
export const channelApi = {
  search: (query: string) => requestWithRetry<ChannelRead>("/api/v1/channels/search", { method: "POST", params: { query } }),
  list: (params?: { offset?: number; limit?: number; search?: string; niche?: string; country?: string; min_subscribers?: number }) =>
    requestWithRetry<ChannelList>("/api/v1/channels", params ? { params } : {}),
  get: (id: number) => requestWithRetry<ChannelRead>(`/api/v1/channels/${id}`),
  update: (id: number, data: Partial<ChannelRead>) =>
    requestWithRetry<ChannelRead>(`/api/v1/channels/${id}`, { method: "PUT", body: data }),
  delete: (id: number) => requestWithRetry<void>(`/api/v1/channels/${id}`, { method: "DELETE" }),
  importYoutube: (youtubeId: string) =>
    requestWithRetry<ChannelRead>("/api/v1/channels/import-youtube", { method: "POST", params: { youtube_id: youtubeId } }),
  getStats: (id: number) =>
    requestWithRetry<{ channel_id: number; channel_title: string; video_count: number; total_views: number; avg_views_per_video: number; subscriber_count: number | null }>(`/api/v1/channels/${id}/stats`),
  getVideos: (channelId: number, params?: { offset?: number; limit?: number }) =>
    requestWithRetry<VideoList>("/api/v1/videos", { params: { ...params, channel_id: channelId } }),
  create: (data: ChannelCreate) =>
    requestWithRetry<ChannelRead>("/api/v1/channels", { method: "POST", body: data }),
  bulkDiscover: (keywords: string[], maxPerKeyword?: number) =>
    requestWithRetry<{ imported: number; skipped: number; failed: number; channels: { youtube_id: string; title: string }[] }>(
      "/api/v1/channels/bulk-discover",
      { method: "POST", body: keywords, ...(maxPerKeyword ? { params: { max_per_keyword: maxPerKeyword } } : {}) }
    ),
  backfillThumbnails: (limit?: number) =>
    requestWithRetry<ThumbnailMaintenanceResult>("/api/v1/channels/backfill-thumbnails", {
      method: "POST",
      ...(limit ? { params: { limit } } : {}),
    }),
  repairThumbnails: (limit?: number) =>
    requestWithRetry<ThumbnailMaintenanceResult>("/api/v1/channels/repair-thumbnails", {
      method: "POST",
      ...(limit ? { params: { limit } } : {}),
    }),
  // CRG: Expose backend thumbnail maintenance endpoints so data repair is usable from the web layer.
}
