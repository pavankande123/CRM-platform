import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    """Test full registration, login, profile retrieval, and logout lifecycle."""
    register_payload = {
        "organization_name": "Enermax Solar Systems",
        "full_name": "Rajesh Sharma",
        "email": "rajesh@enermaxsolar.com",
        "password": "SecurePassword2026!",
    }

    # 1. Register
    reg_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 200, reg_res.text
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    access_token = reg_data["data"]["access_token"]
    refresh_token = reg_data["data"]["refresh_token"]
    assert access_token is not None
    assert reg_data["data"]["user"]["email"] == "rajesh@enermaxsolar.com"
    assert reg_data["data"]["organization"]["name"] == "Enermax Solar Systems"

    # 2. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "rajesh@enermaxsolar.com", "password": "SecurePassword2026!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert "access_token" in login_data["data"]

    # 3. Login with wrong password
    bad_login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "rajesh@enermaxsolar.com", "password": "WrongPassword123!"},
    )
    assert bad_login_res.status_code == 401
    assert bad_login_res.json()["error"]["code"] == "UNAUTHORIZED"

    # 4. Get Current User Profile (/auth/me)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["user"]["email"] == "rajesh@enermaxsolar.com"
    assert me_data["organization"]["name"] == "Enermax Solar Systems"
    assert "admin" in me_data["user"]["role_name"]
    assert "crm:read" in me_data["permissions"]

    # 5. Refresh token
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()["data"]

    # 6. Logout
    logout_res = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["logged_out"] is True


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    """Test that protected endpoints reject unauthenticated requests."""
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"
    assert "X-Request-ID" in res.headers
