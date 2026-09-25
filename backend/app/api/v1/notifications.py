import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.models.user import User
from app.schemas.common import StandardResponse
from app.schemas.notification import NotificationRead
from app.services import notification_service

router = APIRouter()


@router.get("", response_model=StandardResponse[List[NotificationRead]], summary="List User Notifications")
async def list_notifications_endpoint(
    unread_only: bool = Query(False, description="Filter unread notifications only"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[List[NotificationRead]]:
    notifs = await notification_service.list_user_notifications(
        db, current_user.organization_id, current_user.id, unread_only=unread_only, limit=limit
    )
    return StandardResponse(
        data=[NotificationRead.model_validate(n) for n in notifs],
        message="Notifications retrieved successfully",
    )


@router.post("/{notification_id}/read", response_model=StandardResponse[NotificationRead], summary="Mark Notification as Read")
async def mark_read_endpoint(
    notification_id: uuid.UUID,
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[NotificationRead]:
    notif = await notification_service.mark_as_read(
        db, current_user.organization_id, current_user.id, notification_id
    )
    return StandardResponse(data=NotificationRead.model_validate(notif), message="Notification marked as read")


@router.post("/read-all", response_model=StandardResponse[Dict[str, Any]], summary="Mark All Notifications as Read")
async def mark_all_read_endpoint(
    current_user: User = Depends(require_permission("crm:read")),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse[Dict[str, Any]]:
    count = await notification_service.mark_all_as_read(db, current_user.organization_id, current_user.id)
    return StandardResponse(data={"read_count": count}, message=f"Marked {count} notifications as read")
