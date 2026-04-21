"""
Mapping service for seeding catalog and managing mappings.
"""
from sqlalchemy.orm import Session
from typing import List

from app.models.sql_models import IndicatorCatalogItem, FrameworkMapping
from app.domain.mapping.indicator_catalog import INDICATOR_CATALOG
from app.domain.mapping.frameworks import FRAMEWORK_MAPPINGS
from app.domain.audit.service import AuditService


class MappingService:
    """Service for managing indicator catalog and framework mappings."""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
    
    def seed_catalog(self, overwrite: bool = False) -> int:
        """
        Seed the indicator catalog from predefined data.
        
        Args:
            overwrite: If True, update existing indicators
            
        Returns:
            Number of indicators created/updated
        """
        count = 0
        
        for item_data in INDICATOR_CATALOG:
            # Check if exists
            existing = (
                self.db.query(IndicatorCatalogItem)
                .filter(IndicatorCatalogItem.indicator_code == item_data["indicator_code"])
                .first()
            )
            
            if existing and not overwrite:
                continue
            
            if existing and overwrite:
                # Update existing
                for key, value in item_data.items():
                    setattr(existing, key, value)
                count += 1
            else:
                # Create new
                item = IndicatorCatalogItem(**item_data)
                self.db.add(item)
                count += 1
                
                # Log audit event
                self.audit_service.log_event(
                    event_type="catalog_seed",
                    action="create",
                    entity_type="IndicatorCatalogItem",
                    after_state={"indicator_code": item_data["indicator_code"]},
                    metadata={"source": "seed"}
                )
        
        self.db.commit()
        return count
    
    def seed_framework_mappings(
        self,
        framework_name: str,
        overwrite: bool = False
    ) -> int:
        """
        Seed framework mappings for a specific framework.
        
        Args:
            framework_name: GRI, SASB, or TCFD
            overwrite: If True, update existing mappings
            
        Returns:
            Number of mappings created/updated
        """
        if framework_name not in FRAMEWORK_MAPPINGS:
            raise ValueError(f"Unknown framework: {framework_name}")
        
        count = 0
        mappings = FRAMEWORK_MAPPINGS[framework_name]
        
        for mapping_data in mappings:
            # Check if exists
            existing = (
                self.db.query(FrameworkMapping)
                .filter(
                    FrameworkMapping.framework_name == framework_name,
                    FrameworkMapping.framework_item_id == mapping_data["framework_item_id"]
                )
                .first()
            )
            
            if existing and not overwrite:
                continue
            
            full_data = {
                "framework_name": framework_name,
                "mapping_version": "1.0",
                "is_active": True,
                **mapping_data
            }
            
            if existing and overwrite:
                # Update existing
                for key, value in full_data.items():
                    setattr(existing, key, value)
                count += 1
            else:
                # Create new
                mapping = FrameworkMapping(**full_data)
                self.db.add(mapping)
                count += 1
                
                # Log audit event
                self.audit_service.log_event(
                    event_type="framework_mapping_seed",
                    action="create",
                    entity_type="FrameworkMapping",
                    after_state={
                        "framework_name": framework_name,
                        "framework_item_id": mapping_data["framework_item_id"]
                    },
                    metadata={"source": "seed"}
                )
        
        self.db.commit()
        return count
    
    def seed_all_frameworks(self, overwrite: bool = False) -> dict:
        """
        Seed all framework mappings.
        
        Returns:
            Dictionary with counts per framework
        """
        results = {}
        for framework_name in FRAMEWORK_MAPPINGS.keys():
            count = self.seed_framework_mappings(framework_name, overwrite)
            results[framework_name] = count
        return results
    
    def create_mapping(
        self,
        framework_name: str,
        framework_item_id: str,
        framework_item_name: str,
        indicator_code: str,
        relevance_weight: float = 1.0,
        mapping_rationale: str = None,
        user_id: str = None
    ) -> FrameworkMapping:
        """
        Create a new framework mapping.
        
        Args:
            framework_name: Framework name
            framework_item_id: Framework-specific item ID
            framework_item_name: Framework item name
            indicator_code: Canonical indicator code
            relevance_weight: Relevance weight (0.0 to 1.0)
            mapping_rationale: Rationale for mapping
            user_id: User creating the mapping
            
        Returns:
            Created FrameworkMapping
        """
        # Verify indicator exists
        indicator = (
            self.db.query(IndicatorCatalogItem)
            .filter(IndicatorCatalogItem.indicator_code == indicator_code)
            .first()
        )
        
        if not indicator:
            raise ValueError(f"Indicator {indicator_code} not found in catalog")
        
        # Create mapping
        mapping = FrameworkMapping(
            framework_name=framework_name,
            framework_item_id=framework_item_id,
            framework_item_name=framework_item_name,
            indicator_code=indicator_code,
            relevance_weight=relevance_weight,
            mapping_rationale=mapping_rationale,
            mapping_version="1.0",
            is_active=True
        )
        
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        
        # Log audit event
        self.audit_service.log_event(
            event_type="framework_mapping",
            action="create",
            entity_type="FrameworkMapping",
            entity_id=mapping.id,
            user_id=user_id,
            after_state={
                "framework_name": framework_name,
                "framework_item_id": framework_item_id,
                "indicator_code": indicator_code
            }
        )
        
        return mapping
