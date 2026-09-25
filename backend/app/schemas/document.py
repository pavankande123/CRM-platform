import datetime
import uuid
from typing import Optional
from pydantic import Field
from app.schemas.common import BaseSchema


class DocumentMetadataCreate(BaseSchema):
    customer_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    payment_id: Optional[uuid.UUID] = None
    file_name: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., max_length=100)
    file_size_bytes: int = Field(..., ge=0)
    document_category: str = Field("other", description="quotation, invoice, agreement, site_photo, technical_spec")
    storage_url: Optional[str] = None


class DocumentMetadataRead(DocumentMetadataCreate):
    id: uuid.UUID
    tenant_id: uuid.UUID
    uploaded_by_id: Optional[uuid.UUID] = None
    uploaded_by_name: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
