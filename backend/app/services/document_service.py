import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import DocumentMetadata
from app.schemas.document import DocumentMetadataCreate, DocumentMetadataRead
from app.services.activity_service import log_activity


async def list_documents(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: Optional[uuid.UUID] = None,
    project_id: Optional[uuid.UUID] = None,
) -> List[DocumentMetadataRead]:
    base_query = select(DocumentMetadata).where(DocumentMetadata.tenant_id == tenant_id)
    if customer_id:
        base_query = base_query.where(DocumentMetadata.customer_id == customer_id)
    if project_id:
        base_query = base_query.where(DocumentMetadata.project_id == project_id)

    stmt = (
        base_query
        .options(selectinload(DocumentMetadata.uploaded_by))
        .order_by(DocumentMetadata.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return [
        DocumentMetadataRead(
            id=d.id,
            tenant_id=d.tenant_id,
            customer_id=d.customer_id,
            project_id=d.project_id,
            payment_id=d.payment_id,
            file_name=d.file_name,
            file_type=d.file_type,
            file_size_bytes=d.file_size_bytes,
            document_category=d.document_category,
            storage_url=d.storage_url,
            uploaded_by_id=d.uploaded_by_id,
            uploaded_by_name=d.uploaded_by.full_name if d.uploaded_by else None,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in records
    ]


async def create_document(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: DocumentMetadataCreate,
    actor_id: Optional[uuid.UUID] = None,
) -> DocumentMetadata:
    doc = DocumentMetadata(
        tenant_id=tenant_id,
        customer_id=data.customer_id,
        project_id=data.project_id,
        payment_id=data.payment_id,
        file_name=data.file_name.strip(),
        file_type=data.file_type,
        file_size_bytes=data.file_size_bytes,
        document_category=data.document_category or "other",
        storage_url=data.storage_url,
        uploaded_by_id=actor_id,
    )
    db.add(doc)
    await db.flush()

    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="DOCUMENT_ATTACHED",
        title=f"Document linked: {doc.file_name}",
        description=f"Category: {doc.document_category}",
        customer_id=doc.customer_id,
        project_id=doc.project_id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(doc)
    return doc
