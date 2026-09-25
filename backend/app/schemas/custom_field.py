import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
from app.schemas.common import BaseSchema


VALID_ENTITY_TYPES = {"customer", "project", "product"}
VALID_FIELD_TYPES = {"text", "number", "currency", "date", "boolean", "select"}


class CustomFieldBase(BaseSchema):
    entity_type: str = Field(..., max_length=50)
    field_name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=150)
    field_type: str = Field(..., max_length=50)
    is_required: bool = False
    is_searchable: bool = True
    is_active: bool = True
    options: Optional[List[str]] = None

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_ENTITY_TYPES:
            raise ValueError(f"entity_type must be one of {sorted(VALID_ENTITY_TYPES)}")
        return clean

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_FIELD_TYPES:
            raise ValueError(f"field_type must be one of {sorted(VALID_FIELD_TYPES)}")
        return clean

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        clean = v.strip().lower().replace(" ", "_")
        import re
        if not re.match(r"^[a-z0-9_]{2,50}$", clean):
            raise ValueError("field_name must contain only lowercase letters, digits, and underscores (2-50 chars)")
        return clean


class CustomFieldCreate(CustomFieldBase):
    pass


class CustomFieldUpdate(BaseSchema):
    display_name: Optional[str] = Field(None, min_length=1, max_length=150)
    is_required: Optional[bool] = None
    is_searchable: Optional[bool] = None
    is_active: Optional[bool] = None
    options: Optional[List[str]] = None


class CustomFieldRead(CustomFieldBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CustomFieldValueItem(BaseSchema):
    field_id: uuid.UUID
    value: Any


class CustomFieldValueRead(BaseSchema):
    id: uuid.UUID
    tenant_id: uuid.UUID
    field_id: uuid.UUID
    field_name: str
    display_name: str
    field_type: str
    entity_type: str
    entity_id: uuid.UUID
    value: Any


class BulkCustomFieldValuesRequest(BaseSchema):
    values: Dict[str, Any]  # key can be field_name or field_id (UUID string)
