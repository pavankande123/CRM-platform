import datetime
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.approval import ApprovalRequest, ApprovalDecision
from app.models.user import User
from app.schemas.approval import ApprovalDecisionCreate, ApprovalRequestCreate
from app.services import notification_service


async def create_approval_request(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    requester_id: uuid.UUID,
    data: ApprovalRequestCreate,
) -> ApprovalRequest:
    req = ApprovalRequest(
        tenant_id=tenant_id,
        entity_type=data.entity_type.strip().lower(),
        entity_id=data.entity_id,
        requester_id=requester_id,
        approver_id=data.approver_id,
        title=data.title.strip(),
        description=data.description,
        status="pending",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    # Notify specific approver if assigned
    if data.approver_id:
        try:
            await notification_service.create_notification(
                db,
                tenant_id=tenant_id,
                user_id=data.approver_id,
                title=f"Approval Requested: {data.title}",
                message=f"An approval request requires your review for {data.entity_type}.",
                notification_type="approval",
                link_url=f"/approvals/{req.id}",
            )
        except Exception:
            pass

    return req


async def list_approval_requests(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    status: Optional[str] = None,
    entity_type: Optional[str] = None,
) -> List[ApprovalRequest]:
    stmt = (
        select(ApprovalRequest)
        .options(selectinload(ApprovalRequest.decisions))
        .where(ApprovalRequest.tenant_id == tenant_id)
    )
    if status:
        stmt = stmt.where(ApprovalRequest.status == status.strip().lower())
    if entity_type:
        stmt = stmt.where(ApprovalRequest.entity_type == entity_type.strip().lower())

    stmt = stmt.order_by(ApprovalRequest.requested_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_approval_request(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    request_id: uuid.UUID,
) -> ApprovalRequest:
    stmt = (
        select(ApprovalRequest)
        .options(selectinload(ApprovalRequest.decisions))
        .where(ApprovalRequest.id == request_id, ApprovalRequest.tenant_id == tenant_id)
    )
    req = (await db.execute(stmt)).scalar_one_or_none()
    if not req:
        raise NotFoundError(message="Approval request not found.")
    return req


async def decide_approval_request(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    request_id: uuid.UUID,
    user: User,
    data: ApprovalDecisionCreate,
) -> ApprovalRequest:
    req = await get_approval_request(db, tenant_id, request_id)

    if req.status != "pending":
        raise ValidationError(message=f"Approval request is already {req.status}.")

    # Check permission: User must be admin or the assigned approver
    if req.approver_id and req.approver_id != user.id and user.role_name != "admin":
        raise ForbiddenError(message="You are not authorized to make a decision on this approval request.")

    decision_val = data.decision.strip().lower()
    now = datetime.datetime.now(datetime.timezone.utc)

    decision_record = ApprovalDecision(
        tenant_id=tenant_id,
        approval_request_id=req.id,
        decided_by_id=user.id,
        decision=decision_val,
        comments=data.comments,
        decided_at=now,
    )
    db.add(decision_record)

    req.status = decision_val
    req.decided_at = now

    await db.commit()
    await db.refresh(req)

    # Notify requester
    try:
        await notification_service.create_notification(
            db,
            tenant_id=tenant_id,
            user_id=req.requester_id,
            title=f"Approval Request {decision_val.title()}: {req.title}",
            message=f"Your request was {decision_val} by {user.full_name}. Comments: {data.comments or 'None'}",
            notification_type="success" if decision_val == "approved" else "warning",
            link_url=f"/approvals/{req.id}",
        )
    except Exception:
        pass

    return await get_approval_request(db, tenant_id, request_id)
