import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteRead
from app.services.activity_service import log_activity


async def list_notes(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    customer_id: Optional[uuid.UUID] = None,
    project_id: Optional[uuid.UUID] = None,
) -> List[NoteRead]:
    base_query = select(Note).where(Note.tenant_id == tenant_id)
    if customer_id:
        base_query = base_query.where(Note.customer_id == customer_id)
    if project_id:
        base_query = base_query.where(Note.project_id == project_id)

    stmt = (
        base_query
        .options(selectinload(Note.author))
        .order_by(Note.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return [
        NoteRead(
            id=n.id,
            tenant_id=n.tenant_id,
            customer_id=n.customer_id,
            project_id=n.project_id,
            author_id=n.author_id,
            author_name=n.author.full_name if n.author else None,
            content=n.content,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )
        for n in records
    ]


async def create_note(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: NoteCreate,
    actor_id: Optional[uuid.UUID] = None,
) -> Note:
    note = Note(
        tenant_id=tenant_id,
        customer_id=data.customer_id,
        project_id=data.project_id,
        follow_up_id=data.follow_up_id,
        payment_id=data.payment_id,
        author_id=actor_id,
        content=data.content.strip(),
    )
    db.add(note)
    await db.flush()

    preview = (note.content[:60] + "...") if len(note.content) > 60 else note.content
    await log_activity(
        db=db,
        tenant_id=tenant_id,
        activity_type="NOTE_ADDED",
        title=f"Note logged: \"{preview}\"",
        customer_id=note.customer_id,
        project_id=note.project_id,
        actor_id=actor_id,
    )

    await db.commit()
    await db.refresh(note)
    return note
