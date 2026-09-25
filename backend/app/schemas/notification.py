import uuid
from datetime import datetime
from typing import Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class NotificationBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    notification_type: str = Field("info", max_length=50)
    link_url: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID


class NotificationRead(NotificationBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
