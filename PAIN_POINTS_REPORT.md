# TubeFactory 痛点与功能不足报告

## P0 - 致命/严重（功能断裂/假数据/404）

| # | 痛点 | 文件 | 影响 |
|---|------|------|------|
| 1 | **public 目录不存在，所有 placeholder 图片 404** | `ChannelCard.tsx`, `MonitorList.tsx`, `VideoDrawer.tsx` | 频道/视频/头像的 fallback 图片全部 404，显示破图 |
| 2 | **Lab "导出PDF" / "开始执行" 按钮纯 console.log** | `lab/page.tsx` | 用户点击后无任何反馈，功能完全未实现 |
| 3 | **Factory "AI生成脚本" 纯 console.log** | `factory/page.tsx` | 脚本编辑 Tab 的 AI 生成按钮无实际功能 |
| 4 | **前端未集成任何视频分析功能** | `dashboard/page.tsx` | viral/evergreen/sentiment/monetization 分析 API 已就绪但前端无处调用 |
| 5 | **Dashboard "刷新数据" 按钮无功能** | `dashboard/page.tsx` | 点击无反应 |
| 6 | **SearchBox 点击建议项只设文本不搜索** | `SearchBox.tsx` | 用户点击下拉建议中的已有频道名，只设置了输入框文本，没有实际筛选 |
| 7 | **VideoDrawer 视频点击无任何反应** | `VideoDrawer.tsx` | 视频列表项可点击但无跳转/分析/播放等任何操作 |
| 8 | **alert() 粗暴错误提示** | `SearchBox.tsx`, `radar/page.tsx` | 网络错误时使用浏览器 alert，打断用户操作 |
| 9 | **console.warn/log 散落在生产代码中** | 多处 | 生产环境不应有调试日志 |

## P1 - 中等（体验缺陷/功能缺失）

| # | 痛点 | 文件 | 影响 |
|---|------|------|------|
| 10 | **缺少全局错误边界 (Error Boundary)** | 无 | 任何未捕获异常会导致整个页面白屏 |
| 11 | **MonitorList 删除按钮只在 hover 显示** | `MonitorList.tsx` | 移动端无法删除监控频道 |
| 12 | **ChannelCard 无频道详情页** | `ChannelCard.tsx` | 点击频道只能看视频列表，无法查看频道详情/统计/分析 |
| 13 | **Radar handleRemoveChannel 只改前端状态** | `radar/page.tsx` | 删除监控频道只从本地 store 移除，没有调用后端 API 删除监控任务 |
| 14 | **GrowthChart 标题固定"近30天"** | `GrowthChart.tsx` | 不反映实际数据范围 |
| 15 | **ScriptEditor 使用 Textarea 而非 Textarea 组件** | `ScriptEditor.tsx` | 从 `@/components/ui/input` 导入 Textarea，但该组件可能不存在或不符合预期 |

## P2 - 轻微（优化项）

| # | 痛点 | 文件 | 影响 |
|---|------|------|------|
| 16 | **缺少全局 loading 状态管理** | 无 | 多个请求并发时 loading 状态分散管理 |
| 17 | **缺少请求去重/缓存** | `api.ts` | 重复请求同一数据会重复调用 API |
| 18 | **TopicGenerator 热门 niche 直接触发 onGenerate** | `TopicGenerator.tsx` | 点击热门标签直接发送请求，没有确认步骤 |
| 19 | **PathRecommendation 无排序/筛选功能** | `PathRecommendation.tsx` | 推荐结果只能按默认顺序查看 |
| 20 | **WorkflowDetail 步骤状态不可交互** | `WorkflowDetail.tsx` | 用户无法标记步骤为已完成 |
