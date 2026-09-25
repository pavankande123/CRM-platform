import datetime
import uuid
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import Activity
from app.models.customer import Customer
from app.models.follow_up import FollowUp
from app.models.payment import Payment
from app.models.pipeline import PipelineStage
from app.models.project import Project
from app.schemas.activity import ActivityRead
from app.schemas.customer import CustomerRead
from app.schemas.dashboard import CoreDashboardResponse, StageDistribution
from app.services.follow_up_service import list_follow_ups


async def get_core_dashboard(db: AsyncSession, tenant_id: uuid.UUID) -> CoreDashboardResponse:
    """
    Computes real-time operational dashboard metrics strictly for tenant.
    Answers: 'What is happening in the business right now?'
    """
    # 1. Total Customers
    cust_count_stmt = select(func.count(Customer.id)).where(Customer.tenant_id == tenant_id)
    total_customers = (await db.execute(cust_count_stmt)).scalar() or 0

    # 2. Active Projects
    active_proj_stmt = select(func.count(Project.id)).where(
        Project.tenant_id == tenant_id,
        Project.status == "active",
    )
    active_projects = (await db.execute(active_proj_stmt)).scalar() or 0

    # 3. Financial Totals
    val_stmt = select(func.coalesce(func.sum(Project.value), 0)).where(Project.tenant_id == tenant_id)
    total_project_value = Decimal(str((await db.execute(val_stmt)).scalar() or 0))

    paid_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.tenant_id == tenant_id,
        Payment.status == "received",
    )
    total_paid = Decimal(str((await db.execute(paid_stmt)).scalar() or 0))
    total_outstanding = max(Decimal("0.00"), total_project_value - total_paid)

    # 4. Projects by Stage
    stage_stmt = (
        select(
            PipelineStage.id,
            PipelineStage.name,
            PipelineStage.color,
            func.count(Project.id),
            func.coalesce(func.sum(Project.value), 0),
        )
        .join(Project, Project.stage_id == PipelineStage.id)
        .where(PipelineStage.tenant_id == tenant_id)
        .group_by(PipelineStage.id, PipelineStage.name, PipelineStage.color)
        .order_by(PipelineStage.order.asc())
    )
    stage_rows = (await db.execute(stage_stmt)).all()
    projects_by_stage = [
        StageDistribution(
            stage_id=row[0],
            stage_name=row[1],
            stage_color=row[2],
            count=int(row[3]),
            total_value=Decimal(str(row[4])),
        )
        for row in stage_rows
    ]

    # 5. Follow-ups (Due Today & Overdue)
    today_items, _ = await list_follow_ups(db, tenant_id, today_only=True, limit=10)
    overdue_items, _ = await list_follow_ups(db, tenant_id, overdue_only=True, limit=10)

    # 6. Recent Customers (Top 5)
    recent_cust_stmt = (
        select(Customer)
        .options(selectinload(Customer.contacts))
        .where(Customer.tenant_id == tenant_id)
        .order_by(Customer.created_at.desc())
        .limit(5)
    )
    recent_custs = (await db.execute(recent_cust_stmt)).scalars().all()
    recent_customers_out = [
        CustomerRead(
            id=c.id,
            tenant_id=c.tenant_id,
            customer_type=c.customer_type,
            name=c.name,
            email=c.email,
            phone=c.phone,
            address_line1=c.address_line1,
            address_line2=c.address_line2,
            city=c.city,
            state=c.state,
            postal_code=c.postal_code,
            country=c.country,
            status=c.status,
            source=c.source,
            notes=c.notes,
            created_by_id=c.created_by_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            primary_contact_name=c.contacts[0].name if c.contacts else None,
            primary_contact_phone=c.contacts[0].phone if c.contacts else None,
        )
        for c in recent_custs
    ]

    # 7. Recent Activity (Top 10)
    act_stmt = (
        select(Activity)
        .options(selectinload(Activity.actor))
        .where(Activity.tenant_id == tenant_id)
        .order_by(Activity.created_at.desc())
        .limit(10)
    )
    recent_acts = (await db.execute(act_stmt)).scalars().all()
    recent_activity_out = [
        ActivityRead(
            id=a.id,
            tenant_id=a.tenant_id,
            customer_id=a.customer_id,
            project_id=a.project_id,
            actor_id=a.actor_id,
            actor_name=a.actor.full_name if a.actor else None,
            activity_type=a.activity_type,
            title=a.title,
            description=a.description,
            metadata_json=a.metadata_json,
            created_at=a.created_at,
        )
        for a in recent_acts
    ]

    return CoreDashboardResponse(
        total_customers=total_customers,
        active_projects=active_projects,
        projects_by_stage=projects_by_stage,
        todays_follow_ups=today_items,
        overdue_follow_ups=overdue_items,
        total_project_value=total_project_value,
        total_paid=total_paid,
        total_outstanding=total_outstanding,
        recent_customers=recent_customers_out,
        recent_activity=recent_activity_out,
    )
