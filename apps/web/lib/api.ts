/**
 * 前端 API 客户端 v2 — 兼容性聚合导出（Barrel）
 * 实际实现已迁移到 lib/api/ 子模块。
 */

// CRG: Core API primitives
export { requestWithRetry } from "./api/request"
export { ApiError, TimeoutError } from "./api/types"
export type { HttpMethod, PaginatedResponse, RequestConfig } from "./api/types"

// CRG: Channel endpoints (already split out)
export { channelApi } from "./api/channels"
export type { ChannelRead, ChannelList, ChannelCreate, ThumbnailMaintenanceResult } from "./api/channels"

// CRG: Video endpoints
export { videoApi } from "./api/videos"
export type { VideoRead, VideoList, VideoCreate } from "./api/videos"

// CRG: Monitor types
export type { MonitorJobRead, MonitorWithChannel } from "./api/monitors"

// CRG: Analysis endpoints
export { analysisApi } from "./api/analysis"
export type { AnalysisDashboardKPI, BackendAnalysisResult, GrowthDataPoint } from "./api/analysis"

// CRG: Radar endpoints
export { radarApi } from "./api/radar"

// CRG: Lab endpoints
export { labApi } from "./api/lab"
export type { LabPathResponse, PathRecommendation, WorkflowStep, SubStep, BackendUserProfile } from "./api/lab"

// CRG: Factory endpoints
export { factoryApi } from "./api/factory"
export type { TopicItem, ScriptSegment, StoryboardItem } from "./api/factory"

// CRG: Tags endpoints
export { tagApi } from "./api/tags"
export type { TagItem } from "./api/tags"

// CRG: Health endpoints
export { healthApi } from "./api/health"
export type { YouTubeDiagnostics } from "./api/health"

// CRG: Crawler endpoints
export { crawlerApi } from "./api/crawler"
export type { CrawlerTask, CrawlerTaskRun } from "./api/crawler"

// CRG: Project endpoints
export { projectApi } from "./api/projects"
export type { ContentProject, ContentProjectList } from "./api/projects"
