import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError
from app.models.pipeline import Pipeline, PipelineStage
from app.models.project import Project
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineUpdate,
    PipelineStageCreate,
    PipelineStageUpdate,
    StageReorderRequest,
)


DEFAULT_STAGES = [
    ("Enquiry", 1, 10, False, False, "cyan"),
    ("Site Visit", 2, 30, False, False, "sky"),
    ("Quotation", 3, 50, False, False, "blue"),
    ("Approval", 4, 70, False, False, "indigo"),
    ("Installation", 5, 85, False, False, "amber"),
    ("Testing", 6, 95, False, False, "purple"),
    ("Completed", 7, 100, True, False, "emerald"),
    ("Lost", 8, 0, False, True, "rose"),
]


async def ensure_default_pipeline(db: AsyncSession, tenant_id: uuid.UUID) -> Pipeline:
    """Ensures at least one default pipeline with standard solar stages exists for the tenant."""
    stmt = (
        select(Pipeline)
        .options(selectinload(Pipeline.stages))
        .where(Pipeline.tenant_id == tenant_id, Pipeline.is_default == True)  # noqa: E712
    )
    pipeline = (await db.execute(stmt)).scalar_one_or_none()
    if pipeline:
        return pipeline

    # Create default pipeline
    pipeline = Pipeline(
        tenant_id=tenant_id,
        name="Solar Commercial Pipeline",
        is_default=True,
        is_active=True,
    )
    db.add(pipeline)
    await db.flush()

    for name, order, prob, won, lost, color in DEFAULT_STAGES:
        stage = PipelineStage(
            tenant_id=tenant_id,
            pipeline_id=pipeline.id,
            name=name,
            order=order,
            probability_percent=prob,
            is_closed_won=won,
            is_closed_lost=lost,
            color=color,
            is_active=True,
        )
        db.add(stage)

    await db.commit()

    stmt = (
        select(Pipeline)
        .options(selectinload(Pipeline.stages))
        .where(Pipeline.id == pipeline.id)
    )
    return (await db.execute(stmt)).scalar_one()


async def list_pipelines(db: AsyncSession, tenant_id: uuid.UUID, include_inactive: bool = False) -> List[Pipeline]:
    """Retrieve all pipelines configured for the tenant."""
    await ensure_default_pipeline(db, tenant_id)
    stmt = (
        select(Pipeline)
        .options(selectinload(Pipeline.stages))
        .where(Pipeline.tenant_id == tenant_id)
    )
    if not include_inactive:
        stmt = stmt.where(Pipeline.is_active == True)  # noqa: E712

    stmt = stmt.order_by(Pipeline.is_default.desc(), Pipeline.name.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_pipeline(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: PipelineCreate,
) -> Pipeline:
    """Create a new customized pipeline with custom stages."""
    if data.is_default:
        # unset previous default
        stmt = select(Pipeline).where(Pipeline.tenant_id == tenant_id, Pipeline.is_default == True)  # noqa: E712
        existing_defaults = (await db.execute(stmt)).scalars().all()
        for p in existing_defaults:
            p.is_default = False

    pipeline = Pipeline(
        tenant_id=tenant_id,
        name=data.name.strip(),
        product_id=data.product_id,
        is_default=data.is_default,
        is_active=data.is_active,
    )
    db.add(pipeline)
    await db.flush()

    stages_data = data.stages or [
        PipelineStageCreate(name="Enquiry", order=1, probability_percent=10, color="cyan"),
        PipelineStageCreate(name="Site Visit", order=2, probability_percent=30, color="sky"),
        PipelineStageCreate(name="Quotation", order=3, probability_percent=50, color="blue"),
        PipelineStageCreate(name="Completed", order=4, probability_percent=100, is_closed_won=True, color="emerald"),
    ]

    for stg in stages_data:
        stage = PipelineStage(
            tenant_id=tenant_id,
            pipeline_id=pipeline.id,
            name=stg.name.strip(),
            order=stg.order,
            probability_percent=stg.probability_percent,
            is_closed_won=stg.is_closed_won,
            is_closed_lost=stg.is_closed_lost,
            color=stg.color,
            is_active=stg.is_active,
        )
        db.add(stage)

    await db.commit()
    stmt = (
        select(Pipeline)
        .options(selectinload(Pipeline.stages))
        .where(Pipeline.id == pipeline.id)
    )
    return (await db.execute(stmt)).scalar_one()


async def get_pipeline(db: AsyncSession, tenant_id: uuid.UUID, pipeline_id: uuid.UUID) -> Pipeline:
    stmt = (
        select(Pipeline)
        .options(selectinload(Pipeline.stages))
        .where(Pipeline.id == pipeline_id, Pipeline.tenant_id == tenant_id)
    )
    pipeline = (await db.execute(stmt)).scalar_one_or_none()
    if not pipeline:
        raise NotFoundError(message="Pipeline not found.")
    return pipeline


async def update_pipeline(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    data: PipelineUpdate,
) -> Pipeline:
    pipeline = await get_pipeline(db, tenant_id, pipeline_id)

    if data.is_default and not pipeline.is_default:
        stmt = select(Pipeline).where(Pipeline.tenant_id == tenant_id, Pipeline.is_default == True)  # noqa: E712
        existing_defaults = (await db.execute(stmt)).scalars().all()
        for p in existing_defaults:
            p.is_default = False

    if data.name is not None:
        pipeline.name = data.name.strip()
    if data.product_id is not None:
        pipeline.product_id = data.product_id
    if data.is_default is not None:
        pipeline.is_default = data.is_default
    if data.is_active is not None:
        pipeline.is_active = data.is_active

    await db.commit()
    return await get_pipeline(db, tenant_id, pipeline_id)


async def create_stage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    data: PipelineStageCreate,
) -> PipelineStage:
    await get_pipeline(db, tenant_id, pipeline_id)
    stage = PipelineStage(
        tenant_id=tenant_id,
        pipeline_id=pipeline_id,
        name=data.name.strip(),
        order=data.order,
        probability_percent=data.probability_percent,
        is_closed_won=data.is_closed_won,
        is_closed_lost=data.is_closed_lost,
        color=data.color,
        is_active=data.is_active,
    )
    db.add(stage)
    await db.commit()
    await db.refresh(stage)
    return stage


async def update_stage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    stage_id: uuid.UUID,
    data: PipelineStageUpdate,
) -> PipelineStage:
    stmt = select(PipelineStage).where(
        PipelineStage.id == stage_id,
        PipelineStage.pipeline_id == pipeline_id,
        PipelineStage.tenant_id == tenant_id,
    )
    stage = (await db.execute(stmt)).scalar_one_or_none()
    if not stage:
        raise NotFoundError(message="Pipeline stage not found.")

    if data.name is not None:
        stage.name = data.name.strip()
    if data.order is not None:
        stage.order = data.order
    if data.probability_percent is not None:
        stage.probability_percent = data.probability_percent
    if data.is_closed_won is not None:
        stage.is_closed_won = data.is_closed_won
    if data.is_closed_lost is not None:
        stage.is_closed_lost = data.is_closed_lost
    if data.color is not None:
        stage.color = data.color
    if data.is_active is not None:
        stage.is_active = data.is_active

    await db.commit()
    await db.refresh(stage)
    return stage


async def reorder_stages(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    reorder_data: StageReorderRequest,
) -> List[PipelineStage]:
    await get_pipeline(db, tenant_id, pipeline_id)
    for item in reorder_data.stages:
        stmt = select(PipelineStage).where(
            PipelineStage.id == item.stage_id,
            PipelineStage.pipeline_id == pipeline_id,
            PipelineStage.tenant_id == tenant_id,
        )
        stage = (await db.execute(stmt)).scalar_one_or_none()
        if stage:
            stage.order = item.order

    await db.commit()
    stmt = (
        select(PipelineStage)
        .where(PipelineStage.pipeline_id == pipeline_id, PipelineStage.tenant_id == tenant_id)
        .order_by(PipelineStage.order.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def deactivate_or_delete_stage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    stage_id: uuid.UUID,
) -> dict:
    """
    Safely deactivate or delete stage.
    If projects currently use this stage, NEVER delete it to protect historical data integrity.
    Instead, soft-deactivate the stage.
    """
    stmt = select(PipelineStage).where(
        PipelineStage.id == stage_id,
        PipelineStage.pipeline_id == pipeline_id,
        PipelineStage.tenant_id == tenant_id,
    )
    stage = (await db.execute(stmt)).scalar_one_or_none()
    if not stage:
        raise NotFoundError(message="Pipeline stage not found.")

    # Check project count
    project_stmt = select(func.count(Project.id)).where(
        Project.stage_id == stage_id,
        Project.tenant_id == tenant_id,
    )
    project_count = (await db.execute(project_stmt)).scalar() or 0

    if project_count > 0:
        # Protect historical project records! Soft-deactivate stage
        stage.is_active = False
        await db.commit()
        return {
            "status": "deactivated",
            "message": f"Stage has {project_count} existing project records. Soft-deactivated to preserve historical integrity.",
            "is_active": False,
        }
    else:
        # Safe to hard delete since no historical project references exist
        await db.delete(stage)
        await db.commit()
        return {
            "status": "deleted",
            "message": "Stage deleted successfully.",
            "is_active": False,
        }
