import uuid
from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema


class UserBase(BaseSchema):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    role_name: Optional[str] = Field("operator", description="Role to assign within tenant")


class UserUpdate(BaseSchema):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    is_active: bool
    is_verified: bool
    role_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
