import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.project import Project
    from app.models.follow_up import FollowUp
    from app.models.payment import Payment
    from app.models.user import User


class Note(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Operator note attached to Customer, Project, Follow-up, or Payment.
    Preserves historical author and timestamp without overwrite.
    """
    __tablename__ = "notes"

    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    follow_up_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("follow_ups.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="notes_rel")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="notes_rel")
    author: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Note id={self.id} author={self.author_id}>"
