import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


# Many-to-many relationship table between Role and Permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Granular permission code (e.g., 'crm:read', 'users:manage')."""
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Role definition assigned to Users within a Tenant (or system-wide)."""
    __tablename__ = "roles"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="roles")
    users: Mapped[List["User"]] = relationship("User", back_populates="role")
    permissions: Mapped[List[Permission]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )
