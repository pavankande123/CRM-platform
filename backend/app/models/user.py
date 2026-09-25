import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.role import Role
    from app.models.audit import AuditLog


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User model scoped to an Organization tenant.
    Email is unique per Organization.
    """
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_organization_email"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users", lazy="selectin")
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="actor",
        foreign_keys="AuditLog.actor_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} org_id={self.organization_id}>"
