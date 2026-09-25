import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.models.saved_view import SavedView
from app.models.customer import Customer
from app.models.project import Project
from app.models.follow_up import FollowUp
from app.models.payment import Payment
from app.schemas.saved_view import SavedViewCreate, SavedViewUpdate

ENTITY_MODEL_MAP = {
    "customer": Customer,
    "project": Project,
    "follow_up": FollowUp,
    "payment": Payment,
}


async def list_saved_views(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    entity_type: Optional[str] = None,
) -> List[SavedView]:
    stmt = select(SavedView).where(SavedView.tenant_id == tenant_id)
    if entity_type:
        stmt = stmt.where(SavedView.entity_type == entity_type.strip().lower())
    stmt = stmt.order_by(SavedView.is_default.desc(), SavedView.name.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_saved_view(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    view_id: uuid.UUID,
) -> SavedView:
    stmt = select(SavedView).where(
        SavedView.id == view_id,
        SavedView.tenant_id == tenant_id,
    )
    view = (await db.execute(stmt)).scalar_one_or_none()
    if not view:
        raise NotFoundError(message="Saved view not found.")
    return view


async def create_saved_view(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: SavedViewCreate,
) -> SavedView:
    if data.is_default:
        # Unset previous default for this tenant and entity_type
        stmt = select(SavedView).where(
            SavedView.tenant_id == tenant_id,
            SavedView.entity_type == data.entity_type,
            SavedView.is_default == True,  # noqa: E712
        )
        existing = (await db.execute(stmt)).scalars().all()
        for v in existing:
            v.is_default = False

    view = SavedView(
        tenant_id=tenant_id,
        created_by_id=user_id,
        name=data.name.strip(),
        entity_type=data.entity_type,
        is_default=data.is_default,
        is_shared=data.is_shared,
        filters=[f.model_dump() for f in data.filters],
        visible_columns=data.visible_columns or [],
        sort_field=data.sort_field,
        sort_direction=data.sort_direction.lower() if data.sort_direction else "desc",
    )
    db.add(view)
    await db.commit()
    await db.refresh(view)
    return view


async def update_saved_view(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    view_id: uuid.UUID,
    data: SavedViewUpdate,
) -> SavedView:
    view = await get_saved_view(db, tenant_id, view_id)
    if data.name is not None:
        view.name = data.name.strip()
    if data.is_default is not None:
        view.is_default = data.is_default
    if data.is_shared is not None:
        view.is_shared = data.is_shared
    if data.filters is not None:
        view.filters = [f.model_dump() for f in data.filters]
    if data.visible_columns is not None:
        view.visible_columns = data.visible_columns
    if data.sort_field is not None:
        view.sort_field = data.sort_field
    if data.sort_direction is not None:
        view.sort_direction = data.sort_direction.lower()

    await db.commit()
    await db.refresh(view)
    return view


async def delete_saved_view(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    view_id: uuid.UUID,
) -> dict:
    view = await get_saved_view(db, tenant_id, view_id)
    await db.delete(view)
    await db.commit()
    return {"status": "deleted", "message": f"Saved view '{view.name}' deleted successfully."}


async def execute_saved_view(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    view_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    Executes a saved view query safely using SQLAlchemy model expressions.
    Guarantees strict tenant isolation and prevents SQL injection.
    """
    view = await get_saved_view(db, tenant_id, view_id)
    model = ENTITY_MODEL_MAP.get(view.entity_type)
    if not model:
        raise ValidationError(message=f"Unsupported entity type '{view.entity_type}'.")

    stmt = select(model).where(model.tenant_id == tenant_id)
    count_stmt = select(func.count(model.id)).where(model.tenant_id == tenant_id)

    # Apply filters securely
    for f in (view.filters or []):
        field_name = f.get("field")
        op = f.get("operator", "").lower()
        val = f.get("value")

        if not hasattr(model, field_name):
            continue

        column = getattr(model, field_name)

        clause = None
        if op in ("eq", "="):
            clause = column == val
        elif op in ("neq", "!="):
            clause = column != val
        elif op in ("gt", ">"):
            clause = column > val
        elif op in ("gte", ">="):
            clause = column >= val
        elif op in ("lt", "<"):
            clause = column < val
        elif op in ("lte", "<="):
            clause = column <= val
        elif op == "contains" and val:
            clause = column.ilike(f"%{val}%")
        elif op == "in" and isinstance(val, list):
            clause = column.in_(val)
        elif op == "is_empty":
            clause = or_(column == None, column == "")  # noqa: E711
        elif op == "is_not_empty":
            clause = and_(column != None, column != "")  # noqa: E711

        if clause is not None:
            stmt = stmt.where(clause)
            count_stmt = count_stmt.where(clause)

    # Sorting
    if view.sort_field and hasattr(model, view.sort_field):
        sort_col = getattr(model, view.sort_field)
        if view.sort_direction == "asc":
            stmt = stmt.order_by(sort_col.asc())
        else:
            stmt = stmt.order_by(sort_col.desc())
    else:
        stmt = stmt.order_by(model.created_at.desc())

    # Pagination
    total = (await db.execute(count_stmt)).scalar() or 0
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    records = (await db.execute(stmt)).scalars().all()

    return {
        "view": {
            "id": view.id,
            "name": view.name,
            "entity_type": view.entity_type,
            "visible_columns": view.visible_columns,
        },
        "total": total,
        "page": page,
        "page_size": page_size,
        "records": [r.id for r in records],  # Return matched IDs for fast hydration
    }
