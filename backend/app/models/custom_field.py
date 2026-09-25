import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional
from datetime import date
from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CustomField(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Metadata definition for a tenant custom field.
    Defines field name, type, validation, and options without altering physical tables.
    """
    __tablename__ = "custom_fields"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'customer', 'project', 'product'
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)  # identifier e.g. 'solar_capacity_kw'
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)  # UI label e.g. 'Solar Capacity (kW)'
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'text', 'number', 'currency', 'date', 'boolean', 'select'
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_searchable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    options: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # List[str] options for select type

    values: Mapped[List["CustomFieldValue"]] = relationship(
        "CustomFieldValue",
        back_populates="field",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "entity_type", "field_name", name="uq_custom_fields_tenant_entity_name"),
    )

    def __repr__(self) -> str:
        return f"<CustomField id={self.id} entity={self.entity_type} name={self.field_name} type={self.field_type}>"


class CustomFieldValue(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Concrete typed value for a custom field attached to a specific CRM entity record.
    Uses typed columns for query performance, sorting, and indexing.
    """
    __tablename__ = "custom_field_values"

    field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("custom_fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    # Typed storage columns
    value_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_numeric: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    field: Mapped["CustomField"] = relationship("CustomField", back_populates="values", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tenant_id", "field_id", "entity_id", name="uq_custom_field_values_record"),
        Index("ix_custom_field_values_lookup", "tenant_id", "entity_type", "entity_id"),
    )

    def get_typed_value(self) -> Any:
        if self.value_numeric is not None:
            return float(self.value_numeric)
        if self.value_date is not None:
            return self.value_date.isoformat()
        if self.value_boolean is not None:
            return self.value_boolean
        return self.value_text

    def __repr__(self) -> str:
        return f"<CustomFieldValue field_id={self.field_id} entity_id={self.entity_id}>"
