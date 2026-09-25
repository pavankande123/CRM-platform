import datetime
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.project import Project
from app.schemas.payment import FinancialSummary, PaymentCreate, PaymentRead, PaymentUpdate
from app.services.activity_service import log_activity


async def generate_payment_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate sequential payment receipt number (e.g. ENX-PAY-2026-0001)."""
    current_year = datetime.datetime.now().year
    prefix = f"ENX-PAY-{current_year}-"
    count_stmt = select(func.count()).select_from(Payment).where(
        Payment.tenant_id == tenant_id,
        Payment.payment_number.like(f"{prefix}%")
    )
    count = (await db.execute(count_stmt)).scalar() or 0
    return f"{prefix}{count + 1:04d}"


async def list_payments(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: Optional[uuid.UUID] = None,
    project_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[List[PaymentRead], int]:
    base_query = select(Payment).where(Payment.tenant_id == tenant_id)

    if customer_id:
        base_query = base_query.where(Payment.customer_id == customer_id)
    if project_id:
        base_query = base_query.where(Payment.project_id == project_id)
    if status:
        base_query = base_query.where(Payment.status == status.lower())

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        base_query
        .options(
            selectinload(Payment.customer),
            selectinload(Payment.project),
            selectinload(Payment.recorded_by),
        )
        .order_by(Payment.payment_date.desc(), Payment.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = [
        PaymentRead(
            id=p.id,
            tenant_id=p.tenant_id,
            payment_number=p.payment_number,
            customer_id=p.customer_id,
            project_id=p.project_id,
            amount=p.amount,
            currency=p.currency,
            payment_date=p.payment_date,
            payment_method=p.payment_method,
            reference_number=p.reference_number,
            status=p.status,
            notes=p.notes,
            customer_name=p.customer.name if p.customer else None,
            project_name=p.project.name if p.project else None,
            project_number=p.project.project_number if p.project else None,
            recorded_by_id=p.recorded_by_id,
            recorded_by_name=p.recorded_by.full_name if p.recorded_by else None,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in records
    ]
    return items, total


async def create_payment(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: PaymentCreate,
    actor_id: Optional[uuid.UUID] = None,
) -> Payment:
    # Validate project belongs to tenant
    proj_stmt = select(Project).where(
        Project.id == data.project_id,
        Project.tenant_id == tenant_id,
    )
    project = (await db.execute(proj_stmt)).scalar_one_or_none()
    if not project:
        raise NotFoundError(message="Specified Project not found in your organization.")

    # Resolve customer_id
    customer_id = data.customer_id or project.customer_id
    cust_stmt = select(Customer).where(Customer.id == customer_id, Customer.tenant_id == tenant_id)
    customer = (await db.execute(cust_stmt)).scalar_one_or_none()
    if not customer:
        raise NotFoundError(message="Specified Customer not found in your organization.")

    if project.customer_id != customer_id:
        raise ValidationError(message="Specified Project does not belong to this Customer.")

    payment_number = await generate_payment_number(db, tenant_id)

    payment = Payment(
        tenant_id=tenant_id,
        customer_id=customer_id,
        project_id=data.project_id,
        payment_number=payment_number,
        amount=data.amount,
        currency=data.currency or "INR",
        payment_date=data.payment_date,
        payment_method=data.payment_method or "bank_transfer",
        reference_number=data.reference_number,
        status=data.status or "received",
        notes=data.notes,
        recorded_by_id=actor_id,
    )
    db.add(payment)
    await db.flush()

    # Log business activity
    ref_text = f" • Ref: {payment.reference_number}" if payment.reference_number else ""
    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="PAYMENT_RECORDED",
        title=f"Payment received: ₹{payment.amount:,.2f} ({payment.payment_number})",
        description=f"Project: {project.name}{ref_text}",
        customer_id=customer.id,
        project_id=project.id,
        actor_id=actor_id,
    )

    payment_id = payment.id
    record_data = {
        "payment_number": payment.payment_number,
        "amount": float(payment.amount),
        "status": payment.status,
        "payment_method": payment.payment_method,
        "customer_id": str(payment.customer_id),
        "project_id": str(payment.project_id) if payment.project_id else None,
        "recorded_by_id": str(payment.recorded_by_id) if payment.recorded_by_id else None,
    }

    await db.commit()

    # Dispatch workflow event
    try:
        from app.services import workflow_engine
        await workflow_engine.dispatch_event(
            db=db,
            tenant_id=tenant_id,
            trigger_event="payment.created",
            entity_type="payment",
            entity_id=payment_id,
            record_data=record_data,
        )
    except Exception as exc:
        logger.warning(f"Workflow dispatch error for payment.created: {exc}")

    stmt = (
        select(Payment)
        .options(
            selectinload(Payment.customer),
            selectinload(Payment.project),
            selectinload(Payment.recorded_by),
        )
        .where(Payment.id == payment_id)
    )
    return (await db.execute(stmt)).scalar_one()


async def get_financial_summary(db: AsyncSession, tenant_id: uuid.UUID) -> FinancialSummary:
    """Calculate aggregated total project value, total collected, and outstanding balance."""
    # Sum of project values for this tenant
    proj_val_stmt = select(func.coalesce(func.sum(Project.value), 0)).where(Project.tenant_id == tenant_id)
    total_project_val = Decimal(str((await db.execute(proj_val_stmt)).scalar() or 0))

    # Sum of received payments
    paid_stmt = select(
        func.coalesce(func.sum(Payment.amount), 0),
        func.count(Payment.id),
    ).where(Payment.tenant_id == tenant_id, Payment.status == "received")
    row = (await db.execute(paid_stmt)).first()
    total_paid = Decimal(str(row[0] or 0))
    payment_count = int(row[1] or 0)

    total_outstanding = max(Decimal("0.00"), total_project_val - total_paid)

    return FinancialSummary(
        total_project_value=total_project_val,
        total_paid=total_paid,
        total_outstanding=total_outstanding,
        payment_count=payment_count,
    )
