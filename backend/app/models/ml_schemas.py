"""
Pydantic schemas for ML API endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# Dataset schemas
class DatasetSnapshotCreate(BaseModel):
    snapshot_name: str
    feature_schema_version_id: int
    provider: Optional[str] = None
    test_size: float = Field(default=0.2, ge=0.0, le=1.0)
    val_size: float = Field(default=0.1, ge=0.0, le=1.0)
    random_seed: int = 42


class DatasetSnapshotResponse(BaseModel):
    id: int
    snapshot_name: str
    feature_schema_version_id: int
    row_count: int
    train_count: int
    val_count: int
    test_count: int
    target_provider: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, snapshot):
        return cls(
            id=snapshot.id,
            snapshot_name=snapshot.snapshot_name,
            feature_schema_version_id=snapshot.feature_schema_version_id,
            row_count=snapshot.row_count,
            train_count=len(snapshot.train_ids),
            val_count=len(snapshot.val_ids),
            test_count=len(snapshot.test_ids),
            target_provider=snapshot.target_provider,
            created_at=snapshot.created_at
        )


# Model training schemas
class ModelTrainRequest(BaseModel):
    model_name: str
    dataset_snapshot_id: int
    algorithm: str = Field(
        description="Algorithm: linear_regression, ridge, lasso, random_forest, gradient_boosting"
    )
    hyperparameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ModelVersionResponse(BaseModel):
    id: int
    model_name: str
    algorithm: str
    hyperparameters: Dict[str, Any]
    dataset_snapshot_id: int
    train_metrics: Dict[str, float]
    val_metrics: Dict[str, float]
    status: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Prediction schemas
class PredictionRequest(BaseModel):
    feature_vector_id: int
    model_version_id: Optional[int] = None
    compute_subscores: bool = True
    compute_drivers: bool = True
    top_k_drivers: int = 10


class BatchPredictionRequest(BaseModel):
    organization_id: int
    period_id: Optional[int] = None


class PredictionDriverResponse(BaseModel):
    feature_name: str
    contribution: float
    rank: int
    direction: str
    
    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    id: int
    feature_vector_id: int
    model_version_id: int
    composite_score: float
    e_score: Optional[float]
    s_score: Optional[float]
    g_score: Optional[float]
    coverage: float
    drivers: List[PredictionDriverResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


# Scoring config schemas
class ScoringConfigResponse(BaseModel):
    id: int
    config_name: str
    pillar_weights: Dict[str, float]
    normalization_method: str
    is_active: bool
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscoreResponse(BaseModel):
    organization_id: int
    period_id: int
    e_score: float
    s_score: float
    g_score: float
    config_version_id: int


# External rating schemas
class ExternalRatingCreate(BaseModel):
    organization_id: int
    period_id: int
    provider: str
    composite_score: Optional[float] = None
    e_score: Optional[float] = None
    s_score: Optional[float] = None
    g_score: Optional[float] = None
    risk_rating: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ExternalRatingResponse(BaseModel):
    id: int
    organization_id: int
    period_id: int
    provider: str
    composite_score: Optional[float]
    e_score: Optional[float]
    s_score: Optional[float]
    g_score: Optional[float]
    risk_rating: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
