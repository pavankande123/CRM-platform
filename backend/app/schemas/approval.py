import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import Field, field_validator
from app.schemas.common import BaseSchema


VALID_DECISIONS = {"approved", "rejected"}


class ApprovalDecisionCreate(BaseSchema):
    decision: str = Field(..., max_length=50)
    comments: Optional[str] = None

    @field_validator("decision")
    @classmethod
    def validate_dec(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_DECISIONS:
            raise ValueError(f"Decision must be one of {sorted(VALID_DECISIONS)}")
        return clean


class ApprovalDecisionRead(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    approval_request_id: uuid.UUID
    decided_by_id: uuid.UUID
    decision: str
    comments: Optional[str] = None
    decided_at: datetime


class ApprovalRequestBase(BaseSchema):
    entity_type: str = Field(..., max_length=50)  # 'project', 'payment'
    entity_id: uuid.UUID
    approver_id: Optional[uuid.UUID] = None
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None


class ApprovalRequestCreate(ApprovalRequestBase):
    pass


class ApprovalRequestRead(ApprovalRequestBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    requester_id: uuid.UUID
    status: str
    requested_at: datetime
    decided_at: Optional[datetime] = None
    decisions: List[ApprovalDecisionRead] = []
    created_at: datetime
    updated_at: datetime
