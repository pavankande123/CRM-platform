# ENERMAX CRM — PHASE 3 TESTING STRATEGY

## 1. Quality Objectives

Phase 3 introduces critical platform features (configurable pipelines, dynamic custom fields, saved views, and the workflow automation engine). The test suite must verify:
- Functional correctness of all new capabilities.
- Strict multi-tenant isolation across all configuration and execution paths.
- Preservation of historical data integrity upon configuration mutations.
- Workflow idempotency and resilient retry behavior.
- High performance and absence of N+1 database queries.

---

## 2. Test Plan Matrix

| Component | Target Coverage | Key Test Scenarios |
|---|---|---|
| **Configurable Pipelines** | Models, Service, Endpoints | Create, update, reorder stages, stage soft-deactivation, rejection of deleting stages with linked projects, tenant isolation. |
| **Custom Fields** | Models, Service, Endpoints | Create definition per type (text, number, date, select), validate options, store/retrieve typed values, searchability, cross-tenant isolation. |
| **Saved Views** | Models, Service, Endpoints | Create view, update filters, reject invalid operators, tenant-scoped access. |
| **Workflow Engine** | Engine, Dispatcher, Handlers | Trigger on events (`project.stage_changed`, `payment.created`), evaluate conditions (`gte`, `eq`), execute actions (`create_follow_up`, `create_notification`), verify idempotency (duplicate event suppression), retry handling on failure. |
| **In-App Notifications** | Service, Endpoints | Generate notification from workflow, fetch user inbox, mark read/unread, tenant isolation. |
| **Approvals Foundation** | Service, Endpoints | Request approval, approve/reject with comments, unauthorized user rejection, tenant isolation. |
| **End-to-End Workflow** | Integration / API | Onboard Customer -> Create Project -> Trigger Approval -> Auto-create Follow-up -> Generate Notification -> Complete Follow-up. |
| **Performance Benchmarks** | Benchmark Suite | Benchmark pipeline list, custom field retrieval, saved view compilation, workflow dispatch execution, and inbox queries. |

---

## 3. Automation and Execution

All Phase 3 tests will be implemented under `backend/tests/test_phase3_*.py` and executed via pytest.
The existing 21 Phase 1 & Phase 2 tests must continue passing with zero regressions.
All frontend components must compile cleanly with `npm run build`.
