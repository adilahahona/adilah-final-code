"""
Mapping rules engine for indicators.
Deterministic mapping via code matching and aliases.
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.sql_models import IndicatorCatalogItem, FrameworkMapping


class MappingRulesEngine:
    """
    Rules engine for mapping raw indicator codes to canonical indicators.
    Uses exact matching and alias resolution.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._catalog_cache = None
        self._alias_map = None
    
    def _build_cache(self):
        """Build in-memory cache of indicators and aliases."""
        if self._catalog_cache is not None:
            return
        
        # Load all catalog items
        items = self.db.query(IndicatorCatalogItem).all()
        
        # Build catalog cache
        self._catalog_cache = {item.indicator_code: item for item in items}
        
        # Build alias map
        self._alias_map = {}
        for item in items:
            # Add the code itself
            self._alias_map[item.indicator_code.lower()] = item.indicator_code
            
            # Add aliases
            if item.aliases:
                for alias in item.aliases:
                    self._alias_map[alias.lower()] = item.indicator_code
    
    def resolve_indicator_code(self, raw_code: str) -> Optional[str]:
        """
        Resolve a raw indicator code to a canonical indicator code.
        
        Args:
            raw_code: Raw indicator code from data source
            
        Returns:
            Canonical indicator code or None if not found
        """
        self._build_cache()
        
        # Normalize input
        normalized = raw_code.strip().lower()
        
        # Try exact match or alias match
        return self._alias_map.get(normalized)
    
    def get_indicator(self, indicator_code: str) -> Optional[IndicatorCatalogItem]:
        """
        Get catalog item for an indicator code.
        
        Args:
            indicator_code: Canonical indicator code
            
        Returns:
            IndicatorCatalogItem or None
        """
        self._build_cache()
        return self._catalog_cache.get(indicator_code)
    
    def get_indicators_by_pillar(self, pillar: str) -> List[IndicatorCatalogItem]:
        """
        Get all indicators for a specific pillar.
        
        Args:
            pillar: E, S, or G
            
        Returns:
            List of IndicatorCatalogItem
        """
        return (
            self.db.query(IndicatorCatalogItem)
            .filter(IndicatorCatalogItem.pillar == pillar)
            .all()
        )
    
    def get_required_indicators(self) -> List[IndicatorCatalogItem]:
        """Get all required indicators."""
        return (
            self.db.query(IndicatorCatalogItem)
            .filter(IndicatorCatalogItem.is_required == True)
            .all()
        )
    
    def map_framework_item(
        self,
        framework_name: str,
        framework_item_id: str
    ) -> Optional[str]:
        """
        Map a framework item to canonical indicator code.
        
        Args:
            framework_name: Framework name (GRI, SASB, TCFD)
            framework_item_id: Framework-specific item ID
            
        Returns:
            Canonical indicator code or None
        """
        mapping = (
            self.db.query(FrameworkMapping)
            .filter(
                FrameworkMapping.framework_name == framework_name,
                FrameworkMapping.framework_item_id == framework_item_id,
                FrameworkMapping.is_active == True
            )
            .first()
        )
        
        return mapping.indicator_code if mapping else None
    
    def clear_cache(self):
        """Clear the internal cache (call after updating catalog)."""
        self._catalog_cache = None
        self._alias_map = None
