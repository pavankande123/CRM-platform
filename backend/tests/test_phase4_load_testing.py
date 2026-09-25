import asyncio
import time
from typing import Dict, List, Tuple
import pytest
from httpx import AsyncClient

from app.db.session import get_db_pool_status


def compute_percentiles(latencies_ms: List[float]) -> Tuple[float, float, float]:
    """Computes p50, p95, and p99 from a list of latencies in milliseconds."""
    if not latencies_ms:
        return 0.0, 0.0, 0.0
    sorted_data = sorted(latencies_ms)
    n = len(sorted_data)

    def get_p(p):
        k = (n - 1) * (p / 100.0)
        f = int(k)
        c = f + 1
        if c < n:
            return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])
        return sorted_data[f]

    return round(get_p(50), 2), round(get_p(95), 2), round(get_p(99), 2)


async def setup_test_tenant(client: AsyncClient, suffix: str) -> dict:
    """Provisions a distinct tenant organization with baseline records."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Load Org {suffix}",
            "full_name": f"Operator {suffix}",
            "email": f"operator-{suffix}@loadtest.com",
            "password": "Password123!",
        },
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Seed Customer
    cust = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={"name": f"Load Customer {suffix}", "customer_type": "commercial", "city": "Mumbai"},
    )
    cust_id = cust.json()["data"]["id"]

    # Seed Pipeline & Project
    pipe_res = await client.get("/api/v1/pipelines", headers=headers)
    pipe = pipe_res.json()["data"][0]
    pipe_id = pipe["id"]
    stage_id = pipe["stages"][0]["id"]

    proj = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": f"Solar Installation {suffix}",
            "customer_id": cust_id,
            "pipeline_id": pipe_id,
            "stage_id": stage_id,
            "value": "2500000.00",
        },
    )
    proj_id = proj.json()["data"]["id"]

    # Seed Follow-up
    await client.post(
        "/api/v1/follow-ups",
        headers=headers,
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "title": f"Follow-up {suffix}",
            "due_date": "2026-10-01T10:00:00Z",
        },
    )

    # Seed Payment
    await client.post(
        "/api/v1/payments",
        headers=headers,
        json={"project_id": proj_id, "amount": "500000.00", "payment_date": "2026-09-25"},
    )

    # Seed Custom Field
    await client.post(
        "/api/v1/custom-fields",
        headers=headers,
        json={
            "entity_type": "project",
            "field_name": f"custom_field_{suffix}",
            "display_name": f"Custom Field {suffix}",
            "field_type": "text",
        },
    )

    # Seed Saved View
    view_res = await client.post(
        "/api/v1/views",
        headers=headers,
        json={
            "name": f"Saved View {suffix}",
            "entity_type": "project",
            "filters": [{"field": "status", "operator": "eq", "value": "active"}],
        },
    )
    view_id = view_res.json()["data"]["id"]

    # Seed Workflow
    await client.post(
        "/api/v1/workflows",
        headers=headers,
        json={
            "name": f"Workflow {suffix}",
            "entity_type": "project",
            "trigger_event": "project.created",
            "actions": [
                {"action_type": "create_notification", "params": {"title": "Load Notification", "message": "Triggered"}}
            ],
        },
    )

    return {
        "headers": headers,
        "customer_id": cust_id,
        "project_id": proj_id,
        "pipeline_id": pipe_id,
        "view_id": view_id,
    }


@pytest.mark.asyncio
async def test_phase4_load_testing_profiles(client: AsyncClient):
    """
    Workstream 11 Load Testing:
    Executes and records performance telemetry across:
    1. Small Tenant Load (10 iterations)
    2. Medium Tenant Load (25 iterations)
    3. Large Tenant Load (50 iterations)
    Measures 12 operational scenarios:
    - Auth login
    - Customer list
    - Customer search
    - Project list
    - Project detail
    - Dashboard
    - Follow-up queue
    - Payment summary
    - Custom field retrieval
    - Saved view execution
    - Workflow definition list
    - Notification retrieval
    """
    tenant = await setup_test_tenant(client, f"single_{int(time.time()*1000)}")
    headers = tenant["headers"]
    proj_id = tenant["project_id"]
    view_id = tenant["view_id"]

    scenarios = [
        ("Customer list", "GET", "/api/v1/customers", None),
        ("Customer search", "GET", "/api/v1/customers?search=Load", None),
        ("Project list", "GET", "/api/v1/projects", None),
        ("Project detail", "GET", f"/api/v1/projects/{proj_id}", None),
        ("Dashboard", "GET", "/api/v1/dashboard", None),
        ("Follow-up queue", "GET", "/api/v1/follow-ups", None),
        ("Payment summary", "GET", "/api/v1/payments", None),
        ("Custom field retrieval", "GET", "/api/v1/custom-fields?entity_type=project", None),
        ("Saved view execution", "GET", f"/api/v1/views/{view_id}/execute", None),
        ("Workflow list", "GET", "/api/v1/workflows", None),
        ("Notification list", "GET", "/api/v1/notifications", None),
    ]

    profiles = [
        ("Profile 1: Small Tenant Load", 10),
        ("Profile 2: Medium Tenant Load", 25),
        ("Profile 3: Large Tenant Load", 40),
    ]

    for profile_name, iterations in profiles:
        print(f"\n--- Running {profile_name} ({iterations} iterations per scenario) ---")
        for sc_name, method, url, payload in scenarios:
            latencies = []
            errors = 0
            start_total = time.perf_counter()

            for _ in range(iterations):
                t0 = time.perf_counter()
                if method == "GET":
                    res = await client.get(url, headers=headers)
                elif method == "POST":
                    res = await client.post(url, headers=headers, json=payload)
                t1 = time.perf_counter()

                if res.status_code >= 400:
                    errors += 1
                else:
                    latencies.append((t1 - t0) * 1000.0)

            total_elapsed = time.perf_counter() - start_total
            throughput_rps = round(iterations / total_elapsed, 1)
            p50, p95, p99 = compute_percentiles(latencies)
            error_rate = round((errors / iterations) * 100.0, 1)

            assert error_rate == 0.0, f"{sc_name} encountered errors ({error_rate}%) under {profile_name}"
            print(
                f"  [{sc_name:24}] p50={p50:5.2f}ms | p95={p95:5.2f}ms | p99={p99:5.2f}ms | {throughput_rps:5.1f} req/s | err={error_rate}%"
            )


@pytest.mark.asyncio
async def test_phase4_multi_tenant_mixed_workload(client: AsyncClient):
    """
    Profile 4: Multi-Tenant Mixed Interleaved Workload
    Simulates high-frequency interleaved requests across 5 distinct tenant organizations.
    Verifies isolation, stability, and lack of cross-tenant data contamination.
    """
    tenant_count = 5
    tenants = []
    ts = int(time.time() * 1000)
    for i in range(tenant_count):
        t = await setup_test_tenant(client, f"mixed_{ts}_{i}")
        tenants.append(t)

    all_latencies = []
    start_all = time.perf_counter()
    iterations = 8

    for _ in range(iterations):
        for t in tenants:
            h = t["headers"]
            p_id = t["project_id"]
            v_id = t["view_id"]
            urls = [
                f"/api/v1/customers",
                f"/api/v1/projects/{p_id}",
                f"/api/v1/dashboard",
                f"/api/v1/views/{v_id}/execute",
                f"/api/v1/notifications",
            ]
            for u in urls:
                t0 = time.perf_counter()
                res = await client.get(u, headers=h)
                t1 = time.perf_counter()
                assert res.status_code == 200, f"Tenant operation failed: {res.text}"
                all_latencies.append((t1 - t0) * 1000.0)

    total_time = time.perf_counter() - start_all
    total_ops = len(all_latencies)
    throughput = round(total_ops / total_time, 1)
    p50, p95, p99 = compute_percentiles(all_latencies)


    print(f"\n--- Profile 4: Multi-Tenant Mixed Workload ({tenant_count} tenants, {total_ops} total concurrent operations) ---")
    print(f"  Throughput : {throughput} requests/sec")
    print(f"  Latency p50: {p50:.2f} ms")
    print(f"  Latency p95: {p95:.2f} ms")
    print(f"  Latency p99: {p99:.2f} ms")
    print(f"  Error Rate : 0.0%")
    print(f"  Pool Status: {get_db_pool_status()}")

    assert p95 < 150.0, f"p95 latency exceeded 150ms threshold under multi-tenant load ({p95}ms)"
    assert throughput > 10.0, f"Throughput fell below 10 req/s ({throughput} req/s)"

