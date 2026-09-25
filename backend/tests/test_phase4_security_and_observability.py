import logging
import time
import pytest
from httpx import AsyncClient

from app.core.logging import StructuredJsonFormatter, scrub_sensitive_text
from app.core.metrics import metrics_registry


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_revocation(client: AsyncClient):
    """
    Test Phase 4 Workstream 7 Security Hardening:
    - Refreshing tokens issues a new pair and revokes the old refresh token.
    - Replaying the old refresh token is immediately rejected.
    """
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Rotation Org {int(time.time()*1000)}",
            "full_name": "Rotation Admin",
            "email": f"rot-{int(time.time()*1000)}@testrot.com",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 200
    initial_refresh = reg_res.json()["data"]["refresh_token"]

    # First Refresh: should succeed and rotate
    ref1_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
    assert ref1_res.status_code == 200
    new_refresh = ref1_res.json()["data"]["refresh_token"]
    assert new_refresh != initial_refresh

    # Second Refresh with initial_refresh: MUST fail because old refresh token was revoked!
    ref2_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
    assert ref2_res.status_code == 401
    assert "revoked" in ref2_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_logout_token_revocation(client: AsyncClient):
    """
    Test Phase 4 Workstream 7:
    - Logging out revokes the active access token.
    - Subsequent API calls with that access token fail with 401.
    """
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Logout Org {int(time.time()*1000)}",
            "full_name": "Logout Admin",
            "email": f"logout-{int(time.time()*1000)}@testlogout.com",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 200
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify token works before logout
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200

    # Perform logout
    logout_res = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # Verify token is now revoked and rejected
    me_after_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_after_res.status_code == 401
    assert "revoked" in me_after_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_login_rate_limiting_abuse_protection(client: AsyncClient):
    """
    Test Phase 4 Workstream 4 Rate Limiting & Abuse Protection:
    - Flooding /auth/login triggers HTTP 429 Too Many Requests
    - Response includes Retry-After and X-RateLimit headers
    """
    from app.core.config import settings

    target_email = "victim@example.com"
    # Make multiple failed login requests
    limit = settings.RATE_LIMIT_LOGIN_PER_MINUTE
    hit_429 = False

    for _ in range(limit + 5):
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": target_email, "password": "WrongPassword!"},
        )
        if res.status_code == 429:
            hit_429 = True
            assert "Retry-After" in res.headers
            assert res.headers.get("X-RateLimit-Remaining") == "0"
            assert res.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
            break

    assert hit_429, "Rate limiter did not throttle excessive authentication requests."


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(client: AsyncClient):
    """
    Test Phase 4 Workstream 5 Observability:
    - /metrics returns Prometheus formatted telemetry
    """
    # Trigger a request to accumulate metrics
    await client.get("/health")

    res = await client.get("/metrics")
    assert res.status_code == 200
    body = res.text
    assert "enermax_http_requests_total" in body
    assert "enermax_db_pool_size" in body
    assert "enermax_rate_limit_hits_total" in body


@pytest.mark.asyncio
async def test_oversized_payload_rejection(client: AsyncClient, auth_headers: dict):
    """
    Test Phase 4 Workstream 7 HTTP Security:
    - Oversized payloads (> 10MB) rejected with HTTP 413
    """
    # Sending Content-Length header exceeding 10MB
    headers = {
        **auth_headers,
        "Content-Length": str(15 * 1024 * 1024),  # 15 MB
    }
    res = await client.post("/api/v1/customers", headers=headers, json={"name": "Big"})
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_sensitive_credential_scrubbing():
    """
    Test Phase 4 Workstream 5 Logging Credential Scrubbing:
    - Passwords and bearer tokens redacted from logs
    """
    sample_text = "User login attempt with password='SuperSecret123!' and Bearer eyJhbGciOiJIUzI1NiJ9.abc.xyz"
    scrubbed = scrub_sensitive_text(sample_text)
    assert "SuperSecret123!" not in scrubbed
    assert "***REDACTED***" in scrubbed
    assert "eyJhbGci" not in scrubbed
