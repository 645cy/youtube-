# TubeFactory OCP — 代码智能上下文（图谱分析）

> 本文件由 `graphify` (v0.7.7) + `code-review-graph` (v2.3.2) 自动生成并人工精炼，供 AI 助手在分析和优化本项目时参考。
> 项目路径：`D:\Projects\YouTube\tubefactory-ocp`

## 项目规模

- **代码文件**：106 个有效文件（排除 28,000+ node_modules / .next / data 等）
- **Graphify 图谱**：733 节点 / 1,153 边 / 52 社区
- **Code-Review-Graph**：569 节点 / 4,827 边 / 14 社区
- **图谱新鲜度**：基于 commit `8dc8fed8`

## 架构概览（基于知识图谱）

TubeFactory OCP 是 **FastAPI + Next.js + SQLite** 的 YouTube/TikTok 频道分析与内容工厂系统。图谱分析揭示了以下核心架构层：

### 四大核心社区（按规模）

| 社区 | 节点数 | 内聚度 | 位置 | 职责 |
|------|--------|--------|------|------|
| `services-video` | 124 | 0.22 | `apps/api/services/` | 分析算法引擎（情感/ viral / evergreen / 变现 /  niche） |
| `routers-channel` | 112 | 0.07 | `apps/api/routers/` | FastAPI 路由层（REST API 端点） |
| `factory-skeleton` | 70 | 0.16 | `apps/web/components/` | Next.js 前端组件（Dashboard / Factory / Lab） |
| `tests-detector` | 41 | — | `tests/` | 算法单元测试 |

### 系统枢纽（God Nodes）

这些是整个系统的枢纽节点，改动影响面最大：

1. **`cn()`** —— 26 条边
   - 前端工具函数（`apps/web/lib/utils.ts`），被几乎所有前端组件引用
   - **风险**：改动类名合并逻辑会影响全站 UI
2. **`DualTrackExtractor`** —— 21 条边，betweenness 0.150
   - 跨社区桥接节点！连接 crawler / router / analysis / video / sentiment 五大社区
   - 是 yt-dlp + YouTube Data API 的双轨元数据提取器
3. **`PathRecommender`** —— 17 条边
   - 变现路径推荐引擎（Lab 模块核心）
4. **`QuotaManager`** / **`QuotaSnapshot`** —— 17+14 条边
   - YouTube API 配额管理，被 scheduler / youtube_api / test 引用
5. **`CommentSentimentAnalyzer`** —— 15 条边，betweenness 0.086
   - 情感分析是分析流水线与其他模块的桥梁

### 关键依赖关系（Surprising Connections）

图谱分析发现的**非显式依赖**（INFERRED），可能暗示耦合或设计意图：

- `analyzer()` → `CommentSentimentAnalyzer`
  - tests/test_analyzer.py → apps/api/services/analysis/sentiment.py
  - 测试直接调用服务层，缺少抽象层
- `_add_metric_history()` → `MetricHistory`
  - apps/api/routers/channels.py → packages/db/schema.py
  - Router 直接操作 schema，缺少 service 层封装
- `create_channel()` → `Channel`
  - 同样是 Router → Schema 的直接依赖
- `create_video()` → `Video`
  - 同上
- `seed_all()` → `Channel`
  - seed 脚本直接依赖模型

> **模式识别**：Router 层大量直接依赖 `packages/db/schema.py`，而非通过 service/DAO 层。这是典型的 "Fat Router" 反模式信号。

### 执行关键路径（按 criticality）

**后端核心流**：
```
trigger_task (0.60) → detect (0.61) → update_all_channel_stats (0.53)
  → snapshot_metrics (0.51) → batch_analyze (0.50, depth=4)
```

**前端核心流**：
```
DashboardPage (0.68) → FactoryPage (0.68) → LabPage (0.67) → RadarPage (0.67)
```

## 模块详情

### Services 层（`apps/api/services/`）— 内聚度最高

这是项目中最内聚（0.22）且最大的模块（124 节点）。

**分析算法矩阵**：

| 算法 | 类 | 文件 | 输入 | 输出 |
|------|-----|------|------|------|
| Algorithm 1 | `ShortTermViralDetector` | `viral.py` | 视频早期指标 | `ViralDetectionResult` |
| Algorithm 2 | `LongTailEvergreenDetector` | `evergreen.py` | 搜索/竞争指标 | `EvergreenDetectionResult` |
| Algorithm 3 | `CommentSentimentAnalyzer` | `sentiment.py` | 评论文本 | `SentimentResult` |
| Algorithm 7-8 | `VideoFormatAnalyzer` + `ThumbnailCTREstimator` | `format.py` | 标题/缩略图特征 | 格式系数 / CTR 估算 |
| Algorithm 9-10 | `DashboardKPICalculator` + `SchedulerEngine` | `kpi.py` | 多频道数据 | `DashboardKPI` / 调度计划 |
| 变现信号 | `MonetizationSignalDetector` | `monetization.py` | 视频描述/评论 | `MonetizationResult` |
| Niche 评分 | `NicheScoringCard` | `niche.py` | 流量/变现/AI替代性/可复制性 | `NicheScoringResult` |

**注意**：`CommentSentimentAnalyzer` 实现最复杂（181 行），使用关键词情绪词典法（无 NLP 依赖），支持中英文混排、表情符号、否定词反转。

### Routers 层（`apps/api/routers/`）— 最庞大但内聚度低

112 节点，内聚度仅 0.07。说明路由层承载了过多职责。

**关键路由文件**：
- `channels.py` —— 频道 CRUD + 缩略图补全 + 批量发现 + 统计聚合
- `analysis.py` —— 全分析流水线（viral / evergreen / sentiment / monetization / niche / format / KPI）
- `content_factory.py` —— 内容工厂（脚本模板 / 分镜 / 话题生成）
- `crawler.py` —— 爬虫任务触发与管理
- `radar.py` —— 监控雷达
- `lab.py` —— OCP 实验室（用户画像 + 变现路径推荐）

### Frontend 层（`apps/web/components/`）

70 节点，内聚度 0.16。

**核心页面组件**：
- `DashboardPage` —— 频道列表 + 搜索 + 增长图表 + KPI 卡片
- `FactoryPage` —— `ScriptEditor` + `StoryboardHelper` + `TopicGenerator`
- `LabPage` —— `PathRecommendation` + `WorkflowDetail`
- `VideoAnalysisPanel` —— 视频分析结果展示（viral / evergreen / sentiment / monetization）

**前端依赖热点**：
- `cn()` —— 54 条边（来自 `lib/utils.ts`）
- `Button` / `Card` / `CardContent` —— UI 组件高频引用

## 知识缺口（图谱检测）

- **147 个孤立节点**：大量模块级 docstring、配置描述、架构文档节点未被代码引用
  - 例如：`TubeFactory OCP — Architecture Health Scanner`、`Pydantic Settings` 描述、`FastAPI 主应用入口` 描述
  - **建议**：在架构文档中使用 `` `ClassName` `` 显式引用代码实体，帮助静态分析建立边
- **13 个 thin communities**（<3 节点）被省略，可能是边缘工具脚本

## 已配置的代码智能工具

| 工具 | 状态 | 输出位置 | 用途 |
|------|------|----------|------|
| `graphify` | ✅ | `graphify-out/GRAPH_REPORT.md` | 知识图谱、社区检测、God Nodes |
| `code-review-graph` | ✅ | `.code-review-graph/wiki/` | 代码审查图、社区文档 |
| `codegraphcontext` | ❌ | — | KùzuDB Windows 兼容性问题 |
| `Understand-Anything` | ✅ | — | 已构建，需 Claude Code/Cursor 插件加载 |

**重新生成图谱**：
```powershell
graphify update . --force
code-review-graph build
code-review-graph wiki
```

## 已执行的优化（2026-05-06）

### ✅ 优化 1: 提取 ChannelService — 解耦 channels router

**问题**：`routers/channels.py` 536 行，包含大量数据库操作和 YouTube 数据规范化逻辑。

**改动**：
- 新建 `apps/api/services/channel_service.py`（195 行）
- `channels.py` 从 536 行精简到 ~390 行
- 提取内容：
  - `pick_thumbnail` / `missing_thumbnail` / `stat_int` —— 工具函数
  - `build_channel_values` —— YouTube 响应规范化
  - `add_metric_history` —— 指标历史写入
  - `get_channel_by_youtube_id` —— 数据库查询
  - `import_channel_from_youtube` —— 双轨导入
  - `backfill_channel_thumbnails` —— 批量缩略图回填
  - `repair_channel_thumbnails` —— 缩略图修复

**测试**：`tests/test_routers/test_channels.py` 全部通过 ✅

### ✅ 优化 2: 提取 AnalysisHelpers — 解耦 analysis router

**问题**：`routers/analysis.py` 658 行，包含 niche 评分、增长趋势、评论获取等辅助逻辑。

**改动**：
- 新建 `apps/api/services/analysis_helpers.py`（156 行）
- `analysis.py` 从 658 行精简到 552 行
- 提取内容：
  - `resolve_niche_name` / `load_niche_channels` —— Niche 解析
  - `estimate_evergreen_ratio` —— Evergreen 估算
  - `load_metric_growth_rows` / `load_growth_totals` / `build_estimated_growth_rows` —— 增长趋势
  - `fetch_video_comments` —— 远程评论获取

**测试**：`tests/test_analyzer.py` 全部通过 ✅

### ✅ 优化 3: 增强文档减少孤立节点

**问题**：图谱检测到 147 个孤立节点，主要是模块 docstring 缺少代码引用。

**改动**：
- `packages/db/schema.py` —— 在 docstring 中显式列出引用该模块的 8 个上下游模块
- `apps/api/main.py` —— 在 docstring 中显式列出 6 个路由挂载点和依赖模块

### ✅ 优化 4: 提取 VideoService — 解耦 videos router

**问题**：`routers/videos.py` 250 行，包含视频筛选、排序、YouTube 时长解析、批量导入逻辑。

**改动**：
- 新建 `apps/api/services/video_service.py`（142 行）
- `videos.py` 从 250 行精简到 160 行（-36%）
- 提取内容：
  - `build_video_filters` / `apply_video_sorting` —— 筛选与排序
  - `parse_iso8601_duration` / `safe_int_stat` —— YouTube 数据解析
  - `build_video_from_youtube_item` —— item 规范化
  - `import_videos_from_items` —— 批量导入去重

**测试**：语法检查通过，导入测试通过 ✅

### ✅ 优化 5: 提取 SentimentTokenizer — 优化 CommentSentimentAnalyzer

**问题**：`CommentSentimentAnalyzer` 是最大分析类（181 行），分词/评分逻辑与结果聚合耦合。

**改动**：
- 新建 `apps/api/services/analysis/sentiment_tokenizer.py`（142 行）
- `sentiment.py` 从 181 行精简到 85 行（-53%）
- 提取内容：
  - `SentimentTokenizer` —— 分词、词典匹配、否定词/强度修饰符处理
  - `compound_score` / `score_percentages` —— 评分聚合工具函数
- `CommentSentimentAnalyzer` 现在只负责结果聚合（SentimentResult / batch / aggregate）

**测试**：smoke test 通过（"good video" → positive, 0.25）✅

### ✅ 优化 6: 新增 Service 层单元测试

**新增测试文件**：
- `tests/test_channel_service.py` —— 11 个测试（缩略图解析、统计提取、数据规范化）
- `tests/test_video_service.py` —— 13 个测试（ISO8601 解析、筛选排序、YouTube item 转换）
- `tests/test_sentiment_tokenizer.py` —— 19 个测试（分词、评分、否定词、强度修饰符、端到端）
- 修复 `tests/test_routers/test_videos.py` —— 更新导入路径到新 Service 层

**测试结果**：全项目 110 tests passed ✅

## 对 AI 助手的分析建议

1. **修改 `DualTrackExtractor` 时**：这是最高桥接节点（betweenness 0.150），影响 crawler / router / analysis / video / sentiment 五大社区
2. **修改 `cn()` 时**：影响全站前端 UI，需检查所有使用 `cn()` 的组件
3. **优化 Router 层**：`routers-channel` 内聚度仅 0.07，建议将业务逻辑下沉到 service 层，路由层只做参数校验和调用转发
4. **新增分析算法**：继承 `apps/api/services/analysis/common.py` 中的结果模型，参考 `sentiment.py` 的结构
5. **前端组件开发**：关注 `lib/utils.ts` 的 `cn()` 和 `components/ui/` 的通用组件复用
6. **数据库模型改动**：`packages/db/schema.py` 被 router 层大量直接引用，改动时需同步检查所有 router 文件
