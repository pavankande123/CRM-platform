from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_permission
from app.core.errors import ConflictError, NotFoundError
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.user import UserCreate, UserRead
from app.services.audit_service import create_audit_entry

router = APIRouter()


@router.get("", response_model=StandardResponse[List[UserRead]], summary="List Tenant Users")
async def list_users(
    current_user: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[UserRead]]:
    """
    List all users in the authenticated tenant organization.
    Cross-tenant user listing is strictly impossible.
    """
    stmt = (
        select(User)
        .options(selectinload(User.role))
        .where(User.organization_id == current_user.organization_id)
        .order_by(User.created_at.asc())
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    data = [
        UserRead(
            id=u.id,
            organization_id=u.organization_id,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            is_verified=u.is_verified,
            role_name=u.role.name if u.role else None,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in users
    ]
    return StandardResponse(data=data, message="Users retrieved successfully")


@router.post("", response_model=StandardResponse[UserRead], summary="Create Tenant User")
async def create_user(
    request: Request,
    data: UserCreate,
    current_user: User = Depends(require_permission("users:manage")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[UserRead]:
    """
    Provision a new user within the authenticated organization.
    Requires 'users:manage' permission.
    """
    clean_email = data.email.lower().strip()

    # Check email uniqueness within this tenant
    stmt = select(User).where(
        User.organization_id == current_user.organization_id,
        User.email == clean_email,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise ConflictError(message=f"A user with email '{clean_email}' already exists in your organization.")

    # Find requested role in current tenant
    role_name = (data.role_name or "operator").lower()
    role_stmt = select(Role).where(
        Role.organization_id == current_user.organization_id,
        Role.name == role_name,
    )
    role = (await db.execute(role_stmt)).scalar_one_or_none()
    if not role:
        # Fallback to system role if exists
        sys_role_stmt = select(Role).where(Role.is_system == True, Role.name == role_name)  # noqa: E712
        role = (await db.execute(sys_role_stmt)).scalar_one_or_none()

    new_user = User(
        organization_id=current_user.organization_id,
        email=clean_email,
        full_name=data.full_name.strip(),
        hashed_password=get_password_hash(data.password),
        is_active=True,
        is_verified=True,
        role_id=role.id if role else None,
    )
    db.add(new_user)
    await db.flush()

    # Record Audit Log
    await create_audit_entry(
        db=db,
        tenant_id=current_user.organization_id,
        actor_id=current_user.id,
        action="USER_CREATE",
        resource="user",
        resource_id=str(new_user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        metadata={"created_email": new_user.email, "role": role_name},
    )

    await db.commit()

    return StandardResponse(
        data=UserRead(
            id=new_user.id,
            organization_id=new_user.organization_id,
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            role_name=role_name,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
        ),
        message="User created successfully",
    )
