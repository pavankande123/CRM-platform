# ENERMAX CRM — PHASE 3 ARCHITECTURE SPECIFICATION

## Platform Configurability & Automation Architecture

### 1. Executive Summary

Phase 1 and Phase 2 established a hardened, multi-tenant SaaS foundation and Core CRM operations for Enermax (Customers, Contacts, Projects, Pipelines, Follow-ups, Payments, Notes, Documents, Activities, Global Search, and Executive Dashboard).

Phase 3 introduces **Platform Configurability & Automation** without modifying core application code for tenant-specific requirements. The central architectural principle is:
> **"Configuration instead of developer changes wherever practical."**

Organizations operating on the Enermax CRM platform can adapt pipeline flows, define typed custom fields, save custom views and operational filters, automate repetitive business workflows via an idempotent event-driven engine, receive automated notifications, and govern operational sign-offs via approval mechanisms.

---

### 2. System Architecture & Boundaries

```
+-----------------------------------------------------------------------------------+
|                              Client Layer (SPA)                                   |
|  - Operator Workspaces (Dashboard, Customers, Projects, Follow-ups, Payments)     |
|  - Platform Settings (Pipelines, Custom Fields, Saved Views, Workflows, Approvals)|
|  - In-App Notification Center & Approvals Inbox                                   |
+-----------------------------------------+-----------------------------------------+
                                          | REST API (JSON / HTTP)
+-----------------------------------------v-----------------------------------------+
|                               API Gateway / Routers                               |
|  - Security & Authentication (JWT Bearer, Multi-tenant Context Extraction)       |
|  - RBAC & Tenant Isolation Guard (Dependency Injection)                          |
|  - Input Validation & Normalization (Pydantic v2 Models)                         |
+-----------------------------------------+-----------------------------------------+
                                          |
+-----------------------------------------v-----------------------------------------+
|                              Platform Domain Services                             |
|  +--------------------+  +----------------------+  +---------------------------+  |
|  |  Pipeline Service  |  | Custom Field Service |  |    Saved View Service     |  |
|  |  - Stages reorder  |  | - Metadata validation|  |    - Filter compiler      |  |
|  |  - Stage protect   |  | - Typed value store  |  |    - Dynamic projection   |  |
|  +--------------------+  +----------------------+  +---------------------------+  |
|  +-----------------------------------------------------------------------------+  |
|  |                         Workflow Automation Engine                          |  |
|  |  [Event Bus] -> [Workflow Matcher] -> [Condition Engine] -> [Action Worker] |  |
|  |  - Idempotency Manager (Deduplication Keys)                                 |  |
|  |  - Execution History & Audit Logger                                        |  |
|  |  - Retry & Failure State Machine                                           |  |
|  +-----------------------------------------------------------------------------+  |
|  +--------------------+  +----------------------+                                 |
|  |Notification Service|  |   Approval Service   |                                 |
|  | - In-app inbox     |  | - Request/Decide     |                                 |
|  | - Unread indicators|  | - Comments & Audit   |                                 |
|  +--------------------+  +----------------------+                                 |
+-----------------------------------------+-----------------------------------------+
                                          |
+-----------------------------------------v-----------------------------------------+
|                               Persistence Layer                                   |
|  - Multi-tenant PostgreSQL / SQLite (Strict Foreign Keys, WAL mode, Constraints)  |
|  - Partitioned by organization_id (tenant_id)                                     |
+-----------------------------------------------------------------------------------+
```

---

### 3. Core Subsystems

#### 3.1 Configurable Pipelines & Stages
- Pipelines can be created, updated, and activated/deactivated per tenant.
- Stages support custom ordering, win/lost probability percentages, stage metadata (color, descriptions), and active toggles.
- **Historical Data Safety**: Deactivating a stage never damages existing projects or historical `ProjectStageHistory` records. Deletion is restricted if historical project records exist.

#### 3.2 Metadata-Driven Custom Fields
- Defines typed attributes without schema migrations (`ALTER TABLE`).
- Supported field types: `text`, `number`, `currency`, `date`, `boolean`, `select`.
- Values stored in structured columns (`value_text`, `value_numeric`, `value_date`, `value_boolean`) for query efficiency and type validation.

#### 3.3 Saved Views & Configurable Filters
- Allows operators and administrators to persist customized views for projects, customers, follow-ups, and payments.
- Strict server-side filter validation (operators: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `contains`, `in`, `is_empty`, `is_not_empty`). Arbitrary SQL execution is strictly forbidden.

#### 3.4 Workflow Automation Engine
- Event-driven: reacts to domain events (`CUSTOMER_CREATED`, `PROJECT_STAGE_CHANGED`, `PAYMENT_CREATED`, `FOLLOW_UP_COMPLETED`, etc.).
- Evaluates declarative conditions against target record attributes.
- Executes automated actions: `create_follow_up`, `update_record`, `create_notification`, `assign_record`, `add_activity`.
- **Idempotency**: Every execution computes an idempotency key (`{workflow_id}:{event_name}:{entity_id}:{event_key}`) ensuring duplicate events do not create duplicate actions.
- **Traceability**: All executions recorded in `workflow_executions` with execution status (`pending`, `running`, `completed`, `failed`), retry count, and detailed error context.

#### 3.5 In-App Notifications
- Real-time in-app notifications generated by system events or workflow actions.
- Filtered per user and tenant, with read/unread tracking and deep links to CRM entities.

#### 3.6 Approval Foundation
- Generic, reusable approval model for projects, payments, or custom entities.
- Supports requester, assigned approver, status transitions (`pending`, `approved`, `rejected`), decision notes, and audit logging.

---

### 4. Non-Functional Guarantees

1. **Strict Multi-Tenancy**: Every configuration record, workflow definition, custom field, and notification is partitioned by `tenant_id` (`organization_id`). Tenant A cannot read, modify, or execute actions against Tenant B.
2. **Zero Downtime Configuration**: Modifying pipelines or custom fields requires no application reboots or database migrations.
3. **Auditability**: All configuration updates (pipeline modification, custom field definitions, workflow activation) trigger structured audit log entries via the existing Phase 1 audit subsystem.
4. **Performance**: Workflow matching is filtered on indexed `(tenant_id, trigger_event, is_active)`. No unbounded table scans.
