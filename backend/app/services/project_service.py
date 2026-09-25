import datetime
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.pipeline import Pipeline, PipelineStage
from app.models.project import Project, ProjectStageHistory
from app.schemas.project import ProjectCreate, ProjectRead, ProjectStageChange, ProjectStageHistoryRead, ProjectUpdate
from app.services.activity_service import log_activity
from app.services.pipeline_service import ensure_default_pipeline


async def generate_project_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate sequential, human-friendly project identifier (e.g. ENX-PRJ-2026-0001)."""
    current_year = datetime.datetime.now().year
    prefix = f"ENX-PRJ-{current_year}-"
    
    count_stmt = select(func.count()).select_from(Project).where(
        Project.tenant_id == tenant_id,
        Project.project_number.like(f"{prefix}%")
    )
    count = (await db.execute(count_stmt)).scalar() or 0
    return f"{prefix}{count + 1:04d}"


async def list_projects(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: Optional[uuid.UUID] = None,
    stage_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
) -> Tuple[List[ProjectRead], int]:
    """List paginated projects for tenant with joined customer, product, and payment balances."""
    base_query = select(Project).where(Project.tenant_id == tenant_id)

    if customer_id:
        base_query = base_query.where(Project.customer_id == customer_id)
    if stage_id:
        base_query = base_query.where(Project.stage_id == stage_id)
    if status:
        base_query = base_query.where(Project.status == status.lower())
    if search:
        search_pattern = f"%{search.strip().lower()}%"
        base_query = base_query.where(
            or_(
                func.lower(Project.name).like(search_pattern),
                func.lower(Project.project_number).like(search_pattern),
            )
        )

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        base_query
        .options(
            selectinload(Project.customer),
            selectinload(Project.product),
            selectinload(Project.pipeline),
            selectinload(Project.stage),
            selectinload(Project.owner),
            selectinload(Project.payments),
        )
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = []
    for p in records:
        total_paid = sum((pm.amount for pm in p.payments if pm.status == "received"), Decimal("0.00"))
        outstanding = max(Decimal("0.00"), p.value - total_paid)

        items.append(
            ProjectRead(
                id=p.id,
                tenant_id=p.tenant_id,
                project_number=p.project_number,
                name=p.name,
                customer_id=p.customer_id,
                product_id=p.product_id,
                pipeline_id=p.pipeline_id,
                stage_id=p.stage_id,
                description=p.description,
                value=p.value,
                currency=p.currency,
                expected_completion_date=p.expected_completion_date,
                status=p.status,
                priority=p.priority,
                owner_id=p.owner_id,
                customer_name=p.customer.name if p.customer else None,
                product_name=p.product.name if p.product else None,
                pipeline_name=p.pipeline.name if p.pipeline else None,
                stage_name=p.stage.name if p.stage else None,
                stage_color=p.stage.color if p.stage else None,
                owner_name=p.owner.full_name if p.owner else None,
                total_paid=total_paid,
                outstanding_amount=outstanding,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return items, total


async def create_project(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: ProjectCreate,
    actor_id: Optional[uuid.UUID] = None,
) -> Project:
    """Create project, assign pipeline and stage, generate project number, and record stage history."""
    # Ensure customer exists in tenant
    cust_stmt = select(Customer).where(Customer.id == data.customer_id, Customer.tenant_id == tenant_id)
    customer = (await db.execute(cust_stmt)).scalar_one_or_none()
    if not customer:
        raise NotFoundError(message="Specified Customer not found in your organization.")

    # Resolve pipeline
    pipeline_id = data.pipeline_id
    if not pipeline_id:
        def_pipeline = await ensure_default_pipeline(db, tenant_id)
        pipeline_id = def_pipeline.id

    # Resolve stage
    stage_id = data.stage_id
    if not stage_id:
        # Get first stage of pipeline
        stg_stmt = (
            select(PipelineStage)
            .where(PipelineStage.pipeline_id == pipeline_id, PipelineStage.tenant_id == tenant_id)
            .order_by(PipelineStage.order.asc())
        )
        first_stage = (await db.execute(stg_stmt)).scalars().first()
        if not first_stage:
            raise ValidationError(message="Selected Pipeline has no configured stages.")
        stage_id = first_stage.id

    project_number = await generate_project_number(db, tenant_id)

    project = Project(
        tenant_id=tenant_id,
        project_number=project_number,
        name=data.name.strip(),
        customer_id=data.customer_id,
        product_id=data.product_id,
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        description=data.description,
        value=data.value,
        currency=data.currency or "INR",
        expected_completion_date=data.expected_completion_date,
        status=data.status or "active",
        priority=data.priority or "medium",
        owner_id=data.owner_id or actor_id,
    )
    db.add(project)
    await db.flush()

    # Record initial stage history
    stage_history = ProjectStageHistory(
        tenant_id=tenant_id,
        project_id=project.id,
        from_stage_id=None,
        to_stage_id=stage_id,
        changed_by_id=actor_id,
        notes="Project created",
    )
    db.add(stage_history)

    # Record domain activity
    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="PROJECT_CREATED",
        title=f"Project created: {project.name} ({project.project_number})",
        description=f"Value: ₹{project.value:,.2f} • Customer: {customer.name}",
        customer_id=customer.id,
        project_id=project.id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(project)
    return project


async def get_project(db: AsyncSession, tenant_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    stmt = (
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.product),
            selectinload(Project.pipeline),
            selectinload(Project.stage),
            selectinload(Project.owner),
            selectinload(Project.stage_history).selectinload(ProjectStageHistory.from_stage),
            selectinload(Project.stage_history).selectinload(ProjectStageHistory.to_stage),
            selectinload(Project.stage_history).selectinload(ProjectStageHistory.changed_by),
            selectinload(Project.payments),
        )
        .where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise NotFoundError(message=f"Project with ID {project_id} not found.")
    return project


async def change_project_stage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ProjectStageChange,
    actor_id: Optional[uuid.UUID] = None,
) -> Project:
    """Transactionally transition a project to a new stage and record history."""
    project = await get_project(db, tenant_id, project_id)

    # Validate target stage exists and belongs to project's pipeline
    stg_stmt = select(PipelineStage).where(
        PipelineStage.id == data.stage_id,
        PipelineStage.pipeline_id == project.pipeline_id,
        PipelineStage.tenant_id == tenant_id,
    )
    to_stage = (await db.execute(stg_stmt)).scalar_one_or_none()
    if not to_stage:
        raise ValidationError(message="Target stage does not exist in project's pipeline.")

    if project.stage_id == data.stage_id:
        return project  # Already in target stage

    from_stage_id = project.stage_id
    from_stage_name = project.stage.name if project.stage else "Initial"

    # Update project stage
    project.stage_id = data.stage_id

    # If stage is closed won or closed lost, update status
    if to_stage.is_closed_won:
        project.status = "completed"
    elif to_stage.is_closed_lost:
        project.status = "cancelled"

    # Add history record
    history = ProjectStageHistory(
        tenant_id=tenant_id,
        project_id=project.id,
        from_stage_id=from_stage_id,
        to_stage_id=to_stage.id,
        changed_by_id=actor_id,
        notes=data.notes,
    )
    db.add(history)

    # Log business activity
    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="STAGE_CHANGED",
        title=f"Stage changed: {from_stage_name} → {to_stage.name}",
        description=data.notes or f"Project {project.project_number} moved to {to_stage.name}",
        customer_id=project.customer_id,
        project_id=project.id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ProjectUpdate,
    actor_id: Optional[uuid.UUID] = None,
) -> Project:
    project = await get_project(db, tenant_id, project_id)
    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(project, k, v)
    await db.commit()
    await db.refresh(project)
    return project
