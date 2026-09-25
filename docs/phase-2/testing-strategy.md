# Enermax CRM — Phase 2 Testing Strategy & Verification Plan

## 1. Quality Standards

Phase 2 introduces the core business and revenue data of Enermax.
Testing is strictly mandatory across all layers:
1. **API & Service Unit Tests**: Verify business constraints, input validation, and database operations.
2. **Tenant Isolation Verification**: Verify that every single Phase 2 entity strictly obeys multi-tenant security boundaries.
3. **Data Integrity & Financial Math**: Verify decimal calculation for project values, payment sums, and outstanding balances.
4. **End-to-End Workflow Verification**: Simulate the real operator journey from customer onboarding to project execution and payment clearance.

---

## 2. Test Matrix

| Area | Target Test Cases |
| :--- | :--- |
| **Customers** | Creation, listing, pagination, update, deletion, phone validation, tenant isolation |
| **Contacts** | Multiple contacts per customer, primary flag toggle, deletion cascade |
| **Products** | Catalog management, pricing precision, active/inactive filtering |
| **Pipelines** | Custom stage creation, stage ordering, default pipeline assignment |
| **Projects** | Project number generation, customer linkage, stage progression, stage history |
| **Follow-ups** | Due date sorting, today's follow-ups query, overdue query, status changes |
| **Payments** | Payment recording, reference number tracking, sum calculation, outstanding balance math |
| **Notes & Docs** | Polymorphic note attachment, document metadata association |
| **Search** | Case-insensitive multi-field search (name, phone, project number) with tenant scoping |
| **Dashboard** | Total project value, received payments, outstanding balance, count aggregations |
| **E2E Workflow** | Operator full lifecycle test: customer -> project -> stage change -> follow-up -> payment -> dashboard |
