import datetime
import uuid
from decimal import Decimal
from typing import Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class PaymentBase(BaseSchema):
    customer_id: uuid.UUID
    project_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Payment amount must be greater than zero")
    currency: str = "INR"
    payment_date: datetime.date
    payment_method: str = Field("bank_transfer", description="bank_transfer, cheque, neft_rtgs, upi, cash")
    reference_number: Optional[str] = Field(None, max_length=100, description="UTR / Cheque Number / Transaction ID")
    status: str = Field("received", description="received, pending_clearance, bounced, refunded")
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseSchema):
    amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    payment_date: Optional[datetime.date] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PaymentRead(PaymentBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    payment_number: str
    customer_name: Optional[str] = None
    project_name: Optional[str] = None
    recorded_by_id: Optional[uuid.UUID] = None
    recorded_by_name: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class FinancialSummary(BaseSchema):
    total_project_value: Decimal = Decimal("0.00")
    total_paid: Decimal = Decimal("0.00")
    total_outstanding: Decimal = Decimal("0.00")
    payment_count: int = 0
