"""
Framework definitions for GRI, SASB, and TCFD.
Maps framework items to canonical indicators.
"""
from typing import List, Dict, Any

# GRI (Global Reporting Initiative) Framework Items
GRI_FRAMEWORK_ITEMS: List[Dict[str, Any]] = [
    {"framework_item_id": "GRI-305-1", "framework_item_name": "Direct (Scope 1) GHG emissions", "indicator_code": "ENV_GHG_SCOPE1", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-305-2", "framework_item_name": "Energy indirect (Scope 2) GHG emissions", "indicator_code": "ENV_GHG_SCOPE2", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-305-3", "framework_item_name": "Other indirect (Scope 3) GHG emissions", "indicator_code": "ENV_GHG_SCOPE3", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-302-1", "framework_item_name": "Energy consumption within the organization", "indicator_code": "ENV_ENERGY_CONSUMPTION", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-303-3", "framework_item_name": "Water withdrawal", "indicator_code": "ENV_WATER_WITHDRAWAL", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-306-3", "framework_item_name": "Waste generated", "indicator_code": "ENV_WASTE_GENERATED", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-306-4", "framework_item_name": "Waste diverted from disposal", "indicator_code": "ENV_WASTE_RECYCLED_PCT", "relevance_weight": 0.8},
    {"framework_item_id": "GRI-2-7", "framework_item_name": "Employees", "indicator_code": "SOC_EMPLOYEE_COUNT", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-405-1", "framework_item_name": "Diversity of governance bodies and employees", "indicator_code": "SOC_GENDER_DIVERSITY_PCT", "relevance_weight": 0.9},
    {"framework_item_id": "GRI-404-1", "framework_item_name": "Average hours of training per year per employee", "indicator_code": "SOC_TRAINING_HOURS", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-403-9", "framework_item_name": "Work-related injuries", "indicator_code": "SOC_INJURY_RATE", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-403-9-a", "framework_item_name": "Fatalities as a result of work-related injury", "indicator_code": "SOC_FATALITIES", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-2-9", "framework_item_name": "Governance structure and composition", "indicator_code": "GOV_BOARD_INDEPENDENCE_PCT", "relevance_weight": 0.8},
    {"framework_item_id": "GRI-2-27", "framework_item_name": "Compliance with laws and regulations", "indicator_code": "GOV_REGULATORY_FINES", "relevance_weight": 0.9},
    {"framework_item_id": "GRI-205-3", "framework_item_name": "Confirmed incidents of corruption", "indicator_code": "GOV_CORRUPTION_INCIDENTS", "relevance_weight": 1.0},
    {"framework_item_id": "GRI-206-1", "framework_item_name": "Legal actions for anti-competitive behavior", "indicator_code": "GOV_ETHICS_VIOLATIONS", "relevance_weight": 0.7},
]

# SASB (Sustainability Accounting Standards Board) Framework Items
SASB_FRAMEWORK_ITEMS: List[Dict[str, Any]] = [
    {"framework_item_id": "SASB-EM-EP-110a.1", "framework_item_name": "Gross global Scope 1 emissions", "indicator_code": "ENV_GHG_SCOPE1", "relevance_weight": 1.0},
    {"framework_item_id": "SASB-EM-EP-110a.2", "framework_item_name": "Discussion of long-term and short-term strategy", "indicator_code": "ENV_GHG_SCOPE1", "relevance_weight": 0.5},
    {"framework_item_id": "SASB-IF-EN-130a.1", "framework_item_name": "Total energy consumed", "indicator_code": "ENV_ENERGY_CONSUMPTION", "relevance_weight": 1.0},
    {"framework_item_id": "SASB-IF-EN-130a.2", "framework_item_name": "Percentage of renewable energy", "indicator_code": "ENV_RENEWABLE_ENERGY_PCT", "relevance_weight": 1.0},
    {"framework_item_id": "SASB-IF-EN-140a.1", "framework_item_name": "Total water withdrawn", "indicator_code": "ENV_WATER_WITHDRAWAL", "relevance_weight": 1.0},
    {"framework_item_id": "SASB-IF-EN-150a.1", "framework_item_name": "Amount of waste generated", "indicator_code": "ENV_WASTE_GENERATED", "relevance_weight": 1.0},
    {"framework_item_id": "SASB-HC-DI-320a.1", "framework_item_name": "Employee engagement as a percentage", "indicator_code": "SOC_EMPLOYEE_TURNOVER_PCT", "relevance_weight": 0.7},
    {"framework_item_id": "SASB-HC-DI-330a.1", "framework_item_name": "Total amount of monetary losses from legal proceedings", "indicator_code": "GOV_REGULATORY_FINES", "relevance_weight": 1.0},
    {"framework_item_id": "SASB-SV-PS-330a.1", "framework_item_name": "Description of approach to identifying and addressing data security risks", "indicator_code": "SOC_DATA_BREACHES", "relevance_weight": 0.6},
]

# TCFD (Task Force on Climate-related Financial Disclosures) Framework Items
TCFD_FRAMEWORK_ITEMS: List[Dict[str, Any]] = [
    {"framework_item_id": "TCFD-METRICS-a", "framework_item_name": "Scope 1 GHG emissions", "indicator_code": "ENV_GHG_SCOPE1", "relevance_weight": 1.0},
    {"framework_item_id": "TCFD-METRICS-b", "framework_item_name": "Scope 2 GHG emissions", "indicator_code": "ENV_GHG_SCOPE2", "relevance_weight": 1.0},
    {"framework_item_id": "TCFD-METRICS-c", "framework_item_name": "Scope 3 GHG emissions (if appropriate)", "indicator_code": "ENV_GHG_SCOPE3", "relevance_weight": 0.9},
    {"framework_item_id": "TCFD-STRATEGY-b", "framework_item_name": "Impact on organization's businesses, strategy, and financial planning", "indicator_code": "ENV_ENERGY_CONSUMPTION", "relevance_weight": 0.5},
]

# All framework mappings
FRAMEWORK_MAPPINGS = {
    "GRI": GRI_FRAMEWORK_ITEMS,
    "SASB": SASB_FRAMEWORK_ITEMS,
    "TCFD": TCFD_FRAMEWORK_ITEMS
}
