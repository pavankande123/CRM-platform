"""Phase 3: Platform Configurability & Automation (custom fields, saved views, workflows, notifications, approvals, pipeline stage active)

Revision ID: 003_phase3_platform_config
Revises: 002_phase2_core_crm
Create Date: 2026-09-25 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_phase3_platform_config"
down_revision: Union[str, None] = "002_phase2_core_crm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_active to pipeline_stages
    op.add_column(
        "pipeline_stages",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False)
    )

    # 2. Custom Fields definition table
    op.create_table(
        "custom_fields",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("field_type", sa.String(length=50), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_searchable", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_custom_fields_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_custom_fields"),
        sa.UniqueConstraint("tenant_id", "entity_type", "field_name", name="uq_custom_fields_tenant_entity_name"),
    )
    op.create_index("ix_custom_fields_tenant_id", "custom_fields", ["tenant_id"])
    op.create_index("ix_custom_fields_entity_type", "custom_fields", ["entity_type"])

    # 3. Custom Field Values typed table
    op.create_table(
        "custom_field_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("field_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_numeric", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["custom_fields.id"], ondelete="CASCADE", name="fk_custom_field_values_field_id_custom_fields"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_custom_field_values_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_custom_field_values"),
        sa.UniqueConstraint("tenant_id", "field_id", "entity_id", name="uq_custom_field_values_record"),
    )
    op.create_index("ix_custom_field_values_tenant_id", "custom_field_values", ["tenant_id"])
    op.create_index("ix_custom_field_values_field_id", "custom_field_values", ["field_id"])
    op.create_index("ix_custom_field_values_entity_id", "custom_field_values", ["entity_id"])
    op.create_index("ix_custom_field_values_lookup", "custom_field_values", ["tenant_id", "entity_type", "entity_id"])

    # 4. Saved Views
    op.create_table(
        "saved_views",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_shared", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("visible_columns", sa.JSON(), nullable=True),
        sa.Column("sort_field", sa.String(length=100), nullable=True),
        sa.Column("sort_direction", sa.String(length=10), server_default="desc", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="CASCADE", name="fk_saved_views_created_by_id_users"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_saved_views_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_saved_views"),
    )
    op.create_index("ix_saved_views_tenant_id", "saved_views", ["tenant_id"])
    op.create_index("ix_saved_views_entity_type", "saved_views", ["entity_type"])

    # 5. Workflows
    op.create_table(
        "workflows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_event", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_workflows_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_workflows"),
    )
    op.create_index("ix_workflows_tenant_id", "workflows", ["tenant_id"])
    op.create_index("ix_workflows_entity_type", "workflows", ["entity_type"])
    op.create_index("ix_workflows_trigger_event", "workflows", ["trigger_event"])
    op.create_index("ix_workflows_tenant_trigger", "workflows", ["tenant_id", "trigger_event", "is_active"])

    # 6. Workflow Executions
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_id", sa.Uuid(), nullable=False),
        sa.Column("trigger_event", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_data", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_workflow_executions_tenant_id_organizations"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE", name="fk_workflow_executions_workflow_id_workflows"),
        sa.PrimaryKeyConstraint("id", name="pk_workflow_executions"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_workflow_executions_idempotency"),
    )
    op.create_index("ix_workflow_executions_tenant_id", "workflow_executions", ["tenant_id"])
    op.create_index("ix_workflow_executions_workflow_id", "workflow_executions", ["workflow_id"])
    op.create_index("ix_workflow_executions_status", "workflow_executions", ["status"])
    op.create_index("ix_workflow_executions_lookup", "workflow_executions", ["tenant_id", "entity_type", "entity_id"])

    # 7. Notifications
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), server_default="info", nullable=False),
        sa.Column("link_url", sa.String(length=255), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_notifications_tenant_id_organizations"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_notifications_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
    )
    op.create_index("ix_notifications_tenant_id", "notifications", ["tenant_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_user_unread", "notifications", ["tenant_id", "user_id", "is_read"])

    # 8. Approval Requests
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("approver_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"], ondelete="SET NULL", name="fk_approval_requests_approver_id_users"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE", name="fk_approval_requests_requester_id_users"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_approval_requests_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_approval_requests"),
    )
    op.create_index("ix_approval_requests_tenant_id", "approval_requests", ["tenant_id"])
    op.create_index("ix_approval_requests_entity_type", "approval_requests", ["entity_type"])
    op.create_index("ix_approval_requests_entity_id", "approval_requests", ["entity_id"])
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])
    op.create_index("ix_approval_requests_tenant_status", "approval_requests", ["tenant_id", "status"])

    # 9. Approval Decisions
    op.create_table(
        "approval_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("approval_request_id", sa.Uuid(), nullable=False),
        sa.Column("decided_by_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["approval_request_id"], ["approval_requests.id"], ondelete="CASCADE", name="fk_approval_decisions_request_id"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="CASCADE", name="fk_approval_decisions_decided_by_id_users"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_approval_decisions_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_approval_decisions"),
    )
    op.create_index("ix_approval_decisions_tenant_id", "approval_decisions", ["tenant_id"])
    op.create_index("ix_approval_decisions_approval_request_id", "approval_decisions", ["approval_request_id"])


def downgrade() -> None:
    op.drop_table("approval_decisions")
    op.drop_table("approval_requests")
    op.drop_table("notifications")
    op.drop_table("workflow_executions")
    op.drop_table("workflows")
    op.drop_table("saved_views")
    op.drop_table("custom_field_values")
    op.drop_table("custom_fields")
    op.drop_column("pipeline_stages", "is_active")
