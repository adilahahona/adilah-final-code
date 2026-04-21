"""
Feature builder - converts mapped indicators to feature vectors.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.models.sql_models import (
    MappedIndicatorValue,
    FeatureSchemaVersion,
    FeatureVector,
    Organization,
    ReportingPeriod
)
from app.domain.features.schema import FeatureSchemaManager
from app.domain.audit.service import AuditService

logger = logging.getLogger(__name__)


class FeatureBuilder:
    """
    Builds feature vectors from mapped indicator values.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.schema_manager = FeatureSchemaManager(db)
        self.audit_service = AuditService(db)
    
    def build_features(
        self,
        org_id: int,
        period_id: int,
        schema_version_id: Optional[int] = None,
        overwrite: bool = False
    ) -> FeatureVector:
        """
        Build feature vector for organization and period.
        
        Args:
            org_id: Organization ID
            period_id: Reporting period ID
            schema_version_id: Feature schema version ID (uses latest if None)
            overwrite: If True, recreate existing feature vector
            
        Returns:
            Created or updated FeatureVector
        """
        # Verify org and period exist
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise ValueError(f"Organization {org_id} not found")
        
        period = self.db.query(ReportingPeriod).filter(ReportingPeriod.id == period_id).first()
        if not period:
            raise ValueError(f"Reporting period {period_id} not found")
        
        # Get schema
        if schema_version_id:
            schema = self.db.query(FeatureSchemaVersion).filter(
                FeatureSchemaVersion.id == schema_version_id
            ).first()
            if not schema:
                raise ValueError(f"Feature schema {schema_version_id} not found")
        else:
            schema = self.schema_manager.get_latest_active_schema()
        
        # Check if vector already exists
        existing = (
            self.db.query(FeatureVector)
            .filter(
                FeatureVector.organization_id == org_id,
                FeatureVector.period_id == period_id,
                FeatureVector.schema_version_id == schema.id
            )
            .first()
        )
        
        if existing and not overwrite:
            return existing
        
        if existing and overwrite:
            self.db.delete(existing)
            self.db.commit()
        
        # Get mapped values
        mapped_values = (
            self.db.query(MappedIndicatorValue)
            .filter(
                MappedIndicatorValue.organization_id == org_id,
                MappedIndicatorValue.period_id == period_id
            )
            .all()
        )
        
        # Build value dictionary
        value_dict = {mv.indicator_code: mv.numeric_value for mv in mapped_values}
        
        # Build features dictionary
        features = {}
        missing_count = 0
        
        for feature_name in schema.feature_list:
            # Check if it's a missingness flag
            if feature_name.startswith("MISSING_"):
                base_indicator = feature_name.replace("MISSING_", "")
                features[feature_name] = 1 if base_indicator not in value_dict else 0
                continue
            
            # Check if it's a derived feature
            if feature_name.startswith("DERIVED_"):
                derived_value = self._compute_derived_feature(
                    feature_name,
                    schema.transforms.get(feature_name, {}),
                    value_dict
                )
                features[feature_name] = derived_value
                if derived_value is None or derived_value == 0.0:
                    missing_count += 1
                continue
            
            # Regular indicator
            if feature_name in value_dict:
                features[feature_name] = value_dict[feature_name]
            else:
                # Apply imputation
                imputed_value = self._impute_value(feature_name, schema.imputation_rules)
                features[feature_name] = imputed_value
                missing_count += 1
        
        # Create feature vector
        feature_vector = FeatureVector(
            organization_id=org_id,
            period_id=period_id,
            schema_version_id=schema.id,
            features=features,
            feature_count=len(features),
            missing_count=missing_count,
            metadata={
                "schema_version": schema.version_name,
                "total_mapped_values": len(mapped_values)
            }
        )
        
        self.db.add(feature_vector)
        self.db.commit()
        self.db.refresh(feature_vector)
        
        # Log audit event
        self.audit_service.log_event(
            event_type="feature_engineering",
            action="build",
            entity_type="FeatureVector",
            entity_id=feature_vector.id,
            metadata={
                "organization_id": org_id,
                "period_id": period_id,
                "schema_version_id": schema.id,
                "feature_count": len(features),
                "missing_count": missing_count
            }
        )
        
        return feature_vector
    
    def _compute_derived_feature(
        self,
        feature_name: str,
        transform_def: Dict[str, Any],
        value_dict: Dict[str, Optional[float]]
    ) -> Optional[float]:
        """Compute a derived feature from transform definition."""
        if not transform_def:
            return 0.0
        
        transform_type = transform_def.get("type")
        
        if transform_type == "sum":
            inputs = transform_def.get("inputs", [])
            values = [value_dict.get(inp) for inp in inputs]
            if any(v is None for v in values):
                return 0.0  # Missing data
            return sum(values)
        
        elif transform_type == "ratio":
            numerator = value_dict.get(transform_def.get("numerator"))
            denominator = value_dict.get(transform_def.get("denominator"))
            if numerator is None or denominator is None or denominator == 0:
                return 0.0
            return numerator / denominator
        
        elif transform_type == "weighted_sum":
            inputs = transform_def.get("inputs", {})
            total = 0.0
            for indicator, weight in inputs.items():
                value = value_dict.get(indicator)
                if value is not None:
                    total += value * weight
            return total
        
        return 0.0
    
    def _impute_value(
        self,
        feature_name: str,
        imputation_rules: Dict[str, Any]
    ) -> float:
        """Impute value for missing feature."""
        # Get feature-specific rule or default
        rule = imputation_rules.get(feature_name, imputation_rules.get("default", {}))
        
        method = rule.get("method", "constant")
        
        if method == "constant":
            return rule.get("value", 0.0)
        
        # For now, only constant imputation
        # Future: median, mean from training dataset
        return 0.0
