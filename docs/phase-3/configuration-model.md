# ENERMAX CRM — PHASE 3 CONFIGURATION MODEL

## System vs Tenant Configuration Architecture

### 1. Conceptual Separation

Enermax CRM strictly demarcates **System Configuration** from **Tenant Configuration**:

```
+-------------------------------------------------------------+
|                     SYSTEM CONFIGURATION                    |
|  - Platform Infrastructure (PostgreSQL, Connection Pools)   |
|  - Global Security Policies (JWT Algorithms, Token Expiry)  |
|  - Core RBAC Definitions (Platform roles & baseline perms)  |
|  - Global Rate Limiting & Resource Quotas                   |
+-------------------------------------------------------------+
                              |
                              | Multi-Tenant Partitioning
                              v
+-------------------------------------------------------------+
|                     TENANT CONFIGURATION                    |
|  - Project Pipelines & Stage Lifecycles                     |
|  - Custom Field Definitions & Options                       |
|  - Saved Operational Views & Filters                        |
|  - Automated Workflow Triggers, Conditions & Actions        |
|  - Notification Preferences & In-App Alerts                 |
|  - Operational Approval Workflows                           |
+-------------------------------------------------------------+
```

---

### 2. Tenant Boundary & Isolation Rules

1. **Foreign Key Binding**: All configuration entities extend `TenantScopedMixin` and include `tenant_id` mapped to `organizations.id` with `ondelete="CASCADE"`.
2. **Compound Uniqueness**: Identifiers such as pipeline names, stage names within a pipeline, and custom field keys are unique per tenant (e.g., `(tenant_id, entity_type, field_name)`).
3. **Execution Isolation**: When an event triggers a workflow, the workflow query strictly enforces `tenant_id == event.tenant_id`. Under no circumstances can a workflow defined by Tenant A match or execute against an entity in Tenant B.
4. **Administrative Permissions**: Modifying tenant configuration requires the `crm:write` or `admin:manage` permission. Regular read-only users cannot alter pipeline stages or workflow rules.

---

### 3. Configurable Pipelines Specification

#### 3.1 Data Model
- **`Pipeline`**:
  - `id`: UUID Primary Key
  - `tenant_id`: UUID Foreign Key -> `organizations.id`
  - `name`: String(255)
  - `product_id`: UUID Foreign Key -> `products.id` (Optional, allows product-specific pipelines)
  - `is_default`: Boolean (Default pipeline for unassigned projects)
  - `is_active`: Boolean (Soft deactivation)
- **`PipelineStage`**:
  - `id`: UUID Primary Key
  - `tenant_id`: UUID Foreign Key -> `organizations.id`
  - `pipeline_id`: UUID Foreign Key -> `pipelines.id`
  - `name`: String(100)
  - `order`: Integer (Sequence index)
  - `probability_percent`: Integer (0 - 100%)
  - `is_closed_won`: Boolean
  - `is_closed_lost`: Boolean
  - `is_active`: Boolean (Allows soft-deactivation of unused stages)
  - `color`: String(20) (UI badge color)

#### 3.2 Stage Preservation Invariant
When a pipeline stage is deactivated or removed:
- Active projects can still reference the stage if historical.
- If projects are currently assigned to the stage, deletion is prevented (`RESTRICT`), and the user is guided to soft-deactivate the stage or migrate active projects to an active stage.
- All historical stage changes in `ProjectStageHistory` remain fully intact.
