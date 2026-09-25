import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.note import NoteCreate, NoteRead
from app.services import note_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[NoteRead]], summary="List Notes")
async def list_notes_endpoint(
    customer_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[NoteRead]]:
    notes = await note_service.list_notes(
        db, current_user.organization_id, customer_id, project_id
    )
    return StandardResponse(data=notes, message="Notes retrieved")


@router.post("", response_model=StandardResponse[NoteRead], status_code=status.HTTP_201_CREATED, summary="Create Note")
async def create_note_endpoint(
    data: NoteCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[NoteRead]:
    note = await note_service.create_note(
        db, current_user.organization_id, data, current_user.id
    )
    return StandardResponse(
        data=NoteRead(
            id=note.id,
            tenant_id=note.tenant_id,
            customer_id=note.customer_id,
            project_id=note.project_id,
            author_id=note.author_id,
            author_name=current_user.full_name,
            content=note.content,
            created_at=note.created_at,
            updated_at=note.updated_at,
        ),
        message="Note logged successfully",
    )
