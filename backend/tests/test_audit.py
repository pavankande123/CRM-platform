import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_audit_logging_and_sanitization(client: AsyncClient):
    """Test that actions trigger audit logs and sensitive passwords are never logged."""
    # Register tenant
    reg_res = await client.post("/api/v1/auth/register", json={
        "organization_name": "Audit Test Corp",
        "full_name": "Auditor One",
        "email": "auditor@auditcorp.com",
        "password": "MySuperSecretPassword123!",
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch audit logs
    logs_res = await client.get("/api/v1/audit/logs", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()["data"]["items"]

    assert len(logs) >= 1
    register_log = next((l for l in logs if l["action"] == "REGISTER"), None)
    assert register_log is not None
    assert register_log["resource"] == "organization"

    # Verify no raw password leaked into metadata_json
    metadata = register_log["metadata_json"] or ""
    assert "MySuperSecretPassword123!" not in metadata
    assert "password" not in metadata.lower() or "***REDACTED***" in metadata


@pytest.mark.asyncio
async def test_audit_pagination(client: AsyncClient):
    """Test pagination of audit logs."""
    reg_res = await client.post("/api/v1/auth/register", json={
        "organization_name": "Pagination Corp",
        "full_name": "Paginator",
        "email": "page@paginator.com",
        "password": "PasswordPaginator123!",
    })
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/audit/logs?page=1&page_size=5", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert isinstance(data["items"], list)
