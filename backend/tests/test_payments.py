from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_payment_tracking_and_financial_math(client: AsyncClient):
    """Test payment recording, decimal precision math, and balance calculations."""
    reg = await client.post("/api/v1/auth/register", json={
        "organization_name": "Finance Org",
        "full_name": "Finance Admin",
        "email": "admin@financeorg.com",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Customer & Project with Value = ₹50,00,000.00
    cust_res = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"name": "Sterling Biotech", "customer_type": "industrial"},
    )
    cust_id = cust_res.json()["data"]["id"]

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "150kW Solar EPC",
            "customer_id": cust_id,
            "value": "5000000.00",
        },
    )
    proj_id = proj_res.json()["data"]["id"]

    # 2. Record Milestone 1: Advance payment = ₹15,00,000.50
    pay1_res = await client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "amount": "1500000.50",
            "payment_date": "2026-09-25",
            "payment_method": "neft_rtgs",
            "reference_number": "UTR987654321",
            "notes": "30% Advance on signing",
        },
    )
    assert pay1_res.status_code == 201
    pay1 = pay1_res.json()["data"]
    assert pay1["payment_number"].startswith("ENX-PAY-")
    assert Decimal(str(pay1["amount"])) == Decimal("1500000.50")

    # 3. Record Milestone 2: Material delivery = ₹20,00,000.50
    pay2_res = await client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "amount": "2000000.50",
            "payment_date": "2026-09-26",
            "payment_method": "neft_rtgs",
            "reference_number": "UTR987654322",
            "notes": "40% upon panel arrival",
        },
    )
    assert pay2_res.status_code == 201

    # 4. Check Project Balances
    proj_check = await client.get(f"/api/v1/projects/{proj_id}", headers=headers)
    assert proj_check.status_code == 200
    proj_data = proj_check.json()["data"]
    # Total Paid = 1500000.50 + 2000000.50 = 3500001.00
    assert Decimal(str(proj_data["total_paid"])) == Decimal("3500001.00")
    # Outstanding = 5000000.00 - 3500001.00 = 1499999.00
    assert Decimal(str(proj_data["outstanding_amount"])) == Decimal("1499999.00")

    # 5. Check Global Financial Summary
    summary_res = await client.get("/api/v1/payments/summary", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()["data"]
    assert Decimal(str(summary["total_project_value"])) == Decimal("5000000.00")
    assert Decimal(str(summary["total_paid"])) == Decimal("3500001.00")
    assert Decimal(str(summary["total_outstanding"])) == Decimal("1499999.00")
    assert summary["payment_count"] == 2
