import { requestWithRetry } from "./request"
import type { MonitorJobRead, MonitorWithChannel } from "./monitors"

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

  getMonitorLogs: (id: number, limit?: number) =>
    requestWithRetry<Array<{ id: number; analysis_type: string; score: number | null; created_at: string }>>(
      `/api/v1/radar/monitors/${id}/logs`,
      limit ? { params: { limit } } : {}
    ),
}
