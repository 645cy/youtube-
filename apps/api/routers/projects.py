"""ContentProject API Router — 内容项目 CRUD + 关联查询."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas.content_project import (
    ContentProjectCreate,
    ContentProjectList,
    ContentProjectRead,
    ContentProjectUpdate,
)
from packages.db.schema import ContentProject, CrawlerTask, CrawlerTaskRun, get_db_session

router = APIRouter(prefix="/projects", tags=["content-projects"])


@router.get("", response_model=ContentProjectList)
async def list_projects(
    status: str | None = Query(None, pattern="^(draft|active|archived)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """列出内容项目，支持状态筛选和分页."""
    where = []
    if status:
        where.append(ContentProject.status == status)

    total_result = await db.execute(
        select(func.count(ContentProject.id)).where(*where)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(ContentProject)
        .where(*where)
        .order_by(desc(ContentProject.updated_at))
        .limit(limit)
        .offset(offset)
    )
    items = result.scalars().all()

    # 填充关联数据
    enriched = []
    for proj in items:
        row = ContentProjectRead.model_validate(proj)
        if proj.source_task:
            row.source_task_name = proj.source_task.name
        if proj.source_run:
            row.source_run_status = proj.source_run.status
        enriched.append(row)

    return {"items": enriched, "total": total}


@router.post("", response_model=ContentProjectRead)
async def create_project(
    data: ContentProjectCreate,
    db: AsyncSession = Depends(get_db_session),
) -> ContentProject:
    """创建内容项目."""
    project = ContentProject(
        title=data.title,
        description=data.description,
        source_crawler_task_id=data.source_crawler_task_id,
        source_run_id=data.source_run_id,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ContentProjectRead)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> ContentProject:
    """获取单个项目详情."""
    result = await db.execute(
        select(ContentProject).where(ContentProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    row = ContentProjectRead.model_validate(project)
    if project.source_task:
        row.source_task_name = project.source_task.name
    if project.source_run:
        row.source_run_status = project.source_run.status
    return row


@router.put("/{project_id}", response_model=ContentProjectRead)
async def update_project(
    project_id: int,
    data: ContentProjectUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> ContentProject:
    """更新内容项目."""
    result = await db.execute(
        select(ContentProject).where(ContentProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """删除内容项目."""
    result = await db.execute(
        select(ContentProject).where(ContentProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    await db.delete(project)
    return {"message": "项目已删除"}
