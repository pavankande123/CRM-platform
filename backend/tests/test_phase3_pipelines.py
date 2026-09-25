import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_configurable_pipelines_and_stages(
    async_client: AsyncClient,
    auth_headers: dict,
    other_tenant_auth_headers: dict,
):
    """
    Test Phase 3 pipeline capabilities:
    - Create pipeline
    - Update pipeline
    - Add stages
    - Reorder stages
    - Stage soft-deactivation when projects exist (preserving historical data integrity)
    - Strict tenant isolation
    """
    # 1. Create a custom solar pipeline
    create_payload = {
        "name": "Commercial Rooftop EPC Pipeline",
        "is_default": False,
        "is_active": True,
        "stages": [
            {"name": "Initial Site Survey", "order": 1, "probability_percent": 15, "color": "cyan", "is_active": True},
            {"name": "Shadow & Feasibility Analysis", "order": 2, "probability_percent": 35, "color": "blue", "is_active": True},
            {"name": "DISCOM Net Metering Approval", "order": 3, "probability_percent": 60, "color": "amber", "is_active": True},
            {"name": "Grid Commissioning", "order": 4, "probability_percent": 100, "is_closed_won": True, "color": "emerald", "is_active": True},
        ],
    }
    res = await async_client.post("/api/v1/pipelines", json=create_payload, headers=auth_headers)
    assert res.status_code == 201, res.text
    pipeline = res.json()["data"]
    pipeline_id = pipeline["id"]
    stages = pipeline["stages"]
    assert len(stages) == 4
    assert pipeline["name"] == "Commercial Rooftop EPC Pipeline"

    # 2. Update pipeline name
    update_res = await async_client.put(
        f"/api/v1/pipelines/{pipeline_id}",
        json={"name": "Industrial Mega-Watt Solar EPC"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["name"] == "Industrial Mega-Watt Solar EPC"

    # 3. Add a new stage to pipeline
    new_stage_payload = {
        "name": "CEIG Electrical Safety Inspection",
        "order": 5,
        "probability_percent": 85,
        "color": "purple",
        "is_active": True,
    }
    add_stage_res = await async_client.post(
        f"/api/v1/pipelines/{pipeline_id}/stages",
        json=new_stage_payload,
        headers=auth_headers,
    )
    assert add_stage_res.status_code == 201
    new_stage = add_stage_res.json()["data"]
    new_stage_id = new_stage["id"]
    assert new_stage["name"] == "CEIG Electrical Safety Inspection"

    # 4. Reorder stages
    reorder_payload = {
        "stages": [
            {"stage_id": new_stage_id, "order": 3},
            {"stage_id": stages[2]["id"], "order": 4},
        ]
    }
    reorder_res = await async_client.post(
        f"/api/v1/pipelines/{pipeline_id}/stages/reorder",
        json=reorder_payload,
        headers=auth_headers,
    )
    assert reorder_res.status_code == 200
    reordered_stages = reorder_res.json()["data"]
    stage_orders = {s["id"]: s["order"] for s in reordered_stages}
    assert stage_orders[new_stage_id] == 3

    # 5. Historical Data Preservation: Attach a project to a stage and verify stage is soft-deactivated, not deleted
    cust_res = await async_client.post(
        "/api/v1/customers",
        json={"name": "Pipeline Test Customer", "customer_type": "commercial"},
        headers=auth_headers,
    )
    cust_id = cust_res.json()["data"]["id"]

    proj_res = await async_client.post(
        "/api/v1/projects",
        json={
            "name": "Historical Protection Project",
            "customer_id": cust_id,
            "pipeline_id": pipeline_id,
            "stage_id": new_stage_id,
            "value": "2500000.00",
        },
        headers=auth_headers,
    )
    assert proj_res.status_code == 201

    # Attempt to delete the stage that is referenced by active project
    delete_stage_res = await async_client.delete(
        f"/api/v1/pipelines/{pipeline_id}/stages/{new_stage_id}",
        headers=auth_headers,
    )
    assert delete_stage_res.status_code == 200
    del_result = delete_stage_res.json()["data"]
    # Must be soft-deactivated to preserve historical project data integrity!
    assert del_result["status"] == "deactivated"
    assert "existing project records" in del_result["message"]

    # 6. Strict Tenant Isolation: Tenant B cannot view or modify Tenant A's pipeline
    cross_get = await async_client.get(f"/api/v1/pipelines/{pipeline_id}", headers=other_tenant_auth_headers)
    assert cross_get.status_code == 404

    cross_update = await async_client.put(
        f"/api/v1/pipelines/{pipeline_id}",
        json={"name": "Tenant B Malicious Rename"},
        headers=other_tenant_auth_headers,
    )
    assert cross_update.status_code == 404
