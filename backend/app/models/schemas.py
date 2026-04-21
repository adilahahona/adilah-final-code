"""
Pydantic schemas for Organization and ReportingPeriod.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(..., min_length=1, max_length=255)
    external_id: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    metadata: Optional[dict] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    external_id: Optional[str] = Field(None, max_length=100)
    sector: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    metadata: Optional[dict] = None


class Organization(OrganizationBase):
    """Organization response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReportingPeriodBase(BaseModel):
    """Base reporting period schema."""
    organization_id: int
    period_start: datetime
    period_end: datetime
    period_type: str = Field(default="annual", max_length=50)


class ReportingPeriodCreate(ReportingPeriodBase):
    """Schema for creating reporting period."""
    pass


class ReportingPeriod(ReportingPeriodBase):
    """Reporting period response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
