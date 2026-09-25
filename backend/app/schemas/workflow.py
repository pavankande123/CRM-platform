import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
from app.schemas.common import BaseSchema


SUPPORTED_TRIGGERS = {
    "customer.created",
    "customer.updated",
    "project.created",
    "project.updated",
    "project.stage_changed",
    "follow_up.created",
    "follow_up.completed",
    "payment.created",
    "payment.updated",
}

SUPPORTED_ACTION_TYPES = {
    "create_follow_up",
    "update_record",
    "create_notification",
    "assign_record",
    "add_activity",
}


class WorkflowConditionSchema(BaseSchema):
    field: str = Field(..., min_length=1, max_length=100)
    operator: str = Field(..., max_length=20)  # 'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'contains', 'in', 'is_empty', 'is_not_empty'
    value: Optional[Any] = None


class WorkflowActionSchema(BaseSchema):
    action_type: str = Field(..., max_length=50)
    params: Dict[str, Any] = {}

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in SUPPORTED_ACTION_TYPES:
            raise ValueError(f"action_type must be one of {sorted(SUPPORTED_ACTION_TYPES)}")
        return clean


class WorkflowBase(BaseSchema):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    entity_type: str = Field(..., max_length=50)  # 'project', 'customer', 'payment', 'follow_up'
    trigger_event: str = Field(..., max_length=100)
    is_active: bool = True
    conditions: List[WorkflowConditionSchema] = []
    actions: List[WorkflowActionSchema] = []

    @field_validator("trigger_event")
    @classmethod
    def validate_trigger(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in SUPPORTED_TRIGGERS:
            raise ValueError(f"trigger_event must be one of {sorted(SUPPORTED_TRIGGERS)}")
        return clean


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    conditions: Optional[List[WorkflowConditionSchema]] = None
    actions: Optional[List[WorkflowActionSchema]] = None


class WorkflowRead(WorkflowBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class WorkflowExecutionRead(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    workflow_id: uuid.UUID
    trigger_event: str
    entity_type: str
    entity_id: uuid.UUID
    idempotency_key: str
    status: str
    retry_count: int
    error_message: Optional[str] = None
    execution_data: Optional[Any] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
