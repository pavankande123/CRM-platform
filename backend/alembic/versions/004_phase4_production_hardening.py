"""Phase 4: Production Hardening (compound tenant indexes, database performance tuning, durable jobs table)

Revision ID: 004_phase4_production_hardening
Revises: 003_phase3_platform_config
Create Date: 2026-09-25 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_phase4_production_hardening"
down_revision: Union[str, None] = "003_phase3_platform_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Compound Tenant Indexes for High-Scale Multi-Tenant Query Isolation
    # -----------------------------------------------------------------------
    op.create_index(
        "ix_customers_tenant_is_active",
        "customers",
        ["tenant_id", "is_active"],
    )
    op.create_index(
        "ix_customers_tenant_created_at",
        "customers",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_projects_tenant_stage_id",
        "projects",
        ["tenant_id", "stage_id"],
    )
    op.create_index(
        "ix_projects_tenant_customer_id",
        "projects",
        ["tenant_id", "customer_id"],
    )
    op.create_index(
        "ix_projects_tenant_status",
        "projects",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_followups_tenant_status_due_date",
        "follow_ups",
        ["tenant_id", "status", "due_date"],
    )
    op.create_index(
        "ix_payments_tenant_status_date",
        "payments",
        ["tenant_id", "status", "payment_date"],
    )
    op.create_index(
        "ix_notifications_tenant_user_read",
        "notifications",
        ["tenant_id", "user_id", "is_read"],
    )
    op.create_index(
        "ix_approvals_tenant_status",
        "approval_requests",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_wf_exec_tenant_wf_status",
        "workflow_executions",
        ["tenant_id", "workflow_id", "status"],
    )
    op.create_index(
        "ix_audit_logs_tenant_created",
        "audit_logs",
        ["tenant_id", "created_at"],
    )

    # -----------------------------------------------------------------------
    # 2. Durable Background Jobs Table
    # -----------------------------------------------------------------------
    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("queue", sa.String(length=50), server_default="default", nullable=False),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="queued", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False),
        sa.Column("retry_backoff_seconds", sa.Integer(), server_default="5", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", sa.JSON(), nullable=True),
        sa.Column("result_data", sa.JSON(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_jobs_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
    )

    op.create_index("ix_jobs_tenant_id", "jobs", ["tenant_id"])
    op.create_index("ix_jobs_queue", "jobs", ["queue"])
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_scheduled_at", "jobs", ["scheduled_at"])
    op.create_index("ix_jobs_idempotency_key", "jobs", ["idempotency_key"])
    op.create_index("ix_jobs_correlation_id", "jobs", ["correlation_id"])
    op.create_index("ix_jobs_tenant_status_sched", "jobs", ["tenant_id", "status", "scheduled_at"])
    op.create_index("ix_jobs_tenant_idemp", "jobs", ["tenant_id", "idempotency_key"])
    op.create_index("ix_jobs_tenant_created", "jobs", ["tenant_id", "created_at"])


def downgrade() -> None:
    # 1. Drop Jobs Table & Indexes
    op.drop_index("ix_jobs_tenant_created", table_name="jobs")
    op.drop_index("ix_jobs_tenant_idemp", table_name="jobs")
    op.drop_index("ix_jobs_tenant_status_sched", table_name="jobs")
    op.drop_index("ix_jobs_correlation_id", table_name="jobs")
    op.drop_index("ix_jobs_idempotency_key", table_name="jobs")
    op.drop_index("ix_jobs_scheduled_at", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_job_type", table_name="jobs")
    op.drop_index("ix_jobs_queue", table_name="jobs")
    op.drop_index("ix_jobs_tenant_id", table_name="jobs")
    op.drop_table("jobs")

    # 2. Drop Compound Indexes
    op.drop_index("ix_audit_logs_tenant_created", table_name="audit_logs")
    op.drop_index("ix_wf_exec_tenant_wf_status", table_name="workflow_executions")
    op.drop_index("ix_approvals_tenant_status", table_name="approval_requests")
    op.drop_index("ix_notifications_tenant_user_read", table_name="notifications")
    op.drop_index("ix_payments_tenant_status_date", table_name="payments")
    op.drop_index("ix_followups_tenant_status_due_date", table_name="follow_ups")
    op.drop_index("ix_projects_tenant_status", table_name="projects")
    op.drop_index("ix_projects_tenant_customer_id", table_name="projects")
    op.drop_index("ix_projects_tenant_stage_id", table_name="projects")
    op.drop_index("ix_customers_tenant_created_at", table_name="customers")
    op.drop_index("ix_customers_tenant_is_active", table_name="customers")
