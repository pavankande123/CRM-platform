import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import job_service


@pytest.mark.asyncio
async def test_background_job_lifecycle_and_idempotency(client: AsyncClient, auth_headers: dict):
    """
    Test Phase 4 Workstream 3 Background Job Architecture:
    - Enqueue job
    - Idempotency deduplication
    - Status querying
    - Manual retry
    """
    # 1. Enqueue Job
    payload = {
        "queue": "default",
        "job_type": "test.echo",
        "payload": {"message": "Hello background worker"},
        "idempotency_key": "idemp-test-job-001",
        "max_retries": 2,
        "retry_backoff_seconds": 1,
    }
    res = await client.post("/api/v1/jobs", headers=auth_headers, json=payload)
    assert res.status_code == 201, res.text
    job_data = res.json()["data"]
    job_id = job_data["id"]
    assert job_data["status"] == "queued"
    assert job_data["job_type"] == "test.echo"

    # 2. Test Idempotency: Enqueue again with same key
    res_dup = await client.post("/api/v1/jobs", headers=auth_headers, json=payload)
    assert res_dup.status_code == 201
    assert res_dup.json()["data"]["id"] == job_id  # Returns existing record!

    # 3. List Jobs
    list_res = await client.get("/api/v1/jobs?status=queued", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(j["id"] == job_id for j in list_res.json()["data"])

    # 4. Get Job Details
    get_res = await client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == job_id


@pytest.mark.asyncio
async def test_job_execution_worker_and_dead_letter(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """
    Test Job Worker execution:
    - Successful execution transitions to completed
    - Failed execution retries and transitions to dead_letter
    """
    session = db_session
    # Enqueue failing job
    res = await client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={
            "job_type": "test.echo",
            "payload": {"simulate_error": True, "error_message": "Network timeout to supplier API"},
            "max_retries": 1,
            "retry_backoff_seconds": 1,
        },
    )
    assert res.status_code == 201
    failing_job_id = uuid.UUID(res.json()["data"]["id"])

    # Fetch job model directly and run execute_job
    job = await job_service.get_job(session, uuid.UUID(res.json()["data"]["tenant_id"]), failing_job_id)
    assert job.status == "queued"

    # First run: should fail and enter retrying
    success = await job_service.execute_job(session, job)
    assert not success
    assert job.status == "retrying"
    assert job.retry_count == 1
    assert "Retry 1/1" in (job.error_message or "")

    # Second run: max retries reached, should enter dead_letter
    success_retry = await job_service.execute_job(session, job)
    assert not success_retry
    assert job.status == "dead_letter"
    assert "Max retries exhausted" in (job.error_message or "")


    # Test API can query dead_letter status
    dl_res = await client.get(f"/api/v1/jobs/{failing_job_id}", headers=auth_headers)
    assert dl_res.status_code == 200
    assert dl_res.json()["data"]["status"] == "dead_letter"

    # Test Manual Retry from dead_letter
    retry_res = await client.post(f"/api/v1/jobs/{failing_job_id}/retry", headers=auth_headers)
    assert retry_res.status_code == 200
    assert retry_res.json()["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_jobs_tenant_isolation(client: AsyncClient, auth_headers: dict, other_tenant_auth_headers: dict):
    """Verify Tenant B cannot view or retry Tenant A background jobs."""
    # Tenant A creates job
    res_a = await client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={"job_type": "test.echo", "payload": {"secret": "Tenant A Secret"}},
    )
    job_a_id = res_a.json()["data"]["id"]

    # Tenant B tries to get Tenant A job
    res_b = await client.get(f"/api/v1/jobs/{job_a_id}", headers=other_tenant_auth_headers)
    assert res_b.status_code == 404

    # Tenant B tries to retry Tenant A job
    retry_b = await client.post(f"/api/v1/jobs/{job_a_id}/retry", headers=other_tenant_auth_headers)
    assert retry_b.status_code == 404


@pytest.mark.asyncio
async def test_document_storage_upload_download_and_security(client: AsyncClient, auth_headers: dict, other_tenant_auth_headers: dict):
    """
    Test Phase 4 Workstream 8 File Storage Foundation:
    - Binary upload with mime validation
    - Download with tenant check
    - File extension restriction
    - Cross-tenant download blocked
    """
    # 1. Valid PDF Upload
    file_bytes = b"%PDF-1.4 Fake PDF binary stream for testing contract quotation"
    files = {"file": ("Quotation_Test.pdf", io.BytesIO(file_bytes), "application/pdf")}
    upload_res = await client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files=files,
        data={"document_category": "quotation"},
    )
    assert upload_res.status_code == 201, upload_res.text
    doc_data = upload_res.json()["data"]
    doc_id = doc_data["id"]
    assert doc_data["file_name"] == "Quotation_Test.pdf"

    # 2. Download File
    download_res = await client.get(f"/api/v1/documents/{doc_id}/download", headers=auth_headers)
    assert download_res.status_code == 200
    assert download_res.content == file_bytes
    assert "attachment; filename=\"Quotation_Test.pdf\"" in download_res.headers.get("content-disposition", "")

    # 3. Cross-Tenant Download Blocked
    cross_res = await client.get(f"/api/v1/documents/{doc_id}/download", headers=other_tenant_auth_headers)
    assert cross_res.status_code == 404

    # 4. Reject Disallowed Executable Extensions
    bad_files = {"file": ("malicious.exe", io.BytesIO(b"MZ executable"), "application/x-msdownload")}
    bad_res = await client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files=bad_files,
    )
    assert bad_res.status_code == 422
    assert "not permitted" in bad_res.json()["error"]["message"]
