import datetime
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Job(Base, UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampMixin):
    """
    Durable Background Job Model for Phase 4.
    Tracks job state, retries, backoff, and execution results with full tenant isolation.
    """
    __tablename__ = "jobs"

    queue: Mapped[str] = mapped_column(String(50), default="default", nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="queued",
        nullable=False,
        index=True,
    )  # queued, running, completed, failed, retrying, dead_letter

    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_backoff_seconds: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    scheduled_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        index=True,
    )
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    __table_args__ = (
        Index("ix_jobs_tenant_status_sched", "tenant_id", "status", "scheduled_at"),
        Index("ix_jobs_tenant_idemp", "tenant_id", "idempotency_key"),
        Index("ix_jobs_tenant_created", "tenant_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} type={self.job_type} status={self.status} retries={self.retry_count}>"
