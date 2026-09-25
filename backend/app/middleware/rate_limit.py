import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.errors import format_error_response
from app.core.redis import redis_manager

logger = logging.getLogger("enermax.ratelimit")

EXEMPT_PATHS = {
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production-grade, multi-tier rate limiting middleware:
    - Strict IP throttling on authentication endpoints (/auth/login, /auth/register)
    - General tenant/IP throttling on operational API endpoints
    - RFC-standard 429 responses with Retry-After and X-RateLimit headers
    - Multi-instance safe via distributed Redis sliding window with automatic memory fallback
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path

        # Exempt infrastructure probes and documentation
        if path in EXEMPT_PATHS or path.startswith("/static"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"

        # Tier 1: Authentication / Sensitive Endpoints (Strict 10 req/min per IP)
        if path in ("/api/v1/auth/login", "/api/v1/auth/register") and request.method == "POST":
            key = redis_manager.ratelimit_key("auth_ip", client_ip)
            limit = settings.RATE_LIMIT_LOGIN_PER_MINUTE
            allowed, count, retry_after = await redis_manager.check_rate_limit(
                key=key,
                limit=limit,
                window_seconds=60,
            )

            if not allowed:
                logger.warning(
                    f"Authentication rate limit exceeded for IP {client_ip} on {path} (count: {count}/{limit})",
                    extra={"client_ip": client_ip, "path": path, "event": "RATE_LIMIT_EXCEEDED"},
                )
                from app.core.metrics import metrics_registry
                metrics_registry.record_rate_limit_hit(endpoint=path)

                req_id = getattr(request.state, "request_id", None) or "req_ratelimit"
                resp = format_error_response(
                    status_code=429,
                    code="RATE_LIMIT_EXCEEDED",
                    message="Too many login attempts. Please try again later.",
                    request_id=req_id,
                    details={"retry_after_seconds": retry_after},
                )
                resp.headers["Retry-After"] = str(retry_after)
                resp.headers["X-RateLimit-Limit"] = str(limit)
                resp.headers["X-RateLimit-Remaining"] = "0"
                resp.headers["X-RateLimit-Reset"] = str(retry_after)
                return resp

        # Tier 2: General API Endpoints (300 req/min per client)
        elif path.startswith(settings.API_V1_PREFIX):
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Scoped to token identifier
                identifier = auth_header[-16:]
                scope = "token"
            else:
                identifier = client_ip
                scope = "ip"

            key = redis_manager.ratelimit_key(scope, identifier)
            limit = settings.RATE_LIMIT_API_PER_MINUTE
            allowed, count, retry_after = await redis_manager.check_rate_limit(
                key=key,
                limit=limit,
                window_seconds=60,
            )

            if not allowed:
                logger.warning(
                    f"API rate limit exceeded for {scope}:{identifier} on {path} (count: {count}/{limit})",
                    extra={"identifier": identifier, "path": path, "event": "RATE_LIMIT_EXCEEDED"},
                )
                from app.core.metrics import metrics_registry
                metrics_registry.record_rate_limit_hit(endpoint=path)

                req_id = getattr(request.state, "request_id", None) or "req_ratelimit"
                resp = format_error_response(
                    status_code=429,
                    code="RATE_LIMIT_EXCEEDED",
                    message="API request rate limit exceeded. Please throttle your requests.",
                    request_id=req_id,
                    details={"retry_after_seconds": retry_after},
                )
                resp.headers["Retry-After"] = str(retry_after)
                resp.headers["X-RateLimit-Limit"] = str(limit)
                resp.headers["X-RateLimit-Remaining"] = "0"
                resp.headers["X-RateLimit-Reset"] = str(retry_after)
                return resp

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
            return response

        return await call_next(request)
