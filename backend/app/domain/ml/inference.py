"""
Inference service - generates predictions using trained models.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import numpy as np

from app.models.sql_models import (
    Prediction,
    FeatureVector,
    FeatureSchemaVersion,
    ModelVersion
)
from app.domain.ml.training import ModelTrainingService
from app.domain.ml.explainability import ExplainabilityService
from app.domain.ml.scoring import ScoringService
from app.core.security_governance import enforce_approved_model_only, verify_model_checksum


class InferenceService:
    """Service for generating predictions from trained models."""
    
    def __init__(self, db: Session):
        self.db = db
        self.training_service = ModelTrainingService(db)
        self.explainability_service = ExplainabilityService(db)
        self.scoring_service = ScoringService(db)
    
    def generate_prediction(
        self,
        feature_vector_id: int,
        model_version_id: Optional[int] = None,
        compute_subscores: bool = True,
        compute_drivers: bool = True,
        top_k_drivers: int = 10
    ) -> Prediction:
        """
        Generate a prediction for a feature vector.
        
        Args:
            feature_vector_id: FeatureVector ID to score
            model_version_id: Specific model to use (None = latest APPROVED)
            compute_subscores: Whether to compute deterministic E/S/G subscores
            compute_drivers: Whether to compute feature drivers
            top_k_drivers: Number of top drivers to save
            
        Returns:
            Created Prediction record
        """
        # Load feature vector
        fv = self.db.query(FeatureVector).filter(
            FeatureVector.id == feature_vector_id
        ).first()
        
        if not fv:
            raise ValueError(f"Feature vector {feature_vector_id} not found")
        
        # Get model
        if model_version_id:
            model_version = self.db.query(ModelVersion).filter(
                ModelVersion.id == model_version_id
            ).first()
            if not model_version:
                raise ValueError(f"Model version {model_version_id} not found")
        else:
            # Get latest APPROVED model
            model_version = self.db.query(ModelVersion).filter(
                ModelVersion.status == "APPROVED"
            ).order_by(ModelVersion.created_at.desc()).first()
            
            if not model_version:
                raise ValueError("No APPROVED models found")
        
        # GOVERNANCE: Enforce that only APPROVED models can be used
        enforce_approved_model_only(model_version)
        
        # GOVERNANCE: Verify model artifact checksum before loading
        if model_version.artifact_checksum:
            verify_model_checksum(model_version)
        
        # Load model artifacts
        artifacts = self.training_service.load_model(model_version.id)
        model = artifacts["model"]
        scaler = artifacts["scaler"]
        
        # Get feature schema
        schema = self.db.query(FeatureSchemaVersion).filter(
            FeatureSchemaVersion.id == fv.schema_version_id
        ).first()
        
        feature_names = schema.feature_list
        
        # Prepare features
        X = np.array([[fv.features.get(fname, 0.0) for fname in feature_names]])
        X_scaled = scaler.transform(X)
        
        # Generate prediction
        composite_score = float(model.predict(X_scaled)[0])
        
        # Compute subscores if requested
        e_score = None
        s_score = None
        g_score = None
        
        if compute_subscores:
            subscores = self.scoring_service.compute_subscores(
                fv.organization_id,
                fv.period_id
            )
            e_score = subscores.get("E")
            s_score = subscores.get("S")
            g_score = subscores.get("G")
        
        # Create prediction record
        prediction = Prediction(
            feature_vector_id=feature_vector_id,
            model_version_id=model_version.id,
            composite_score=composite_score,
            e_score=e_score,
            s_score=s_score,
            g_score=g_score,
            coverage=fv.extra_metadata.get("coverage", 0.0) if fv.extra_metadata else 0.0
        )
        
        self.db.add(prediction)
        self.db.flush()  # Get prediction ID
        
        # Compute drivers if requested
        if compute_drivers:
            drivers = self.explainability_service.compute_linear_contributions(
                feature_vector_id=feature_vector_id,
                model=model,
                scaler=scaler,
                feature_names=feature_names,
                top_k=top_k_drivers
            )
            
            self.explainability_service.save_prediction_drivers(
                prediction.id,
                drivers
            )
        
        self.db.commit()
        self.db.refresh(prediction)
        
        return prediction
    
    def batch_predict(
        self,
        organization_id: int,
        period_id: Optional[int] = None
    ) -> List[Prediction]:
        """
        Generate predictions for all feature vectors of an organization.
        
        Args:
            organization_id: Organization ID
            period_id: Optional period filter
            
        Returns:
            List of created Prediction records
        """
        # Get feature vectors
        query = self.db.query(FeatureVector).filter(
            FeatureVector.organization_id == organization_id
        )
        
        if period_id:
            query = query.filter(FeatureVector.period_id == period_id)
        
        feature_vectors = query.all()
        
        predictions = []
        for fv in feature_vectors:
            try:
                pred = self.generate_prediction(fv.id)
                predictions.append(pred)
            except Exception as e:
                # Log and continue
                print(f"Failed to generate prediction for FV {fv.id}: {e}")
        
        return predictions
