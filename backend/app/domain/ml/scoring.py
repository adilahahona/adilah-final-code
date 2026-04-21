"""
Scoring service - computes deterministic E/S/G subscores from mapped indicators.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import numpy as np
from datetime import datetime

from app.models.sql_models import (
    ScoringConfigVersion,
    MappedIndicatorValue,
    IndicatorCatalogItem,
    PillarEnum
)


class ScoringService:
    """Service for computing deterministic E/S/G subscores."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_config(self) -> ScoringConfigVersion:
        """Get the active scoring configuration."""
        config = self.db.query(ScoringConfigVersion).filter(
            ScoringConfigVersion.is_active == True
        ).first()
        
        if not config:
            # Create default config
            config = self._create_default_config()
        
        return config
    
    def _create_default_config(self) -> ScoringConfigVersion:
        """Create default scoring configuration."""
        config = ScoringConfigVersion(
            config_name="default_v1",
            pillar_weights={
                "E": 0.34,
                "S": 0.33,
                "G": 0.33
            },
            indicator_bounds={
                # GHG emissions - lower is better (tonnes CO2e)
                "GHG_SCOPE1": {"min": 0, "max": 1000000, "direction": "minimize"},
                "GHG_SCOPE2": {"min": 0, "max": 500000, "direction": "minimize"},
                "GHG_SCOPE3": {"min": 0, "max": 2000000, "direction": "minimize"},
                
                # Energy - lower is better (MWh)
                "ENERGY_CONSUMPTION": {"min": 0, "max": 5000000, "direction": "minimize"},
                "RENEWABLE_ENERGY_PCT": {"min": 0, "max": 100, "direction": "maximize"},
                
                # Water - lower is better (m³)
                "WATER_WITHDRAWAL": {"min": 0, "max": 10000000, "direction": "minimize"},
                
                # Waste - lower is better (tonnes)
                "HAZARDOUS_WASTE": {"min": 0, "max": 100000, "direction": "minimize"},
                "NON_HAZARDOUS_WASTE": {"min": 0, "max": 500000, "direction": "minimize"},
                "WASTE_RECYCLED_PCT": {"min": 0, "max": 100, "direction": "maximize"},
                
                # Social - higher is better
                "EMPLOYEE_COUNT": {"min": 0, "max": 1000000, "direction": "neutral"},
                "WOMEN_EMPLOYEES_PCT": {"min": 0, "max": 100, "direction": "maximize"},
                "TRAINING_HOURS_AVG": {"min": 0, "max": 200, "direction": "maximize"},
                "INJURY_RATE": {"min": 0, "max": 20, "direction": "minimize"},
                "LIVING_WAGE_PCT": {"min": 0, "max": 100, "direction": "maximize"},
                
                # Governance - higher is better
                "BOARD_INDEPENDENCE_PCT": {"min": 0, "max": 100, "direction": "maximize"},
                "WOMEN_BOARD_PCT": {"min": 0, "max": 100, "direction": "maximize"},
                "ETHICS_VIOLATIONS": {"min": 0, "max": 100, "direction": "minimize"},
                "CORRUPTION_INCIDENTS": {"min": 0, "max": 50, "direction": "minimize"}
            },
            normalization_method="min_max",
            is_active=True,
            description="Default scoring configuration v1 with min-max normalization"
        )
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        return config
    
    def compute_subscores(
        self,
        organization_id: int,
        period_id: int,
        config_version_id: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Compute E/S/G subscores for an organization-period.
        
        Args:
            organization_id: Organization ID
            period_id: Reporting period ID
            config_version_id: Specific config to use (None = active)
            
        Returns:
            Dictionary with E, S, G scores (0-100 scale)
        """
        # Get config
        if config_version_id:
            config = self.db.query(ScoringConfigVersion).filter(
                ScoringConfigVersion.id == config_version_id
            ).first()
        else:
            config = self.get_active_config()
        
        # Get mapped indicators
        mapped_values = self.db.query(MappedIndicatorValue).filter(
            MappedIndicatorValue.organization_id == organization_id,
            MappedIndicatorValue.period_id == period_id
        ).all()
        
        # Group by pillar
        pillar_scores = {}
        
        for pillar in ["E", "S", "G"]:
            pillar_indicators = [
                mv for mv in mapped_values
                if self._get_indicator_pillar(mv.indicator_code) == pillar
            ]
            
            if not pillar_indicators:
                pillar_scores[pillar] = 0.0
                continue
            
            # Normalize and aggregate
            normalized_scores = []
            
            for mv in pillar_indicators:
                norm_score = self._normalize_indicator(
                    mv.indicator_code,
                    mv.normalized_value,
                    config
                )
                if norm_score is not None:
                    normalized_scores.append(norm_score)
            
            # Average normalized scores
            if normalized_scores:
                pillar_scores[pillar] = float(np.mean(normalized_scores))
            else:
                pillar_scores[pillar] = 0.0
        
        return pillar_scores
    
    def _get_indicator_pillar(self, indicator_code: str) -> str:
        """Get pillar for an indicator code."""
        catalog_item = self.db.query(IndicatorCatalogItem).filter(
            IndicatorCatalogItem.indicator_code == indicator_code
        ).first()
        
        if catalog_item:
            return catalog_item.pillar.value
        
        # Fallback: guess from code prefix
        if indicator_code.startswith(("GHG_", "ENERGY_", "WATER_", "WASTE_", "BIODIVERSITY_", "AIR_", "SPILLS_")):
            return "E"
        elif indicator_code.startswith(("EMPLOYEE_", "WOMEN_", "TRAINING_", "TURNOVER_", "INJURY_", "FATALITIES_", "SAFETY_", "LIVING_", "UNION_", "HUMAN_", "SUPPLY_", "COMMUNITY_", "CUSTOMER_", "DATA_")):
            return "S"
        else:
            return "G"
    
    def _normalize_indicator(
        self,
        indicator_code: str,
        value: float,
        config: ScoringConfigVersion
    ) -> Optional[float]:
        """
        Normalize an indicator value to 0-100 scale.
        
        Args:
            indicator_code: Indicator code
            value: Raw value
            config: Scoring configuration
            
        Returns:
            Normalized score (0-100) or None if not configured
        """
        bounds = config.indicator_bounds.get(indicator_code)
        
        if not bounds:
            return None
        
        min_val = bounds["min"]
        max_val = bounds["max"]
        direction = bounds["direction"]
        
        # Clamp to bounds
        value = np.clip(value, min_val, max_val)
        
        # Normalize to 0-1
        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (value - min_val) / (max_val - min_val)
        
        # Invert if minimize direction
        if direction == "minimize":
            normalized = 1.0 - normalized
        elif direction == "neutral":
            normalized = 0.5
        
        # Scale to 0-100
        return float(normalized * 100)
