import re
import uuid
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.organization import Organization
from app.models.role import Permission, Role
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.organization import OrganizationRead
from app.schemas.user import UserRead
from app.services.audit_service import create_audit_entry


def slugify(text: str) -> str:
    """Generate a clean URL slug from organization name."""
    clean = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", clean)


async def ensure_permissions(db: AsyncSession) -> dict[str, Permission]:
    """Ensure baseline system permissions exist in database."""
    default_permissions = [
        ("tenant:read", "View tenant details and configuration"),
        ("tenant:update", "Update tenant details and configuration"),
        ("users:read", "View users in current organization"),
        ("users:manage", "Create, update, or deactivate organization users"),
        ("audit:read", "View organization audit trail"),
        ("crm:read", "View CRM records"),
        ("crm:write", "Create and update CRM records"),
        ("crm:delete", "Delete CRM records"),
    ]
    perm_map = {}
    for code, desc in default_permissions:
        stmt = select(Permission).where(Permission.code == code)
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()
        if not perm:
            perm = Permission(code=code, description=desc)
            db.add(perm)
            await db.flush()
        perm_map[code] = perm
    return perm_map


async def create_tenant_roles(db: AsyncSession, organization_id: uuid.UUID) -> Role:
    """Create default roles (Admin, Operator, Viewer) for a new tenant."""
    perms = await ensure_permissions(db)

    # Admin role with full permissions
    admin_role = Role(
        organization_id=organization_id,
        name="admin",
        description="Tenant Administrator with full access",
        is_system=True,
    )
    admin_role.permissions.extend(perms.values())
    db.add(admin_role)

    # Operator role (operator-driven workflow matching Enermax business problem)
    operator_role = Role(
        organization_id=organization_id,
        name="operator",
        description="Daily CRM Operator with read, write, and audit access",
        is_system=True,
    )
    operator_role.permissions.extend([
        perms["tenant:read"],
        perms["users:read"],
        perms["audit:read"],
        perms["crm:read"],
        perms["crm:write"],
    ])
    db.add(operator_role)

    # Viewer role
    viewer_role = Role(
        organization_id=organization_id,
        name="viewer",
        description="Read-only access to CRM records",
        is_system=True,
    )
    viewer_role.permissions.extend([
        perms["tenant:read"],
        perms["crm:read"],
    ])
    db.add(viewer_role)

    await db.flush()
    return admin_role


async def register_tenant(
    db: AsyncSession,
    data: RegisterRequest,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> TokenResponse:
    """
    Registers a new Tenant Organization along with the initial Admin User.
    Enforces uniqueness, provisions default RBAC roles, generates JWT tokens, and writes audit record.
    """
    slug = slugify(data.organization_name)

    # Check organization slug uniqueness
    stmt = select(Organization).where(Organization.slug == slug)
    existing_org = (await db.execute(stmt)).scalar_one_or_none()
    if existing_org:
        # Append unique random suffix if slug exists
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    # Create Organization
    org = Organization(
        name=data.organization_name,
        slug=slug,
        is_active=True,
        tier="standard",
    )
    db.add(org)
    await db.flush()

    # Create standard tenant roles
    admin_role = await create_tenant_roles(db, org.id)

    # Hash user password
    hashed_pwd = get_password_hash(data.password)

    # Create User
    user = User(
        organization_id=org.id,
        email=data.email.lower().strip(),
        full_name=data.full_name.strip(),
        hashed_password=hashed_pwd,
        is_active=True,
        is_verified=True,
        role_id=admin_role.id,
    )
    db.add(user)
    await db.flush()

    # Generate JWT Tokens
    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(org.id),
        role="admin",
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(org.id),
    )

    # Record Audit Log
    await create_audit_entry(
        db=db,
        tenant_id=org.id,
        actor_id=user.id,
        action="REGISTER",
        resource="organization",
        resource_id=str(org.id),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"organization_name": org.name, "user_email": user.email},
    )

    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead(
            id=user.id,
            organization_id=user.organization_id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role_name="admin",
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
        organization=OrganizationRead(
            id=org.id,
            name=org.name,
            slug=org.slug,
            tier=org.tier,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at,
        ),
    )


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
    org_slug: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> TokenResponse:
    """
    Authenticates a user by email and password, optionally scoped to an organization slug.
    Verifies active status, verifies password with Argon2/Bcrypt, logs audit entry, and generates tokens.
    """
    clean_email = email.lower().strip()
    query = (
        select(User)
        .join(Organization, User.organization_id == Organization.id)
        .options(selectinload(User.role), selectinload(User.organization))
        .where(User.email == clean_email)
    )

    if org_slug:
        query = query.where(Organization.slug == org_slug.strip().lower())

    result = await db.execute(query)
    users = result.scalars().all()

    if not users:
        raise UnauthorizedError(message="Invalid email or password")

    # If multiple organizations have the same email and no slug was passed, require org_slug
    if len(users) > 1 and not org_slug:
        raise ConflictError(
            message="Multiple organizations found for this email. Please specify your organization slug.",
            details={"organizations": [u.organization.slug for u in users]},
        )

    user = users[0]

    if not user.is_active:
        raise UnauthorizedError(message="This account has been deactivated.")

    if not user.organization.is_active:
        raise UnauthorizedError(message="Organization account is suspended.")

    if not verify_password(password, user.hashed_password):
        raise UnauthorizedError(message="Invalid email or password")

    role_name = user.role.name if user.role else "user"

    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.organization_id),
        role=role_name,
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(user.organization_id),
    )

    # Record Audit Log
    await create_audit_entry(
        db=db,
        tenant_id=user.organization_id,
        actor_id=user.id,
        action="LOGIN",
        resource="auth",
        resource_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"email": user.email},
    )

    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead(
            id=user.id,
            organization_id=user.organization_id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role_name=role_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
        organization=OrganizationRead(
            id=user.organization.id,
            name=user.organization.name,
            slug=user.organization.slug,
            tier=user.organization.tier,
            is_active=user.organization.is_active,
            created_at=user.organization.created_at,
            updated_at=user.organization.updated_at,
        ),
    )


async def refresh_tokens(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """Validate a refresh token and issue a fresh pair of tokens."""
    try:
        payload = decode_token(refresh_token_str)
    except Exception:
        raise UnauthorizedError(message="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedError(message="Token type is not a refresh token")

    old_jti = payload.get("jti")
    from app.core.redis import redis_manager
    if old_jti and settings.TOKEN_BLACKLIST_ENABLED:
        if await redis_manager.is_token_revoked(old_jti):
            raise UnauthorizedError(message="Refresh token has been revoked")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    query = (
        select(User)
        .options(selectinload(User.role), selectinload(User.organization))
        .where(User.id == uuid.UUID(user_id), User.organization_id == uuid.UUID(tenant_id))
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.is_active or not user.organization.is_active:
        raise UnauthorizedError(message="User or organization is inactive")

    role_name = user.role.name if user.role else "user"

    new_access = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.organization_id),
        role=role_name,
    )
    new_refresh = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(user.organization_id),
    )

    # Invalidate old refresh token (Token Rotation)
    if old_jti and settings.TOKEN_BLACKLIST_ENABLED:
        await redis_manager.revoke_token(old_jti, ttl_seconds=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)


    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead(
            id=user.id,
            organization_id=user.organization_id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role_name=role_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
        organization=OrganizationRead(
            id=user.organization.id,
            name=user.organization.name,
            slug=user.organization.slug,
            tier=user.organization.tier,
            is_active=user.organization.is_active,
            created_at=user.organization.created_at,
            updated_at=user.organization.updated_at,
        ),
    )
