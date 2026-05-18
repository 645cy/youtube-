import { requestWithRetry } from "./request"

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
    }),
}
