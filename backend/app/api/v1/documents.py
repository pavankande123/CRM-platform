import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.core.errors import NotFoundError, ValidationError
from app.core.storage import get_storage_backend, sanitize_filename, validate_file_metadata
from app.models.document import DocumentMetadata
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


@router.post("/upload", response_model=StandardResponse[DocumentMetadataRead], status_code=status.HTTP_201_CREATED, summary="Upload Document Binary")
async def upload_document_endpoint(
    file: UploadFile = File(...),
    customer_id: Optional[uuid.UUID] = Form(None),
    project_id: Optional[uuid.UUID] = Form(None),
    payment_id: Optional[uuid.UUID] = Form(None),
    document_category: str = Form("other"),
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[DocumentMetadataRead]:
    """Uploads document binary to tenant storage abstraction and creates metadata record."""
    content = await file.read()
    file_name = file.filename or "document.dat"
    content_type = file.content_type or "application/octet-stream"

    validate_file_metadata(file_name, content_type, len(content))

    storage = get_storage_backend()
    saved = await storage.save_file(
        tenant_id=current_user.organization_id,
        file_name=file_name,
        content=content,
        content_type=content_type,
    )

    doc_create = DocumentMetadataCreate(
        customer_id=customer_id,
        project_id=project_id,
        payment_id=payment_id,
        file_name=saved["file_name"],
        file_type=saved["file_type"],
        file_size_bytes=saved["file_size_bytes"],
        document_category=document_category,
        storage_url=saved["storage_path"],
    )

    doc = await document_service.create_document(
        db, current_user.organization_id, doc_create, current_user.id
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
        message="Document uploaded successfully",
    )


@router.get("/{id}/download", summary="Download Document File")
async def download_document_endpoint(
    id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download document binary with tenant boundary check."""
    stmt = select(DocumentMetadata).where(
        DocumentMetadata.id == id,
        DocumentMetadata.tenant_id == current_user.organization_id,
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc or not doc.storage_url:
        raise NotFoundError(message="Document not found or has no attached binary.")

    storage = get_storage_backend()
    content = await storage.get_file(tenant_id=current_user.organization_id, storage_path=doc.storage_url)

    safe_name = sanitize_filename(doc.file_name)
    return Response(
        content=content,
        media_type=doc.file_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
