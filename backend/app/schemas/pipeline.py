import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class PipelineStageBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    order: int = Field(..., ge=0)
    probability_percent: int = Field(0, ge=0, le=100)
    is_closed_won: bool = False
    is_closed_lost: bool = False
    color: str = Field("cyan", max_length=20)


class PipelineStageCreate(PipelineStageBase):
    pass


class PipelineStageRead(PipelineStageBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    pipeline_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PipelineBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    product_id: Optional[uuid.UUID] = None
    is_default: bool = False
    is_active: bool = True


class PipelineCreate(PipelineBase):
    stages: Optional[List[PipelineStageCreate]] = None


class PipelineRead(PipelineBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    stages: List[PipelineStageRead] = []
    created_at: datetime
    updated_at: datetime
