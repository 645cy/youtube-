import { requestWithRetry } from "./request"

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

export const labApi = {
  listPaths: () =>
    requestWithRetry<LabPathResponse[]>("/api/v1/lab/paths"),

  getPath: (id: number | string) =>
    requestWithRetry<LabPathResponse>(`/api/v1/lab/paths/${id}`),

  recommend: (profile: BackendUserProfile) =>
    requestWithRetry<{ recommendations: LabPathResponse[]; user_profile_summary: Record<string, unknown>; top_path?: LabPathResponse }>(
      "/api/v1/lab/recommend",
      { method: "POST", body: profile }
    ),

  createProfile: (profile: BackendUserProfile) =>
    requestWithRetry<{ profile_id: string; status: string }>("/api/v1/lab/profile", {
      method: "POST",
      body: profile,
    }),

  quickMatch: (profile: BackendUserProfile) =>
    requestWithRetry<unknown>("/api/v1/lab/quick-match", {
      method: "POST",
      params: profile as unknown as Record<string, unknown>,
    }),
}
