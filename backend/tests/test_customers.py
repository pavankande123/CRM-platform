import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_customer_lifecycle_and_tenant_isolation(client: AsyncClient):
    """
    Test customer creation, contact linkage, retrieval, update, and strict tenant isolation.
    """
    # 1. Register Tenant A
    reg_a = await client.post("/api/v1/auth/register", json={
        "organization_name": "Solar Tech A",
        "full_name": "Admin A",
        "email": "admin@solara.com",
        "password": "Password123!",
    })
    token_a = reg_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register Tenant B
    reg_b = await client.post("/api/v1/auth/register", json={
        "organization_name": "Solar Tech B",
        "full_name": "Admin B",
        "email": "admin@solarb.com",
        "password": "Password123!",
    })
    token_b = reg_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Tenant A creates Customer with primary contact
    create_res = await client.post(
        "/api/v1/customers",
        headers=headers_a,
        json={
            "customer_type": "industrial",
            "name": "Tata Steel Facility",
            "email": "contact@tatasteel.com",
            "phone": "+91 9876543210",
            "city": "Jamshedpur",
            "state": "Jharkhand",
            "source": "referral",
            "primary_contact": {
                "name": "Sanjay Verma",
                "designation": "Chief Engineer",
                "phone": "+91 9876500001",
                "email": "sanjay@tatasteel.com",
                "is_primary": True,
            },
        },
    )
    assert create_res.status_code == 201
    cust_a = create_res.json()["data"]
    cust_a_id = cust_a["id"]
    assert cust_a["name"] == "Tata Steel Facility"
    assert cust_a["primary_contact_name"] == "Sanjay Verma"

    # 4. Tenant A lists customers: sees Tata Steel
    list_a = await client.get("/api/v1/customers", headers=headers_a)
    assert list_a.status_code == 200
    assert list_a.json()["data"]["total"] == 1
    assert list_a.json()["data"]["items"][0]["id"] == cust_a_id

    # 5. MANDATORY TENANT ISOLATION: Tenant B lists customers -> sees 0
    list_b = await client.get("/api/v1/customers", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json()["data"]["total"] == 0

    # 6. Tenant B tries to fetch Tenant A's customer directly -> 404
    get_b = await client.get(f"/api/v1/customers/{cust_a_id}", headers=headers_b)
    assert get_b.status_code == 404

    # 7. Tenant B tries to update Tenant A's customer -> 404
    patch_b = await client.patch(
        f"/api/v1/customers/{cust_a_id}",
        headers=headers_b,
        json={"name": "Hacked Name"},
    )
    assert patch_b.status_code == 404

    # 8. Tenant A updates customer successfully
    patch_a = await client.patch(
        f"/api/v1/customers/{cust_a_id}",
        headers=headers_a,
        json={"city": "Ranchi"},
    )
    assert patch_a.status_code == 200
    assert patch_a.json()["data"]["city"] == "Ranchi"

    # 9. Tenant A adds a second contact
    contact_res = await client.post(
        f"/api/v1/customers/{cust_a_id}/contacts",
        headers=headers_a,
        json={
            "name": "Priya Singh",
            "designation": "Procurement Officer",
            "phone": "+91 9876500002",
            "email": "priya@tatasteel.com",
            "is_primary": False,
        },
    )
    assert contact_res.status_code == 201

    # 10. Tenant A gets full customer details (verifies both contacts present)
    detail_res = await client.get(f"/api/v1/customers/{cust_a_id}", headers=headers_a)
    assert detail_res.status_code == 200
    assert len(detail_res.json()["data"]["contacts"]) == 2
