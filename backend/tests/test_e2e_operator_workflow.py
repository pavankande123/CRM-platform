from decimal import Decimal
import datetime
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_operator_workflow(client: AsyncClient):
    """
    Simulates the complete daily journey of a single operator handling a commercial solar project:
    1. Register/Login
    2. Create Customer & Primary Contact
    3. Create Product
    4. Create Project
    5. Advance Project Pipeline Stages (with history logs)
    6. Schedule and Complete Follow-ups
    7. Record Milestone Payments
    8. Attach Notes & Documents
    9. Verify Financials & Dashboard KPIs
    """
    # 1. Onboarding Operator & Tenant
    reg_res = await client.post("/api/v1/auth/register", json={
        "organization_name": "Enermax Solar Systems India",
        "full_name": "K. Murugan",
        "email": "murugan@enermax.com",
        "password": "SecureOperator2026!",
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Operator checks initial Dashboard
    dash_init = await client.get("/api/v1/dashboard", headers=headers)
    assert dash_init.status_code == 200
    assert dash_init.json()["data"]["total_customers"] == 0

    # 3. Create Commercial Customer
    cust_res = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "customer_type": "industrial",
            "name": "Kalyani Cotton Mills Pvt Ltd",
            "email": "contact@kalyanimills.com",
            "phone": "+91 9842100001",
            "city": "Tirupur",
            "state": "Tamil Nadu",
            "source": "referral",
            "primary_contact": {
                "name": "S. Kalyanasundaram",
                "designation": "Managing Director",
                "phone": "+91 9842199999",
                "email": "md@kalyanimills.com",
                "is_primary": True,
            },
        },
    )
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["data"]["id"]

    # 4. Create Product
    prod_res = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "name": "100kW Industrial Rooftop Solar PV",
            "code": "SOL-100KW-IND",
            "category": "Solar PV",
            "unit_price": "4000000.00",
        },
    )
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["data"]["id"]

    # 5. Create Project for Kalyani Cotton Mills
    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Kalyani Spinning Unit 100kW Solar",
            "customer_id": cust_id,
            "product_id": prod_id,
            "value": "4000000.00",
            "priority": "high",
        },
    )
    assert proj_res.status_code == 201
    proj = proj_res.json()["data"]
    proj_id = proj["id"]
    assert proj["stage_name"] == "Enquiry"

    # 6. Fetch Pipeline stages to find 'Site Visit' and 'Quotation'
    pipe_res = await client.get("/api/v1/pipelines", headers=headers)
    stages = pipe_res.json()["data"][0]["stages"]
    site_visit_stg = next(s for s in stages if s["name"] == "Site Visit")
    quotation_stg = next(s for s in stages if s["name"] == "Quotation")
    approval_stg = next(s for s in stages if s["name"] == "Approval")

    # Move to Site Visit
    await client.post(
        f"/api/v1/projects/{proj_id}/stage",
        headers=headers,
        json={"stage_id": site_visit_stg["id"], "notes": "Site shadow analysis completed."},
    )

    # Move to Quotation
    await client.post(
        f"/api/v1/projects/{proj_id}/stage",
        headers=headers,
        json={"stage_id": quotation_stg["id"], "notes": "Commercial proposal ₹40 Lakhs submitted."},
    )

    # 7. Schedule a Follow-up for proposal confirmation
    now = datetime.datetime.now(datetime.timezone.utc)
    fu_res = await client.post(
        "/api/v1/follow-ups",
        headers=headers,
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "title": "Call MD regarding commercial quotation sign-off",
            "due_date": (now + datetime.timedelta(hours=4)).isoformat(),
            "priority": "high",
        },
    )
    assert fu_res.status_code == 201
    fu_id = fu_res.json()["data"]["id"]

    # 8. Complete the Follow-up
    await client.patch(
        f"/api/v1/follow-ups/{fu_id}/complete",
        headers=headers,
        json={"completed_notes": "MD approved terms and agreed to issue 25% advance cheque."},
    )

    # Move Project to Approval
    await client.post(
        f"/api/v1/projects/{proj_id}/stage",
        headers=headers,
        json={"stage_id": approval_stg["id"], "notes": "Contract signed."},
    )

    # 9. Record 25% Advance Payment (₹10,00,000.00)
    pay_res = await client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "amount": "1000000.00",
            "payment_date": "2026-09-25",
            "payment_method": "neft_rtgs",
            "reference_number": "SBI9918273645",
            "notes": "25% Advance payment received via RTGS",
        },
    )
    assert pay_res.status_code == 201

    # 10. Record Document Metadata and Operator Note
    await client.post(
        "/api/v1/documents",
        headers=headers,
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "file_name": "Kalyani_Signed_Agreement_2026.pdf",
            "file_type": "application/pdf",
            "file_size_bytes": 2097152,
            "document_category": "agreement",
        },
    )

    await client.post(
        "/api/v1/notes",
        headers=headers,
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "content": "Net metering application filed with TANGEDCO.",
        },
    )

    # 11. Verify Final Dashboard State
    dash_final = await client.get("/api/v1/dashboard", headers=headers)
    assert dash_final.status_code == 200
    df = dash_final.json()["data"]

    assert df["total_customers"] == 1
    assert df["active_projects"] == 1
    assert Decimal(str(df["total_project_value"])) == Decimal("4000000.00")
    assert Decimal(str(df["total_paid"])) == Decimal("1000000.00")
    assert Decimal(str(df["total_outstanding"])) == Decimal("3000000.00")
    assert len(df["recent_activity"]) >= 5
    assert df["recent_customers"][0]["name"] == "Kalyani Cotton Mills Pvt Ltd"
