import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """Test that /health returns 200 and healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time" in response.headers


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    """Test that /ready returns 200 and database health report."""
    response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "database" in data["dependencies"]
    assert data["dependencies"]["database"]["status"] == "healthy"
