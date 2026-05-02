# TubeFactory OCP - Agent Context

> 本文件由 Kimi Code CLI 生成并维护，用于跨会话快速恢复项目上下文。
> 项目缓存：`./project-context.json`（由 `kimi-scan.py` 生成）

---

## 1. 项目概述

TubeFactory OCP 是一个 YouTube/TikTok 频道分析与内容工厂系统。
- **后端**：FastAPI + SQLAlchemy + APScheduler（Python）
- **前端**：Next.js + React + TypeScript（TSX）
- **核心能力**：频道爬虫、元数据提取、评论情感分析、KPI 仪表板、内容推荐

---

## 2. 技术栈速查

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI (Python) |
| ORM | SQLAlchemy (`Base` 基类) |
| 调度器 | APScheduler (`AsyncIOScheduler`) |
| HTTP 客户端 | httpx |
| 前端框架 | Next.js (App Router) |
| 前端语言 | TypeScript / TSX |
| 元数据提取 | yt-dlp (通过 `AsyncYTDLPMetaExtractor` 封装) |

---

## 3. 核心模块地图

### 🔧 后端核心 (Python)

| 模块 | 关键类 | 职责 |
|------|--------|------|
| 爬虫引擎 | `CrawlerEngine`, `CrawlerPolicy` | 调度与控制爬虫行为 |
| 爬虫任务管理 | `CrawlerTask`, `CrawlerTaskCreate`, `CrawlerTaskRead`, `CrawlerTaskRun`, `CrawlerTaskRunRead`, `CrawlerTaskStatus`, `CrawlerRunStatus` | 爬虫任务的 CRUD 与状态流转 |
| 元数据提取 | `AsyncYTDLPMetaExtractor`, `DualTrackExtractor` | 通过 yt-dlp 抓视频/频道元数据，双轨备份策略 |
| YouTube API | `youtube_api.py` | YouTube Data API 封装 |
| 调度器 | `scheduler.py` | APScheduler 定时任务管理 |
| 评论分析 | `CommentSentimentAnalyzer` | 评论情感分析流水线 |
| 分析流水线 | `AnalysisRequest`, `AnalysisRequestExtended`, `AnalysisResult`, `AnalysisType` | 异步分析任务定义与结果存储 |
| 常青内容 | `EvergreenDetectionResult`, `EvergreenResult` | 常青视频检测与结果存储 |
| API 成本 | `EndpointCost` | 接口调用成本追踪 |
| 数据模型 | `Channel`, `ChannelCreate`, `ChannelRead`, `ChannelUpdate` | 频道 CRUD |
| 指标计算 | `DashboardKPI`, `DashboardKPICalculator`, `AnalysisLog` | 仪表板数据聚合与日志 |
| 退避策略 | `AdaptiveBackoff` | 自适应重试/限流 |

### 🎨 前端核心 (TSX)

| 页面/模块 | 组件 | 职责 |
|-----------|------|------|
| 首页 | `HomePage` | 入口页 |
| 爬虫管理 | `CrawlerPage` | 爬虫任务监控与配置 |
| 工厂 | `FactoryPage`, `ScriptEditor`, `StoryboardHelper`, `TopicGenerator` | 内容生产流水线与脚本编辑 |
| 仪表盘 | `DashboardPage`, `KPICards`, `GrowthChart`, `SearchBox`, `VideoDrawer` | 数据可视化、KPI 展示与视频详情抽屉 |
| 雷达监控 | `RadarPage`, `RadarGrowthChart`, `MonitorList` | 增长雷达与监控列表 |
| 实验室 | `LabPage`, `PathRecommendation`, `UserProfileForm`, `WorkflowDetail` | A/B 测试、路径推荐与实验工作流 |
| 频道卡片 | `ChannelCard`, `ChannelList` | 频道展示与列表 |
| 视频分析 | `VideoAnalysisPanel`, `SentimentBadge` | 视频深度分析与情感标签 |
| 布局骨架 | `ClientLayout`, `LayoutInner`, `BackgroundLayer`, `RootLayout` | 全局布局与加载态 |
| 详情页 | `DetailSection`, `MonetizationDetail`, `EvergreenDetail` | 各类详情展示 |

### 🧩 状态与类型

- `FactoryState`, `AppState`, `IntelState` —— 全局状态结构
- `ChannelCardProps`, `KPICardsProps`, `GrowthChartProps` —— 组件 Props 接口
- `AnalysisResult`, `ChannelRead`, `DashboardKPI` —— 前后端共享 DTO 接口

---

## 4. 项目统计（静态快照）

- **代码文件**：88 个
- **代码行数**：~17,775 行
- **语言分布**：Python 40 | TSX 35 | TypeScript 11 | JavaScript 2
- **类定义**：81 个
- **函数定义**：283 个
- **接口定义**：54 个
- **后端路由**：53 个（分布在 7 个 router 文件）
- **前端 API 端点**：29 个

---

## 4.5 深度分析洞察（由 kimi-deep-scan.py 生成）

### 🔥 复杂度最高的文件（重构风险点）

| 排名 | 文件 | 复杂度 | 行数 | 说明 |
|------|------|--------|------|------|
| 1 | `apps/api/schemas.py` | 99.7 | 437 行 | **30 个 Pydantic 模型**集中定义，项目的核心数据结构 |
| 2 | `apps/api/services/analyzer.py` | 95.2 | 862 行 | **17 类 27 函数**，分析引擎主逻辑，最重的业务文件 |
| 3 | `apps/web/lib/api.ts` | 55.7 | 584 行 | **44 个函数**，前端 API 兼容层（已拆分 channels，其余待拆分） |
| 4 | `packages/db/schema.py` | 53.2 | 409 行 | **14 个 SQLAlchemy 模型**，数据库表定义 |
| 5 | `apps/api/services/youtube_api.py` | 47.7 | 584 行 | YouTube Data API 封装，外部依赖重 |

> ⚠️ `analyzer.py` 和 `schemas.py` 是项目的**心脏**，修改时需格外谨慎。
> ✅ `api.ts` 已重构：频道端点已迁移至 `api/channels.ts`，整体从 841 行降至 584 行。

### 🔌 前后端 API 契约全景

**后端路由分布：**

| Router 文件 | 路由数 | 职责 |
|-------------|--------|------|
| `routers/analysis.py` | 11 | 视频分析流水线（病毒检测、常青分析、情感、变现、缩略图 CTR 等） |
| `routers/channels.py` | 11 | 频道 CRUD、搜索、导入、缩略图修复 |
| `routers/content_factory.py` | 12 | 内容工厂（选题、脚本、分镜、标题优化、SEO、发布时间） |
| `routers/radar.py` | 9 | 雷达监控（创建监控任务、触发、对比、日志） |
| `routers/crawler.py` | 6 | 爬虫任务管理（CRUD + 触发执行） |
| `routers/lab.py` | 5 | 实验室（用户画像、推荐、路径匹配） |
| `routers/videos.py` | 3 | 视频单条管理、批量导入 |

**前端调用端点（`apps/web/lib/api.ts`）：**

覆盖了全部 6 大模块：
- `/api/v1/analysis/*` — 分析流水线
- `/api/v1/channels/*` — 频道管理
- `/api/v1/content-factory/*` — 内容工厂
- `/api/v1/radar/*` — 雷达监控
- `/api/v1/crawler/*` — 爬虫任务
- `/api/v1/lab/*` — 实验室
- `/api/v1/videos/*` — 视频管理

---

## 5. 快速索引：重要文件路径

```
# 后端入口
apps/api/main.py                <- FastAPI 应用入口
apps/api/routers/analysis.py    <- 分析结果 API
apps/api/routers/channels.py    <- 频道管理 API
apps/api/routers/content_factory.py  <- 内容工厂 API
apps/api/routers/crawler.py     <- 爬虫任务 API
apps/api/routers/lab.py         <- 实验室 API
apps/api/routers/radar.py       <- 雷达监控 API
apps/api/routers/videos.py      <- 视频管理 API
apps/api/schemas.py             <- Pydantic 模型
apps/api/services/              <- 业务逻辑
  ├── analyzer.py               <- 分析引擎
  ├── crawler_engine.py         <- 爬虫核心
  ├── recommender.py            <- 推荐系统
  ├── scheduler.py              <- 任务调度
  └── youtube_api.py            <- YouTube API 封装
apps/api/seed/                  <- 数据种子脚本

# 前端入口
apps/web/app/                   <- Next.js App Router
  ├── page.tsx                  <- 首页
  ├── crawler/page.tsx          <- 爬虫管理页
  ├── dashboard/page.tsx        <- 仪表盘
  ├── factory/page.tsx          <- 内容工厂
  ├── lab/page.tsx              <- 实验室
  └── radar/page.tsx            <- 雷达监控
apps/web/components/            <- React 组件
  ├── analysis/                 <- 分析相关组件
  ├── dashboard/                <- 仪表盘组件
  ├── factory/                  <- 工厂组件
  ├── lab/                      <- 实验室组件
  ├── radar/                    <- 雷达组件
  └── ui/                       <- 基础 UI 组件
apps/web/lib/                   <- 工具函数与状态管理
```

---

## 6. Agent 操作指南

### 如何快速恢复上下文
每次进入本项目时，Agent 应：
1. 读取本文件（AGENTS.md）
2. 读取 `./project-context.json` 获取完整符号表和文件列表
3. 优先在已识别的核心类/函数中定位改动点

### 如何更新认知缓存
项目结构发生重大变化后，运行：
```bash
python C:\Users\1\Desktop\kimi-scan.py . ./project-context.json
```
或重新让 Agent 执行扫描并更新本文件。

### 常见任务入口
- **改爬虫逻辑**：搜 `CrawlerEngine`, `CrawlerPolicy`, `DualTrackExtractor`, `CrawlerTask`
- **改分析算法**：搜 `CommentSentimentAnalyzer`, `AnalysisRequest`, `AnalysisRequestExtended`
- **改前端展示**：搜 `DashboardPage`, `KPICards`, `GrowthChart`, `RadarPage`
- **改内容工厂**：搜 `FactoryPage`, `ScriptEditor`, `TopicGenerator`
- **改数据模型**：搜 `Channel`, `ChannelCreate/Read/Update`
- **改常青检测**：搜 `EvergreenDetectionResult`, `EvergreenResult`
- **改 API 成本**：搜 `EndpointCost`

---

## 7. 注意事项

- 后端使用 `apscheduler` 做定时任务，修改爬虫/分析调度逻辑时注意调度器生命周期
- `AsyncYTDLPMetaExtractor` 依赖 yt-dlp，涉及外部网络请求和自适应退避 (`AdaptiveBackoff`)
- 前端大量组件使用 Props 接口驱动，修改组件时注意同步更新对应接口定义
- 项目为 monorepo 结构（`apps/api/` + `apps/web/`）
