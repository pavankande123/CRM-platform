import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every incoming request has a unique Request ID.
    If the client provided X-Request-ID, it is reused; otherwise a new UUID is generated.
    The ID is propagated through contextvars and attached to the response header.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = f"req_{uuid.uuid4().hex[:16]}"

        request.state.request_id = req_id
        token = request_id_ctx.set(req_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)
