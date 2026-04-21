"""
Routes for ESG mapping and coverage.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import verify_admin_key
from app.models.mapping_coverage_schemas import (
    MappingStats,
    CoverageResponse
)
from app.domain.mapping.esg_mapping_service import ESGMappingService


router = APIRouter(prefix="/api/v1/mapping", tags=["Mapping"])


@router.post("/run", response_model=MappingStats)
async def run_mapping(
    org_id: int = Query(..., description="Organization ID"),
    period_id: int = Query(..., description="Reporting Period ID"),
    mapping_version: str = Query(default="1.0", description="Mapping version"),
    overwrite: bool = Query(default=False, description="Overwrite existing mapped values"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    Run mapping to convert raw indicator values to canonical mapped values.
    
    This endpoint:
    - Resolves raw indicator codes to canonical codes using aliases
    - Normalizes units to standard forms
    - Stores mapped values with full provenance
    
    Requires admin API key.
    """
    service = ESGMappingService(db)
    
    try:
        stats = service.run_mapping(
            org_id=org_id,
            period_id=period_id,
            mapping_version=mapping_version,
            overwrite=overwrite
        )
        
        return MappingStats(**stats)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mapping failed: {str(e)}"
        )


@router.get("/coverage", response_model=CoverageResponse)
async def get_coverage(
    org_id: int = Query(..., description="Organization ID"),
    period_id: int = Query(..., description="Reporting Period ID"),
    db: Session = Depends(get_db)
):
    """
    Get indicator coverage for an organization and period.
    
    Returns:
    - Overall coverage percentage
    - Coverage by pillar (E, S, G)
    - List of missing required indicators
    """
    service = ESGMappingService(db)
    
    try:
        coverage = service.compute_coverage(
            org_id=org_id,
            period_id=period_id
        )
        
        return CoverageResponse(**coverage)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coverage computation failed: {str(e)}"
        )
