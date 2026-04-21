"""
Unit normalization utilities.
Converts common units to standard forms.
"""
from typing import Optional, Tuple


# Unit conversion table
# Format: {from_unit: (to_unit, multiplier)}
UNIT_CONVERSIONS = {
    # Weight
    "kg": ("tonnes", 0.001),
    "kilogram": ("tonnes", 0.001),
    "kilograms": ("tonnes", 0.001),
    "ton": ("tonnes", 1.0),
    "tons": ("tonnes", 1.0),
    "tonne": ("tonnes", 1.0),
    "tonnes": ("tonnes", 1.0),
    "mt": ("tonnes", 1.0),  # metric ton
    
    # Energy
    "kwh": ("MWh", 0.001),
    "mwh": ("MWh", 1.0),
    "gwh": ("MWh", 1000.0),
    
    # Volume - water
    "m3": ("m3", 1.0),
    "cubic_meters": ("m3", 1.0),
    "liters": ("m3", 0.001),
    "l": ("m3", 0.001),
    
    # Percentage
    "percent": ("percent", 1.0),
    "%": ("percent", 1.0),
    "percentage": ("percent", 1.0),
    
    # Currency (keep as is, no conversion)
    "usd": ("currency", 1.0),
    "eur": ("currency", 1.0),
    "currency": ("currency", 1.0),
    
    # GHG emissions
    "tco2e": ("tCO2e", 1.0),
    "tco2": ("tCO2e", 1.0),
    "mtco2e": ("tCO2e", 1000000.0),
    "ktco2e": ("tCO2e", 1000.0),
    
    # Area
    "hectares": ("hectares", 1.0),
    "ha": ("hectares", 1.0),
    "sqm": ("hectares", 0.0001),
    
    # Counts and ratios
    "count": ("count", 1.0),
    "number": ("count", 1.0),
    "ratio": ("ratio", 1.0),
    "rate": ("rate", 1.0),
    "score": ("score", 1.0),
    
    # Time
    "hours": ("hours", 1.0),
    "days": ("hours", 24.0),
}


class UnitNormalizer:
    """Utility for normalizing units to standard forms."""
    
    @staticmethod
    def normalize_unit(
        value: float,
        unit: Optional[str]
    ) -> Tuple[float, Optional[str]]:
        """
        Normalize a value and unit to standard form.
        
        Args:
            value: Numeric value
            unit: Original unit string
            
        Returns:
            Tuple of (normalized_value, normalized_unit)
        """
        if unit is None or unit.strip() == "":
            return value, None
        
        # Clean unit string
        unit_clean = unit.strip().lower()
        
        # Look up conversion
        if unit_clean in UNIT_CONVERSIONS:
            normalized_unit, multiplier = UNIT_CONVERSIONS[unit_clean]
            normalized_value = value * multiplier
            return normalized_value, normalized_unit
        
        # No conversion available, return original
        return value, unit
    
    @staticmethod
    def get_standard_unit(unit: Optional[str]) -> Optional[str]:
        """
        Get the standard unit without converting value.
        
        Args:
            unit: Original unit string
            
        Returns:
            Standard unit name or None
        """
        if unit is None or unit.strip() == "":
            return None
        
        unit_clean = unit.strip().lower()
        
        if unit_clean in UNIT_CONVERSIONS:
            return UNIT_CONVERSIONS[unit_clean][0]
        
        return unit
