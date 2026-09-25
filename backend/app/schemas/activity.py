import datetime
import uuid
from typing import Optional
from app.schemas.common import BaseSchema


class ActivityRead(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    actor_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    activity_type: str
    title: str
    description: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime.datetime
