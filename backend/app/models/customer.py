import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.project import Project
    from app.models.follow_up import FollowUp
    from app.models.payment import Payment
    from app.models.note import Note
    from app.models.activity import Activity
    from app.models.document import DocumentMetadata


class Customer(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Central business customer entity scoped to a tenant organization.
    Represents commercial, industrial, or residential clients.
    """
    __tablename__ = "customers"

    customer_type: Mapped[str] = mapped_column(String(50), default="commercial", nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), default="direct", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    follow_ups: Mapped[List["FollowUp"]] = relationship(
        "FollowUp",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="customer",
    )
    notes_rel: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["DocumentMetadata"]] = relationship(
        "DocumentMetadata",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name={self.name} tenant={self.tenant_id}>"


class Contact(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Individual contact person belonging to a customer organization.
    """
    __tablename__ = "contacts"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="contacts")

    def __repr__(self) -> str:
        return f"<Contact id={self.id} name={self.name} customer_id={self.customer_id}>"
