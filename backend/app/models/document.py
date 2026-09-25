import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.project import Project
    from app.models.payment import Payment
    from app.models.user import User


class DocumentMetadata(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Metadata representation of commercial documents (Quotation, Invoice, Contract, Site Photos).
    """
    __tablename__ = "document_metadata"

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
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)  # MIME type
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_category: Mapped[str] = mapped_column(String(50), default="other", nullable=False)  # quotation, invoice, etc.
    storage_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="documents")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="documents")
    uploaded_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DocumentMetadata id={self.id} file={self.file_name}>"
