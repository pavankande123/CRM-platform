import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models.pipeline import Pipeline, PipelineStage
from app.schemas.pipeline import PipelineCreate, PipelineStageCreate


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
        )
        db.add(stage)

    await db.commit()

    # Re-query with eager stages
    stmt = (
        select(Pipeline)
        .options(selectinload(Pipeline.stages))
        .where(Pipeline.id == pipeline.id)
    )
    return (await db.execute(stmt)).scalar_one()


async def list_pipelines(db: AsyncSession, tenant_id: uuid.UUID) -> List[Pipeline]:
    """Retrieve all pipelines configured for the tenant."""
    await ensure_default_pipeline(db, tenant_id)
    stmt = (
        select(Pipeline)
        .options(selectinload(Pipeline.stages))
        .where(Pipeline.tenant_id == tenant_id, Pipeline.is_active == True)  # noqa: E712
        .order_by(Pipeline.is_default.desc(), Pipeline.name.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_pipeline(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: PipelineCreate,
) -> Pipeline:
    """Create a new customized pipeline with custom stages."""
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
