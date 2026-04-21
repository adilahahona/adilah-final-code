"""
ESG mapping service - maps raw values to canonical indicators.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.models.sql_models import (
    RawIndicatorValue,
    MappedIndicatorValue,
    IndicatorCatalogItem,
    Organization,
    ReportingPeriod
)
from app.domain.mapping.rules import MappingRulesEngine
from app.domain.mapping.unit_normalization import UnitNormalizer
from app.domain.audit.service import AuditService

logger = logging.getLogger(__name__)


class ESGMappingService:
    """
    Service for mapping raw indicator values to canonical indicators.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.rules_engine = MappingRulesEngine(db)
        self.unit_normalizer = UnitNormalizer()
        self.audit_service = AuditService(db)
    
    def run_mapping(
        self,
        org_id: int,
        period_id: int,
        mapping_version: str = "1.0",
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Run mapping for a specific organization and period.
        
        Args:
            org_id: Organization ID
            period_id: Reporting period ID
            mapping_version: Version identifier for mapping
            overwrite: If True, delete existing mapped values first
            
        Returns:
            Dictionary with mapping statistics
        """
        # Verify org and period exist
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise ValueError(f"Organization {org_id} not found")
        
        period = self.db.query(ReportingPeriod).filter(ReportingPeriod.id == period_id).first()
        if not period:
            raise ValueError(f"Reporting period {period_id} not found")
        
        # Clear existing mapped values if overwrite
        if overwrite:
            self.db.query(MappedIndicatorValue).filter(
                MappedIndicatorValue.organization_id == org_id,
                MappedIndicatorValue.period_id == period_id
            ).delete()
            self.db.commit()
        
        # Get all raw values for this org/period
        raw_values = (
            self.db.query(RawIndicatorValue)
            .filter(
                RawIndicatorValue.organization_id == org_id,
                RawIndicatorValue.period_id == period_id
            )
            .all()
        )
        
        stats = {
            "total_raw_values": len(raw_values),
            "mapped_count": 0,
            "unmapped_count": 0,
            "errors": []
        }
        
        # Group raw values by indicator code
        grouped = {}
        for raw_val in raw_values:
            code = raw_val.indicator_code
            if code not in grouped:
                grouped[code] = []
            grouped[code].append(raw_val)
        
        # Map each group
        for raw_code, raw_vals in grouped.items():
            try:
                # Resolve canonical code
                canonical_code = self.rules_engine.resolve_indicator_code(raw_code)
                
                if not canonical_code:
                    stats["unmapped_count"] += len(raw_vals)
                    stats["errors"].append({
                        "raw_code": raw_code,
                        "error": "No mapping found"
                    })
                    continue
                
                # Get catalog item
                catalog_item = self.rules_engine.get_indicator(canonical_code)
                if not catalog_item:
                    stats["unmapped_count"] += len(raw_vals)
                    stats["errors"].append({
                        "raw_code": raw_code,
                        "error": f"Catalog item {canonical_code} not found"
                    })
                    continue
                
                # Take most recent raw value (or aggregate if needed - v1 just takes first)
                raw_val = raw_vals[0]
                
                # Normalize unit and value
                if raw_val.numeric_value is not None:
                    normalized_value, normalized_unit = self.unit_normalizer.normalize_unit(
                        raw_val.numeric_value,
                        raw_val.unit
                    )
                else:
                    normalized_value = None
                    normalized_unit = self.unit_normalizer.get_standard_unit(raw_val.unit)
                
                # Create mapped value
                mapped_val = MappedIndicatorValue(
                    organization_id=org_id,
                    period_id=period_id,
                    indicator_code=canonical_code,
                    numeric_value=normalized_value,
                    unit_normalized=normalized_unit,
                    pillar=catalog_item.pillar,
                    raw_indicator_value_ids=[v.id for v in raw_vals],
                    mapping_method="aliased" if raw_code.lower() != canonical_code.lower() else "direct",
                    mapping_version=mapping_version,
                    confidence=raw_val.confidence,
                    metadata={
                        "raw_code": raw_code,
                        "original_unit": raw_val.unit,
                        "source_count": len(raw_vals)
                    }
                )
                
                self.db.add(mapped_val)
                stats["mapped_count"] += 1
                
            except Exception as e:
                logger.error(f"Error mapping {raw_code}: {str(e)}")
                stats["unmapped_count"] += len(raw_vals)
                stats["errors"].append({
                    "raw_code": raw_code,
                    "error": str(e)
                })
        
        # Commit all mapped values
        self.db.commit()
        
        # Log audit event
        self.audit_service.log_event(
            event_type="mapping",
            action="run",
            entity_type="MappedIndicatorValue",
            metadata={
                "organization_id": org_id,
                "period_id": period_id,
                "mapping_version": mapping_version,
                "stats": {
                    "total_raw_values": stats["total_raw_values"],
                    "mapped_count": stats["mapped_count"],
                    "unmapped_count": stats["unmapped_count"]
                }
            }
        )
        
        return stats
    
    def compute_coverage(
        self,
        org_id: int,
        period_id: int
    ) -> Dict[str, Any]:
        """
        Compute indicator coverage for organization and period.
        
        Args:
            org_id: Organization ID
            period_id: Reporting period ID
            
        Returns:
            Coverage statistics by pillar
        """
        # Get all required indicators
        required_indicators = self.rules_engine.get_required_indicators()
        
        # Group by pillar
        required_by_pillar = {}
        for indicator in required_indicators:
            pillar = indicator.pillar.value
            if pillar not in required_by_pillar:
                required_by_pillar[pillar] = []
            required_by_pillar[pillar].append(indicator.indicator_code)
        
        # Get mapped values for this org/period
        mapped_values = (
            self.db.query(MappedIndicatorValue)
            .filter(
                MappedIndicatorValue.organization_id == org_id,
                MappedIndicatorValue.period_id == period_id
            )
            .all()
        )
        
        # Build set of present indicators
        present_codes = {v.indicator_code for v in mapped_values}
        
        # Compute coverage by pillar
        coverage_by_pillar = {}
        missing_by_pillar = {}
        
        for pillar, required_codes in required_by_pillar.items():
            present = [c for c in required_codes if c in present_codes]
            missing = [c for c in required_codes if c not in present_codes]
            
            coverage_by_pillar[pillar] = {
                "required_count": len(required_codes),
                "present_count": len(present),
                "coverage_pct": (len(present) / len(required_codes) * 100) if required_codes else 0,
                "missing_count": len(missing)
            }
            missing_by_pillar[pillar] = missing
        
        # Overall coverage
        all_required = sum(len(codes) for codes in required_by_pillar.values())
        all_present = len([c for c in present_codes if any(c in codes for codes in required_by_pillar.values())])
        
        overall_coverage = {
            "total_required": all_required,
            "total_present": all_present,
            "overall_coverage_pct": (all_present / all_required * 100) if all_required else 0
        }
        
        return {
            "organization_id": org_id,
            "period_id": period_id,
            "overall": overall_coverage,
            "by_pillar": coverage_by_pillar,
            "missing_indicators": missing_by_pillar
        }
