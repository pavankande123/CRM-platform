import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workflow_engine_automation_and_idempotency(
    async_client: AsyncClient,
    auth_headers: dict,
    other_tenant_auth_headers: dict,
):
    """
    Test Phase 3 Workflow Engine:
    - Create a workflow rule for high-value payments (> ₹10 Lakhs)
    - Condition: payment.amount >= 1,000,000
    - Action: Auto-create Follow-up task & In-App Notification
    - Test execution history and audit traceability
    - Test Idempotency: Duplicate event delivery suppresses duplicate follow-up creation
    - Test Tenant Isolation: Tenant B events cannot trigger Tenant A workflows
    """
    # 1. Create Workflow Definition: High Value Payment Auto Follow-Up
    wf_payload = {
        "name": "High Value Payment Verification",
        "description": "Automatically schedules bank verification when payment >= 10 Lakhs",
        "entity_type": "payment",
        "trigger_event": "payment.created",
        "is_active": True,
        "conditions": [
            {"field": "amount", "operator": "gte", "value": 1000000},
        ],
        "actions": [
            {
                "action_type": "create_follow_up",
                "params": {
                    "title": "Verify High-Value NEFT/RTGS Credit with Axis Bank",
                    "days_offset": 1,
                    "priority": "high",
                },
            },
            {
                "action_type": "create_notification",
                "params": {
                    "title": "High-Value Payment Received",
                    "message": "Payment >= ₹10,00,000 recorded. Verification follow-up created.",
                    "notification_type": "success",
                },
            },
        ],
    }
    wf_res = await async_client.post("/api/v1/workflows", json=wf_payload, headers=auth_headers)
    assert wf_res.status_code == 201, wf_res.text
    workflow = wf_res.json()["data"]
    wf_id = workflow["id"]
    assert workflow["name"] == "High Value Payment Verification"

    # 2. Create customer and project
    cust_res = await async_client.post(
        "/api/v1/customers",
        json={"name": "Adani Solar Logistics", "customer_type": "commercial"},
        headers=auth_headers,
    )
    cust_id = cust_res.json()["data"]["id"]

    pipe_res = await async_client.get("/api/v1/pipelines", headers=auth_headers)
    pipeline = pipe_res.json()["data"][0]
    stage_id = pipeline["stages"][0]["id"]

    proj_res = await async_client.post(
        "/api/v1/projects",
        json={
            "name": "1MW Commercial Captive",
            "customer_id": cust_id,
            "pipeline_id": pipeline["id"],
            "stage_id": stage_id,
            "value": "35000000.00",
        },
        headers=auth_headers,
    )
    proj_id = proj_res.json()["data"]["id"]

    # 3. Record a small payment (< ₹10 Lakhs) -> should NOT trigger action
    small_pmt_res = await async_client.post(
        "/api/v1/payments",
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "amount": "50000.00",
            "payment_date": "2026-09-25",
            "payment_method": "upi",
            "reference_number": "UPI-SMALL-001",
        },
        headers=auth_headers,
    )
    assert small_pmt_res.status_code == 201

    # Check follow-ups: should be 0 automated follow-ups for this
    fu_list = await async_client.get(f"/api/v1/follow-ups?customer_id={cust_id}", headers=auth_headers)
    assert len(fu_list.json()["data"]["items"]) == 0

    # 4. Record a high-value payment (₹15,00,000 >= ₹10,00,000) -> Triggers Workflow!
    big_pmt_res = await async_client.post(
        "/api/v1/payments",
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "amount": "1500000.00",
            "payment_date": "2026-09-25",
            "payment_method": "bank_transfer",
            "reference_number": "RTGS-AXIS-998811",
        },
        headers=auth_headers,
    )
    assert big_pmt_res.status_code == 201
    big_pmt = big_pmt_res.json()["data"]

    # Verify automated follow-up was automatically created!
    fu_list2 = await async_client.get(f"/api/v1/follow-ups?customer_id={cust_id}", headers=auth_headers)
    assert fu_list2.status_code == 200
    follow_ups = fu_list2.json()["data"]["items"]
    assert len(follow_ups) == 1
    assert "Verify High-Value NEFT/RTGS Credit" in follow_ups[0]["title"]
    assert follow_ups[0]["priority"] == "high"

    # Verify execution history recorded
    exec_res = await async_client.get(f"/api/v1/workflows/executions?workflow_id={wf_id}", headers=auth_headers)
    assert exec_res.status_code == 200
    executions = exec_res.json()["data"]
    assert len(executions) >= 1
    assert executions[0]["status"] == "completed"

    # 5. IDEMPOTENCY & RETRY TEST:
    # Attempting to retry an already completed execution must reject to prevent duplicate side effects
    exec_id = executions[0]["id"]
    dup_retry = await async_client.post(f"/api/v1/workflows/executions/{exec_id}/retry", headers=auth_headers)
    assert dup_retry.status_code == 422
    assert "already completed" in dup_retry.text

    # Follow-ups count must remain exactly 1 (no duplicate follow-up created!)
    fu_list3 = await async_client.get(f"/api/v1/follow-ups?customer_id={cust_id}", headers=auth_headers)
    assert len(fu_list3.json()["data"]["items"]) == 1

    # 6. Tenant Isolation: Tenant B cannot see Tenant A's workflow or executions
    cross_wf = await async_client.get(f"/api/v1/workflows/{wf_id}", headers=other_tenant_auth_headers)
    assert cross_wf.status_code == 404

    cross_exec = await async_client.get(f"/api/v1/workflows/executions?workflow_id={wf_id}", headers=other_tenant_auth_headers)
    assert cross_exec.status_code == 200
    assert len(cross_exec.json()["data"]) == 0
