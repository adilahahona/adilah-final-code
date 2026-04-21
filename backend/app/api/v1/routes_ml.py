"""
API routes for ML pipeline - datasets, training, inference.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.security import verify_admin_key
from app.models.ml_schemas import (
    DatasetSnapshotCreate,
    DatasetSnapshotResponse,
    ModelTrainRequest,
    ModelVersionResponse,
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    SubscoreResponse,
    ScoringConfigResponse,
    ExternalRatingCreate,
    ExternalRatingResponse,
    PredictionDriverResponse
)
from app.models.sql_models import (
    DatasetSnapshot,
    ModelVersion,
    Prediction,
    ScoringConfigVersion,
    ExternalRating,
    PredictionDriver
)
from app.domain.ml.datasets import DatasetService
from app.domain.ml.training import ModelTrainingService
from app.domain.ml.inference import InferenceService
from app.domain.ml.scoring import ScoringService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ml", tags=["ml"])


# === Dataset Endpoints ===

@router.post("/datasets", response_model=DatasetSnapshotResponse)
async def create_dataset_snapshot(
    request: DatasetSnapshotCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key)
):
    """Create a dataset snapshot for model training."""
    logger.info(f"Creating dataset snapshot: {request.snapshot_name}")
    
    service = DatasetService(db)
    
    try:
        snapshot = service.create_snapshot(
            snapshot_name=request.snapshot_name,
            feature_schema_version_id=request.feature_schema_version_id,
            provider=request.provider,
            test_size=request.test_size,
            val_size=request.val_size,
            random_seed=request.random_seed
        )
        
        return DatasetSnapshotResponse.from_orm(snapshot)
    
    except Exception as e:
        logger.error(f"Failed to create dataset snapshot: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasets", response_model=List[DatasetSnapshotResponse])
async def list_datasets(
    db: Session = Depends(get_db)
):
    """List all dataset snapshots."""
    snapshots = db.query(DatasetSnapshot).order_by(
        DatasetSnapshot.created_at.desc()
    ).all()
    
    return [DatasetSnapshotResponse.from_orm(s) for s in snapshots]


@router.get("/datasets/{snapshot_id}", response_model=DatasetSnapshotResponse)
async def get_dataset(
    snapshot_id: int,
    db: Session = Depends(get_db)
):
    """Get dataset snapshot details."""
    snapshot = db.query(DatasetSnapshot).filter(
        DatasetSnapshot.id == snapshot_id
    ).first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Dataset snapshot not found")
    
    return DatasetSnapshotResponse.from_orm(snapshot)


# === Model Training Endpoints ===

@router.post("/models/train", response_model=ModelVersionResponse)
async def train_model(
    request: ModelTrainRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key)
):
    """Train a new model on a dataset snapshot."""
    logger.info(f"Training model: {request.model_name} with {request.algorithm}")
    
    service = ModelTrainingService(db)
    
    try:
        model_version = service.train_model(
            model_name=request.model_name,
            dataset_snapshot_id=request.dataset_snapshot_id,
            algorithm=request.algorithm,
            hyperparameters=request.hyperparameters,
            description=request.description
        )
        
        return model_version
    
    except Exception as e:
        logger.error(f"Failed to train model: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models", response_model=List[ModelVersionResponse])
async def list_models(
    status: str = None,
    db: Session = Depends(get_db)
):
    """List all model versions."""
    query = db.query(ModelVersion)
    
    if status:
        query = query.filter(ModelVersion.status == status)
    
    models = query.order_by(ModelVersion.created_at.desc()).all()
    
    return models


@router.get("/models/{model_id}", response_model=ModelVersionResponse)
async def get_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Get model version details."""
    model = db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model


@router.post("/models/{model_id}/approve", response_model=ModelVersionResponse)
async def approve_model(
    model_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key)
):
    """Approve a model for production inference."""
    logger.info(f"Approving model: {model_id}")
    
    service = ModelTrainingService(db)
    
    try:
        model = service.approve_model(model_id)
        return model
    except Exception as e:
        logger.error(f"Failed to approve model: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# === Inference Endpoints ===

@router.post("/predict", response_model=PredictionResponse)
async def generate_prediction(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """Generate a prediction for a feature vector."""
    logger.info(f"Generating prediction for FV: {request.feature_vector_id}")
    
    service = InferenceService(db)
    
    try:
        prediction = service.generate_prediction(
            feature_vector_id=request.feature_vector_id,
            model_version_id=request.model_version_id,
            compute_subscores=request.compute_subscores,
            compute_drivers=request.compute_drivers,
            top_k_drivers=request.top_k_drivers
        )
        
        # Load drivers
        drivers = db.query(PredictionDriver).filter(
            PredictionDriver.prediction_id == prediction.id
        ).order_by(PredictionDriver.rank).all()
        
        response = PredictionResponse.from_orm(prediction)
        response.drivers = [PredictionDriverResponse.from_orm(d) for d in drivers]
        
        return response
    
    except Exception as e:
        logger.error(f"Failed to generate prediction: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/predict/batch", response_model=List[PredictionResponse])
async def batch_predict(
    request: BatchPredictionRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key)
):
    """Generate predictions for all feature vectors of an organization."""
    logger.info(f"Batch predicting for org: {request.organization_id}")
    
    service = InferenceService(db)
    
    try:
        predictions = service.batch_predict(
            organization_id=request.organization_id,
            period_id=request.period_id
        )
        
        return [PredictionResponse.from_orm(p) for p in predictions]
    
    except Exception as e:
        logger.error(f"Failed to batch predict: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/predictions", response_model=List[PredictionResponse])
async def list_predictions(
    feature_vector_id: int = None,
    db: Session = Depends(get_db)
):
    """List predictions with optional filtering."""
    query = db.query(Prediction)
    
    if feature_vector_id:
        query = query.filter(Prediction.feature_vector_id == feature_vector_id)
    
    predictions = query.order_by(Prediction.created_at.desc()).limit(100).all()
    
    return [PredictionResponse.from_orm(p) for p in predictions]


# === Scoring Endpoints ===

@router.get("/scoring/config", response_model=ScoringConfigResponse)
async def get_active_scoring_config(
    db: Session = Depends(get_db)
):
    """Get active scoring configuration."""
    service = ScoringService(db)
    config = service.get_active_config()
    
    return config


@router.post("/scoring/subscores", response_model=SubscoreResponse)
async def compute_subscores(
    organization_id: int,
    period_id: int,
    db: Session = Depends(get_db)
):
    """Compute deterministic E/S/G subscores."""
    logger.info(f"Computing subscores for org {organization_id}, period {period_id}")
    
    service = ScoringService(db)
    
    try:
        subscores = service.compute_subscores(organization_id, period_id)
        
        config = service.get_active_config()
        
        return SubscoreResponse(
            organization_id=organization_id,
            period_id=period_id,
            e_score=subscores["E"],
            s_score=subscores["S"],
            g_score=subscores["G"],
            config_version_id=config.id
        )
    
    except Exception as e:
        logger.error(f"Failed to compute subscores: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# === External Ratings Endpoints ===

@router.post("/ratings", response_model=ExternalRatingResponse)
async def create_external_rating(
    request: ExternalRatingCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_admin_key)
):
    """Create an external rating record."""
    logger.info(f"Creating external rating for org {request.organization_id}")
    
    rating = ExternalRating(
        organization_id=request.organization_id,
        period_id=request.period_id,
        provider=request.provider,
        composite_score=request.composite_score,
        e_score=request.e_score,
        s_score=request.s_score,
        g_score=request.g_score,
        risk_rating=request.risk_rating,
        metadata=request.metadata
    )
    
    db.add(rating)
    db.commit()
    db.refresh(rating)
    
    return rating


@router.get("/ratings", response_model=List[ExternalRatingResponse])
async def list_external_ratings(
    organization_id: int = None,
    provider: str = None,
    db: Session = Depends(get_db)
):
    """List external ratings."""
    query = db.query(ExternalRating)
    
    if organization_id:
        query = query.filter(ExternalRating.organization_id == organization_id)
    
    if provider:
        query = query.filter(ExternalRating.provider == provider)
    
    ratings = query.order_by(ExternalRating.created_at.desc()).all()
    
    return ratings
