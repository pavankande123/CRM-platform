import datetime
import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    message: str,
    notification_type: str = "info",
    link_url: Optional[str] = None,
) -> Notification:
    notif = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        title=title.strip(),
        message=message.strip(),
        notification_type=notification_type,
        link_url=link_url,
        is_read=False,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def list_user_notifications(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    unread_only: bool = False,
    limit: int = 50,
) -> List[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.tenant_id == tenant_id, Notification.user_id == user_id)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_as_read(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
) -> Notification:
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.tenant_id == tenant_id,
        Notification.user_id == user_id,
    )
    notif = (await db.execute(stmt)).scalar_one_or_none()
    if not notif:
        raise NotFoundError(message="Notification not found.")

    notif.is_read = True
    notif.read_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()
    await db.refresh(notif)
    return notif


async def mark_all_as_read(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> int:
    stmt = select(Notification).where(
        Notification.tenant_id == tenant_id,
        Notification.user_id == user_id,
        Notification.is_read == False,  # noqa: E712
    )
    unreads = (await db.execute(stmt)).scalars().all()
    count = 0
    now = datetime.datetime.now(datetime.timezone.utc)
    for notif in unreads:
        notif.is_read = True
        notif.read_at = now
        count += 1
    await db.commit()
    return count
