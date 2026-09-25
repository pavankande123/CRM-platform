import datetime
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class ApprovalRequest(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Approval request for operational governance (e.g. project discount, contract sign-off, high-value payment).
    """
    __tablename__ = "approval_requests"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'project', 'payment'
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    approver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)  # 'pending', 'approved', 'rejected'
    
    requested_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    decided_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id], lazy="selectin")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approver_id], lazy="selectin")
    decisions: Mapped[List["ApprovalDecision"]] = relationship(
        "ApprovalDecision",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="ApprovalDecision.decided_at.desc()",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_approval_requests_tenant_status", "tenant_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequest id={self.id} entity={self.entity_type} status={self.status}>"


class ApprovalDecision(Base, UUIDPrimaryKeyMixin, TenantScopedMixin):
    """
    Immutable audit record of an approval or rejection decision.
    """
    __tablename__ = "approval_decisions"

    approval_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("approval_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decided_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # 'approved', 'rejected'
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    request: Mapped["ApprovalRequest"] = relationship("ApprovalRequest", back_populates="decisions")
    decided_by: Mapped["User"] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ApprovalDecision id={self.id} decision={self.decision}>"
