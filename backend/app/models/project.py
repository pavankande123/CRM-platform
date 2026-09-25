import datetime
import uuid
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.pipeline import Pipeline, PipelineStage
    from app.models.user import User
    from app.models.payment import Payment
    from app.models.follow_up import FollowUp
    from app.models.note import Note
    from app.models.activity import Activity
    from app.models.document import DocumentMetadata


class Project(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Project execution and deal tracking entity.
    Connects Customer, Product, Pipeline, Stage, and Financials.
    """
    __tablename__ = "projects"

    project_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pipelines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    expected_completion_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="projects", lazy="selectin")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="projects", lazy="selectin")
    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="projects", lazy="selectin")
    stage: Mapped["PipelineStage"] = relationship("PipelineStage", back_populates="projects", lazy="selectin")
    owner: Mapped[Optional["User"]] = relationship("User", lazy="selectin")

    stage_history: Mapped[List["ProjectStageHistory"]] = relationship(
        "ProjectStageHistory",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectStageHistory.changed_at.desc()",
        lazy="selectin",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    follow_ups: Mapped[List["FollowUp"]] = relationship(
        "FollowUp",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    notes_rel: Mapped[List["Note"]] = relationship(
        "Note",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["DocumentMetadata"]] = relationship(
        "DocumentMetadata",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} number={self.project_number} name={self.name}>"


class ProjectStageHistory(Base, UUIDPrimaryKeyMixin, TenantScopedMixin):
    """
    Immutable audit history of project stage transitions.
    """
    __tablename__ = "project_stage_history"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("pipeline_stages.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_stage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"),
        nullable=False,
    )
    changed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="stage_history")
    from_stage: Mapped[Optional["PipelineStage"]] = relationship("PipelineStage", foreign_keys=[from_stage_id], lazy="selectin")
    to_stage: Mapped["PipelineStage"] = relationship("PipelineStage", foreign_keys=[to_stage_id], lazy="selectin")
    changed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[changed_by_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<ProjectStageHistory project={self.project_id} to_stage={self.to_stage_id}>"
