import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Standard naming conventions for constraints and indexes (critical for clean Alembic migrations)
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative Base class for all Enermax CRM models."""
    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)

    # Automatic table naming based on lowercase class name + 's'
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"


class UUIDPrimaryKeyMixin:
    """Provides a UUID v4 primary key column."""
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        sort_order=-10,
    )


class TimestampMixin:
    """Provides UTC created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        sort_order=900,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        sort_order=901,
    )


class TenantScopedMixin:
    """Provides tenant_id foreign key scoping for multi-tenancy isolation."""
    @declared_attr
    def tenant_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            ForeignKey("organizations.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
            sort_order=-5,
        )
