import uuid
from typing import Any, List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class SavedView(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Persisted custom operational view and saved filter configuration.
    Allows operators to save customized grid views with server-validated filters.
    """
    __tablename__ = "saved_views"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'customer', 'project', 'follow_up', 'payment'
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Saved configurations stored as structured JSON
    filters: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)  # List of {field, operator, value}
    visible_columns: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)  # List of column names
    sort_field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sort_direction: Mapped[str] = mapped_column(String(10), default="desc", nullable=False)  # 'asc' or 'desc'

    created_by: Mapped["User"] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<SavedView id={self.id} entity={self.entity_type} name={self.name}>"
