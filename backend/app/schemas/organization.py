import uuid
from datetime import datetime
from typing import Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class OrganizationBase(BaseSchema):
    name: str = Field(..., min_length=2, max_length=255, description="Tenant organization name")


class OrganizationCreate(OrganizationBase):
    slug: Optional[str] = Field(None, min_length=2, max_length=100)


class OrganizationUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=255)


class OrganizationRead(OrganizationBase):
    id: uuid.UUID
    slug: str
    tier: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
