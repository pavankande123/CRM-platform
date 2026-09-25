import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.document import DocumentMetadataCreate, DocumentMetadataRead
from app.services import document_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[DocumentMetadataRead]], summary="List Document Metadata")
async def list_documents_endpoint(
    customer_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[DocumentMetadataRead]]:
    docs = await document_service.list_documents(
        db, current_user.organization_id, customer_id, project_id
    )
    return StandardResponse(data=docs, message="Documents retrieved")


@router.post("", response_model=StandardResponse[DocumentMetadataRead], status_code=status.HTTP_201_CREATED, summary="Record Document Metadata")
async def create_document_endpoint(
    data: DocumentMetadataCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[DocumentMetadataRead]:
    doc = await document_service.create_document(
        db, current_user.organization_id, data, current_user.id
    )
    return StandardResponse(
        data=DocumentMetadataRead(
            id=doc.id,
            tenant_id=doc.tenant_id,
            customer_id=doc.customer_id,
            project_id=doc.project_id,
            payment_id=doc.payment_id,
            file_name=doc.file_name,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            document_category=doc.document_category,
            storage_url=doc.storage_url,
            uploaded_by_id=doc.uploaded_by_id,
            uploaded_by_name=current_user.full_name,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        ),
        message="Document metadata recorded successfully",
    )
