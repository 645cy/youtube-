import { requestWithRetry } from "./request"
import type { PaginatedResponse } from "./types"

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
