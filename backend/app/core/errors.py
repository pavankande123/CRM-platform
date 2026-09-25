from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception with error code and status code."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="RESOURCE_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(AppException):
    def __init__(self, message: str = "Access forbidden", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class TenantIsolationError(ForbiddenError):
    def __init__(self, message: str = "Cross-tenant access prohibited", details: Optional[Any] = None):
        super().__init__(message=message, details=details)
        self.code = "TENANT_ACCESS_DENIED"


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


def format_error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[Any] = None,
) -> JSONResponse:
    """Format standard RFC-compliant error payload."""
    payload = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id or "unknown",
            "details": details,
        }
    }
    headers = {}
    if request_id:
        headers["X-Request-ID"] = request_id
    return JSONResponse(status_code=status_code, content=payload, headers=headers)
