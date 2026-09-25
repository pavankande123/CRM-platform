import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class LatencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that records execution latency and attaches an X-Response-Time header.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_sec = time.perf_counter() - start_time
        duration_ms = duration_sec * 1000.0
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        request.state.duration_ms = duration_ms

        # Record metrics
        from app.core.metrics import metrics_registry
        metrics_registry.record_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration_sec=duration_sec,
        )
        return response

