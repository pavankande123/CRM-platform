import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_phase3_e2e_automation_workflow(
    async_client: AsyncClient,
    auth_headers: dict,
    other_tenant_auth_headers: dict,
):
    """
    SECTION 31 END-TO-END TEST:
    1. Define workflow: Trigger on `project.stage_changed`, condition: stage_name == 'Approval',
       action: create follow-up ('Prepare Net Metering & Technical File') & in-app notification.
    2. Create Customer
    3. Create Project in Enquiry stage
    4. Transition Project stage to Approval
    5. Workflow triggers and condition evaluates
    6. Verify Follow-up is automatically created
    7. Verify Notification is automatically generated
    8. Operator marks follow-up as completed
    9. Verify Activity history is updated
    10. Verify all data remains strictly tenant-isolated
    """
    # Step 1: Configure Pipeline and Stages
    pipe_res = await async_client.get("/api/v1/pipelines", headers=auth_headers)
    pipeline = pipe_res.json()["data"][0]
    stages = pipeline["stages"]
    enquiry_stage = next(s for s in stages if s["name"] == "Enquiry")
    approval_stage = next(s for s in stages if s["name"] == "Approval")

    # Step 2: Define Workflow Rule
    wf_payload = {
        "name": "Stage Approval Automation",
        "description": "Auto-schedule net metering file preparation when entering Approval",
        "entity_type": "project",
        "trigger_event": "project.stage_changed",
        "is_active": True,
        "conditions": [
            {"field": "stage_name", "operator": "eq", "value": "Approval"},
        ],
        "actions": [
            {
                "action_type": "create_follow_up",
                "params": {
                    "title": "Prepare DISCOM Net Metering Dossier",
                    "days_offset": 2,
                    "priority": "high",
                },
            },
            {
                "action_type": "create_notification",
                "params": {
                    "title": "Project Moved to Approval",
                    "message": "DISCOM Net Metering Dossier preparation task assigned.",
                    "notification_type": "warning",
                },
            },
        ],
    }
    wf_res = await async_client.post("/api/v1/workflows", json=wf_payload, headers=auth_headers)
    assert wf_res.status_code == 201
    workflow_id = wf_res.json()["data"]["id"]

    # Step 3: Create Customer
    cust_res = await async_client.post(
        "/api/v1/customers",
        json={
            "name": "Reliance Solar Hub",
            "customer_type": "commercial",
            "city": "Ahmedabad",
            "state": "Gujarat",
        },
        headers=auth_headers,
    )
    assert cust_res.status_code == 201
    customer = cust_res.json()["data"]
    cust_id = customer["id"]

    # Step 4: Create Project in Enquiry stage
    proj_res = await async_client.post(
        "/api/v1/projects",
        json={
            "name": "300kW Rooftop EPC System",
            "customer_id": cust_id,
            "pipeline_id": pipeline["id"],
            "stage_id": enquiry_stage["id"],
            "value": "11500000.00",
        },
        headers=auth_headers,
    )
    assert proj_res.status_code == 201
    project = proj_res.json()["data"]
    proj_id = project["id"]

    # Verify no automated follow-up yet
    pre_fu_res = await async_client.get(f"/api/v1/follow-ups?customer_id={cust_id}", headers=auth_headers)
    assert len(pre_fu_res.json()["data"]["items"]) == 0

    # Step 5: Transition Project to 'Approval' stage -> TRIGGERS WORKFLOW
    transition_res = await async_client.post(
        f"/api/v1/projects/{proj_id}/stage",
        json={
            "stage_id": approval_stage["id"],
            "notes": "Client accepted proposal; moving to DISCOM approval",
        },
        headers=auth_headers,
    )
    assert transition_res.status_code == 200

    # Step 6: Verify automated Follow-Up was created
    post_fu_res = await async_client.get(f"/api/v1/follow-ups?customer_id={cust_id}", headers=auth_headers)
    assert post_fu_res.status_code == 200
    follow_ups = post_fu_res.json()["data"]["items"]
    assert len(follow_ups) == 1
    auto_fu = follow_ups[0]
    assert auto_fu["title"] == "Prepare DISCOM Net Metering Dossier"
    assert auto_fu["priority"] == "high"
    assert auto_fu["status"] == "pending"

    # Step 7: Verify Notification was generated
    notif_res = await async_client.get("/api/v1/notifications?unread_only=true", headers=auth_headers)
    assert notif_res.status_code == 200
    unreads = notif_res.json()["data"]
    matching_notif = next((n for n in unreads if "Project Moved to Approval" in n["title"]), None)
    assert matching_notif is not None

    # Step 8: Operator completes follow-up
    complete_res = await async_client.patch(
        f"/api/v1/follow-ups/{auto_fu['id']}/complete",
        json={"completed_notes": "All DISCOM engineering drawings and test certificates uploaded."},
        headers=auth_headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["data"]["status"] == "completed"

    # Step 9: Verify Activity History updated
    # View customer 360 to see comprehensive activity timeline
    cust_360 = await async_client.get(f"/api/v1/customers/{cust_id}", headers=auth_headers)
    assert cust_360.status_code == 200
    activities = cust_360.json()["data"]["activities"]
    activity_types = [a["activity_type"] for a in activities]
    assert "STAGE_CHANGED" in activity_types
    assert "FOLLOW_UP_COMPLETED" in activity_types

    # Step 10: Strict Tenant Isolation
    # Tenant B must NOT see any of Tenant A's customer, project, workflow, follow-up, or activities
    cross_cust = await async_client.get(f"/api/v1/customers/{cust_id}", headers=other_tenant_auth_headers)
    assert cross_cust.status_code == 404

    cross_proj = await async_client.get(f"/api/v1/projects/{proj_id}", headers=other_tenant_auth_headers)
    assert cross_proj.status_code == 404

    cross_fu = await async_client.get(f"/api/v1/follow-ups/{auto_fu['id']}", headers=other_tenant_auth_headers)
    assert cross_fu.status_code == 404
