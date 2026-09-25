# ENERMAX CRM — WORKFLOW AUTOMATION ENGINE

## 1. Engine Mission & Principles

The Enermax Workflow Engine provides safe, deterministic, declarative business automation.
It allows tenant administrators to trigger actions when key CRM milestones occur, without running arbitrary code or risking infinite loops.

**Core Rules**:
1. **No Arbitrary Code Execution**: No `eval()`, JavaScript runtime, Python exec, or dynamic SQL. All conditions and actions use strongly typed, predefined handlers.
2. **Strict Tenant Scoping**: Workflows trigger and execute exclusively within the tenant where the event occurred.
3. **Idempotency by Design**: Every execution generates a deterministic idempotency key. Duplicate events (from retries or duplicate network requests) produce no duplicate side effects.
4. **Resilience & Traceability**: Every execution step is logged to `workflow_executions`. Failures are preserved with full error context.

---

## 2. Event Lifecycle & Architecture

```
[Domain Mutation (e.g. Project Stage Changed)]
                      |
                      v
            [Domain Event Created]
                      |
                      v
             [Workflow Matcher]
   - Filters active workflows for (tenant_id, trigger_event)
                      |
                      v
            [Condition Evaluator]
   - Evaluates boolean conditions (e.g., stage == 'Approval' AND value > 500000)
                      |
        +-------------+-------------+
        | (Pass)                    | (Fail)
        v                           v
  [Idempotency Check]       [Execution Skipped / Logged]
        |
        +-- (Already executed?) --> [Short-circuit deduplication]
        |
        +-- (New execution) ------> [Action Executor]
                                          |
                              +-----------+-----------+
                              |                       |
                              v                       v
                      [Action Handlers]      [Execution Recorder]
                      - create_follow_up      - status: completed / failed
                      - update_record         - completed_at
                      - create_notification   - error_message
                      - assign_record         - retry_count
                      - add_activity
```

---

## 3. Supported Triggers

| Trigger Identifier | Source Entity | Description |
|---|---|---|
| `customer.created` | Customer | Triggered immediately upon new customer onboarding |
| `customer.updated` | Customer | Triggered upon customer profile modification |
| `project.created` | Project | Triggered upon new project creation |
| `project.updated` | Project | Triggered when project attributes are modified |
| `project.stage_changed` | Project | Triggered when project transitions to a new pipeline stage |
| `follow_up.created` | FollowUp | Triggered when an operator schedules a follow-up |
| `follow_up.completed` | FollowUp | Triggered when a follow-up is marked completed |
| `payment.created` | Payment | Triggered when a customer payment milestone is recorded |
| `payment.updated` | Payment | Triggered when payment status changes (e.g., cleared, refunded) |

---

## 4. Condition Evaluation

Conditions are structured as declarative triples or logical groups:
```json
{
  "field": "value",
  "operator": "gte",
  "value": 1000000
}
```

### Supported Operators:
- `eq`: Exact equality (`==`)
- `neq`: Not equal (`!=`)
- `gt`: Greater than (`>`)
- `gte`: Greater than or equal (`>=`)
- `lt`: Less than (`<`)
- `lte`: Less than or equal (`<=`)
- `contains`: Substring match or collection containment
- `in`: Membership in array of values
- `is_empty`: Null, empty string, or zero length
- `is_not_empty`: Not null and non-empty

---

## 5. Supported Actions

1. **`create_follow_up`**: Automatically schedules an operator follow-up task (e.g., "Verify advance payment receipt within 2 days").
2. **`create_notification`**: Dispatches an in-app notification to the project owner or designated role.
3. **`assign_record`**: Automatically sets the `owner_id` of a project or customer based on product line or customer tier.
4. **`update_record`**: Updates status or priority on the target record (e.g., auto-set project priority to "high" when value > ₹50L).
5. **`add_activity`**: Appends an immutable activity log entry documenting the automated milestone.

---

## 6. Idempotency & Failure Strategy

### 6.1 Idempotency Key Formula
```
idempotency_key = sha256("{workflow_id}:{event_name}:{entity_id}:{event_payload_digest}")
```
If a `workflow_executions` record exists with this `idempotency_key` and status `completed` or `running`, subsequent triggers are safely skipped.

### 6.2 Retry Handling
- Transient database errors or network timeouts trigger retry attempts up to `max_retries = 3` with exponential backoff.
- If retries exceed the threshold, the status is set to `failed`, the stack trace is recorded in `error_message`, and an administrator alert is logged.
- Failed executions can be manually retried via `POST /api/v1/workflows/executions/{id}/retry`.
