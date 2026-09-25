import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_flexible_pipelines_and_stages(client: AsyncClient):
    """Test default pipeline auto-creation and custom pipeline configuration."""
    reg = await client.post("/api/v1/auth/register", json={
        "organization_name": "Pipeline Org",
        "full_name": "Pipeline Admin",
        "email": "admin@pipelineorg.com",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch pipelines (triggers automatic default pipeline generation)
    list_res = await client.get("/api/v1/pipelines", headers=headers)
    assert list_res.status_code == 200
    pipelines = list_res.json()["data"]
    assert len(pipelines) >= 1
    default_pipe = pipelines[0]
    assert default_pipe["is_default"] is True
    assert len(default_pipe["stages"]) == 8  # 8 default stages
    assert default_pipe["stages"][0]["name"] == "Enquiry"

    # 2. Create custom pipeline for Heat Pumps
    custom_res = await client.post(
        "/api/v1/pipelines",
        headers=headers,
        json={
            "name": "Heat Pump Fast Track",
            "is_default": False,
            "stages": [
                {"name": "Initial Assessment", "order": 1, "probability_percent": 25, "color": "cyan"},
                {"name": "Audit Done", "order": 2, "probability_percent": 60, "color": "blue"},
                {"name": "Delivered", "order": 3, "probability_percent": 100, "is_closed_won": True, "color": "emerald"},
            ],
        },
    )
    assert custom_res.status_code == 201
    custom_pipe = custom_res.json()["data"]
    assert custom_pipe["name"] == "Heat Pump Fast Track"
    assert len(custom_pipe["stages"]) == 3
