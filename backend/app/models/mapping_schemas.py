"""
Pydantic schemas for catalog and mapping endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class IndicatorCatalogItemSchema(BaseModel):
    """Indicator catalog item response."""
    id: int
    indicator_code: str
    name: str
    description: Optional[str] = None
    pillar: str
    unit: Optional[str] = None
    data_type: str
    is_required: bool
    aliases: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FrameworkItemSchema(BaseModel):
    """Framework item with mapping."""
    framework_item_id: str
    framework_item_name: Optional[str] = None
    indicator_code: str
    relevance_weight: float
    mapping_rationale: Optional[str] = None
    
    class Config:
        from_attributes = True


class CreateMappingRequest(BaseModel):
    """Request to create a new framework mapping."""
    framework_name: str = Field(..., max_length=100)
    framework_item_id: str = Field(..., max_length=255)
    framework_item_name: Optional[str] = Field(None, max_length=500)
    indicator_code: str = Field(..., max_length=255)
    relevance_weight: float = Field(default=1.0, ge=0.0, le=1.0)
    mapping_rationale: Optional[str] = None


class SeedCatalogRequest(BaseModel):
    """Request to seed indicator catalog."""
    overwrite: bool = Field(default=False)


class SeedFrameworkRequest(BaseModel):
    """Request to seed framework mappings."""
    framework_name: str
    overwrite: bool = Field(default=False)
