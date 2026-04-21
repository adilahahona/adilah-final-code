"""
Feature engineering API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.security import verify_admin_key
from app.models.sql_models import FeatureSchemaVersion, FeatureVector
from app.domain.features.builder import FeatureBuilder
from app.domain.features.schema import FeatureSchemaManager
from pydantic import BaseModel


class FeatureVectorResponse(BaseModel):
    id: int
    organization_id: int
    period_id: int
    schema_version_id: int
    feature_count: int
    missing_count: int
    
    class Config:
        from_attributes = True


class FeatureSchemaResponse(BaseModel):
    id: int
    version_name: str
    feature_count: int
    scaling_policy: Optional[str] = None
    is_active: bool
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/api/v1/features", tags=["Features"])


@router.post("/build", response_model=FeatureVectorResponse)
async def build_features(
    org_id: int = Query(..., description="Organization ID"),
    period_id: int = Query(..., description="Reporting Period ID"),
    schema_version_id: Optional[int] = Query(None, description="Feature schema version ID"),
    overwrite: bool = Query(default=False, description="Overwrite existing feature vector"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    Build feature vector for an organization and period.
    
    - Extracts mapped indicator values
    - Applies imputation for missing values
    - Computes derived features
    - Creates missingness flags
    
    Requires admin API key.
    """
    builder = FeatureBuilder(db)
    
    try:
        feature_vector = builder.build_features(
            org_id=org_id,
            period_id=period_id,
            schema_version_id=schema_version_id,
            overwrite=overwrite
        )
        
        return FeatureVectorResponse.model_validate(feature_vector)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature building failed: {str(e)}"
        )


@router.get("/schema/latest", response_model=FeatureSchemaResponse)
async def get_latest_schema(
    db: Session = Depends(get_db)
):
    """
    Get the latest active feature schema.
    """
    manager = FeatureSchemaManager(db)
    schema = manager.get_latest_active_schema()
    
    return FeatureSchemaResponse(
        id=schema.id,
        version_name=schema.version_name,
        feature_count=len(schema.feature_list),
        scaling_policy=schema.scaling_policy,
        is_active=schema.is_active,
        description=schema.description
    )


@router.get("/schema/{schema_id}")
async def get_schema_details(
    schema_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed feature schema including feature list and transforms."""
    schema = db.query(FeatureSchemaVersion).filter(
        FeatureSchemaVersion.id == schema_id
    ).first()
    
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature schema {schema_id} not found"
        )
    
    return {
        "id": schema.id,
        "version_name": schema.version_name,
        "feature_list": schema.feature_list,
        "transforms": schema.transforms,
        "imputation_rules": schema.imputation_rules,
        "scaling_policy": schema.scaling_policy,
        "is_active": schema.is_active,
        "description": schema.description,
        "created_at": schema.created_at
    }
