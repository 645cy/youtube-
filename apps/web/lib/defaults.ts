export const APP_DEFAULTS = {
  niche: process.env.NEXT_PUBLIC_DEFAULT_NICHE || "",
  targetRegion: process.env.NEXT_PUBLIC_DEFAULT_TARGET_REGION || "global",
  videoType: process.env.NEXT_PUBLIC_DEFAULT_VIDEO_TYPE || "",
  crawlerTaskType: process.env.NEXT_PUBLIC_DEFAULT_CRAWLER_TASK_TYPE || "keyword_search",
  crawlerFrequency: process.env.NEXT_PUBLIC_DEFAULT_CRAWLER_FREQUENCY || "manual",
  monitorFrequency: process.env.NEXT_PUBLIC_DEFAULT_MONITOR_FREQUENCY || "daily",
} as const

export const CRAWLER_TASK_TYPES = [
  { value: "channel_latest", label: "频道最新视频" },
  { value: "channel_stats", label: "频道本地快照" },
  { value: "keyword_search", label: "关键词搜索" },
  { value: "channel_discovery", label: "🎯 频道发现 (潜力新号)" },
] as const

export const CRAWLER_FREQUENCIES = [
  { value: "manual", label: "手动" },
  { value: "hourly", label: "每小时" },
  { value: "daily", label: "每天" },
  { value: "weekly", label: "每周" },
] as const
