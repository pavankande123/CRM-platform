import json
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity import Activity


async def log_activity(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    activity_type: str,
    title: str,
    description: Optional[str] = None,
    customer_id: Optional[uuid.UUID] = None,
    project_id: Optional[uuid.UUID] = None,
    actor_id: Optional[uuid.UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Activity:
    """
    Records a domain business activity for customer and project historical timelines.
    """
    metadata_str = None
    if metadata:
        try:
            metadata_str = json.dumps(metadata)
        except Exception:
            metadata_str = str(metadata)

    activity = Activity(
        tenant_id=tenant_id,
        activity_type=activity_type.upper(),
        title=title,
        description=description,
        customer_id=customer_id,
        project_id=project_id,
        actor_id=actor_id,
        metadata_json=metadata_str,
    )
    db.add(activity)
    await db.flush()
    return activity
