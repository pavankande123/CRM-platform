from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.errors import format_error_response

DEFAULT_MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB default limit


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Guards against denial-of-service via oversized request payloads.
    Enforces 10MB limit on general API requests and 25MB on file upload endpoints.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                max_bytes = (
                    settings.STORAGE_MAX_FILE_SIZE_BYTES
                    if request.url.path.endswith("/documents/upload")
                    else DEFAULT_MAX_BODY_BYTES
                )
                if length > max_bytes:
                    req_id = getattr(request.state, "request_id", None) or "req_oversized"
                    return format_error_response(
                        status_code=413,
                        code="PAYLOAD_TOO_LARGE",
                        message=f"Request payload exceeds allowed limit of {max_bytes // (1024 * 1024)} MB.",
                        request_id=req_id,
                    )
            except ValueError:
                pass

        return await call_next(request)
