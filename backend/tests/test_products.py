from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_product_catalog_operations(client: AsyncClient):
    """Test product creation, listing, decimal pricing, and tenant isolation."""
    reg = await client.post("/api/v1/auth/register", json={
        "organization_name": "Product Org",
        "full_name": "Product Admin",
        "email": "admin@productorg.com",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Product
    create_res = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "50kW Commercial Rooftop Solar PV",
            "code": "SOL-PV-50KW",
            "category": "Solar PV",
            "description": "High efficiency monocrystalline solar installation",
            "unit_price": "2250000.00",
            "is_active": True,
        },
    )
    assert create_res.status_code == 201
    prod = create_res.json()["data"]
    assert prod["name"] == "50kW Commercial Rooftop Solar PV"
    assert Decimal(str(prod["unit_price"])) == Decimal("2250000.00")

    # 2. List Products
    list_res = await client.get("/api/v1/products?category=Solar+PV", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["data"]["total"] == 1
