import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema


class ContactBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    designation: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    is_primary: bool = False
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    designation: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class ContactRead(ContactBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CustomerBase(BaseSchema):
    customer_type: str = Field("commercial", description="commercial, industrial, residential, institution")
    name: str = Field(..., min_length=1, max_length=255, description="Customer or company name")
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"
    status: str = Field("active", description="active, lead, inactive")
    source: str = Field("direct", description="referral, website, direct, exhibition")
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    primary_contact: Optional[ContactCreate] = None


class CustomerUpdate(BaseSchema):
    customer_type: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class CustomerRead(CustomerBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    primary_contact_name: Optional[str] = None
    primary_contact_phone: Optional[str] = None


from app.schemas.project import ProjectRead
from app.schemas.payment import PaymentRead
from app.schemas.follow_up import FollowUpRead
from app.schemas.note import NoteRead
from app.schemas.document import DocumentMetadataRead
from app.schemas.activity import ActivityRead


class CustomerDetailRead(CustomerRead):
    contacts: List[ContactRead] = []
    projects: List[ProjectRead] = []
    payments: List[PaymentRead] = []
    follow_ups: List[FollowUpRead] = []
    notes_list: List[NoteRead] = []
    documents: List[DocumentMetadataRead] = []
    activities: List[ActivityRead] = []
