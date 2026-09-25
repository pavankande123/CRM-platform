from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_core_dashboard_metrics(client: AsyncClient):
    """Test operational core dashboard aggregates all business dimensions accurately."""
    reg = await client.post("/api/v1/auth/register", json={
        "organization_name": "Dashboard Metrics Org",
        "full_name": "Executive Admin",
        "email": "admin@dashboardorg.com",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create 2 Customers
    c1 = await client.post("/api/v1/customers", headers=headers, json={"name": "Client 1"})
    c2 = await client.post("/api/v1/customers", headers=headers, json={"name": "Client 2"})
    c1_id = c1.json()["data"]["id"]
    c2_id = c2.json()["data"]["id"]

    # 2. Create 2 Projects
    p1 = await client.post("/api/v1/projects", headers=headers, json={
        "name": "Project 1",
        "customer_id": c1_id,
        "value": "2000000.00",
    })
    p2 = await client.post("/api/v1/projects", headers=headers, json={
        "name": "Project 2",
        "customer_id": c2_id,
        "value": "3000000.00",
    })
    p1_id = p1.json()["data"]["id"]

    # 3. Record Payment on Project 1 of ₹10,00,000.00
    await client.post("/api/v1/payments", headers=headers, json={
        "customer_id": c1_id,
        "project_id": p1_id,
        "amount": "1000000.00",
        "payment_date": "2026-09-25",
    })

    # 4. Fetch Dashboard
    dash_res = await client.get("/api/v1/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()["data"]

    assert dash["total_customers"] == 2
    assert dash["active_projects"] == 2
    assert Decimal(str(dash["total_project_value"])) == Decimal("5000000.00")
    assert Decimal(str(dash["total_paid"])) == Decimal("1000000.00")
    assert Decimal(str(dash["total_outstanding"])) == Decimal("4000000.00")
    assert len(dash["recent_customers"]) == 2
    assert len(dash["recent_activity"]) >= 3
    assert len(dash["projects_by_stage"]) >= 1
