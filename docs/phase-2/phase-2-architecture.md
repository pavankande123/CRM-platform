# Enermax CRM — Phase 2 Architecture Proposal

**Document Version**: 2.0.0  
**Phase**: Phase 2 — Core Enermax CRM  
**Status**: Architecture Proposal & Design Review  
**Foundation**: Built strictly upon Phase 1 (Frozen & Verified)

---

## 1. Executive Summary & Design Vision

Enermax is an operational business handling approximately **₹5 crore** in commercial and industrial solar and energy projects. The core operational reality is that business operations are **driven by a single operator** rather than large distributed departmental teams.

Phase 2 builds the **Core Enermax CRM** on top of the Phase 1 production foundation:
* **Simple Operator Surface**: Fast single-page workflows, unified customer timelines, zero bloated CRM menus.
* **Strict Multi-Tenant Isolation**: Every database entity is partitioned by `tenant_id` foreign key referencing `organizations.id`.
* **Flexible Project Pipelines**: Products define their own pipeline stages (e.g. *Enquiry → Site Visit → Quotation → Approval → Installation → Testing → Completed*), eliminating hardcoded pipeline rigidity.
* **Accurate Financial Tracking**: Numeric decimal accounting for project values, payment receipts, and outstanding balances.
* **Observability & Auditability**: Every major domain mutation produces an immutable, sanitized audit and activity event.

---

## 2. Phase 2 Component Architecture

```mermaid
graph TD
    Client[Operator Web Client: React 19 + TypeScript + Tailwind] -->|REST / JSON + Bearer JWT| API[FastAPI Core Gateway]
    
    subgraph API Endpoints [/api/v1/]
        CustomersAPI[/customers & /contacts]
        ProductsAPI[/products]
        PipelinesAPI[/pipelines & /stages]
        ProjectsAPI[/projects]
        FollowUpsAPI[/follow-ups]
        PaymentsAPI[/payments]
        NotesAPI[/notes]
        DocsAPI[/documents]
        SearchAPI[/search]
        DashboardAPI[/dashboard]
    end

    API --> CustomersAPI
    API --> ProductsAPI
    API --> PipelinesAPI
    API --> ProjectsAPI
    API --> FollowUpsAPI
    API --> PaymentsAPI
    API --> NotesAPI
    API --> DocsAPI
    API --> SearchAPI
    API --> DashboardAPI

    subgraph Service Layer
        CustomerService[Customer & Contact Service]
        PipelineService[Pipeline & Stage Engine]
        ProjectService[Project & Stage History Service]
        PaymentService[Payment & Financial Balance Service]
        FollowUpService[Follow-Up Scheduling Service]
        SearchService[PostgreSQL Search Service]
        DashboardService[Dashboard Aggregation Service]
        ActivityService[Activity Timeline Service]
    end

    CustomersAPI --> CustomerService
    PipelinesAPI --> PipelineService
    ProjectsAPI --> ProjectService
    PaymentsAPI --> PaymentService
    FollowUpsAPI --> FollowUpService
    SearchAPI --> SearchService
    DashboardAPI --> DashboardService

    subgraph Persistence Layer [PostgreSQL 16]
        DB_Customers[(customers & contacts)]
        DB_Pipelines[(pipelines & pipeline_stages)]
        DB_Projects[(projects & project_stage_history)]
        DB_Payments[(payments)]
        DB_FollowUps[(follow_ups)]
        DB_Notes[(notes)]
        DB_Docs[(document_metadata)]
        DB_Activities[(activities)]
    end

    CustomerService --> DB_Customers
    PipelineService --> DB_Pipelines
    ProjectService --> DB_Projects
    PaymentService --> DB_Payments
    FollowUpService --> DB_FollowUps
```

---

## 3. Core Modules & Responsibilities

1. **Customers & Contacts**:
   - Central business entity storing customer type (Commercial, Industrial, Residential), contact information, and geographic location.
   - 1-to-many Contact persons per customer with `is_primary` flag.
2. **Products**:
   - Reusable catalog of energy systems and services (Solar PV, Heat Pumps, Energy Audits).
3. **Flexible Pipelines & Stages**:
   - Allows different products to run through customized stages.
   - Records full chronological `ProjectStageHistory` whenever a project transitions between stages.
4. **Projects**:
   - The central operational hub connecting Customer, Product, Pipeline, Stage, Follow-ups, Payments, and Notes.
5. **Follow-ups**:
   - First-class operational task management with due dates, priority, status (Pending, Completed, Cancelled), and overdue alerting.
6. **Payments & Financial Tracking**:
   - Records customer payments with method, reference number (UTR/Cheque), and status.
   - Calculates total project value, total paid, and total outstanding with exact decimal arithmetic.
7. **Notes & Document Metadata**:
   - Operator notes attached to Customers, Projects, Follow-ups, and Payments.
   - Secure metadata tracking for quotations, invoices, agreements, and technical sheets.
8. **Activity Timeline**:
   - Unified chronological stream answering *"What happened with this customer or project?"*
9. **PostgreSQL Search Service**:
   - High-performance multi-entity search across customer names, phone numbers, emails, project numbers, and products.
10. **Core Business Dashboard**:
    - Real-time operational dashboard providing answers to *"What is happening in the business right now?"*

---

## 4. Phase 1 Compatibility Verification

* **Authentication & RBAC**: Reuses Phase 1 JWT tokens and `require_permission` dependency.
* **Tenant Isolation**: Extends Phase 1 `TenantScopedMixin` to all 11 new tables. Every query is filtered by `tenant_id`.
* **Database Session**: Uses existing SQLAlchemy 2.0 async engine and connection pooling.
* **Error Handling**: Uses Phase 1 standardized error envelopes with `request_id`.
* **Zero Phase 1 Changes**: No modifications are required to Phase 1 tables or security layers.
