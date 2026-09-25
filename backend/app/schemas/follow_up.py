import datetime
import uuid
from typing import Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class FollowUpBase(BaseSchema):
    customer_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: datetime.datetime
    priority: str = Field("medium", description="low, medium, high")
    assigned_to_id: Optional[uuid.UUID] = None


class FollowUpCreate(FollowUpBase):
    pass


class FollowUpUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    priority: Optional[str] = None
    assigned_to_id: Optional[uuid.UUID] = None
    status: Optional[str] = None


class FollowUpComplete(BaseSchema):
    completed_notes: Optional[str] = None


class FollowUpRead(FollowUpBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    completed_at: Optional[datetime.datetime] = None
    completed_notes: Optional[str] = None
    created_by_id: Optional[uuid.UUID] = None
    customer_name: Optional[str] = None
    project_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    is_overdue: bool = False
    is_today: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime
