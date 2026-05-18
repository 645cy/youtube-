# TubeFactory OCP — 代码智能分析脚本
# 一键重新生成项目的知识图谱和代码审查图

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TubeFactory OCP — 代码智能分析" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Graphify —— 代码知识图谱
Write-Host "[1/3] 运行 graphify 代码结构提取..." -ForegroundColor Yellow
if (Get-Command graphify -ErrorAction SilentlyContinue) {
    graphify update . --force
    Write-Host "      ✓ 输出: graphify-out/GRAPH_REPORT.md" -ForegroundColor Green
    Write-Host "      ✓ 可视化: graphify-out/graph.html" -ForegroundColor Green
} else {
    Write-Host "      ✗ graphify 未安装. 运行: pip install graphifyy" -ForegroundColor Red
}
Write-Host ""

# 2. Code-Review-Graph —— 审查图与 Wiki
Write-Host "[2/3] 运行 code-review-graph 构建与 Wiki 生成..." -ForegroundColor Yellow
if (Get-Command code-review-graph -ErrorAction SilentlyContinue) {
    code-review-graph build
    code-review-graph wiki
    code-review-graph visualize
    Write-Host "      ✓ Wiki: .code-review-graph/wiki/" -ForegroundColor Green
    Write-Host "      ✓ 可视化: .code-review-graph/graph.html" -ForegroundColor Green
} else {
    Write-Host "      ✗ code-review-graph 未安装. 运行: pip install code-review-graph" -ForegroundColor Red
}
Write-Host ""

# 3. CodeGraphContext —— 图数据库索引（Windows 受限）
Write-Host "[3/3] 运行 codegraphcontext 索引..." -ForegroundColor Yellow
if (Get-Command cgc -ErrorAction SilentlyContinue) {
    Write-Host "      ⚠ 注意: codegraphcontext 在 Windows 上可能因 KùzuDB 兼容性问题失败" -ForegroundColor DarkYellow
    Write-Host "      如遇错误，建议在 WSL2 / Docker / Linux 环境中运行: cgc index ." -ForegroundColor DarkYellow
    try {
        cgc index . --force
        Write-Host "      ✓ 索引成功" -ForegroundColor Green
    } catch {
        Write-Host "      ✗ 索引失败（预期行为）: $_" -ForegroundColor Red
    }
} else {
    Write-Host "      ✗ codegraphcontext 未安装. 运行: pip install codegraphcontext" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "分析完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "推荐阅读:" -ForegroundColor White
Write-Host "  - graphify-out/GRAPH_REPORT.md       (知识图谱报告)"
Write-Host "  - .code-review-graph/wiki/index.md   (模块 Wiki)"
Write-Host "  - CODE_INTELLIGENCE.md               (综合架构分析)"
Write-Host "  - .kimi/AGENTS.md                    (AI 助手上下文)"
Write-Host ""
Write-Host "可视化查看:" -ForegroundColor White
Write-Host "  - graphify-out/graph.html            (交互式图谱)"
Write-Host "  - .code-review-graph/graph.html      (审查关系图)"
Write-Host ""
