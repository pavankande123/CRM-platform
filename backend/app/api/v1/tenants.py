from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_current_user, get_db, require_permission
from app.models.organization import Organization
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.organization import OrganizationRead, OrganizationUpdate
from app.services.audit_service import create_audit_entry

router = APIRouter()


@router.get("/me", response_model=StandardResponse[OrganizationRead], summary="Get Current Tenant Details")
async def get_current_tenant_details(
    tenant: Organization = Depends(get_current_tenant),
) -> StandardResponse[OrganizationRead]:
    """
    Returns information regarding the caller's active tenant organization.
    """
    return StandardResponse(
        data=OrganizationRead.model_validate(tenant),
        message="Tenant information retrieved successfully",
    )


@router.patch("/me", response_model=StandardResponse[OrganizationRead], summary="Update Current Tenant")
async def update_current_tenant(
    request: Request,
    data: OrganizationUpdate,
    tenant: Organization = Depends(get_current_tenant),
    current_user: User = Depends(require_permission("tenant:update")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[OrganizationRead]:
    """
    Update tenant organization settings. Requires 'tenant:update' permission.
    """
    if data.name:
        tenant.name = data.name.strip()

    await create_audit_entry(
        db=db,
        tenant_id=tenant.id,
        actor_id=current_user.id,
        action="ORGANIZATION_UPDATE",
        resource="organization",
        resource_id=str(tenant.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        metadata={"new_name": tenant.name},
    )

    await db.commit()
    await db.refresh(tenant)

    return StandardResponse(
        data=OrganizationRead.model_validate(tenant),
        message="Tenant updated successfully",
    )
