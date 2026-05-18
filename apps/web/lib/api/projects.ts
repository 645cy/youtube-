import { requestWithRetry } from "./request"

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
