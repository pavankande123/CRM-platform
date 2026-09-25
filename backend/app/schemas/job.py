import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    queue: str = Field(default="default", max_length=50)
    job_type: str = Field(..., max_length=100)
    payload: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_backoff_seconds: int = Field(default=5, ge=1, le=3600)
    scheduled_at: Optional[datetime.datetime] = None
    idempotency_key: Optional[str] = Field(default=None, max_length=128)
    correlation_id: Optional[str] = Field(default=None, max_length=64)


class JobRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    queue: str
    job_type: str
    payload: Dict[str, Any]
    status: str
    retry_count: int
    max_retries: int
    retry_backoff_seconds: int
    scheduled_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    result_data: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class JobRetryResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    message: str
