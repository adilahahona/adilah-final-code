"""
Model training service - trains regression/classification models.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime
import joblib
from pathlib import Path

from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

from app.models.sql_models import ModelVersion, DatasetSnapshot
from app.domain.ml.datasets import DatasetService
from app.core.config import settings
from app.core.security_governance import calculate_file_checksum


class ModelTrainingService:
    """Service for training and persisting ML models."""
    
    SUPPORTED_ALGORITHMS = {
        "linear_regression": LinearRegression,
        "ridge": Ridge,
        "lasso": Lasso,
        "random_forest": RandomForestRegressor,
        "gradient_boosting": GradientBoostingRegressor
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.dataset_service = DatasetService(db)
        self.artifacts_path = Path(settings.ARTIFACTS_DIR) / "models"
        self.artifacts_path.mkdir(parents=True, exist_ok=True)
    
    def train_model(
        self,
        model_name: str,
        dataset_snapshot_id: int,
        algorithm: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> ModelVersion:
        """
        Train a regression model on a dataset snapshot.
        
        Args:
            model_name: Name for this model
            dataset_snapshot_id: Dataset to train on
            algorithm: Algorithm name (linear_regression, ridge, etc.)
            hyperparameters: Algorithm hyperparameters
            description: Optional description
            
        Returns:
            Created ModelVersion record
        """
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        hyperparameters = hyperparameters or {}
        
        # Load dataset
        X_train, y_train = self.dataset_service.load_dataset(
            dataset_snapshot_id, "train"
        )
        X_val, y_val = self.dataset_service.load_dataset(
            dataset_snapshot_id, "val"
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        # Train model
        model_class = self.SUPPORTED_ALGORITHMS[algorithm]
        model = model_class(**hyperparameters)
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_train_pred = model.predict(X_train_scaled)
        y_val_pred = model.predict(X_val_scaled)
        
        train_metrics = {
            "mse": float(mean_squared_error(y_train, y_train_pred)),
            "mae": float(mean_absolute_error(y_train, y_train_pred)),
            "r2": float(r2_score(y_train, y_train_pred))
        }
        
        val_metrics = {
            "mse": float(mean_squared_error(y_val, y_val_pred)),
            "mae": float(mean_absolute_error(y_val, y_val_pred)),
            "r2": float(r2_score(y_val, y_val_pred))
        }
        
        # Save artifacts
        artifact_name = f"{model_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.joblib"
        artifact_path = self.artifacts_path / artifact_name
        
        artifacts = {
            "model": model,
            "scaler": scaler,
            "algorithm": algorithm,
            "hyperparameters": hyperparameters
        }
        
        joblib.dump(artifacts, artifact_path)
        
        # GOVERNANCE: Calculate checksum for artifact
        artifact_checksum = calculate_file_checksum(artifact_path)
        
        # Create model version record
        model_version = ModelVersion(
            model_name=model_name,
            algorithm=algorithm,
            hyperparameters=hyperparameters,
            dataset_snapshot_id=dataset_snapshot_id,
            train_metrics=train_metrics,
            val_metrics=val_metrics,
            artifact_path=str(artifact_path),
            artifact_checksum=artifact_checksum,  # Store checksum
            status="TRAINED",
            description=description
        )
        
        self.db.add(model_version)
        self.db.commit()
        self.db.refresh(model_version)
        
        return model_version
    
    def load_model(self, model_version_id: int) -> Dict[str, Any]:
        """
        Load a trained model and its artifacts.
        
        Args:
            model_version_id: ModelVersion ID
            
        Returns:
            Dictionary with model, scaler, metadata
        """
        model_version = self.db.query(ModelVersion).filter(
            ModelVersion.id == model_version_id
        ).first()
        
        if not model_version:
            raise ValueError(f"Model version {model_version_id} not found")
        
        if not os.path.exists(model_version.artifact_path):
            raise FileNotFoundError(f"Model artifacts not found: {model_version.artifact_path}")
        
        artifacts = joblib.load(model_version.artifact_path)
        
        return {
            "model": artifacts["model"],
            "scaler": artifacts["scaler"],
            "algorithm": artifacts["algorithm"],
            "hyperparameters": artifacts["hyperparameters"],
            "model_version": model_version
        }
    
    def approve_model(self, model_version_id: int) -> ModelVersion:
        """Mark a model as APPROVED for production inference."""
        model_version = self.db.query(ModelVersion).filter(
            ModelVersion.id == model_version_id
        ).first()
        
        if not model_version:
            raise ValueError(f"Model version {model_version_id} not found")
        
        model_version.status = "APPROVED"
        self.db.commit()
        self.db.refresh(model_version)
        
        return model_version
