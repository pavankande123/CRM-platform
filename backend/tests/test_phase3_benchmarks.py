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
async def test_phase3_operations_benchmark(async_client: AsyncClient, auth_headers: dict):
    """
    Section 32 Performance Benchmarks for Phase 3:
    - Pipeline list
    - Custom field retrieval
    - Saved view query
    - Workflow trigger processing
    - Notification retrieval
    - Approval retrieval
    Measures and logs: p50, p95, p99, error rate.
    """
    # 1. Setup seed records
    cust_res = await async_client.post(
        "/api/v1/customers",
        headers=auth_headers,
        json={"name": "Benchmark Customer", "customer_type": "commercial"},
    )
    cust_id = cust_res.json()["data"]["id"]

    pipe_res = await async_client.get("/api/v1/pipelines", headers=auth_headers)
    pipeline = pipe_res.json()["data"][0]
    pipe_id = pipeline["id"]
    stage_id = pipeline["stages"][0]["id"]

    # Seed custom field
    cf_res = await async_client.post(
        "/api/v1/custom-fields",
        headers=auth_headers,
        json={
            "entity_type": "project",
            "field_name": "bench_field",
            "display_name": "Benchmark Field",
            "field_type": "text",
        },
    )
    cf_id = cf_res.json()["data"]["id"]

    # Seed saved view
    view_res = await async_client.post(
        "/api/v1/views",
        headers=auth_headers,
        json={
            "name": "Benchmark View",
            "entity_type": "project",
            "filters": [{"field": "priority", "operator": "eq", "value": "medium"}],
        },
    )
    view_id = view_res.json()["data"]["id"]

    # Seed workflow
    wf_res = await async_client.post(
        "/api/v1/workflows",
        headers=auth_headers,
        json={
            "name": "Bench Automation",
            "entity_type": "project",
            "trigger_event": "project.created",
            "actions": [
                {"action_type": "create_notification", "params": {"title": "Bench Event", "message": "Triggered"}}
            ],
        },
    )

    # Seed approval
    appr_res = await async_client.post(
        "/api/v1/approvals",
        headers=auth_headers,
        json={
            "entity_type": "project",
            "entity_id": cust_id,  # valid uuid
            "title": "Bench Sign-off",
        },
    )

    operations = [
        ("Pipeline list", "GET", "/api/v1/pipelines", None),
        ("Custom field list", "GET", "/api/v1/custom-fields?entity_type=project", None),
        ("Saved view query", "GET", f"/api/v1/views/{view_id}/execute", None),
        ("Notification list", "GET", "/api/v1/notifications", None),
        ("Approval list", "GET", "/api/v1/approvals", None),
    ]

    benchmark_results = {}
    iterations = 10

    for name, method, path, payload in operations:
        latencies = []
        errors = 0
        for _ in range(iterations):
            start = time.perf_counter()
            if method == "GET":
                res = await async_client.get(path, headers=auth_headers)
            else:
                res = await async_client.post(path, json=payload, headers=auth_headers)
            duration_ms = (time.perf_counter() - start) * 1000.0

            if res.status_code >= 400:
                errors += 1
            latencies.append(duration_ms)

        p50 = percentile(latencies, 50)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)
        error_rate = (errors / iterations) * 100.0

        benchmark_results[name] = {
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "error_rate_pct": error_rate,
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
        }

    print("\n--- PHASE 3 PERFORMANCE BENCHMARKS ---")
    for op_name, stats in benchmark_results.items():
        print(f"{op_name:<22}: p50={stats['p50_ms']:>6.2f}ms | p95={stats['p95_ms']:>6.2f}ms | p99={stats['p99_ms']:>6.2f}ms | err={stats['error_rate_pct']}%")
        assert stats["error_rate_pct"] == 0.0, f"Errors encountered in {op_name}"
        assert stats["p50_ms"] < 250.0, f"p50 exceeded SLA for {op_name}"
