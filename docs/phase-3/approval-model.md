# ENERMAX CRM — APPROVAL MODEL FOUNDATION

## 1. Objective

Enermax business operations frequently require administrative sign-off before significant milestones proceed (e.g., project discounts over 10%, commercial contracts over ₹25 Lakhs, or stage transition to final commissioning).

Phase 3 introduces a lightweight, reusable **Approval Foundation** adhering to the simplicity principle.

---

## 2. Domain Model

```
+-------------------------------------------------------------+
|                      ApprovalRequest                        |
|  - id: UUID                                                 |
|  - tenant_id: UUID -> organizations.id                      |
|  - entity_type: VARCHAR(50) ('project', 'payment')          |
|  - entity_id: UUID                                          |
|  - requester_id: UUID -> users.id                           |
|  - approver_id: UUID -> users.id (Optional specific user)   |
|  - title: VARCHAR(255)                                      |
|  - description: TEXT                                        |
|  - status: VARCHAR(50) ('pending', 'approved', 'rejected')  |
|  - requested_at: TIMESTAMP WITH TIME ZONE                   |
|  - decided_at: TIMESTAMP WITH TIME ZONE                     |
+-------------------------------------------------------------+
                              | 1
                              |
                              | 0..*
                              v
+-------------------------------------------------------------+
|                      ApprovalDecision                       |
|  - id: UUID                                                 |
|  - tenant_id: UUID -> organizations.id                      |
|  - approval_request_id: UUID -> approval_requests.id        |
|  - decided_by_id: UUID -> users.id                          |
|  - decision: VARCHAR(50) ('approved', 'rejected')           |
|  - comments: TEXT                                           |
|  - decided_at: TIMESTAMP WITH TIME ZONE                     |
+-------------------------------------------------------------+
```

---

## 3. Workflow & Authorization Rules

1. **Submission**: Any user with `crm:write` on the target entity may create an `ApprovalRequest`.
2. **Review & Decision**: Only users with the `admin` role or assigned `approver_id` may approve or reject a request (`decision = "approved"` or `"rejected"`).
3. **Immutability**: Once an approval request is decided (`approved` or `rejected`), its state cannot be toggled back. A new request must be submitted if parameters change.
4. **Audit & Notifications**: Deciding an approval records an audit log entry and dispatches an in-app notification to the original requester with the approver's comments.
