import uuid
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with ORM mode enabled by default."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class StandardResponse(BaseSchema, Generic[T]):
    """Standard success API response envelope."""
    success: bool = True
    data: T
    message: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Standard paginated response envelope."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorDetail(BaseModel):
    """Error representation for RFC-compliant error payloads."""
    code: str
    message: str
    request_id: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Top-level error response model."""
    error: ErrorDetail
