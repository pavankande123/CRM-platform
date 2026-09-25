"""Phase 2: Core CRM entities (customers, contacts, products, pipelines, projects, follow-ups, payments, notes, docs, activities)

Revision ID: 002_phase2_core_crm
Revises: 001_initial_schema
Create Date: 2026-09-25 12:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_phase2_core_crm"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Customers
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_type", sa.String(length=50), server_default="commercial", nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=True),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=100), server_default="India", nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("source", sa.String(length=100), server_default="direct", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL", name="fk_customers_created_by_id_users"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_customers_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
    )
    op.create_index("ix_customers_tenant_id", "customers", ["tenant_id"])
    op.create_index("ix_customers_name", "customers", ["name"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_phone", "customers", ["phone"])
    op.create_index("ix_customers_city", "customers", ["city"])
    op.create_index("ix_customers_state", "customers", ["state"])
    op.create_index("ix_customers_status", "customers", ["status"])

    # 2. Contacts
    op.create_table(
        "contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("designation", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE", name="fk_contacts_customer_id_customers"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_contacts_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_contacts"),
    )
    op.create_index("ix_contacts_tenant_id", "contacts", ["tenant_id"])
    op.create_index("ix_contacts_customer_id", "contacts", ["customer_id"])
    op.create_index("ix_contacts_name", "contacts", ["name"])

    # 3. Products
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit_price", sa.Numeric(precision=15, scale=2), server_default="0.00", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_products_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
    )
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_code", "products", ["code"])

    # 4. Pipelines
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL", name="fk_pipelines_product_id_products"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_pipelines_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_pipelines"),
    )
    op.create_index("ix_pipelines_tenant_id", "pipelines", ["tenant_id"])

    # 5. Pipeline Stages
    op.create_table(
        "pipeline_stages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("pipeline_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("probability_percent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_closed_won", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_closed_lost", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("color", sa.String(length=20), server_default="cyan", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["pipeline_id"], ["pipelines.id"], ondelete="CASCADE", name="fk_pipeline_stages_pipeline_id_pipelines"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_pipeline_stages_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_pipeline_stages"),
    )
    op.create_index("ix_pipeline_stages_tenant_id", "pipeline_stages", ["tenant_id"])
    op.create_index("ix_pipeline_stages_pipeline_id", "pipeline_stages", ["pipeline_id"])
    op.create_index("ix_pipeline_stages_order", "pipeline_stages", ["order"])

    # 6. Projects
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_number", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.Column("pipeline_id", sa.Uuid(), nullable=False),
        sa.Column("stage_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("value", sa.Numeric(precision=15, scale=2), server_default="0.00", nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="INR", nullable=False),
        sa.Column("expected_completion_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT", name="fk_projects_customer_id_customers"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL", name="fk_projects_owner_id_users"),
        sa.ForeignKeyConstraint(["pipeline_id"], ["pipelines.id"], ondelete="RESTRICT", name="fk_projects_pipeline_id_pipelines"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL", name="fk_projects_product_id_products"),
        sa.ForeignKeyConstraint(["stage_id"], ["pipeline_stages.id"], ondelete="RESTRICT", name="fk_projects_stage_id_pipeline_stages"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_projects_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_projects"),
    )
    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"])
    op.create_index("ix_projects_customer_id", "projects", ["customer_id"])
    op.create_index("ix_projects_stage_id", "projects", ["stage_id"])
    op.create_index("ix_projects_project_number", "projects", ["project_number"])
    op.create_index("ix_projects_name", "projects", ["name"])

    # 7. Project Stage History
    op.create_table(
        "project_stage_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("from_stage_id", sa.Uuid(), nullable=True),
        sa.Column("to_stage_id", sa.Uuid(), nullable=False),
        sa.Column("changed_by_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"], ondelete="SET NULL", name="fk_project_stage_history_changed_by_id_users"),
        sa.ForeignKeyConstraint(["from_stage_id"], ["pipeline_stages.id"], ondelete="SET NULL", name="fk_project_stage_history_from_stage_id_pipeline_stages"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE", name="fk_project_stage_history_project_id_projects"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_project_stage_history_tenant_id_organizations"),
        sa.ForeignKeyConstraint(["to_stage_id"], ["pipeline_stages.id"], ondelete="RESTRICT", name="fk_project_stage_history_to_stage_id_pipeline_stages"),
        sa.PrimaryKeyConstraint("id", name="pk_project_stage_history"),
    )
    op.create_index("ix_project_stage_history_tenant_id", "project_stage_history", ["tenant_id"])
    op.create_index("ix_project_stage_history_project_id", "project_stage_history", ["project_id"])

    # 8. Follow-ups
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_notes", sa.Text(), nullable=True),
        sa.Column("assigned_to_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL", name="fk_follow_ups_assigned_to_id_users"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL", name="fk_follow_ups_created_by_id_users"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE", name="fk_follow_ups_customer_id_customers"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL", name="fk_follow_ups_project_id_projects"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_follow_ups_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_follow_ups"),
    )
    op.create_index("ix_follow_ups_tenant_id", "follow_ups", ["tenant_id"])
    op.create_index("ix_follow_ups_customer_id", "follow_ups", ["customer_id"])
    op.create_index("ix_follow_ups_project_id", "follow_ups", ["project_id"])
    op.create_index("ix_follow_ups_due_date", "follow_ups", ["due_date"])
    op.create_index("ix_follow_ups_status", "follow_ups", ["status"])

    # 9. Payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("payment_number", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="INR", nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("payment_method", sa.String(length=50), server_default="bank_transfer", nullable=False),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="received", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT", name="fk_payments_customer_id_customers"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT", name="fk_payments_project_id_projects"),
        sa.ForeignKeyConstraint(["recorded_by_id"], ["users.id"], ondelete="SET NULL", name="fk_payments_recorded_by_id_users"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_payments_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
    )
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index("ix_payments_customer_id", "payments", ["customer_id"])
    op.create_index("ix_payments_project_id", "payments", ["project_id"])
    op.create_index("ix_payments_payment_date", "payments", ["payment_date"])
    op.create_index("ix_payments_status", "payments", ["status"])

    # 10. Notes
    op.create_table(
        "notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("follow_up_id", sa.Uuid(), nullable=True),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL", name="fk_notes_author_id_users"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE", name="fk_notes_customer_id_customers"),
        sa.ForeignKeyConstraint(["follow_up_id"], ["follow_ups.id"], ondelete="SET NULL", name="fk_notes_follow_up_id_follow_ups"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL", name="fk_notes_payment_id_payments"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE", name="fk_notes_project_id_projects"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_notes_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_notes"),
    )
    op.create_index("ix_notes_tenant_id", "notes", ["tenant_id"])
    op.create_index("ix_notes_customer_id", "notes", ["customer_id"])
    op.create_index("ix_notes_project_id", "notes", ["project_id"])

    # 11. Document Metadata
    op.create_table(
        "document_metadata",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("document_category", sa.String(length=50), server_default="other", nullable=False),
        sa.Column("storage_url", sa.String(length=500), nullable=True),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE", name="fk_document_metadata_customer_id_customers"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL", name="fk_document_metadata_payment_id_payments"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE", name="fk_document_metadata_project_id_projects"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_document_metadata_tenant_id_organizations"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL", name="fk_document_metadata_uploaded_by_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_document_metadata"),
    )
    op.create_index("ix_document_metadata_tenant_id", "document_metadata", ["tenant_id"])
    op.create_index("ix_document_metadata_customer_id", "document_metadata", ["customer_id"])
    op.create_index("ix_document_metadata_project_id", "document_metadata", ["project_id"])

    # 12. Activities
    op.create_table(
        "activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL", name="fk_activities_actor_id_users"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE", name="fk_activities_customer_id_customers"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE", name="fk_activities_project_id_projects"),
        sa.ForeignKeyConstraint(["tenant_id"], ["organizations.id"], ondelete="CASCADE", name="fk_activities_tenant_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_activities"),
    )
    op.create_index("ix_activities_tenant_id", "activities", ["tenant_id"])
    op.create_index("ix_activities_customer_id", "activities", ["customer_id"])
    op.create_index("ix_activities_project_id", "activities", ["project_id"])
    op.create_index("ix_activities_created_at", "activities", ["created_at"])


def downgrade() -> None:
    op.drop_table("activities")
    op.drop_table("document_metadata")
    op.drop_table("notes")
    op.drop_table("payments")
    op.drop_table("follow_ups")
    op.drop_table("project_stage_history")
    op.drop_table("projects")
    op.drop_table("pipeline_stages")
    op.drop_table("pipelines")
    op.drop_table("products")
    op.drop_table("contacts")
    op.drop_table("customers")
