"""Standardized API response schemas."""
from typing import Any

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Minimal response envelope."""

    status: str = Field(default="ok", description="Overall status of the response.")
    data: dict[str, Any] | None = Field(default=None, description="Response payload.")


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str = Field(description="Machine-readable error code.")
    message: str = Field(description="Human-readable error description.")


class ErrorResponse(BaseModel):
    """Standard error response contract."""

    status: str = Field(default="error", description="Always 'error' for error responses.")
    error: ErrorDetail = Field(description="Error detail object.")
    request_id: str | None = Field(default=None, description="Request tracking ID.")


# Re-export
__all__ = ["BaseResponse", "ErrorResponse", "ErrorDetail"]
