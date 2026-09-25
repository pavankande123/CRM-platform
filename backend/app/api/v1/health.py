import time
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse


from app.core.config import settings
from app.db.session import check_database_health
from app.schemas.health import DependencyStatus, HealthCheckResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, summary="Liveness Probe")
async def liveness_probe() -> HealthCheckResponse:
    """
    Liveness probe returning 200 OK if the application process is running.
    Used by orchestrators (Kubernetes/Docker) to determine container health.
    """
    return HealthCheckResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness Probe")
async def readiness_probe():
    """
    Readiness probe validating dependencies (Database, Redis).
    Returns 200 OK when ready to accept traffic, or 503 SERVICE UNAVAILABLE if a critical dependency is down.
    """
    start = time.perf_counter()
    db_healthy = await check_database_health()
    db_latency = (time.perf_counter() - start) * 1000.0

    redis_start = time.perf_counter()
    from app.core.redis import redis_manager
    redis_healthy = await redis_manager.ping()
    redis_latency = (time.perf_counter() - redis_start) * 1000.0

    dependencies = {
        "database": DependencyStatus(
            status="healthy" if db_healthy else "unhealthy",
            latency_ms=round(db_latency, 2) if db_healthy else None,
            error=None if db_healthy else "Database connection ping failed",
        ),
        "redis": DependencyStatus(
            status="healthy" if redis_healthy else "degraded",
            latency_ms=round(redis_latency, 2) if redis_healthy else None,
            error=None if redis_healthy else "Redis unavailable; operating in memory fallback mode",
        ),
    }

    all_ready = db_healthy
    status_str = "ready" if all_ready else "not_ready"
    http_status = status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "status": status_str,
            "dependencies": {
                k: {"status": v.status, "latency_ms": v.latency_ms, "error": v.error}
                for k, v in dependencies.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/metrics", summary="Prometheus Metrics")
async def metrics_endpoint() -> Response:
    """Prometheus-compatible operational metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    from app.core.metrics import metrics_registry
    return PlainTextResponse(
        content=metrics_registry.generate_prometheus_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )

