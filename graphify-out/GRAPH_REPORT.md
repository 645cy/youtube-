# Graph Report - tubefactory-ocp  (2026-05-07)

## Corpus Check
- 117 files · ~64,839 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 938 nodes · 1477 edges · 63 communities (49 shown, 14 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 257 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8dc8fed8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 53|Community 53]]

## God Nodes (most connected - your core abstractions)
1. `cn()` - 28 edges
2. `SentimentTokenizer` - 27 edges
3. `DualTrackExtractor` - 26 edges
4. `PathRecommender` - 17 edges
5. `QuotaManager` - 17 edges
6. `CommentSentimentAnalyzer` - 17 edges
7. `toastError()` - 15 edges
8. `QuotaSnapshot` - 14 edges
9. `Badge()` - 14 edges
10. `Video` - 14 edges

## Surprising Connections (you probably didn't know these)
- `analyzer()` --calls--> `CommentSentimentAnalyzer`  [INFERRED]
  tests/test_analyzer.py → apps/api/services/analysis/sentiment.py
- `sentiment_analysis()` --calls--> `AnalysisLog`  [INFERRED]
  apps/api/routers/analysis.py → packages/db/schema.py
- `niche_scoring()` --calls--> `AnalysisLog`  [INFERRED]
  apps/api/routers/analysis.py → packages/db/schema.py
- `create_channel()` --calls--> `Channel`  [INFERRED]
  apps/api/routers/channels.py → packages/db/schema.py
- `create_task()` --calls--> `CrawlerTask`  [INFERRED]
  apps/api/routers/crawler.py → packages/db/schema.py

## Communities (63 total, 14 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (44): Enum, AsyncYTDLPMetaExtractor, EndpointCost, _get_blocking_executor(), _normalize(), QuotaManager, QuotaSnapshot, YouTube Data API v3 瀹㈡埛绔?+ yt-dlp 闄嶇骇鍙岃建鏂规  鏍稿績璁捐:   1. YouTubeAPIClient: 瀹樻柟 (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (33): CommentSentimentAnalyzer, _compound_score(), Algorithm 3: 评论情感分析 — 关键词情绪词典法 (零 NLP 依赖).  被以下模块使用:   - apps.api.routers.analys, 评论情感分析器 — 关键词情绪词典法 (零 NLP 依赖).      支持中英文混合, 表情符号识别, 否定词反转, 强度修饰符.     Time: O(m, 评论情感分析器 — 关键词情绪词典法 (零 NLP 依赖).      支持中英文混合, 表情符号识别, 否定词反转, 强度修饰符.     Time: O(m, 分析单条评论的情感.          Args:             comment_id: 评论唯一标识.             text: 评论原文, 批量分析评论列表.          Args:             comments: [(comment_id, text), ...], 聚合多条评论的分析结果.          Returns:             包含 total_comments、positive_pct、negati (+25 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (49): AsyncAttrs, AnalysisType, Base, CrawlerRunStatus, CrawlerTask, CrawlerTaskRun, CrawlerTaskStatus, JobType (+41 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (32): EvergreenDetectionResult, KeywordMetrics, MonetizationResult, NicheMetrics, NicheScoringResult, Shared data models for analysis algorithms., 视频早期指标数据类 (Algorithm 1 输入)., 关键词/主题指标 (Algorithm 2 输入). (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (51): BaseModel, _convert_profile(), get_path_detail(), get_recommendations(), _get_recommender(), _infer_difficulty(), list_paths(), quick_match() (+43 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (35): YouTube 视频信息表.      设计决策:       - youtube_id: 11 字符公开视频 ID       - channel_i, YouTube 视频信息表.      设计决策:       - youtube_id: 11 字符公开视频 ID       - channel_id ->, Video, create_video(), import_videos_batch(), list_videos(), _order_video_query(), _parse_youtube_duration() (+27 more)

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (49): Channel, MetricHistory, YouTube 频道信息表.      设计决策:       - youtube_id: YouTube 公开频道 ID (如 UCxxxx), YouTube 频道信息表.      设计决策:       - youtube_id: YouTube 公开频道 ID (如 UCxxxx)       -, 频道/视频指标历史记录表 (时间序列数据).      每条记录是一个时间点的指标快照。     单表 + 索引设计，支撑百万级记录。, 频道/视频指标历史记录表 (时间序列数据).      每条记录是一个时间点的指标快照。     单表 + 索引设计，支撑百万级记录。, _add_metric_history(), backfill_thumbnails() (+41 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (47): health_check(), health_check_v1(), _initialize_database(), _initialize_youtube_extractor(), lifespan(), _preload_recommender(), FastAPI 主应用入口  架构概览:   - Lifespan 上下文管理器 (`_initialize_database`, `_seed_develop, 服务健康检查端点.      返回:       - status: ok/error       - env: 当前环境       - youtube_ap (+39 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (24): analyzer(), detector(), Tests for core analysis algorithms., Tests for Algorithm 3: comment sentiment analysis., Empty comment should be neutral., Positive English words should yield positive sentiment., Negative English words should yield negative sentiment., Positive Chinese words should yield positive sentiment.          Note: tokenizer (+16 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (34): ai_script_generate(), _build_pattern_keywords(), _build_script_replacements(), _build_script_segment(), _build_section_shot_plan(), _build_section_shots(), _build_template_keywords(), _calculate_section_duration() (+26 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (29): create_task(), _execute_channel_latest(), _execute_channel_stats(), _execute_keyword_search(), _execute_task(), get_task(), list_tasks(), _resolve_channel() (+21 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (16): backfill_channel_thumbnails(), build_channel_values(), missing_thumbnail(), pick_thumbnail(), 频道业务服务层 — 封装 Channel 的数据库操作与 YouTube 数据同步.  被以下模块使用:   - apps.api.routers.channe, 批量回查 YouTube 并更新频道缩略图.      Returns:         {"updated": int, "skipped": int}, 逐个频道回查缩略图 (比批量更容错).      Returns:         {"checked": int, "updated": int, "fail, 从 YouTube snippet 中按质量优先级提取缩略图 URL. (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (13): load_default_paths(), MonetizationPath, PathMatchResult, PathRecommender, 用户画像匹配引擎 — OCP 实验室核心  功能:   1. 用户画像模型 (五维: 技能/时间/资金/兴趣/设备)   2. 20 条变现路径匹配算法 (加权, 用户画像-变现路径匹配引擎.      匹配算法:       Score = sum(weight_i * factor_i) * confidence_ad, 时间匹配度 (0-100).          用户时间 >= 路径需求 -> 100 分         用户时间 < 路径需求 -> 按比例递减, OCP 实验室用户画像 — 五维评估模型. (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (3): ChannelCard(), cn(), formatCompactNumber()

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (16): AnalysisLog, 分析任务执行日志表.      append-only 设计，记录每次分析的结果。     result_json 存储灵活的 JSON 分析结果。, 分析任务执行日志表.      append-only 设计，记录每次分析的结果。     result_json 存储灵活的 JSON 分析结果。, evergreen_detection(), full_analysis(), monetization_detection(), Algorithm 2: evergreen detection., Algorithm 2: evergreen detection. (+8 more)

### Community 15 - "Community 15"
Cohesion: 0.26
Nodes (9): createTask(), deleteTask(), triggerTask(), runThumbnailMaintenance(), toast(), toastError(), toastInfo(), toastSuccess() (+1 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (3): debounce(), formatDate(), formatNumber()

### Community 17 - "Community 17"
Cohesion: 0.22
Nodes (7): buildUrl(), requestFresh(), requestWithRetry(), showToast(), ApiError, TimeoutError, sleep()

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (4): run(), UserProfileForm(), WorkflowDetail(), Badge()

### Community 19 - "Community 19"
Cohesion: 0.36
Nodes (9): get_channel_details(), get_channel_videos(), get_video_stats(), import_channel(), import_videos_for_channel(), main(), r""" 批量导入真实高价值频道 — AI/变现/副业领域  用法 (在本机运行):     cd D:\Projects\YouTube\tubefactor, 用 YouTube Data API 搜索视频. (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.22
Nodes (8): build_estimated_growth_rows(), load_growth_totals(), load_metric_growth_rows(), load_niche_channels(), Analysis Router 辅助函数 — 提取自 analysis.py 以减少 Router 层复杂度.  被以下模块使用:   - apps.api.r, 基于当前总量生成平滑的估算增长趋势（当历史数据不足时回退使用）., 加载指定 niche 的频道列表；若无匹配则返回全部频道., 从 MetricHistory 加载按日聚合的订阅/观看增长数据.

### Community 22 - "Community 22"
Cohesion: 0.25
Nodes (7): estimate(), Algorithm 7-8: 视频格式分析与缩略图 CTR 估算., Algorithm 8: 缩略图 CTR 启发式估算.      基于标题和缩略图特征进行启发式评分 (无需实际 A/B 测试数据)., Algorithm 7: Shorts vs Long-form 爆款系数差异模型., ThumbnailCTREstimator, _tips(), VideoFormatAnalyzer

### Community 23 - "Community 23"
Cohesion: 0.47
Nodes (7): createWorkflowSteps(), mapChannelToIntelChannel(), mapMonitorToRadarChannel(), mapPathToOCPPath(), mapVideoToVideoItem(), toNumber(), toStringArray()

### Community 25 - "Community 25"
Cohesion: 0.36
Nodes (7): _build_estimated_growth_rows(), get_growth_data(), _load_growth_totals(), _load_metric_growth_rows(), Analysis router endpoints for video, niche, sentiment, KPI, and growth analysis., Return growth trend rows for the requested number of days.      Prefers stored, Return growth trend rows for the requested number of days.      Prefers stored m

### Community 26 - "Community 26"
Cohesion: 0.25
Nodes (8): _load_niche_channels(), _niche_result_payload(), niche_scoring(), Algorithm 5: niche scoring., Algorithm 5: niche scoring., _resolve_niche_name(), 将分析请求的目标解析为 niche 名称字符串., resolve_niche_name()

### Community 27 - "Community 27"
Cohesion: 0.29
Nodes (7): _fetch_video_comments(), Algorithm 3: comment sentiment analysis.      Uses provided comments or explicit, Algorithm 3: comment sentiment analysis.      Uses provided comments or explic, Fetch YouTube comments through the configured extractor.      Returns:, sentiment_analysis(), fetch_video_comments(), 通过 DualTrackExtractor 获取 YouTube 视频评论.      Raises:         RuntimeError: 当远程评论获

### Community 31 - "Community 31"
Cohesion: 0.4
Nodes (3): Pydantic Settings - 环境变量配置管理 统一管理数据库、YouTube API、爬虫、日志等配置, Settings, BaseSettings

### Community 32 - "Community 32"
Cohesion: 0.4
Nodes (5): _build_niche_metrics(), _estimate_evergreen_ratio(), 构建 NicheMetrics（保留在 Router 中因为依赖 NicheMetrics 数据类）., estimate_evergreen_ratio(), 基于频道视频标题关键词估算 evergreen 内容比例.

### Community 39 - "Community 39"
Cohesion: 0.83
Nodes (3): run_migrations_offline(), run_migrations_online(), _sync_database_url()

### Community 41 - "Community 41"
Cohesion: 0.67
Nodes (3): get_analysis_history(), Return recent analysis history rows., Return recent analysis history rows.

### Community 42 - "Community 42"
Cohesion: 0.67
Nodes (3): get_dashboard_kpi(), Algorithm 9: dashboard KPI aggregation., Algorithm 9: dashboard KPI aggregation.

### Community 43 - "Community 43"
Cohesion: 0.67
Nodes (3): calculate_format_coefficient(), Algorithm 7: video format analysis., Algorithm 7: video format analysis.

### Community 44 - "Community 44"
Cohesion: 0.67
Nodes (3): estimate_thumbnail_ctr(), Algorithm 8: thumbnail CTR estimation., Algorithm 8: thumbnail CTR estimation.

## Knowledge Gaps
- **239 isolated node(s):** `TubeFactory OCP — Architecture Health Scanner.`, `Find public functions with no project-wide name or attribute reference.`, `Pydantic Settings - 环境变量配置管理 统一管理数据库、YouTube API、爬虫、日志等配置`, `FastAPI 主应用入口  架构概览:   - Lifespan 上下文管理器 (`_initialize_database`, `_seed_develop`, `服务健康检查端点.      返回:       - status: ok/error       - env: 当前环境       - youtube_ap` (+234 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DualTrackExtractor` connect `Community 10` to `Community 0`, `Community 2`, `Community 5`, `Community 6`, `Community 7`, `Community 27`?**
  _High betweenness centrality (0.196) - this node is a cross-community bridge._
- **Why does `CommentSentimentAnalyzer` connect `Community 1` to `Community 27`, `Community 8`, `Community 3`, `Community 7`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Why does `scrape_video_comments()` connect `Community 7` to `Community 1`, `Community 10`, `Community 2`, `Community 14`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `str` (e.g. with `parse_file()` and `build_import_graph()`) actually correct?**
  _`str` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `SentimentTokenizer` (e.g. with `CommentSentimentAnalyzer` and `TestSentimentTokenizerTokenize`) actually correct?**
  _`SentimentTokenizer` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `DualTrackExtractor` (e.g. with `_initialize_youtube_extractor()` and `search_channels()`) actually correct?**
  _`DualTrackExtractor` has 18 INFERRED edges - model-reasoned connections that need verification._
- **What connects `TubeFactory OCP — Architecture Health Scanner.`, `Find public functions with no project-wide name or attribute reference.`, `Pydantic Settings - 环境变量配置管理 统一管理数据库、YouTube API、爬虫、日志等配置` to the rest of the system?**
  _239 weakly-connected nodes found - possible documentation gaps or missing edges._