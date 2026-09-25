import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_global_search_and_tenant_isolation(client: AsyncClient):
    """Test global multi-entity search and tenant isolation."""
    # Tenant A
    reg_a = await client.post("/api/v1/auth/register", json={
        "organization_name": "Search Org A",
        "full_name": "Admin A",
        "email": "admin@searcha.com",
        "password": "Password123!",
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['data']['access_token']}"}

    # Tenant B
    reg_b = await client.post("/api/v1/auth/register", json={
        "organization_name": "Search Org B",
        "full_name": "Admin B",
        "email": "admin@searchb.com",
        "password": "Password123!",
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['data']['access_token']}"}

    # Tenant A creates Customer and Project
    cust_res = await client.post(
        "/api/v1/customers",
        headers=headers_a,
        json={
            "name": "Apollo Hospitals Chennai",
            "phone": "9840012345",
            "email": "facilities@apollo.com",
            "city": "Chennai",
        },
    )
    cust_id = cust_res.json()["data"]["id"]

    await client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={
            "name": "Apollo Main Block Rooftop Solar",
            "customer_id": cust_id,
            "value": "8500000.00",
        },
    )

    # 1. Tenant A searches by name keyword: "Apollo"
    search_name = await client.get("/api/v1/search?q=Apollo", headers=headers_a)
    assert search_name.status_code == 200
    res_a = search_name.json()["data"]
    assert res_a["total_results"] >= 2
    assert any("Apollo Hospitals" in c["name"] for c in res_a["customers"])
    assert any("Apollo Main Block" in p["name"] for p in res_a["projects"])

    # 2. Tenant A searches by phone number: "9840012345"
    search_phone = await client.get("/api/v1/search?q=9840012345", headers=headers_a)
    assert search_phone.status_code == 200
    assert any(c["phone"] == "9840012345" for c in search_phone.json()["data"]["customers"])

    # 3. MANDATORY TENANT ISOLATION: Tenant B searches for "Apollo" -> returns 0 results
    search_b = await client.get("/api/v1/search?q=Apollo", headers=headers_b)
    assert search_b.status_code == 200
    assert search_b.json()["data"]["total_results"] == 0
    assert len(search_b.json()["data"]["customers"]) == 0
    assert len(search_b.json()["data"]["projects"]) == 0
