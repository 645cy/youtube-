"""
Analysis router endpoints for video, niche, sentiment, KPI, and growth analysis.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas import AnalysisRequest, AnalysisResult
from apps.api.config import settings
from apps.api.services.analysis_helpers import (
    build_estimated_growth_rows,
    fetch_video_comments,
    load_growth_totals,
    load_metric_growth_rows,
    load_niche_channels,
    resolve_niche_name,
)
from apps.api.services.analyzer import (
    CommentSentimentAnalyzer,
    DashboardKPICalculator,
    LongTailEvergreenDetector,
    MonetizationSignalDetector,
    NicheMetrics,
    NicheScoringCard,
    ShortTermViralDetector,
    VideoFormatAnalyzer,
    VideoMetrics,
    KeywordMetrics,
)
from packages.db.schema import AnalysisLog, AnalysisType, Channel, MetricHistory, MetricType, Video, get_db_session

router = APIRouter(prefix="/analysis", tags=["Analysis"])
logger = logging.getLogger(__name__)  # CRG: Preserve partial full-analysis errors instead of raising NameError.


@router.post("/viral-detection")
async def viral_detection(
    request: AnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResult:
    """Algorithm 1: short-term viral detection.

    Builds metrics from stored video and channel data.
    """
    start = time.monotonic()

    if request.target_type == "video":
        # CRG: Load the target video before building viral metrics.
        result = await session.execute(
            select(Video).where(Video.youtube_id == request.target_id)
        )
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {request.target_id} not found")

        # CRG: Load the owning channel for subscriber baseline.
        ch_result = await session.execute(
            select(Channel).where(Channel.id == video.channel_id)
        )
        channel = ch_result.scalar_one_or_none()

        # CRG: Build viral metrics from stored video/channel data.
        vm = VideoMetrics(
            video_id=request.target_id,
            channel_subscribers=channel.subscriber_count or 1,
            publish_time=video.published_at or datetime.now(timezone.utc) - timedelta(days=1),
            views_history=[(datetime.now(timezone.utc), video.view_count or 0)],
            ctr_history=[],
            retention_history=[],
            video_type="shorts" if video.is_short else "long_form",
        )

        detector = ShortTermViralDetector()
        detection_result = detector.detect(vm)

        # CRG: Persist the viral score for dashboard/history consumers.
        log = AnalysisLog(
            video_id=video.id,
            analysis_type=AnalysisType.VIRAL_DETECTION,
            result_json=detection_result.__dict__.__str__(),
            score=detection_result.viral_score,
        )
        session.add(log)
        await session.flush()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return AnalysisResult(
            analysis_type="viral_detection",
            target_id=request.target_id,
            target_type="video",
            status="success",
            result=detection_result.__dict__,
            score=detection_result.viral_score,
            processing_time_ms=elapsed_ms,
        )
    else:
        raise HTTPException(status_code=400, detail="Only video target_type supported for viral detection")


@router.post("/evergreen")
async def evergreen_detection(
    request: AnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResult:
    """Algorithm 2: evergreen detection."""
    start = time.monotonic()

    detector = LongTailEvergreenDetector()

    if request.target_type == "video":
        result = await session.execute(
            select(Video).where(Video.youtube_id == request.target_id)
        )
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {request.target_id} not found")

        kw = KeywordMetrics(
            keyword=video.title[:50],
            monthly_search_volume=video.view_count or 1000,
            weekly_search_history=[(video.view_count or 1000) * (0.95 + i * 0.01) for i in range(12)],
            competing_videos_count=50,
            top_video_age_days=180,
            avg_view_count_top10=video.view_count or 5000,
            niche="general",
        )
        detection_result = detector.detect(kw)

        log = AnalysisLog(
            video_id=video.id,
            analysis_type=AnalysisType.EVERGREEN,
            score=detection_result.evergreen_score,
        )
        session.add(log)
        await session.flush()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return AnalysisResult(
            analysis_type="evergreen",
            target_id=request.target_id,
            target_type="video",
            status="success",
            result=detection_result.__dict__,
            score=detection_result.evergreen_score,
            processing_time_ms=elapsed_ms,
        )
    else:
        raise HTTPException(status_code=400, detail="Only video target_type supported")


@router.post("/sentiment")
async def sentiment_analysis(
    request: AnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResult:
    """Algorithm 3: comment sentiment analysis.

    Uses provided comments or explicitly configured remote comments.
    """
    start = time.monotonic()

    # CRG: Read comment rows from the request body when callers provide them.
    comments_data = []
    if hasattr(request, "comments") and request.comments:
        comments_data = request.comments
    else:
        # CRG: Fetch remote comments only when configured; otherwise keep analysis explicit.
        try:
            comments_data = (
                await fetch_video_comments(request.target_id)
                if settings.FETCH_REMOTE_COMMENTS_FOR_ANALYSIS
                else []
            )
        except RuntimeError:
            comments_data = []
        if not comments_data:
            # CRG: Missing comments must return skipped rather than simulated sentiment.
            # CRG: Do not synthesize comments; callers need real-data status.
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return AnalysisResult(
                analysis_type="sentiment",
                target_id=request.target_id,
                target_type=request.target_type,
                status="skipped",
                result={
                    "source": "none",
                    "reason": "No comment data provided or fetched.",
                    "aggregation": None,
                    "sample_results": [],
                },
                score=None,
                processing_time_ms=elapsed_ms,
            )

    analyzer = CommentSentimentAnalyzer()
    results = analyzer.batch_analyze(comments_data)
    aggregation = analyzer.aggregate(results)

    # CRG: Convert average sentiment into the existing 0-100 score scale.
    score = aggregation.get("avg_compound", 0) * 50 + 50
    log = AnalysisLog(
        analysis_type=AnalysisType.SENTIMENT,
        score=score,
    )
    session.add(log)
    await session.flush()

    elapsed_ms = int((time.monotonic() - start) * 1000)
    return AnalysisResult(
        analysis_type="sentiment",
        target_id=request.target_id,
        target_type=request.target_type,
        status="success",
        result={"aggregation": aggregation, "sample_results": [r.__dict__ for r in results[:5]]},
        score=score,
        processing_time_ms=elapsed_ms,
    )


@router.post("/monetization")
async def monetization_detection(
    request: AnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResult:
    """Algorithm 4: monetization signal detection."""
    start = time.monotonic()

    if request.target_type == "video":
        result = await session.execute(
            select(Video).where(Video.youtube_id == request.target_id)
        )
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {request.target_id} not found")

        detector = MonetizationSignalDetector()
        detection_result = detector.detect(
            video_id=request.target_id,
            title=video.title or "",
            description=video.description or "",
        )

        log = AnalysisLog(
            video_id=video.id,
            analysis_type=AnalysisType.MONETIZATION,
            score=detection_result.monetization_score,
        )
        session.add(log)
        await session.flush()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return AnalysisResult(
            analysis_type="monetization",
            target_id=request.target_id,
            target_type="video",
            status="success",
            result=detection_result.__dict__,
            score=detection_result.monetization_score,
            processing_time_ms=elapsed_ms,
        )
    else:
        raise HTTPException(status_code=400, detail="Only video target_type supported")


async def _build_niche_metrics(
    session: AsyncSession,
    niche_name: str,
    channels: list[Channel],
) -> NicheMetrics:
    """构建 NicheMetrics（保留在 Router 中因为依赖 NicheMetrics 数据类）."""
    from apps.api.services.analysis_helpers import estimate_evergreen_ratio

    competing_count = len(channels)
    avg_upload_freq = 2.0
    if channels:
        total_videos = sum(c.video_count or 0 for c in channels)
        avg_upload_freq = round(total_videos / max(len(channels) * 30, 1) * 7, 2)

    avg_rpm = 3.5
    max_rpm = 8.0
    if channels:
        total_views = sum(c.view_count or 0 for c in channels)
        total_subs = sum(c.subscriber_count or 0 for c in channels)
        if total_views > 0:
            avg_rpm = round(min(10.0, max(1.0, total_subs / total_views * 100)), 2)
            max_rpm = round(avg_rpm * 2.5, 2)

    monthly_search = 50000
    if channels:
        avg_subs = sum(c.subscriber_count or 0 for c in channels) / len(channels)
        monthly_search = int(avg_subs * 0.1 * competing_count)

    return NicheMetrics(
        niche_name=niche_name,
        monthly_search_volume=monthly_search,
        growth_trend_12m=0.15,
        avg_rpm=avg_rpm,
        max_rpm_in_niche=max_rpm,
        competing_channels_count=competing_count,
        avg_video_upload_frequency=avg_upload_freq,
        evergreen_content_ratio=await estimate_evergreen_ratio(session, channels),
        ai_content_detected_ratio=0.3,
        personality_dependency=0.7,
        required_skill_level=5,
        creator_skill_level=6,
        weekly_time_available=15,
        estimated_production_hours=8,
        passion_score=7,
        startup_cost_estimate=100,
    )


def _niche_result_payload(result: Any) -> dict[str, Any]:
    # CRG: Keep API response shaping separate from scoring and persistence logic.
    return {
        "niche_name": result.niche_name,
        "total_score": result.total_score,
        "traffic_potential": result.traffic_potential,
        "monetization_density": result.monetization_density,
        "ai_replaceability": result.ai_replaceability,
        "reproducibility": result.reproducibility,
        "opportunity_level": result.opportunity_level,
        "swot_summary": result.swot_summary,
        "recommendation": result.recommendation,
    }


@router.post("/niche-score")
async def niche_scoring(
    request: AnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnalysisResult:
    """Algorithm 5: niche scoring."""
    start = time.monotonic()
    niche_name = await resolve_niche_name(session, request.target_type, request.target_id)
    metrics = await _build_niche_metrics(
        session,
        niche_name,
        await load_niche_channels(session, niche_name),
    )
    result = NicheScoringCard().score(metrics)

    session.add(AnalysisLog(analysis_type=AnalysisType.NICHE_SCORE, score=result.total_score))
    await session.flush()

    return AnalysisResult(
        analysis_type="niche_score",
        target_id=request.target_id,
        target_type=request.target_type,
        status="success",
        result=_niche_result_payload(result),
        score=result.total_score,
        processing_time_ms=int((time.monotonic() - start) * 1000),
    )


@router.post("/full-analysis")
async def full_analysis(
    request: AnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AnalysisResult]:
    """Run the requested analysis types and return partial results when possible."""
    results = []

    for analysis_type in request.analysis_types:
        try:
            req = AnalysisRequest(
                target_type=request.target_type,
                target_id=request.target_id,
                analysis_types=[analysis_type],
            )
            if analysis_type == "viral_detection":
                results.append(await viral_detection(req, session))
            elif analysis_type == "evergreen":
                results.append(await evergreen_detection(req, session))
            elif analysis_type == "sentiment":
                results.append(await sentiment_analysis(req, session))
            elif analysis_type == "monetization":
                results.append(await monetization_detection(req, session))
            elif analysis_type == "niche_score":
                results.append(await niche_scoring(req, session))
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(
                f"Analysis '{analysis_type}' failed for {request.target_type}={request.target_id}: {e}"
            )
            results.append(AnalysisResult(
                analysis_type=analysis_type,
                target_id=request.target_id,
                target_type=request.target_type,
                status="error",
                result={"error": str(e)},
            ))

    # CRG: If every requested analysis failed, surface a single actionable error.
    if all(r.status == "error" for r in results):
        raise HTTPException(
            status_code=422,
            detail={
                "message": "All requested analyses failed",
                "target_id": request.target_id,
                "failed_types": [r.analysis_type for r in results],
                "errors": {r.analysis_type: r.result.get("error") for r in results},
            },
        )

    return results


@router.get("/history")
async def get_analysis_history(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    video_id: Annotated[int | None, Query()] = None,
    analysis_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[dict[str, Any]]:
    """Return recent analysis history rows."""
    query = select(AnalysisLog).order_by(desc(AnalysisLog.created_at)).limit(limit)

    if video_id:
        query = query.where(AnalysisLog.video_id == video_id)
    if analysis_type:
        query = query.where(AnalysisLog.analysis_type == analysis_type)

    result = await session.execute(query)
    logs = result.scalars().all()
    return [  # CRG: Preserve the API response shape for recent analysis logs.
        {
            "id": log.id,
            "video_id": log.video_id,
            "analysis_type": log.analysis_type,
            "score": log.score,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.post("/format-coefficient")
async def calculate_format_coefficient(
    video_id: Annotated[str, Query(min_length=1)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Algorithm 7: video format analysis."""
    result = await session.execute(select(Video).where(Video.youtube_id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    ch_result = await session.execute(select(Channel).where(Channel.id == video.channel_id))
    channel = ch_result.scalar_one_or_none()

    return VideoFormatAnalyzer.calculate_viral_coefficient(
        view_count=video.view_count or 0,
        subscriber_count=channel.subscriber_count or 1,
        is_short=video.is_short,
    )


@router.post("/thumbnail-ctr")
async def estimate_thumbnail_ctr(
    video_id: Annotated[str, Query(min_length=1)],
    has_face: Annotated[bool, Query()] = True,
    has_text: Annotated[bool, Query()] = True,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> dict[str, Any]:
    """Algorithm 8: thumbnail CTR estimation."""
    from apps.api.services.analyzer import ThumbnailCTREstimator

    if session:
        result = await session.execute(select(Video).where(Video.youtube_id == video_id))
        video = result.scalar_one_or_none()
        title = video.title if video else "Unknown"
    else:
        title = video_id

    return ThumbnailCTREstimator.estimate(title, has_face, has_text)


@router.get("/dashboard")
async def get_dashboard_kpi(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Algorithm 9: dashboard KPI aggregation."""
    # CRG: Load dashboard source rows explicitly; damaged comments previously hid this query.
    ch_result = await session.execute(select(Channel))
    channels = ch_result.scalars().all()

    v_result = await session.execute(select(Video))
    videos = v_result.scalars().all()

    # CRG: Load the latest analysis logs for KPI aggregation.
    a_result = await session.execute(
        select(AnalysisLog).order_by(desc(AnalysisLog.created_at)).limit(100)
    )
    analyses = a_result.scalars().all()

    channel_dicts = [
        {
            "id": c.id,
            "title": c.title,
            "subscriber_count": c.subscriber_count,
            "view_count": c.view_count,
            "has_active_monitor": bool(c.monitor_jobs),
        }
        for c in channels
    ]
    video_dicts = [
        {
            "id": v.id,
            "view_count": v.view_count,
        }
        for v in videos
    ]
    analysis_dicts = [
        {
            "analysis_type": a.analysis_type,
            "score": a.score,
        }
        for a in analyses
    ]

    return DashboardKPICalculator.calculate(channel_dicts, video_dicts, analysis_dicts)


@router.get("/growth")
async def get_growth_data(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    days: Annotated[int, Query(ge=1, le=90)] = 30,
) -> list[dict[str, Any]]:
    """Return growth trend rows for the requested number of days.

    Prefers stored metric history and otherwise returns deterministic estimated rows.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    stored_rows = await load_metric_growth_rows(session, since, minimum_points=days // 2)
    if stored_rows:
        return stored_rows

    totals = await load_growth_totals(session)
    # CRG: Keep the route as orchestration; query and estimation details stay in testable helpers.
    return build_estimated_growth_rows(days, *totals)


