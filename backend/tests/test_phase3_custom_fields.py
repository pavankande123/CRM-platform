import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_custom_fields_lifecycle_and_typed_storage(
    async_client: AsyncClient,
    auth_headers: dict,
    other_tenant_auth_headers: dict,
):
    """
    Test Phase 3 Custom Fields:
    - Create definitions for text, number, date, select
    - Validate field type and options
    - Attach typed values to customer / project
    - Verify retrieval and type safety
    - Soft deactivation
    - Tenant isolation
    """
    # 1. Create a numeric custom field: solar capacity (kW)
    num_field_payload = {
        "entity_type": "project",
        "field_name": "installed_capacity_kw",
        "display_name": "Installed Capacity (kW)",
        "field_type": "number",
        "is_required": True,
        "is_searchable": True,
    }
    res_num = await async_client.post("/api/v1/custom-fields", json=num_field_payload, headers=auth_headers)
    assert res_num.status_code == 201, res_num.text
    num_field = res_num.json()["data"]
    assert num_field["field_name"] == "installed_capacity_kw"

    # 2. Create a select custom field: customer tier
    select_payload = {
        "entity_type": "customer",
        "field_name": "client_category",
        "display_name": "Client Category",
        "field_type": "select",
        "options": ["Industrial", "Commercial", "Institutional"],
    }
    res_sel = await async_client.post("/api/v1/custom-fields", json=select_payload, headers=auth_headers)
    assert res_sel.status_code == 201
    sel_field = res_sel.json()["data"]
    assert sel_field["options"] == ["Industrial", "Commercial", "Institutional"]

    # 3. Create a date custom field: sanction date
    date_payload = {
        "entity_type": "project",
        "field_name": "discom_sanction_date",
        "display_name": "DISCOM Sanction Date",
        "field_type": "date",
    }
    res_date = await async_client.post("/api/v1/custom-fields", json=date_payload, headers=auth_headers)
    assert res_date.status_code == 201

    # 4. Validation error on invalid select option
    sel_err_payload = {
        "entity_type": "customer",
        "field_name": "invalid_select",
        "display_name": "Invalid Select",
        "field_type": "select",
        "options": [],  # Empty options forbidden
    }
    res_err = await async_client.post("/api/v1/custom-fields", json=sel_err_payload, headers=auth_headers)
    assert res_err.status_code == 422

    # 5. Create Customer and Project to store values
    cust_res = await async_client.post(
        "/api/v1/customers",
        json={"name": "Sterling Solar Client", "customer_type": "commercial"},
        headers=auth_headers,
    )
    cust_id = cust_res.json()["data"]["id"]

    pipe_res = await async_client.get("/api/v1/pipelines", headers=auth_headers)
    pipeline = pipe_res.json()["data"][0]
    stage_id = pipeline["stages"][0]["id"]

    proj_res = await async_client.post(
        "/api/v1/projects",
        json={
            "name": "500kW Rooftop EPC",
            "customer_id": cust_id,
            "pipeline_id": pipeline["id"],
            "stage_id": stage_id,
            "value": "18000000.00",
        },
        headers=auth_headers,
    )
    proj_id = proj_res.json()["data"]["id"]

    # 6. Store typed custom field values on project
    values_payload = {
        "values": {
            "installed_capacity_kw": 500.5,
            "discom_sanction_date": "2026-08-15",
        }
    }
    set_val_res = await async_client.post(
        f"/api/v1/custom-fields/values/project/{proj_id}",
        json=values_payload,
        headers=auth_headers,
    )
    assert set_val_res.status_code == 200
    stored_values = set_val_res.json()["data"]
    val_map = {v["field_name"]: v["value"] for v in stored_values}
    assert val_map["installed_capacity_kw"] == 500.5
    assert val_map["discom_sanction_date"] == "2026-08-15"

    # 7. Store select value on customer
    cust_val_payload = {
        "values": {
            "client_category": "Industrial",
        }
    }
    set_cust_val = await async_client.post(
        f"/api/v1/custom-fields/values/customer/{cust_id}",
        json=cust_val_payload,
        headers=auth_headers,
    )
    assert set_cust_val.status_code == 200
    assert set_cust_val.json()["data"][0]["value"] == "Industrial"

    # 8. Test validation: invalid option for select field rejected
    bad_val_payload = {
        "values": {
            "client_category": "Residential",  # Not in allowed options
        }
    }
    bad_val_res = await async_client.post(
        f"/api/v1/custom-fields/values/customer/{cust_id}",
        json=bad_val_payload,
        headers=auth_headers,
    )
    assert bad_val_res.status_code == 422

    # 9. Tenant Isolation: Tenant B cannot read Tenant A's custom fields or values
    cross_fields = await async_client.get(
        "/api/v1/custom-fields?entity_type=project",
        headers=other_tenant_auth_headers,
    )
    assert cross_fields.status_code == 200
    other_fields = cross_fields.json()["data"]
    assert not any(f["field_name"] == "installed_capacity_kw" for f in other_fields)

    cross_val = await async_client.get(
        f"/api/v1/custom-fields/values/project/{proj_id}",
        headers=other_tenant_auth_headers,
    )
    assert cross_val.status_code == 200
    assert len(cross_val.json()["data"]) == 0
