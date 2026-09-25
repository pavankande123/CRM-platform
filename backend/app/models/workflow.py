import datetime
import uuid
from typing import Any, List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowDefinition(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Workflow rule definition configured per tenant.
    Defines event triggers, conditions, and actions for automated execution.
    """
    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'project', 'customer', 'payment', 'follow_up'
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # 'project.stage_changed', 'payment.created', etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Declarative conditions and actions stored as structured JSON for flexibility
    # Example conditions: [{"field": "value", "operator": "gte", "value": 500000}]
    conditions: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)

    # Example actions: [{"action_type": "create_follow_up", "params": {"title": "Verify advance payment", "days_offset": 2}}]
    actions: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)

    executions: Mapped[List["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowExecution.created_at.desc()",
    )

    __table_args__ = (
        Index("ix_workflows_tenant_trigger", "tenant_id", "trigger_event", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowDefinition id={self.id} name={self.name} trigger={self.trigger_event}>"


class WorkflowExecution(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Traceable log of a workflow execution instance.
    Guarantees idempotency via unique idempotency_key and records execution status & errors.
    """
    __tablename__ = "workflow_executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)  # 'pending', 'running', 'completed', 'failed'
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Details of actions executed

    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="executions", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_workflow_executions_idempotency"),
        Index("ix_workflow_executions_lookup", "tenant_id", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowExecution id={self.id} workflow={self.workflow_id} status={self.status}>"
