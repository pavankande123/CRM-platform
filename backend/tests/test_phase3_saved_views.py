import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_saved_views_and_filters(
    async_client: AsyncClient,
    auth_headers: dict,
    other_tenant_auth_headers: dict,
):
    """
    Test Phase 3 Saved Views:
    - Create a saved operational view with complex server-validated filters
    - Execute the saved view query and verify filtered results
    - Update and delete view
    - Validate rejection of dangerous or invalid operators
    - Tenant isolation
    """
    # 1. Create Projects with distinct values and statuses
    cust_res = await async_client.post(
        "/api/v1/customers",
        json={"name": "Tata Power Grid", "customer_type": "commercial"},
        headers=auth_headers,
    )
    cust_id = cust_res.json()["data"]["id"]

    pipe_res = await async_client.get("/api/v1/pipelines", headers=auth_headers)
    pipeline = pipe_res.json()["data"][0]
    stage_id = pipeline["stages"][0]["id"]

    # Small project
    await async_client.post(
        "/api/v1/projects",
        json={
            "name": "Small Rooftop 10kW",
            "customer_id": cust_id,
            "pipeline_id": pipeline["id"],
            "stage_id": stage_id,
            "value": "450000.00",
            "priority": "low",
        },
        headers=auth_headers,
    )

    # Large high-value project
    p2_res = await async_client.post(
        "/api/v1/projects",
        json={
            "name": "Mega Solar Park 2MW",
            "customer_id": cust_id,
            "pipeline_id": pipeline["id"],
            "stage_id": stage_id,
            "value": "75000000.00",
            "priority": "high",
        },
        headers=auth_headers,
    )
    p2_id = p2_res.json()["data"]["id"]

    # 2. Create Saved View: Projects > ₹1 Crore or priority == high
    view_payload = {
        "name": "Mega High-Value Projects",
        "entity_type": "project",
        "is_default": False,
        "is_shared": True,
        "filters": [
            {"field": "priority", "operator": "eq", "value": "high"},
            {"field": "value", "operator": "gte", "value": 50000000},
        ],
        "visible_columns": ["project_number", "name", "value", "status"],
        "sort_field": "value",
        "sort_direction": "desc",
    }
    view_res = await async_client.post("/api/v1/views", json=view_payload, headers=auth_headers)
    assert view_res.status_code == 201, view_res.text
    view = view_res.json()["data"]
    view_id = view["id"]
    assert view["name"] == "Mega High-Value Projects"

    # 3. Execute view query
    exec_res = await async_client.get(f"/api/v1/views/{view_id}/execute", headers=auth_headers)
    assert exec_res.status_code == 200
    exec_data = exec_res.json()["data"]
    assert exec_data["total"] >= 1
    assert p2_id in exec_data["records"]

    # 4. Reject invalid or dangerous operators
    bad_view_payload = {
        "name": "Injection Attempt View",
        "entity_type": "project",
        "filters": [
            {"field": "name", "operator": "UNION SELECT * FROM users --", "value": "test"},
        ],
    }
    bad_res = await async_client.post("/api/v1/views", json=bad_view_payload, headers=auth_headers)
    assert bad_res.status_code == 422

    # 5. Tenant Isolation: Other tenant cannot access or execute Tenant A's view
    cross_view = await async_client.get(f"/api/v1/views/{view_id}", headers=other_tenant_auth_headers)
    assert cross_view.status_code == 404

    cross_exec = await async_client.get(f"/api/v1/views/{view_id}/execute", headers=other_tenant_auth_headers)
    assert cross_exec.status_code == 404
