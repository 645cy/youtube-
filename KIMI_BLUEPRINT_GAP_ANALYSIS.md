# KimiAgent Blueprint Gap Analysis

Date: 2026-05-02

This document compares the original KimiAgent blueprints in `D:\Projects\kimiagent` with the current TubeFactory implementation in `D:\Projects\YouTube\tubefactory-ocp`.

## Blueprint Inputs Reviewed

- `Kimi_Agent_Agent联邦调度`: product requirements and research synthesis.
- `Kimi_Agent_YouTube情报系统`: MapReduce-style research clusters for YouTube intelligence.
- `Kimi_Agent_全栈情报变现系统`: early TubeFactory OCP template and feature map.
- `Kimi_Agent_自建油管爬虫平台`: crawler/intelligence/dashboard prototype.

## Original Architecture Intent

The original design was not just a crawler or dashboard. It described a full operating system for YouTube content:

- Intelligence system: discover niches, low-subscriber breakout channels, viral videos, trends, competitors, and monetization signals.
- Agent federation: split work across research, data, compliance, content, monetization, and operations agents.
- Content factory: topic, script, storyboard, thumbnail, packaging, publishing, and post-publish review.
- Monetization system: AdSense, SaaS affiliate, digital products, sponsorship paths, and revenue-fit scoring.
- Crawler platform: scheduled tasks, task logs, monitoring lists, data export, and historical tracking.
- Human-in-the-loop compliance: human decision records, source provenance, script revision logs, asset-rights checks, AI disclosure, and final review.

## Current Implementation Status

Implemented:

- FastAPI backend and Next.js frontend with channel, video, radar, lab, analysis, and content-factory modules.
- Radar monitor CRUD and manual trigger flow.
- Viral, evergreen, sentiment, monetization, and full-analysis endpoints.
- Content factory flow for topic discovery, SEO keywords, script generation, shot list generation, title optimization, thumbnail suggestions, and publish-time optimization.
- Local one-click startup scripts and smoke-test scripts.

Partially implemented:

- YouTube data acquisition works, but external API timeouts are handled as degraded status rather than a full task log system.
- Monetization analysis exists at video level, but not yet as a dedicated revenue dashboard with affiliate/product path tracking.
- Content factory is useful, but does not yet persist a full production workflow per video.
- Radar can monitor channels, but crawler task scheduling, retries, exports, and visible execution logs are still thin.
- Compliance and evidence workflow has now started with `/api/v1/content-factory/human-review-checklist`, but evidence files are not yet persisted automatically.

Missing or high-value gaps:

- Agent federation orchestrator and explicit agent roles.
- Persistent production workflow state per video.
- Evidence archive per video: topic decision, sources, revision notes, rights check, publish review, and 24h postmortem.
- Crawler task center: task wizard, task queue, retry policy, execution logs, and export.
- Monetization center: revenue path scoring, affiliate fit, sponsorship fit, product ideas, and next actions.
- A/B testing records for title, thumbnail, publish time, and hook style.
- ComfyUI workflow integration for repeatable visual/video generation.

## Migration Priorities

P0 - keep the product usable:

- Preserve current FastAPI/Next architecture instead of replacing it with the older Vite prototype.
- Keep all live endpoints graceful under YouTube API timeout or quota failure.
- Add visible task status and no-blocking UI behavior for slow analysis/crawl paths.

P1 - directly migrate blueprint value:

- Add human review and evidence checklist into the content factory.
- Add crawler task logs and a scheduled-task screen inspired by the crawler prototype.
- Add monetization route scoring: AdSense, SaaS affiliate, product, sponsorship, and funnel fit.
- Add source provenance labels to analysis and recommendations.

P2 - larger architecture upgrades:

- Add an agent-style workflow planner around discovery -> analysis -> script -> publish -> review.
- Persist each video project as a production record.
- Add ComfyUI/local AI workflow connectors.
- Add exportable reports for competitor analysis and content plans.

## Changes Already Applied From This Review

- Added `GET /api/v1/content-factory/human-review-checklist`.
- Added frontend API client `factoryApi.humanReviewChecklist`.
- Added a Content Factory UI panel for human review and evidence-chain generation.
- Added the first Crawler Task Center pass:
  - `crawler_tasks` and `crawler_task_runs` tables.
  - `/api/v1/crawler/tasks` create/list/delete endpoints.
  - `/api/v1/crawler/tasks/{id}/trigger` execution endpoint.
  - `/api/v1/crawler/tasks/{id}/runs` run history endpoint.
  - `/crawler` frontend page with task creation, manual trigger, deletion, and execution logs.
- Earlier fixes from this pass also improved full-analysis latency, radar trigger degradation, content-factory thumbnail/publish tooling, and startup cleanup.

## Next Best Engineering Step

Extend the new Crawler Task Center:

- Add scheduler integration for hourly/daily/weekly tasks.
- Connect radar monitor triggers to crawler task run records.
- Add export for task results and run logs.
- Add retry/backoff policy for YouTube API timeout and quota failures.
