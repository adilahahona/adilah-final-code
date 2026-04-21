"""
Explainability service - computes feature contributions for predictions.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import numpy as np

from app.models.sql_models import (
    PredictionDriver,
    FeatureVector,
    FeatureSchemaVersion
)


class ExplainabilityService:
    """Service for computing prediction explanations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def compute_linear_contributions(
        self,
        feature_vector_id: int,
        model: Any,
        scaler: Any,
        feature_names: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Compute feature contributions for linear models using coefficients.
        
        Args:
            feature_vector_id: FeatureVector ID
            model: Trained sklearn model
            scaler: Fitted StandardScaler
            feature_names: List of feature names in order
            top_k: Return top K contributors
            
        Returns:
            List of dicts with feature_name, contribution, rank, direction
        """
        # Load feature vector
        fv = self.db.query(FeatureVector).filter(
            FeatureVector.id == feature_vector_id
        ).first()
        
        if not fv:
            raise ValueError(f"Feature vector {feature_vector_id} not found")
        
        # Get features in correct order
        X = np.array([[fv.features.get(fname, 0.0) for fname in feature_names]])
        X_scaled = scaler.transform(X)
        
        # Get coefficients
        if hasattr(model, 'coef_'):
            coeffs = model.coef_
        else:
            # For tree models, use feature importances as proxy
            coeffs = model.feature_importances_
        
        # Compute contributions
        contributions = X_scaled[0] * coeffs
        
        # Create driver records
        drivers = []
        for i, fname in enumerate(feature_names):
            contrib = float(contributions[i])
            drivers.append({
                "feature_name": fname,
                "contribution": abs(contrib),
                "contribution_signed": contrib,
                "direction": "positive" if contrib > 0 else "negative"
            })
        
        # Sort by absolute contribution
        drivers.sort(key=lambda x: x["contribution"], reverse=True)
        
        # Add rank and limit to top_k
        for rank, driver in enumerate(drivers[:top_k], 1):
            driver["rank"] = rank
        
        return drivers[:top_k]
    
    def save_prediction_drivers(
        self,
        prediction_id: int,
        drivers: List[Dict[str, Any]]
    ) -> List[PredictionDriver]:
        """
        Save prediction drivers to database.
        
        Args:
            prediction_id: Prediction ID
            drivers: List of driver dictionaries
            
        Returns:
            List of created PredictionDriver records
        """
        driver_records = []
        
        for driver_data in drivers:
            driver = PredictionDriver(
                prediction_id=prediction_id,
                feature_name=driver_data["feature_name"],
                contribution=driver_data["contribution_signed"],
                rank=driver_data["rank"],
                direction=driver_data["direction"]
            )
            self.db.add(driver)
            driver_records.append(driver)
        
        self.db.commit()
        
        return driver_records
