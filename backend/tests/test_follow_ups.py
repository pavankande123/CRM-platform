import datetime
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_follow_up_management_and_alerts(client: AsyncClient):
    """Test follow-up scheduling, today/overdue queries, and completion."""
    reg = await client.post("/api/v1/auth/register", json={
        "organization_name": "FollowUp Org",
        "full_name": "FollowUp Admin",
        "email": "admin@followup.com",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Customer
    cust_res = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"name": "Premier Hospitals", "customer_type": "commercial"},
    )
    cust_id = cust_res.json()["data"]["id"]

    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Schedule follow-up due in 2 hours (Today's follow-up)
    today_due = (now + datetime.timedelta(hours=2)).isoformat()
    create_today = await client.post(
        "/api/v1/follow-ups",
        headers=headers,
        json={
            "customer_id": cust_id,
            "title": "Call Dr. Sharma regarding technical proposal",
            "due_date": today_due,
            "priority": "high",
        },
    )
    assert create_today.status_code == 201
    today_fu_id = create_today.json()["data"]["id"]

    # 2. Schedule follow-up that was due yesterday (Overdue follow-up)
    yesterday_due = (now - datetime.timedelta(days=1)).isoformat()
    create_overdue = await client.post(
        "/api/v1/follow-ups",
        headers=headers,
        json={
            "customer_id": cust_id,
            "title": "Collect electrical single line diagram",
            "due_date": yesterday_due,
            "priority": "medium",
        },
    )
    assert create_overdue.status_code == 201
    overdue_fu_id = create_overdue.json()["data"]["id"]

    # 3. Query overdue follow-ups
    overdue_res = await client.get("/api/v1/follow-ups?overdue_only=true", headers=headers)
    assert overdue_res.status_code == 200
    overdue_items = overdue_res.json()["data"]["items"]
    assert any(f["id"] == overdue_fu_id for f in overdue_items)

    # 4. Mark overdue follow-up as completed
    comp_res = await client.patch(
        f"/api/v1/follow-ups/{overdue_fu_id}/complete",
        headers=headers,
        json={"completed_notes": "Diagram received via email from chief electrician."},
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["status"] == "completed"

    # 5. Verify it is no longer returned in overdue query
    recheck_res = await client.get("/api/v1/follow-ups?overdue_only=true", headers=headers)
    assert not any(f["id"] == overdue_fu_id for f in recheck_res.json()["data"]["items"])
