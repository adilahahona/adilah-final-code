"""
Feature schema definition and management.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import json
import os

from app.models.sql_models import FeatureSchemaVersion
from app.core.config import settings


# Default feature schema v1
DEFAULT_FEATURE_SCHEMA_V1 = {
    "version_name": "v1.0",
    "description": "Default ESG feature schema v1.0",
    "feature_list": [
        # Environmental features
        "ENV_GHG_SCOPE1",
        "ENV_GHG_SCOPE2",
        "ENV_GHG_SCOPE3",
        "ENV_ENERGY_CONSUMPTION",
        "ENV_RENEWABLE_ENERGY_PCT",
        "ENV_WATER_WITHDRAWAL",
        "ENV_WASTE_GENERATED",
        "ENV_WASTE_RECYCLED_PCT",
        "ENV_HAZARDOUS_WASTE",
        "ENV_SPILLS_INCIDENTS",
        # Missingness flags for environmental
        "MISSING_ENV_GHG_SCOPE1",
        "MISSING_ENV_GHG_SCOPE2",
        "MISSING_ENV_ENERGY_CONSUMPTION",
        "MISSING_ENV_WATER_WITHDRAWAL",
        "MISSING_ENV_WASTE_GENERATED",
        # Social features
        "SOC_EMPLOYEE_COUNT",
        "SOC_GENDER_DIVERSITY_PCT",
        "SOC_BOARD_DIVERSITY_PCT",
        "SOC_TRAINING_HOURS",
        "SOC_EMPLOYEE_TURNOVER_PCT",
        "SOC_INJURY_RATE",
        "SOC_FATALITIES",
        "SOC_HEALTH_SAFETY_INCIDENTS",
        "SOC_HUMAN_RIGHTS_VIOLATIONS",
        "SOC_DATA_BREACHES",
        # Missingness flags for social
        "MISSING_SOC_INJURY_RATE",
        "MISSING_SOC_FATALITIES",
        "MISSING_SOC_GENDER_DIVERSITY_PCT",
        # Governance features
        "GOV_BOARD_INDEPENDENCE_PCT",
        "GOV_BOARD_MEETINGS",
        "GOV_ETHICS_VIOLATIONS",
        "GOV_CORRUPTION_INCIDENTS",
        "GOV_ANTI_CORRUPTION_TRAINING_PCT",
        "GOV_REGULATORY_FINES",
        "GOV_ESG_COMMITTEE_EXISTS",
        # Missingness flags for governance
        "MISSING_GOV_BOARD_INDEPENDENCE_PCT",
        "MISSING_GOV_CORRUPTION_INCIDENTS",
        # Derived features
        "DERIVED_GHG_TOTAL",
        "DERIVED_WASTE_INTENSITY",
        "DERIVED_SAFETY_SCORE"
    ],
    "transforms": {
        "DERIVED_GHG_TOTAL": {
            "type": "sum",
            "inputs": ["ENV_GHG_SCOPE1", "ENV_GHG_SCOPE2"]
        },
        "DERIVED_WASTE_INTENSITY": {
            "type": "ratio",
            "numerator": "ENV_WASTE_GENERATED",
            "denominator": "SOC_EMPLOYEE_COUNT"
        },
        "DERIVED_SAFETY_SCORE": {
            "type": "weighted_sum",
            "inputs": {
                "SOC_INJURY_RATE": -0.5,
                "SOC_FATALITIES": -10.0,
                "SOC_HEALTH_SAFETY_INCIDENTS": -0.1
            }
        }
    },
    "imputation_rules": {
        "default": {
            "method": "constant",
            "value": 0.0,
            "add_missing_flag": True
        },
        "ENV_RENEWABLE_ENERGY_PCT": {
            "method": "constant",
            "value": 0.0
        },
        "GOV_ESG_COMMITTEE_EXISTS": {
            "method": "constant",
            "value": 0  # Assume no committee if not reported
        }
    },
    "scaling_policy": "standard"  # StandardScaler
}


class FeatureSchemaManager:
    """Manager for feature schema versions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_default_schema(self) -> FeatureSchemaVersion:
        """Get or create the default feature schema."""
        schema = (
            self.db.query(FeatureSchemaVersion)
            .filter(FeatureSchemaVersion.version_name == DEFAULT_FEATURE_SCHEMA_V1["version_name"])
            .first()
        )
        
        if not schema:
            schema = FeatureSchemaVersion(
                version_name=DEFAULT_FEATURE_SCHEMA_V1["version_name"],
                feature_list=DEFAULT_FEATURE_SCHEMA_V1["feature_list"],
                transforms=DEFAULT_FEATURE_SCHEMA_V1["transforms"],
                imputation_rules=DEFAULT_FEATURE_SCHEMA_V1["imputation_rules"],
                scaling_policy=DEFAULT_FEATURE_SCHEMA_V1["scaling_policy"],
                is_active=True,
                description=DEFAULT_FEATURE_SCHEMA_V1["description"]
            )
            self.db.add(schema)
            self.db.commit()
            self.db.refresh(schema)
            
            # Save to artifacts
            self._save_schema_to_file(schema)
        
        return schema
    
    def get_latest_active_schema(self) -> FeatureSchemaVersion:
        """Get the latest active schema."""
        schema = (
            self.db.query(FeatureSchemaVersion)
            .filter(FeatureSchemaVersion.is_active == True)
            .order_by(FeatureSchemaVersion.created_at.desc())
            .first()
        )
        
        if not schema:
            schema = self.get_or_create_default_schema()
        
        return schema
    
    def _save_schema_to_file(self, schema: FeatureSchemaVersion):
        """Save schema to artifacts directory."""
        os.makedirs(settings.FEATURE_SCHEMAS_PATH, exist_ok=True)
        
        filepath = os.path.join(
            settings.FEATURE_SCHEMAS_PATH,
            f"schema_{schema.version_name}.json"
        )
        
        schema_data = {
            "id": schema.id,
            "version_name": schema.version_name,
            "feature_list": schema.feature_list,
            "transforms": schema.transforms,
            "imputation_rules": schema.imputation_rules,
            "scaling_policy": schema.scaling_policy,
            "description": schema.description,
            "created_at": schema.created_at.isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(schema_data, f, indent=2)
