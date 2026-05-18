/**
 * Zustand 状态管理
 * 3个 Store：
 * - appStore: 主题、侧边栏状态
 * - intelStore: 频道数据、搜索状态
 * - ocpStore: 用户画像、推荐结果
 */

import { create } from "zustand"


// =============================================================================
// 类型定义
// =============================================================================

/** 情报频道 */
export interface IntelChannel {
  id: string
  name: string
  description: string
  coverUrl: string
  subscriberCount: number
  lastUpdateTime: string
  tags: string[]
  sourceType: "youtube" | "twitter" | "rss" | "custom"
  status: "active" | "paused" | "error"
  metrics: ChannelMetrics
}

/** 频道指标 */
export interface ChannelMetrics {
  totalVideos: number
  avgViews: number
  growthRate: number
  sentimentScore: number
  engagementRate: number
}

/** 视频内容 */
export interface VideoItem {
  id: string
  youtubeId?: string
  channelId: string
  title: string
  thumbnailUrl: string
  duration: string
  publishDate: string
  viewCount: number
  transcript?: string
  summary?: string
}

/** 标签项 */
export interface TagItem {
  name: string
  count: number
  trend: "up" | "down" | "stable"
}

/** KPI 概览 */
export interface DashboardKPI {
  totalChannels: number
  totalVideos: number
  totalViews: number
  todayNewVideos: number
  monitoringStatus: "normal" | "warning" | "error"
  avgGrowthRate: number
}

/** 增长数据点 */
export interface GrowthDataPoint {
  date: string
  [key: string]: string | number
}

/** 工作流步骤 */
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
  estimatedHours: number
}

/** 用户画像表单 */
export interface UserProfile {
  skills: string[]
  availableTime: number     // 每周可用小时
  budget: number            // 可用资金（USD）
  interests: string[]
  equipment: string[]
  experience: string        // 经验级别
  targetPlatforms: string[]
}

/** 推荐路径 */
export interface OCPPath {
  id: string
  name: string
  matchScore: number
  description: string
  estimatedRevenue: string
  timeline: string
  steps: WorkflowStep[]
  tools: string[]
  // 后端返回的额外字段
  matchReasons?: string[]
  estimatedStartupCost?: number
  estimatedMonthlyIncomeLow?: number
  estimatedMonthlyIncomeHigh?: number
  difficulty?: string
  pros?: string[]
  cons?: string[]
}

/** 选题 */
export interface TopicItem {
  id: string
  title: string
  description: string
  searchVolume: string
  competition: string
  score: number
}

// =============================================================================
// 1. App Store - 全局UI状态
// =============================================================================

interface AppState {
  sidebarOpen: boolean
  activeNav: string
  toast: { type: "success" | "error" | "info"; message: string } | null
  isLoading: boolean

  // Actions
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setActiveNav: (nav: string) => void
  showToast: (type: "success" | "error" | "info", message: string) => void
  clearToast: () => void
  setLoading: (loading: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  activeNav: "/dashboard",
  toast: null,
  isLoading: false,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveNav: (nav) => set({ activeNav: nav }),
  showToast: (type, message) => {
    set({ toast: { type, message } })
    // 3秒后自动清除（Zustand 不绑定组件生命周期，简单 timeout 即可）
    setTimeout(() => set({ toast: null }), 3000)
  },
  clearToast: () => set({ toast: null }),
  setLoading: (loading) => set({ isLoading: loading }),
}))

// =============================================================================
// 2. Intel Store - 情报数据状态
// =============================================================================

interface IntelState {
  channels: IntelChannel[]
  selectedChannelId: string | null
  searchQuery: string
  searchFilters: {
    categories: string[]
    status: string[]
    sortBy: string
  }
  tags: TagItem[]
  selectedTags: string[]
  kpis: DashboardKPI | null
  growthData: GrowthDataPoint[]
  isLoading: boolean

  // Actions
  setChannels: (channels: IntelChannel[]) => void
  selectChannel: (id: string | null) => void
  setSearchQuery: (query: string) => void
  setSearchFilters: (filters: Partial<IntelState["searchFilters"]>) => void
  setTags: (tags: TagItem[]) => void
  toggleTag: (tag: string) => void
  setKPIs: (kpis: DashboardKPI) => void
  setGrowthData: (data: GrowthDataPoint[]) => void
  setLoading: (loading: boolean) => void
  filteredChannels: () => IntelChannel[]
}

export const useIntelStore = create<IntelState>((set, get) => ({
  channels: [],
  selectedChannelId: null,
  searchQuery: "",
  searchFilters: {
    categories: [],
    status: [],
    sortBy: "subscribers",
  },
  tags: [],
  selectedTags: [],
  kpis: null,
  growthData: [],
  isLoading: false,

  setChannels: (channels) => set({ channels }),
  selectChannel: (id) => set({ selectedChannelId: id }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSearchFilters: (filters) =>
    set((s) => ({ searchFilters: { ...s.searchFilters, ...filters } })),
  setTags: (tags) => set({ tags }),
  toggleTag: (tag) =>
    set((s) => ({
      selectedTags: s.selectedTags.includes(tag)
        ? s.selectedTags.filter((t) => t !== tag)
        : [...s.selectedTags, tag],
    })),
  setKPIs: (kpis) => set({ kpis }),
  setGrowthData: (data) => set({ growthData: data }),
  setLoading: (loading) => set({ isLoading: loading }),

  filteredChannels: () => {
    const state = get()
    let result = [...state.channels]

    // 搜索词过滤
    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase()
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.description.toLowerCase().includes(q) ||
          c.tags.some((t) => t.toLowerCase().includes(q))
      )
    }

    // 标签过滤
    if (state.selectedTags.length > 0) {
      result = result.filter((c) =>
        state.selectedTags.some((t) => c.tags.includes(t))
      )
    }

    // 分类过滤
    if (state.searchFilters.categories.length > 0) {
      result = result.filter((c) =>
        state.searchFilters.categories.includes(c.sourceType)
      )
    }

    // 排序
    const sort = state.searchFilters.sortBy
    result.sort((a, b) => {
      if (sort === "subscribers") return b.subscriberCount - a.subscriberCount
      if (sort === "growth") return b.metrics.growthRate - a.metrics.growthRate
      if (sort === "videos") return b.metrics.totalVideos - a.metrics.totalVideos
      return 0
    })

    return result
  },
}))

// =============================================================================
// 3. OCP Store - 变现实验室状态
// =============================================================================

interface OCPState {
  userProfile: UserProfile | null
  recommendedPaths: OCPPath[]
  selectedPathId: string | null
  workflowSteps: WorkflowStep[]
  isGenerating: boolean

  // Actions
  setUserProfile: (profile: UserProfile) => void
  setRecommendedPaths: (paths: OCPPath[]) => void
  selectPath: (id: string | null) => void
  setWorkflowSteps: (steps: WorkflowStep[]) => void
  setGenerating: (generating: boolean) => void
  getSelectedPath: () => OCPPath | null
}

export const useOCPStore = create<OCPState>((set, get) => ({
  userProfile: null,
  recommendedPaths: [],
  selectedPathId: null,
  workflowSteps: [],
  isGenerating: false,

  setUserProfile: (profile) => set({ userProfile: profile }),
  setRecommendedPaths: (paths) => set({ recommendedPaths: paths }),
  selectPath: (id) => set({ selectedPathId: id }),
  setWorkflowSteps: (steps) => set({ workflowSteps: steps }),
  setGenerating: (generating) => set({ isGenerating: generating }),

  getSelectedPath: () => {
    const state = get()
    return state.recommendedPaths.find((p) => p.id === state.selectedPathId) || null
  },
}));

// =============================================================================
// 4. Radar Store - 竞品雷达状态
// =============================================================================

interface RadarState {
  monitoredChannels: {
    id: string
    monitorJobId?: number
    name: string
    avatarUrl: string
    subscriberCount: number
    newVideoCount: number
    growthRate: number
    lastChecked: string
  }[]
  selectedChannelId: string | null
  growthData: GrowthDataPoint[]
  isLoading: boolean

  setMonitoredChannels: (channels: RadarState["monitoredChannels"]) => void
  selectChannel: (id: string | null) => void
  setGrowthData: (data: GrowthDataPoint[]) => void
  setLoading: (loading: boolean) => void
}

export const useRadarStore = create<RadarState>((set) => ({
  monitoredChannels: [],
  selectedChannelId: null,
  growthData: [],
  isLoading: false,

  setMonitoredChannels: (channels) => set({ monitoredChannels: channels }),
  selectChannel: (id) => set({ selectedChannelId: id }),
  setGrowthData: (data) => set({ growthData: data }),
  setLoading: (loading) => set({ isLoading: loading }),
}))

// =============================================================================
// 5. Factory Store - 内容工厂状态
// =============================================================================

interface FactoryState {
  activeTab: string
  topics: TopicItem[]
  scriptSegments: { id: string; type: string; content: string }[]
  storyboardItems: { id: string; timestamp: string; scene: string; shot: string; source: string }[]
  isGenerating: boolean

  setActiveTab: (tab: string) => void
  setTopics: (topics: TopicItem[]) => void
  setScriptSegments: (segments: FactoryState["scriptSegments"]) => void
  setStoryboardItems: (items: FactoryState["storyboardItems"]) => void
  setGenerating: (generating: boolean) => void
}

export const useFactoryStore = create<FactoryState>((set) => ({
  activeTab: "topics",
  topics: [],
  scriptSegments: [],
  storyboardItems: [],
  isGenerating: false,

  setActiveTab: (tab) => set({ activeTab: tab }),
  setTopics: (topics) => set({ topics }),
  setScriptSegments: (segments) => set({ scriptSegments: segments }),
  setStoryboardItems: (items) => set({ storyboardItems: items }),
  setGenerating: (generating) => set({ isGenerating: generating }),
}))