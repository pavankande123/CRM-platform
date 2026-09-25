import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class AuditLogRead(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    actor_email: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime


class AuditLogFilter(BaseSchema):
    action: Optional[str] = None
    resource: Optional[str] = None
    actor_id: Optional[uuid.UUID] = None
