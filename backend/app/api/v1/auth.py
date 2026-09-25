from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse
from app.schemas.common import StandardResponse
from app.schemas.organization import OrganizationRead
from app.schemas.user import UserRead
from app.services.audit_service import create_audit_entry
from app.services.auth_service import authenticate_user, refresh_tokens, register_tenant

router = APIRouter()


@router.post("/register", response_model=StandardResponse[TokenResponse], summary="Register Tenant and Admin User")
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[TokenResponse]:
    """
    Register a new tenant organization and initial administrator user.
    Provisions tenant isolation boundary, default RBAC roles, and generates auth credentials.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    tokens = await register_tenant(
        db=db,
        data=data,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return StandardResponse(data=tokens, message="Organization registered successfully")


@router.post("/login", response_model=StandardResponse[TokenResponse], summary="User Login")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[TokenResponse]:
    """
    Authenticate user with email and password, issuing access and refresh tokens.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    tokens = await authenticate_user(
        db=db,
        email=data.email,
        password=data.password,
        org_slug=data.organization_slug,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return StandardResponse(data=tokens, message="Authenticated successfully")


@router.post("/refresh", response_model=StandardResponse[TokenResponse], summary="Refresh Access Token")
async def refresh(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[TokenResponse]:
    """
    Renew access and refresh tokens using a valid refresh token.
    """
    tokens = await refresh_tokens(db=db, refresh_token_str=data.refresh_token)
    return StandardResponse(data=tokens, message="Tokens refreshed successfully")


@router.post("/logout", response_model=StandardResponse[dict], summary="User Logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[dict]:
    """
    Log out current session, logging audit event.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Phase 4 Token Revocation on Logout
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token_str = auth_header.split(" ", 1)[1]
        try:
            import time
            from app.core.security import decode_token
            from app.core.redis import redis_manager
            payload = decode_token(token_str)
            jti = payload.get("jti")
            if jti:
                exp = payload.get("exp", 0)
                now_ts = int(time.time())
                remaining = max(1, exp - now_ts) if exp else 3600
                await redis_manager.revoke_token(jti, ttl_seconds=remaining)
        except Exception:
            pass

    await create_audit_entry(
        db=db,
        tenant_id=current_user.organization_id,
        actor_id=current_user.id,
        action="LOGOUT",
        resource="auth",
        resource_id=str(current_user.id),
        ip_address=client_ip,
        user_agent=user_agent,
    )
    await db.commit()

    return StandardResponse(data={"logged_out": True}, message="Successfully logged out")


@router.get("/me", response_model=StandardResponse[dict], summary="Get Current User Profile")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """
    Returns current authenticated user details and active organization tenant.
    """
    role_name = current_user.role.name if current_user.role else "user"
    permissions = [p.code for p in current_user.role.permissions] if current_user.role else []

    user_data = UserRead(
        id=current_user.id,
        organization_id=current_user.organization_id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        role_name=role_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
    org_data = OrganizationRead(
        id=current_user.organization.id,
        name=current_user.organization.name,
        slug=current_user.organization.slug,
        tier=current_user.organization.tier,
        is_active=current_user.organization.is_active,
        created_at=current_user.organization.created_at,
        updated_at=current_user.organization.updated_at,
    )

    return StandardResponse(
        data={
            "user": user_data,
            "organization": org_data,
            "permissions": permissions,
        },
        message="Current user profile",
    )
