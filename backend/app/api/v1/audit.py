from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_permission
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse

router = APIRouter()


@router.get("/logs", response_model=StandardResponse[PaginatedResponse[AuditLogRead]], summary="Get Tenant Audit Logs")
async def get_audit_logs(
    pagination: PaginationParams = Depends(),
    action: Optional[str] = Query(None, description="Filter by action code"),
    resource: Optional[str] = Query(None, description="Filter by resource type"),
    current_user: User = Depends(require_permission("audit:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PaginatedResponse[AuditLogRead]]:
    """
    Retrieve audit logs strictly scoped to the caller's organization.
    Cross-tenant log access is prohibited.
    """
    # Strict tenant isolation filter
    base_query = select(AuditLog).where(AuditLog.tenant_id == current_user.organization_id)

    if action:
        base_query = base_query.where(AuditLog.action == action.upper())
    if resource:
        base_query = base_query.where(AuditLog.resource == resource.lower())

    # Count total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Query items ordered by created_at DESC
    stmt = (
        base_query
        .options(selectinload(AuditLog.actor))
        .order_by(AuditLog.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = [
        AuditLogRead(
            id=r.id,
            tenant_id=r.tenant_id,
            actor_id=r.actor_id,
            actor_email=r.actor.email if r.actor else None,
            action=r.action,
            resource=r.resource,
            resource_id=r.resource_id,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            metadata_json=r.metadata_json,
            created_at=r.created_at,
        )
        for r in records
    ]

    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0

    return StandardResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
        ),
        message="Audit logs retrieved successfully",
    )
