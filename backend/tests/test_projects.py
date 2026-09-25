from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_lifecycle_and_stage_transitions(client: AsyncClient):
    """Test project creation, stage transitions, history recording, and tenant isolation."""
    # 1. Setup Tenant A
    reg_a = await client.post("/api/v1/auth/register", json={
        "organization_name": "Project Corp A",
        "full_name": "Project Admin A",
        "email": "admin@projecta.com",
        "password": "Password123!",
    })
    token_a = reg_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Setup Tenant B
    reg_b = await client.post("/api/v1/auth/register", json={
        "organization_name": "Project Corp B",
        "full_name": "Project Admin B",
        "email": "admin@projectb.com",
        "password": "Password123!",
    })
    token_b = reg_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Create Customer in Tenant A
    cust_res = await client.post(
        "/api/v1/customers",
        headers=headers_a,
        json={"name": "Kaveri Spinning Mills", "customer_type": "industrial"},
    )
    cust_id = cust_res.json()["data"]["id"]

    # 3. Create Project in Tenant A
    proj_create = await client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={
            "name": "100kW Solar Installation",
            "customer_id": cust_id,
            "value": "4500000.00",
            "currency": "INR",
            "priority": "high",
        },
    )
    assert proj_create.status_code == 201
    proj_a = proj_create.json()["data"]
    proj_id = proj_a["id"]
    assert proj_a["project_number"].startswith("ENX-PRJ-")
    assert Decimal(str(proj_a["value"])) == Decimal("4500000.00")
    assert proj_a["stage_name"] == "Enquiry"

    # 4. Advance Stage: Move from Enquiry to Site Visit
    # Fetch stages to get target stage ID
    pipe_res = await client.get("/api/v1/pipelines", headers=headers_a)
    stages = pipe_res.json()["data"][0]["stages"]
    site_visit_stage = next(s for s in stages if s["name"] == "Site Visit")

    stage_move_res = await client.post(
        f"/api/v1/projects/{proj_id}/stage",
        headers=headers_a,
        json={
            "stage_id": site_visit_stage["id"],
            "notes": "Site visit scheduled for upcoming Monday with structural engineer",
        },
    )
    assert stage_move_res.status_code == 200

    # 5. Fetch project details and verify stage history
    detail_res = await client.get(f"/api/v1/projects/{proj_id}", headers=headers_a)
    assert detail_res.status_code == 200
    proj_detail = detail_res.json()["data"]
    assert proj_detail["stage_name"] == "Site Visit"
    assert len(proj_detail["stage_history"]) >= 2  # initial + transition
    latest_hist = proj_detail["stage_history"][0]
    assert latest_hist["to_stage_name"] == "Site Visit"
    assert "Site visit scheduled" in latest_hist["notes"]

    # 6. MANDATORY TENANT ISOLATION: Tenant B cannot access or update Tenant A's project
    get_b = await client.get(f"/api/v1/projects/{proj_id}", headers=headers_b)
    assert get_b.status_code == 404

    stage_move_b = await client.post(
        f"/api/v1/projects/{proj_id}/stage",
        headers=headers_b,
        json={"stage_id": site_visit_stage["id"]},
    )
    assert stage_move_b.status_code == 404
