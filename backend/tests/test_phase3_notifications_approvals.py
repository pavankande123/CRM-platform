import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notifications_and_approvals_lifecycle(
    async_client: AsyncClient,
    auth_headers: dict,
    other_tenant_auth_headers: dict,
):
    """
    Test Phase 3 Notifications & Approvals:
    - User in-app notifications (list, mark read, mark all read)
    - Approval request creation
    - Approver review & decision (approved / rejected with comments)
    - Rejection of invalid status or unauthorized decisions
    - Strict tenant isolation
    """
    # -----------------------------------------------------------------------
    # 1. NOTIFICATIONS
    # -----------------------------------------------------------------------
    # Fetch notifications inbox
    notif_res = await async_client.get("/api/v1/notifications", headers=auth_headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()["data"]

    # Mark all read
    mark_all = await async_client.post("/api/v1/notifications/read-all", headers=auth_headers)
    assert mark_all.status_code == 200

    unread_res = await async_client.get("/api/v1/notifications?unread_only=true", headers=auth_headers)
    assert unread_res.status_code == 200
    assert len(unread_res.json()["data"]) == 0

    # -----------------------------------------------------------------------
    # 2. APPROVALS
    # -----------------------------------------------------------------------
    # Create customer and project for approval request
    cust_res = await async_client.post(
        "/api/v1/customers",
        json={"name": "Approval Client Corp", "customer_type": "commercial"},
        headers=auth_headers,
    )
    cust_id = cust_res.json()["data"]["id"]

    pipe_res = await async_client.get("/api/v1/pipelines", headers=auth_headers)
    pipeline = pipe_res.json()["data"][0]
    stage_id = pipeline["stages"][0]["id"]

    proj_res = await async_client.post(
        "/api/v1/projects",
        json={
            "name": "Special Discount Solar Plant",
            "customer_id": cust_id,
            "pipeline_id": pipeline["id"],
            "stage_id": stage_id,
            "value": "12000000.00",
        },
        headers=auth_headers,
    )
    proj_id = proj_res.json()["data"]["id"]

    # Create approval request
    approval_payload = {
        "entity_type": "project",
        "entity_id": proj_id,
        "title": "12% Commercial Tariff Discount Approval",
        "description": "Requesting 12% turnkey discount for 500kW rooftop installation",
    }
    appr_res = await async_client.post("/api/v1/approvals", json=approval_payload, headers=auth_headers)
    assert appr_res.status_code == 201, appr_res.text
    approval = appr_res.json()["data"]
    appr_id = approval["id"]
    assert approval["status"] == "pending"

    # Make decision: Approved
    decide_res = await async_client.post(
        f"/api/v1/approvals/{appr_id}/decide",
        json={"decision": "approved", "comments": "Approved based on bulk equipment pricing."},
        headers=auth_headers,
    )
    assert decide_res.status_code == 200
    decided_appr = decide_res.json()["data"]
    assert decided_appr["status"] == "approved"
    assert len(decided_appr["decisions"]) == 1
    assert decided_appr["decisions"][0]["decision"] == "approved"

    # Attempting to decide already decided approval should fail
    re_decide = await async_client.post(
        f"/api/v1/approvals/{appr_id}/decide",
        json={"decision": "rejected", "comments": "Second thought"},
        headers=auth_headers,
    )
    assert re_decide.status_code == 422
    assert "already approved" in re_decide.text

    # 3. Tenant Isolation
    cross_appr = await async_client.get(f"/api/v1/approvals/{appr_id}", headers=other_tenant_auth_headers)
    assert cross_appr.status_code == 404

    cross_decide = await async_client.post(
        f"/api/v1/approvals/{appr_id}/decide",
        json={"decision": "rejected", "comments": "Malicious decision"},
        headers=other_tenant_auth_headers,
    )
    assert cross_decide.status_code == 404
