import datetime
import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.project import Project
    from app.models.user import User


class Payment(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Commercial payment receipt entity for milestone and invoice collections.
    Uses strict decimal arithmetic.
    """
    __tablename__ = "payments"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_number: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    payment_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(50), default="bank_transfer", nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="received", nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    recorded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="payments", lazy="selectin")
    project: Mapped["Project"] = relationship("Project", back_populates="payments", lazy="selectin")
    recorded_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} number={self.payment_number} amount={self.amount}>"
