import datetime
import uuid
from typing import Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class NoteCreate(BaseSchema):
    customer_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    follow_up_id: Optional[uuid.UUID] = None
    payment_id: Optional[uuid.UUID] = None
    content: str = Field(..., min_length=1)


class NoteRead(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    author_id: Optional[uuid.UUID] = None
    author_name: Optional[str] = None
    content: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
