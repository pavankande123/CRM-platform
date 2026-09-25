import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
from app.schemas.common import BaseSchema


ALLOWED_VIEW_ENTITIES = {"customer", "project", "follow_up", "payment"}
ALLOWED_FILTER_OPERATORS = {
    "eq", "=",
    "neq", "!=",
    "gt", ">",
    "gte", ">=",
    "lt", "<",
    "lte", "<=",
    "contains",
    "in",
    "is_empty",
    "is_not_empty",
}


class FilterCondition(BaseSchema):
    field: str = Field(..., min_length=1, max_length=100)
    operator: str = Field(..., max_length=20)
    value: Optional[Any] = None

    @field_validator("operator")
    @classmethod
    def validate_op(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_FILTER_OPERATORS:
            raise ValueError(f"Invalid filter operator '{v}'. Allowed: {sorted(ALLOWED_FILTER_OPERATORS)}")
        return clean

    @field_validator("field")
    @classmethod
    def validate_field(cls, v: str) -> str:
        clean = v.strip().lower()
        import re
        if not re.match(r"^[a-z0-9_]{1,50}$", clean):
            raise ValueError("Field name must be alphanumeric with underscores")
        return clean


class SavedViewBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    entity_type: str = Field(..., max_length=50)
    is_default: bool = False
    is_shared: bool = True
    filters: List[FilterCondition] = []
    visible_columns: Optional[List[str]] = None
    sort_field: Optional[str] = None
    sort_direction: str = Field("desc", max_length=10)

    @field_validator("entity_type")
    @classmethod
    def validate_entity(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ALLOWED_VIEW_ENTITIES:
            raise ValueError(f"entity_type must be one of {sorted(ALLOWED_VIEW_ENTITIES)}")
        return clean


class SavedViewCreate(SavedViewBase):
    pass


class SavedViewUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_default: Optional[bool] = None
    is_shared: Optional[bool] = None
    filters: Optional[List[FilterCondition]] = None
    visible_columns: Optional[List[str]] = None
    sort_field: Optional[str] = None
    sort_direction: Optional[str] = None


class SavedViewRead(SavedViewBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
