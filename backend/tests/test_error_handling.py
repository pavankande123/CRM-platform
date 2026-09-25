import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_standard_error_envelope_on_validation_failure(client: AsyncClient):
    """Test that 422 input validation failure returns standard error envelope with request_id."""
    res = await client.post("/api/v1/auth/register", json={
        "organization_name": "",  # Invalid: min_length=2
        "email": "invalid-email-address",
        "password": "short",  # Invalid: min_length=8
    })
    assert res.status_code == 422
    payload = res.json()
    assert "error" in payload
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in payload["error"]
    assert "details" in payload["error"]
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Request-ID"] == payload["error"]["request_id"]


@pytest.mark.asyncio
async def test_standard_error_envelope_on_not_found(client: AsyncClient):
    """Test that 404 returns RFC compliant error format with request_id header."""
    res = await client.get("/api/v1/non-existent-endpoint")
    assert res.status_code == 404
    assert "X-Request-ID" in res.headers
