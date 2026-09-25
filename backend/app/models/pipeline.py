import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.project import Project, ProjectStageHistory


class Pipeline(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Flexible project pipeline configured per product or as general organizational pipeline.
    """
    __tablename__ = "pipelines"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="pipelines")
    stages: Mapped[List["PipelineStage"]] = relationship(
        "PipelineStage",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        order_by="PipelineStage.order.asc()",
        lazy="selectin",
    )
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="pipeline")

    def __repr__(self) -> str:
        return f"<Pipeline id={self.id} name={self.name} tenant={self.tenant_id}>"


class PipelineStage(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Individual sequential stage inside a pipeline.
    """
    __tablename__ = "pipeline_stages"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    probability_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_closed_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_closed_lost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="cyan", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="stages")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="stage")

    def __repr__(self) -> str:
        return f"<PipelineStage id={self.id} name={self.name} order={self.order}>"
