"""
Common Pydantic models for API responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")


class MetaResponse(BaseModel):
    """Service metadata response."""
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    git_sha: str = Field(..., description="Git commit SHA")
    environment: str = Field(..., description="Environment")


class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field name if validation error")


class ErrorResponse(BaseModel):
    """Standard error response envelope."""
    error: ErrorDetail = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = Field(True, description="Success flag")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
