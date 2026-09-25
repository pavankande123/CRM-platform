from typing import Optional
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema
from app.schemas.organization import OrganizationRead
from app.schemas.user import UserRead


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(..., min_length=1)
    organization_slug: Optional[str] = Field(None, description="Optional tenant slug to disambiguate organization")


class RegisterRequest(BaseSchema):
    organization_name: str = Field(..., min_length=2, max_length=255, description="Tenant organization name")
    full_name: str = Field(..., min_length=2, max_length=255, description="User full name")
    email: EmailStr = Field(..., description="Corporate email address")
    password: str = Field(..., min_length=8, max_length=128, description="Strong password (min 8 chars)")


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
    organization: OrganizationRead


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class PasswordResetRequest(BaseSchema):
    email: EmailStr
