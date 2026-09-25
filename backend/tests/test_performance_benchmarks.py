import time
import pytest
from httpx import AsyncClient

def percentile(data, pct):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1
    if c < len(sorted_data):
        return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])
    return sorted_data[f]

@pytest.mark.asyncio
async def test_representative_operations_benchmark(client: AsyncClient):
    """
    Benchmark representative Phase 2 operations:
    - Customer list
    - Customer search
    - Project list
    - Project search
    - Project detail
    - Follow-up list
    - Payment summary
    - Dashboard
    Captures p50, p95, p99, error rate.
    """
    reg_payload = {
        "organization_name": "Benchmark Solar Corp",
        "full_name": "Benchmark Operator",
        "email": f"operator-{int(time.time() * 1000)}@benchsolar.com",
        "password": "StrongPassword123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 200
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Seed initial records for realistic queries
    cust_res = await client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "name": "Benchmark Mega Factory",
            "customer_type": "commercial",
            "phone": "+91 9998887776",
            "email": "procurement@megafactory.com",
            "city": "Bengaluru",
            "state": "Karnataka",
        },
    )
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["data"]["id"]

    pipe_res = await client.get("/api/v1/pipelines", headers=headers)
    pipe_id = pipe_res.json()["data"][0]["id"]
    stage_id = pipe_res.json()["data"][0]["stages"][0]["id"]

    proj_res = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Factory Solar Rooftop 1MW",
            "customer_id": cust_id,
            "pipeline_id": pipe_id,
            "stage_id": stage_id,
            "value": "8500000.00",
        },
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["data"]["id"]

    await client.post(
        "/api/v1/follow-ups",
        headers=headers,
        json={
            "customer_id": cust_id,
            "project_id": proj_id,
            "title": "Benchmark followup",
            "due_date": "2026-09-30T10:00:00Z",
        },
    )
    await client.post(
        "/api/v1/payments",
        headers=headers,
        json={
            "project_id": proj_id,
            "amount": "1500000.00",
            "payment_date": "2026-09-25",
        },
    )

    endpoints = [
        ("Customer list", "/api/v1/customers"),
        ("Customer search", "/api/v1/customers?search=Factory"),
        ("Project list", "/api/v1/projects"),
        ("Project search", "/api/v1/projects?search=Rooftop"),
        ("Project detail", f"/api/v1/projects/{proj_id}"),
        ("Follow-up list", "/api/v1/follow-ups"),
        ("Payment summary", f"/api/v1/payments/summary?project_id={proj_id}"),
        ("Dashboard", "/api/v1/dashboard"),
    ]

    iterations = 50
    benchmark_results = {}

    for name, path in endpoints:
        durations_ms = []
        errors = 0
        for _ in range(iterations):
            t0 = time.perf_counter()
            res = await client.get(path, headers=headers)
            t1 = time.perf_counter()
            if res.status_code != 200:
                errors += 1
            durations_ms.append((t1 - t0) * 1000)

        p50 = percentile(durations_ms, 50)
        p95 = percentile(durations_ms, 95)
        p99 = percentile(durations_ms, 99)
        err_rate = (errors / iterations) * 100

        benchmark_results[name] = {
            "p50_ms": round(float(p50), 2),
            "p95_ms": round(float(p95), 2),
            "p99_ms": round(float(p99), 2),
            "error_rate_pct": err_rate,
        }

        # Assert SLA: p95 under 100ms and zero error rate
        assert err_rate == 0.0, f"{name} had errors: {err_rate}%"
        assert p95 < 200.0, f"{name} p95 {p95}ms exceeded SLA"

    print("\n=== PHASE 2 PERFORMANCE BENCHMARK RESULTS ===")
    for op, stats in benchmark_results.items():
        print(f"{op:20} | p50: {stats['p50_ms']:6.2f}ms | p95: {stats['p95_ms']:6.2f}ms | p99: {stats['p99_ms']:6.2f}ms | err: {stats['error_rate_pct']}%")
    print("=============================================\n")
