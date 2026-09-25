import json
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.audit import AuditLog

# Sensitive keys to sanitize from audit metadata
SENSITIVE_KEYS = {"password", "secret", "token", "access_token", "refresh_token", "authorization", "hashed_password"}


def sanitize_metadata(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """Sanitizes metadata removing sensitive keys before persistence."""
    if not data:
        return None
    sanitized = {}
    for k, v in data.items():
        if any(s in k.lower() for s in SENSITIVE_KEYS):
            sanitized[k] = "***REDACTED***"
        else:
            sanitized[k] = v
    try:
        return json.dumps(sanitized)
    except Exception:
        return str(sanitized)


async def create_audit_entry(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    action: str,
    resource: str,
    actor_id: Optional[uuid.UUID] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Persist an audit log entry for auditing security and domain events.
    """
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action.upper(),
        resource=resource.lower(),
        resource_id=str(resource_id) if resource_id else None,
        ip_address=ip_address,
        user_agent=user_agent[:255] if user_agent else None,
        metadata_json=sanitize_metadata(metadata),
    )
    db.add(audit_log)
    await db.flush()
    logger.info(
        f"Audit: {action} on {resource} by {actor_id or 'system'} [tenant: {tenant_id}]",
        extra={"event": "AUDIT_RECORDED", "tenant_id": str(tenant_id), "user_id": str(actor_id) if actor_id else None},
    )
    return audit_log
