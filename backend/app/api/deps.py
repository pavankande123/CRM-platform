import uuid
from typing import AsyncGenerator, Callable, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.logging import tenant_id_ctx, user_id_ctx
from app.core.security import decode_token
from app.db.session import get_db
from app.models.organization import Organization
from app.models.role import Permission, Role
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the JWT Bearer token,
    loading the active User along with their Organization and Role permissions.
    Sets tenant and user contextvars for tracing.
    """
    if not auth or not auth.credentials:
        raise UnauthorizedError(message="Authentication token missing")

    try:
        payload = decode_token(auth.credentials)
    except Exception:
        raise UnauthorizedError(message="Invalid or expired authentication token")

    if payload.get("type") != "access":
        raise UnauthorizedError(message="Invalid token type (access token expected)")

    # Phase 4 Token Revocation Check
    jti = payload.get("jti")
    if jti and settings.TOKEN_BLACKLIST_ENABLED:
        from app.core.redis import redis_manager
        if await redis_manager.is_token_revoked(jti):
            raise UnauthorizedError(message="Token has been revoked. Please log in again.")


    user_id_str = payload.get("sub")
    tenant_id_str = payload.get("tenant_id")
    if not user_id_str or not tenant_id_str:
        raise UnauthorizedError(message="Malformed token payload")

    try:
        user_uuid = uuid.UUID(user_id_str)
        tenant_uuid = uuid.UUID(tenant_id_str)
    except ValueError:
        raise UnauthorizedError(message="Invalid identifier in token")

    query = (
        select(User)
        .options(
            selectinload(User.organization),
            selectinload(User.role).selectinload(Role.permissions),
        )
        .where(User.id == user_uuid, User.organization_id == tenant_uuid)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError(message="User not found")

    if not user.is_active:
        raise UnauthorizedError(message="User account is deactivated")

    if not user.organization or not user.organization.is_active:
        raise UnauthorizedError(message="Organization account is suspended")

    # Set context variables for structured logs
    tenant_id_ctx.set(str(user.organization_id))
    user_id_ctx.set(str(user.id))

    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
) -> Organization:
    """
    Returns the Organization (Tenant) associated with the authenticated user.
    Guarantees strict tenant resolution at the server level.
    """
    return current_user.organization


def require_permission(permission_code: str) -> Callable:
    """
    Dependency factory to enforce RBAC permissions on endpoints.
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role:
            raise ForbiddenError(message=f"Missing required permission: {permission_code}")

        # If role is system admin, grant all
        if current_user.role.name == "admin":
            return current_user

        user_perms = {p.code for p in current_user.role.permissions}
        if permission_code not in user_perms:
            raise ForbiddenError(message=f"Insufficient permissions: requires '{permission_code}'")

        return current_user

    return permission_checker
