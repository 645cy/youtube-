import type {
  ChannelRead,
  MonitorWithChannel,
  VideoRead,
} from "@/lib/api"
import type {
  IntelChannel,
  OCPPath,
  VideoItem,
  WorkflowStep,
} from "@/lib/store"

const PLACEHOLDER_CHANNEL = "/images/placeholder-channel.svg"
const PLACEHOLDER_VIDEO = "/images/placeholder-video.svg"
const PLACEHOLDER_AVATAR = "/images/avatar-placeholder.svg"

function toNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback
}

function toStringArray(value: unknown): string[] {
  if (Array.isArray(value)) return value.filter((item): item is string => typeof item === "string")
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : []
    } catch {
      return value ? [value] : []
    }
  }
  return []
}

export function mapChannelToIntelChannel(channel: ChannelRead): IntelChannel {
  const videoCount = toNumber(channel.video_count)
  const viewCount = toNumber(channel.view_count)

  return {
    id: String(channel.id),
    name: channel.title || "未命名频道",
    description: channel.description || "",
    subscriberCount: toNumber(channel.subscriber_count),
    metrics: {
      totalVideos: videoCount,
      avgViews: Math.round(viewCount / Math.max(videoCount, 1)),
      growthRate: 0,
      sentimentScore: 75,
      engagementRate: 4.5,
    },
    tags: channel.niche ? [channel.niche] : [],
    sourceType: "youtube",
    status: "active",
    coverUrl: channel.thumbnail_url || PLACEHOLDER_CHANNEL,
    lastUpdateTime: channel.updated_at || new Date().toISOString(),
  }
}

export function mapVideoToVideoItem(video: VideoRead): VideoItem {
  const duration = toNumber(video.duration)
  const item: VideoItem = {
    id: String(video.id),
    channelId: String(video.channel_id),
    title: video.title || "无标题",
    thumbnailUrl: video.thumbnail_url || PLACEHOLDER_VIDEO,
    duration: duration > 0
      ? `${Math.floor(duration / 60)}:${String(duration % 60).padStart(2, "0")}`
      : "",
    publishDate: video.published_at || video.created_at || new Date().toISOString(),
    viewCount: toNumber(video.view_count),
    summary: video.description || toStringArray(video.tags).join("、"),
  }
  if (video.youtube_id) {
    item.youtubeId = video.youtube_id
  }
  return item
}

export function mapMonitorToRadarChannel(monitor: MonitorWithChannel) {
  return {
    id: String(monitor.channel_id),
    monitorJobId: monitor.id,
    name: monitor.channel_name || "未命名",
    avatarUrl: monitor.channel_thumbnail || PLACEHOLDER_AVATAR,
    subscriberCount: toNumber(monitor.subscriber_count),
    newVideoCount: 0,
    growthRate: 0,
    lastChecked: monitor.last_run_at || monitor.created_at || new Date().toISOString(),
  }
}

function createWorkflowSteps(rawSteps: unknown, tools: string[] = []): WorkflowStep[] {
  if (Array.isArray(rawSteps) && rawSteps.length > 0 && typeof rawSteps[0] === "object") {
    return rawSteps.map((step: any, index) => ({
      id: String(step.id ?? `step-${index + 1}`),
      order: toNumber(step.order, index + 1),
      title: step.title || `步骤 ${index + 1}`,
      description: step.description || "",
      status: (step.status || (index === 0 ? "active" : "pending")) as WorkflowStep["status"],
      substeps: Array.isArray(step.substeps)
        ? step.substeps.map((substep: any, subIndex: number) => ({
            id: String(substep.id ?? `step-${index + 1}-sub-${subIndex + 1}`),
            title: substep.title || `子步骤 ${subIndex + 1}`,
            detail: substep.detail || "",
            estimatedHours: toNumber(substep.estimated_hours ?? substep.estimatedHours, 1),
          }))
        : [],
      tools: toStringArray(step.tools).length ? toStringArray(step.tools) : tools,
      deliverables: toStringArray(step.deliverables),
    }))
  }

  return toStringArray(rawSteps).map((description, index) => ({
    id: `step-${index + 1}`,
    order: index + 1,
    title: description.length > 26 ? description.slice(0, 26) : description,
    description,
    status: index === 0 ? "active" : "pending",
    substeps: [
      {
        id: `step-${index + 1}-sub-1`,
        title: "执行并记录结果",
        detail: description,
        estimatedHours: 2,
      },
    ],
    tools,
    deliverables: ["执行记录", "阶段结果"],
  }))
}

export function mapPathToOCPPath(path: any): OCPPath {
  const id = String(path.id ?? path.path_id ?? path.pathId)
  const name = path.name ?? path.path_name ?? path.pathName ?? "未命名路径"
  const tools = toStringArray(path.tools ?? path.required_tools)
  const low = path.estimated_monthly_income_low_usd ?? path.estimated_monthly_income_low
  const high = path.estimated_monthly_income_high_usd ?? path.estimated_monthly_income_high
  const currency = path.estimated_revenue?.currency || "$"

  return {
    id,
    name,
    matchScore: toNumber(path.match_score ?? path.matchScore, 0),
    description: path.description || "",
    estimatedRevenue: path.estimated_revenue
      ? `${currency}${path.estimated_revenue.min} - ${currency}${path.estimated_revenue.max}/月`
      : low !== undefined || high !== undefined
        ? `$${low ?? "?"} - $${high ?? "?"}/月`
        : "未知",
    timeline: path.timeline || (path.time_to_first_income_months ? `${path.time_to_first_income_months} 个月起收` : "未知"),
    tools,
    steps: createWorkflowSteps(path.steps ?? path.workflow_steps, tools),
    matchReasons: toStringArray(path.match_reasons ?? path.matchReasons),
    estimatedStartupCost: path.estimated_startup_cost_usd ?? path.estimated_startup_cost,
    estimatedMonthlyIncomeLow: low,
    estimatedMonthlyIncomeHigh: high,
    difficulty: path.difficulty,
    pros: toStringArray(path.pros),
    cons: toStringArray(path.cons),
  }
}
