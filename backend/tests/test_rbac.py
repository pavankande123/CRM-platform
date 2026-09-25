import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rbac_permission_enforcement(client: AsyncClient):
    """
    Test RBAC enforcement:
    Admin has full permissions; Operator has restricted permissions.
    """
    # 1. Register organization (initial user is admin)
    reg_res = await client.post("/api/v1/auth/register", json={
        "organization_name": "RBAC Enterprise",
        "full_name": "Admin Boss",
        "email": "admin@rbac.com",
        "password": "AdminPassword2026!",
    })
    admin_token = reg_res.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Admin creates an Operator user
    create_op_res = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "Sam Operator",
            "email": "sam@rbac.com",
            "password": "SamPassword123!",
            "role_name": "operator",
        },
    )
    assert create_op_res.status_code == 200
    assert create_op_res.json()["data"]["role_name"] == "operator"

    # 3. Login as Operator
    op_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "sam@rbac.com", "password": "SamPassword123!"},
    )
    assert op_login.status_code == 200
    op_token = op_login.json()["data"]["access_token"]
    op_headers = {"Authorization": f"Bearer {op_token}"}

    # 4. Operator CAN list users (has users:read)
    list_res = await client.get("/api/v1/users", headers=op_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 2

    # 5. Operator CANNOT update tenant organization name (requires tenant:update)
    patch_res = await client.patch(
        "/api/v1/tenants/me",
        headers=op_headers,
        json={"name": "Hacked Tenant Name"},
    )
    assert patch_res.status_code == 403
    assert patch_res.json()["error"]["code"] == "FORBIDDEN"

    # 6. Admin CAN update tenant organization name
    admin_patch_res = await client.patch(
        "/api/v1/tenants/me",
        headers=admin_headers,
        json={"name": "RBAC Enterprise Renamed"},
    )
    assert admin_patch_res.status_code == 200
    assert admin_patch_res.json()["data"]["name"] == "RBAC Enterprise Renamed"
