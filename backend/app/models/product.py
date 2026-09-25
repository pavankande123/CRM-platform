from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.pipeline import Pipeline


class Product(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Product or service catalog entity (e.g., Rooftop Solar PV, Solar Water Heater, Energy Audit).
    """
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    projects: Mapped[List["Project"]] = relationship("Project", back_populates="product")
    pipelines: Mapped[List["Pipeline"]] = relationship("Pipeline", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name} code={self.code}>"
