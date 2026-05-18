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
