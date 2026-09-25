import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Audit log entry recording security and business domain events for auditability.
    Immutable record with actor, tenant, action, resource, timestamp, and metadata.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_tenant_action", "tenant_id", "action"),
        Index("ix_audit_logs_tenant_created", "tenant_id", "created_at"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., LOGIN, USER_CREATE, TENANT_SWITCH
    resource: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., auth, user, organization
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="audit_logs")
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[actor_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} tenant={self.tenant_id}>"
