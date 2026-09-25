import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_strict_tenant_isolation(client: AsyncClient):
    """
    MANDATORY SECURITY TEST:
    Verify that Tenant A cannot access or mutate Tenant B's users, audit logs, or data.
    """
    # 1. Register Tenant A
    reg_a = await client.post("/api/v1/auth/register", json={
        "organization_name": "Alpha Corp",
        "full_name": "Alice Alpha",
        "email": "alice@alpha.com",
        "password": "PasswordAlpha123!",
    })
    assert reg_a.status_code == 200
    token_a = reg_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register Tenant B
    reg_b = await client.post("/api/v1/auth/register", json={
        "organization_name": "Beta Corp",
        "full_name": "Bob Beta",
        "email": "bob@beta.com",
        "password": "PasswordBeta123!",
    })
    assert reg_b.status_code == 200
    token_b = reg_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Tenant A creates a user in Tenant A
    create_user_a = await client.post(
        "/api/v1/users",
        headers=headers_a,
        json={
            "full_name": "Aaron Operator",
            "email": "aaron@alpha.com",
            "password": "AaronPassword123!",
            "role_name": "operator",
        },
    )
    assert create_user_a.status_code == 200
    user_a_id = create_user_a.json()["data"]["id"]

    # 4. Tenant B lists users: Must NOT see Alice or Aaron
    users_b_res = await client.get("/api/v1/users", headers=headers_b)
    assert users_b_res.status_code == 200
    users_b_list = users_b_res.json()["data"]
    emails_in_b = [u["email"] for u in users_b_list]

    assert "bob@beta.com" in emails_in_b
    assert "alice@alpha.com" not in emails_in_b
    assert "aaron@alpha.com" not in emails_in_b
    for u in users_b_list:
        assert u["id"] != user_a_id

    # 5. Tenant B lists audit logs: Must NOT see Tenant A's audit entries
    logs_b_res = await client.get("/api/v1/audit/logs", headers=headers_b)
    assert logs_b_res.status_code == 200
    logs_b = logs_b_res.json()["data"]["items"]

    # All logs in B must belong strictly to Tenant B's organization
    tenant_b_id = reg_b.json()["data"]["organization"]["id"]
    for log in logs_b:
        assert log["tenant_id"] == tenant_b_id
        assert log["actor_email"] != "alice@alpha.com"
        assert log["actor_email"] != "aaron@alpha.com"

    # 6. Tenant A lists audit logs: Must NOT see Tenant B's audit entries
    logs_a_res = await client.get("/api/v1/audit/logs", headers=headers_a)
    assert logs_a_res.status_code == 200
    logs_a = logs_a_res.json()["data"]["items"]

    tenant_a_id = reg_a.json()["data"]["organization"]["id"]
    for log in logs_a:
        assert log["tenant_id"] == tenant_a_id
        assert log["actor_email"] != "bob@beta.com"

    # 7. Updating Tenant A's organization from Tenant A updates A, not B
    update_a = await client.patch(
        "/api/v1/tenants/me",
        headers=headers_a,
        json={"name": "Alpha Corp Renamed"},
    )
    assert update_a.status_code == 200
    assert update_a.json()["data"]["name"] == "Alpha Corp Renamed"

    # Verify Tenant B's organization was unchanged
    tenant_b_check = await client.get("/api/v1/tenants/me", headers=headers_b)
    assert tenant_b_check.status_code == 200
    assert tenant_b_check.json()["data"]["name"] == "Beta Corp"
