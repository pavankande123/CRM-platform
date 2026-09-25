import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class ProductBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    is_active: Optional[bool] = None


class ProductRead(ProductBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
