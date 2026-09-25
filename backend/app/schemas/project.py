import datetime
import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class ProjectBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    customer_id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    pipeline_id: Optional[uuid.UUID] = None
    stage_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    value: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = "INR"
    expected_completion_date: Optional[datetime.date] = None
    status: str = Field("active", description="active, completed, on_hold, cancelled")
    priority: str = Field("medium", description="low, medium, high, critical")
    owner_id: Optional[uuid.UUID] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    product_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    value: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    expected_completion_date: Optional[datetime.date] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None


class ProjectStageChange(BaseSchema):
    stage_id: uuid.UUID
    notes: Optional[str] = None


class ProjectStageHistoryRead(BaseSchema):
    id: uuid.UUID
    project_id: uuid.UUID
    from_stage_id: Optional[uuid.UUID] = None
    from_stage_name: Optional[str] = None
    to_stage_id: uuid.UUID
    to_stage_name: str
    changed_by_id: Optional[uuid.UUID] = None
    changed_by_name: Optional[str] = None
    notes: Optional[str] = None
    changed_at: datetime.datetime


class ProjectRead(ProjectBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    project_number: str
    pipeline_id: uuid.UUID
    stage_id: uuid.UUID
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    pipeline_name: Optional[str] = None
    stage_name: Optional[str] = None
    stage_color: Optional[str] = None
    owner_name: Optional[str] = None
    total_paid: Decimal = Decimal("0.00")
    outstanding_amount: Decimal = Decimal("0.00")
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ProjectDetailRead(ProjectRead):
    stage_history: List[ProjectStageHistoryRead] = []
