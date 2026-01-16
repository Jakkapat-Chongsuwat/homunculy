"""Base HTTP response models."""

from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response shape."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(description="Indicates if the request was successful")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp (UTC)"
    )
    request_id: str = Field(default="", description="Request tracking ID for debugging and tracing")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional response metadata"
    )


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str = Field(description="Machine-readable error code (e.g., VALIDATION_ERROR, NOT_FOUND)")
    message: str = Field(description="Human-readable error message")
    field: Optional[str] = Field(
        default=None, description="Field that caused the error (for validation errors)"
    )
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error context")


class ErrorResponse(BaseResponse):
    """Error response envelope."""

    success: bool = Field(default=False, description="Always False for error responses")
    error: ErrorDetail = Field(description="Detailed error information")


class SuccessResponse(BaseResponse, Generic[T]):
    """Success response envelope."""

    success: bool = Field(default=True, description="Always True for success responses")
    data: T = Field(description="Response payload")


class PaginationMetadata(BaseModel):
    """Pagination metadata."""

    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_previous: bool = Field(description="Whether there are previous pages")


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response envelope."""

    success: bool = Field(default=True, description="Always True for success responses")
    data: list[T] = Field(description="List of items for current page")
    pagination: PaginationMetadata = Field(description="Pagination metadata")
