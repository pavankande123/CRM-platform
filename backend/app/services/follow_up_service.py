import datetime
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models.follow_up import FollowUp
from app.schemas.follow_up import FollowUpComplete, FollowUpCreate, FollowUpRead, FollowUpUpdate
from app.services.activity_service import log_activity


async def list_follow_ups(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status: Optional[str] = None,
    overdue_only: bool = False,
    today_only: bool = False,
    customer_id: Optional[uuid.UUID] = None,
    project_id: Optional[uuid.UUID] = None,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[List[FollowUpRead], int]:
    """List follow-ups with overdue and due today calculations."""
    base_query = select(FollowUp).where(FollowUp.tenant_id == tenant_id)

    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    if customer_id:
        base_query = base_query.where(FollowUp.customer_id == customer_id)
    if project_id:
        base_query = base_query.where(FollowUp.project_id == project_id)

    if status:
        base_query = base_query.where(FollowUp.status == status.lower())
    elif overdue_only:
        base_query = base_query.where(FollowUp.status == "pending", FollowUp.due_date < now)
    elif today_only:
        base_query = base_query.where(
            FollowUp.status == "pending",
            FollowUp.due_date >= today_start,
            FollowUp.due_date <= today_end,
        )

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        base_query
        .options(
            selectinload(FollowUp.customer),
            selectinload(FollowUp.project),
            selectinload(FollowUp.assigned_to),
        )
        .order_by(FollowUp.due_date.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = []
    for f in records:
        # Check if overdue (pending and due_date < now)
        due = f.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=datetime.timezone.utc)

        is_over = f.status == "pending" and (due < now)
        is_tod = f.status == "pending" and (today_start <= due <= today_end)

        items.append(
            FollowUpRead(
                id=f.id,
                tenant_id=f.tenant_id,
                customer_id=f.customer_id,
                project_id=f.project_id,
                title=f.title,
                description=f.description,
                due_date=f.due_date,
                status=f.status,
                priority=f.priority,
                completed_at=f.completed_at,
                completed_notes=f.completed_notes,
                created_by_id=f.created_by_id,
                assigned_to_id=f.assigned_to_id,
                customer_name=f.customer.name if f.customer else None,
                project_name=f.project.name if f.project else None,
                assigned_to_name=f.assigned_to.full_name if f.assigned_to else None,
                is_overdue=is_over,
                is_today=is_tod,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
        )

    return items, total


async def create_follow_up(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: FollowUpCreate,
    actor_id: Optional[uuid.UUID] = None,
) -> FollowUp:
    follow_up = FollowUp(
        tenant_id=tenant_id,
        customer_id=data.customer_id,
        project_id=data.project_id,
        title=data.title.strip(),
        description=data.description,
        due_date=data.due_date,
        priority=data.priority or "medium",
        assigned_to_id=data.assigned_to_id or actor_id,
        created_by_id=actor_id,
        status="pending",
    )
    db.add(follow_up)
    await db.flush()

    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="FOLLOW_UP_CREATED",
        title=f"Follow-up scheduled: {follow_up.title}",
        description=f"Due: {follow_up.due_date.strftime('%Y-%m-%d %H:%M')}",
        customer_id=follow_up.customer_id,
        project_id=follow_up.project_id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(follow_up)
    return follow_up


async def complete_follow_up(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    follow_up_id: uuid.UUID,
    data: FollowUpComplete,
    actor_id: Optional[uuid.UUID] = None,
) -> FollowUp:
    stmt = select(FollowUp).where(FollowUp.id == follow_up_id, FollowUp.tenant_id == tenant_id)
    follow_up = (await db.execute(stmt)).scalar_one_or_none()
    if not follow_up:
        raise NotFoundError(message="Follow-up not found.")

    follow_up.status = "completed"
    follow_up.completed_at = datetime.datetime.now(datetime.timezone.utc)
    follow_up.completed_notes = data.completed_notes

    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="FOLLOW_UP_COMPLETED",
        title=f"Follow-up completed: {follow_up.title}",
        description=data.completed_notes or "Marked as completed",
        customer_id=follow_up.customer_id,
        project_id=follow_up.project_id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(follow_up)
    return follow_up


async def cancel_follow_up(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    follow_up_id: uuid.UUID,
    actor_id: Optional[uuid.UUID] = None,
) -> FollowUp:
    stmt = select(FollowUp).where(FollowUp.id == follow_up_id, FollowUp.tenant_id == tenant_id)
    follow_up = (await db.execute(stmt)).scalar_one_or_none()
    if not follow_up:
        raise NotFoundError(message="Follow-up not found.")

    follow_up.status = "cancelled"

    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="FOLLOW_UP_CANCELLED",
        title=f"Follow-up cancelled: {follow_up.title}",
        customer_id=follow_up.customer_id,
        project_id=follow_up.project_id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(follow_up)
    return follow_up
