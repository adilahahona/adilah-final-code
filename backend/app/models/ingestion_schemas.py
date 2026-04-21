"""
Pydantic schemas for ingestion endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class UploadMetadata(BaseModel):
    """Metadata for file upload."""
    source_name: str = Field(..., description="Name of the data source")
    source_type: str = Field(default="csv_upload", description="Type of data source")
    uploaded_by: Optional[str] = Field(None, description="User identifier")
    description: Optional[str] = None


class RejectionReason(BaseModel):
    """Reason for row rejection."""
    row_number: int
    field: Optional[str] = None
    error: str
    value: Optional[str] = None


class UploadSummary(BaseModel):
    """Summary of upload operation."""
    upload_batch_id: int
    rows_received: int
    rows_inserted: int
    rows_rejected: int
    rejection_reasons: List[RejectionReason] = []
    document_id: int
    checksum: str
    message: str


class RatingRow(BaseModel):
    """Single rating row."""
    org_name: str
    period_start: str
    period_end: str
    provider: str
    composite_score: Optional[float] = None
    risk_label: Optional[str] = None  # "high", "medium", "low"
    e_score: Optional[float] = None
    s_score: Optional[float] = None
    g_score: Optional[float] = None


class RatingsUploadSummary(BaseModel):
    """Summary of ratings upload."""
    rows_received: int
    rows_inserted: int
    rows_rejected: int
    rejection_reasons: List[RejectionReason] = []
    message: str
