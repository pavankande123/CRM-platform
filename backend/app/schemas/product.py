import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import Field, model_validator
from app.schemas.common import BaseSchema


class ProductBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    is_active: bool = True

    @model_validator(mode="before")
    @classmethod
    def sync_code_sku(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val = data.get("code") or data.get("sku")
            if val:
                data["code"] = val
                data["sku"] = val
        return data


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    is_active: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def sync_code_sku(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val = data.get("code") or data.get("sku")
            if val:
                data["code"] = val
                data["sku"] = val
        return data


class ProductRead(ProductBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def sync_sku(self) -> "ProductRead":
        if not self.sku and self.code:
            self.sku = self.code
        elif not self.code and self.sku:
            self.code = self.sku
        return self
