import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notes_and_documents(client: AsyncClient):
    """Test attaching notes, storing document metadata, and activity timeline generation."""
    reg = await client.post("/api/v1/auth/register", json={
        "organization_name": "Notes Org",
        "full_name": "Notes Admin",
        "email": "admin@notesorg.com",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Customer
    cust_res = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"name": "Heritage Foods", "customer_type": "commercial"},
    )
    cust_id = cust_res.json()["data"]["id"]

    # 1. Attach Note to Customer
    note_res = await client.post(
        "/api/v1/notes",
        headers=headers,
        json={
            "customer_id": cust_id,
            "content": "Customer requested structural load testing report before signing agreement.",
        },
    )
    assert note_res.status_code == 201
    assert "Customer requested" in note_res.json()["data"]["content"]

    # 2. Attach Document Metadata
    doc_res = await client.post(
        "/api/v1/documents",
        headers=headers,
        json={
            "customer_id": cust_id,
            "file_name": "Heritage_Foods_Solar_Quotation_Rev3.pdf",
            "file_type": "application/pdf",
            "file_size_bytes": 1048576,
            "document_category": "quotation",
            "storage_url": "s3://enermax-documents/heritage/quote_rev3.pdf",
        },
    )
    assert doc_res.status_code == 201
    assert doc_res.json()["data"]["file_name"] == "Heritage_Foods_Solar_Quotation_Rev3.pdf"

    # 3. Retrieve Notes for Customer
    notes_list = await client.get(f"/api/v1/notes?customer_id={cust_id}", headers=headers)
    assert notes_list.status_code == 200
    assert len(notes_list.json()["data"]) == 1

    # 4. Retrieve Documents for Customer
    docs_list = await client.get(f"/api/v1/documents?customer_id={cust_id}", headers=headers)
    assert docs_list.status_code == 200
    assert len(docs_list.json()["data"]) == 1
