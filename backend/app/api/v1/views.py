import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.saved_view import (
    SavedViewCreate,
    SavedViewRead,
    SavedViewUpdate,
)
from app.services import saved_view_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[SavedViewRead]], summary="List Saved Views")
async def list_saved_views_endpoint(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (customer, project, follow_up, payment)"),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[SavedViewRead]]:
    views = await saved_view_service.list_saved_views(db, current_user.organization_id, entity_type=entity_type)
    return StandardResponse(
        data=[SavedViewRead.model_validate(v) for v in views],
        message="Saved views retrieved successfully",
    )


@router.post("", response_model=StandardResponse[SavedViewRead], status_code=status.HTTP_201_CREATED, summary="Create Saved View")
async def create_saved_view_endpoint(
    data: SavedViewCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[SavedViewRead]:
    view = await saved_view_service.create_saved_view(db, current_user.organization_id, current_user.id, data)
    return StandardResponse(data=SavedViewRead.model_validate(view), message="Saved view created successfully")


@router.get("/{view_id}", response_model=StandardResponse[SavedViewRead], summary="Get Saved View")
async def get_saved_view_endpoint(
    view_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[SavedViewRead]:
    view = await saved_view_service.get_saved_view(db, current_user.organization_id, view_id)
    return StandardResponse(data=SavedViewRead.model_validate(view), message="Saved view details")


@router.put("/{view_id}", response_model=StandardResponse[SavedViewRead], summary="Update Saved View")
async def update_saved_view_endpoint(
    view_id: uuid.UUID,
    data: SavedViewUpdate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[SavedViewRead]:
    view = await saved_view_service.update_saved_view(db, current_user.organization_id, view_id, data)
    return StandardResponse(data=SavedViewRead.model_validate(view), message="Saved view updated successfully")


@router.delete("/{view_id}", response_model=StandardResponse[Dict[str, Any]], summary="Delete Saved View")
async def delete_saved_view_endpoint(
    view_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[Dict[str, Any]]:
    result = await saved_view_service.delete_saved_view(db, current_user.organization_id, view_id)
    return StandardResponse(data=result, message=result["message"])


@router.get("/{view_id}/execute", response_model=StandardResponse[Dict[str, Any]], summary="Execute Saved View Query")
async def execute_saved_view_endpoint(
    view_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[Dict[str, Any]]:
    result = await saved_view_service.execute_saved_view(
        db, current_user.organization_id, view_id, page=page, page_size=page_size
    )
    return StandardResponse(data=result, message="Saved view query executed successfully")
