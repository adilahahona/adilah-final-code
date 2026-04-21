"""
Catalog and framework mapping API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.core.security import verify_admin_key
from app.models.sql_models import IndicatorCatalogItem, FrameworkMapping
from app.models.mapping_schemas import (
    IndicatorCatalogItemSchema,
    FrameworkItemSchema,
    CreateMappingRequest,
    SeedCatalogRequest,
    SeedFrameworkRequest
)
from app.models.common import SuccessResponse
from app.domain.mapping.service import MappingService


router = APIRouter(prefix="/api/v1", tags=["Catalog & Frameworks"])


@router.get("/catalog/indicators", response_model=List[IndicatorCatalogItemSchema])
async def list_catalog_indicators(
    pillar: Optional[str] = Query(None, description="Filter by pillar: E, S, or G"),
    is_required: Optional[bool] = Query(None, description="Filter by required status"),
    db: Session = Depends(get_db)
):
    """
    List all indicators in the catalog with optional filtering.
    
    - **pillar**: Filter by E, S, or G
    - **is_required**: Filter by required status
    """
    query = db.query(IndicatorCatalogItem)
    
    if pillar:
        query = query.filter(IndicatorCatalogItem.pillar == pillar.upper())
    
    if is_required is not None:
        query = query.filter(IndicatorCatalogItem.is_required == is_required)
    
    indicators = query.all()
    return indicators


@router.get("/frameworks/{framework_name}/items", response_model=List[FrameworkItemSchema])
async def list_framework_items(
    framework_name: str,
    db: Session = Depends(get_db)
):
    """
    List all items for a specific framework.
    
    - **framework_name**: GRI, SASB, or TCFD
    """
    items = (
        db.query(FrameworkMapping)
        .filter(
            FrameworkMapping.framework_name == framework_name.upper(),
            FrameworkMapping.is_active == True
        )
        .all()
    )
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No items found for framework: {framework_name}"
        )
    
    return items


@router.post("/mappings", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_mapping(
    mapping_data: CreateMappingRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    Create a new framework mapping.
    
    Requires admin API key.
    """
    service = MappingService(db)
    
    try:
        mapping = service.create_mapping(
            framework_name=mapping_data.framework_name,
            framework_item_id=mapping_data.framework_item_id,
            framework_item_name=mapping_data.framework_item_name,
            indicator_code=mapping_data.indicator_code,
            relevance_weight=mapping_data.relevance_weight,
            mapping_rationale=mapping_data.mapping_rationale
        )
        
        return SuccessResponse(
            success=True,
            message=f"Mapping created for {mapping_data.framework_item_id}",
            data={"mapping_id": mapping.id}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/admin/seed-catalog", response_model=SuccessResponse)
async def seed_catalog(
    request: SeedCatalogRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    Seed the indicator catalog with predefined indicators.
    
    Requires admin API key.
    """
    service = MappingService(db)
    count = service.seed_catalog(overwrite=request.overwrite)
    
    return SuccessResponse(
        success=True,
        message=f"Seeded {count} indicators",
        data={"count": count}
    )


@router.post("/admin/seed-framework", response_model=SuccessResponse)
async def seed_framework(
    request: SeedFrameworkRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    Seed framework mappings for a specific framework.
    
    Requires admin API key.
    """
    service = MappingService(db)
    
    try:
        count = service.seed_framework_mappings(
            framework_name=request.framework_name.upper(),
            overwrite=request.overwrite
        )
        
        return SuccessResponse(
            success=True,
            message=f"Seeded {count} mappings for {request.framework_name}",
            data={"count": count, "framework": request.framework_name}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/admin/seed-all-frameworks", response_model=SuccessResponse)
async def seed_all_frameworks(
    overwrite: bool = False,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    Seed all framework mappings (GRI, SASB, TCFD).
    
    Requires admin API key.
    """
    service = MappingService(db)
    results = service.seed_all_frameworks(overwrite=overwrite)
    
    total = sum(results.values())
    
    return SuccessResponse(
        success=True,
        message=f"Seeded {total} total framework mappings",
        data=results
    )
