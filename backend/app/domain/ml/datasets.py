"""
Dataset assembly service - creates training datasets from feature vectors and ratings.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.model_selection import train_test_split

from app.models.sql_models import (
    FeatureVector,
    ExternalRating,
    DatasetSnapshot,
    FeatureSchemaVersion
)


class DatasetService:
    """Service for assembling and managing training datasets."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_snapshot(
        self,
        snapshot_name: str,
        feature_schema_version_id: int,
        provider: str = None,
        test_size: float = 0.2,
        val_size: float = 0.1,
        random_seed: int = 42
    ) -> DatasetSnapshot:
        """
        Create a dataset snapshot from feature vectors with ratings.
        
        Args:
            snapshot_name: Name for this snapshot
            feature_schema_version_id: Feature schema to use
            provider: Rating provider to use (None = any)
            test_size: Proportion for test set
            val_size: Proportion of remaining for validation
            random_seed: Random seed for reproducibility
            
        Returns:
            Created DatasetSnapshot
        """
        # Get feature vectors with this schema
        fv_query = self.db.query(FeatureVector).filter(
            FeatureVector.schema_version_id == feature_schema_version_id
        )
        
        # Join with ratings
        fv_with_ratings = []
        for fv in fv_query.all():
            rating_query = self.db.query(ExternalRating).filter(
                ExternalRating.organization_id == fv.organization_id,
                ExternalRating.period_id == fv.period_id
            )
            
            if provider:
                rating_query = rating_query.filter(ExternalRating.provider == provider)
            
            rating = rating_query.first()
            if rating and rating.composite_score is not None:
                fv_with_ratings.append(fv.id)
        
        if not fv_with_ratings:
            raise ValueError("No feature vectors with ratings found")
        
        # Split into train/val/test
        all_ids = np.array(fv_with_ratings)
        
        train_val_ids, test_ids = train_test_split(
            all_ids,
            test_size=test_size,
            random_state=random_seed
        )
        
        train_ids, val_ids = train_test_split(
            train_val_ids,
            test_size=val_size / (1 - test_size),
            random_state=random_seed
        )
        
        # Create snapshot
        snapshot = DatasetSnapshot(
            snapshot_name=snapshot_name,
            feature_schema_version_id=feature_schema_version_id,
            row_count=len(all_ids),
            feature_vector_ids=all_ids.tolist(),
            train_ids=train_ids.tolist(),
            val_ids=val_ids.tolist(),
            test_ids=test_ids.tolist(),
            target_provider=provider,
            metadata={
                "test_size": test_size,
                "val_size": val_size,
                "random_seed": random_seed
            }
        )
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        return snapshot
    
    def load_dataset(
        self,
        snapshot_id: int,
        split: str = "train"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load features and targets for a specific split.
        
        Args:
            snapshot_id: Dataset snapshot ID
            split: 'train', 'val', or 'test'
            
        Returns:
            Tuple of (X, y) as numpy arrays
        """
        snapshot = self.db.query(DatasetSnapshot).filter(
            DatasetSnapshot.id == snapshot_id
        ).first()
        
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # Get IDs for this split
        if split == "train":
            ids = snapshot.train_ids
        elif split == "val":
            ids = snapshot.val_ids
        elif split == "test":
            ids = snapshot.test_ids
        else:
            raise ValueError(f"Invalid split: {split}")
        
        if not ids:
            raise ValueError(f"No data for split: {split}")
        
        # Load feature vectors
        feature_vectors = self.db.query(FeatureVector).filter(
            FeatureVector.id.in_(ids)
        ).all()
        
        # Get schema to ensure correct feature ordering
        schema = self.db.query(FeatureSchemaVersion).filter(
            FeatureSchemaVersion.id == snapshot.feature_schema_version_id
        ).first()
        
        feature_names = schema.feature_list
        
        # Build X matrix
        X = []
        y = []
        
        for fv in feature_vectors:
            # Get features in correct order
            feature_row = [fv.features.get(fname, 0.0) for fname in feature_names]
            X.append(feature_row)
            
            # Get target
            rating = self.db.query(ExternalRating).filter(
                ExternalRating.organization_id == fv.organization_id,
                ExternalRating.period_id == fv.period_id
            ).first()
            
            if rating:
                y.append(rating.composite_score)
        
        return np.array(X), np.array(y)
