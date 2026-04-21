"""
Pydantic schemas for mapping and coverage.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class RunMappingRequest(BaseModel):
    """Request to run mapping."""
    org_id: int
    period_id: int
    mapping_version: str = Field(default="1.0")
    overwrite: bool = Field(default=False)


class MappingStats(BaseModel):
    """Mapping operation statistics."""
    total_raw_values: int
    mapped_count: int
    unmapped_count: int
    errors: List[Dict[str, str]] = []


class PillarCoverage(BaseModel):
    """Coverage for a single pillar."""
    required_count: int
    present_count: int
    coverage_pct: float
    missing_count: int


class CoverageResponse(BaseModel):
    """Coverage statistics response."""
    organization_id: int
    period_id: int
    overall: Dict[str, Any]
    by_pillar: Dict[str, PillarCoverage]
    missing_indicators: Dict[str, List[str]]
