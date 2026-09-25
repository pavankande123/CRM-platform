import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, StandardResponse
from app.schemas.follow_up import FollowUpComplete, FollowUpCreate, FollowUpRead, FollowUpUpdate
from app.services import follow_up_service

router = APIRouter()


@router.get("", response_model=StandardResponse[PaginatedResponse[FollowUpRead]], summary="List Follow-ups")
async def list_follow_ups_endpoint(
    pagination: PaginationParams = Depends(),
    status: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    today_only: bool = Query(False),
    customer_id: Optional[uuid.UUID] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[PaginatedResponse[FollowUpRead]]:
    items, total = await follow_up_service.list_follow_ups(
        db=db,
        tenant_id=current_user.organization_id,
        status=status,
        overdue_only=overdue_only,
        today_only=today_only,
        customer_id=customer_id,
        project_id=project_id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 0
    return StandardResponse(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
        ),
        message="Follow-ups retrieved successfully",
    )


@router.post("", response_model=StandardResponse[FollowUpRead], status_code=status.HTTP_201_CREATED, summary="Create Follow-up")
async def create_follow_up_endpoint(
    data: FollowUpCreate,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[FollowUpRead]:
    follow_up = await follow_up_service.create_follow_up(
        db=db,
        tenant_id=current_user.organization_id,
        data=data,
        actor_id=current_user.id,
    )
    return StandardResponse(
        data=FollowUpRead.model_validate(follow_up),
        message="Follow-up scheduled successfully",
    )


@router.patch("/{follow_up_id}/complete", response_model=StandardResponse[FollowUpRead], summary="Complete Follow-up")
async def complete_follow_up_endpoint(
    follow_up_id: uuid.UUID,
    data: FollowUpComplete,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[FollowUpRead]:
    follow_up = await follow_up_service.complete_follow_up(
        db=db,
        tenant_id=current_user.organization_id,
        follow_up_id=follow_up_id,
        data=data,
        actor_id=current_user.id,
    )
    return StandardResponse(data=FollowUpRead.model_validate(follow_up), message="Follow-up marked as completed")


@router.patch("/{follow_up_id}/cancel", response_model=StandardResponse[FollowUpRead], summary="Cancel Follow-up")
async def cancel_follow_up_endpoint(
    follow_up_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:write")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[FollowUpRead]:
    follow_up = await follow_up_service.cancel_follow_up(
        db=db,
        tenant_id=current_user.organization_id,
        follow_up_id=follow_up_id,
        actor_id=current_user.id,
    )
    return StandardResponse(data=FollowUpRead.model_validate(follow_up), message="Follow-up cancelled")
