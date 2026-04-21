"""
Indicator catalog - canonical ESG indicators.
Seed data for the indicator catalog.
"""
from typing import List, Dict, Any

# Canonical ESG indicator catalog
# 40+ indicators across E, S, G pillars

INDICATOR_CATALOG: List[Dict[str, Any]] = [
    # ENVIRONMENTAL (E) INDICATORS
    {
        "indicator_code": "ENV_GHG_SCOPE1",
        "name": "GHG Emissions Scope 1",
        "description": "Direct greenhouse gas emissions from owned or controlled sources",
        "pillar": "E",
        "unit": "tCO2e",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["scope1_emissions", "direct_emissions", "ghg_scope_1"]
    },
    {
        "indicator_code": "ENV_GHG_SCOPE2",
        "name": "GHG Emissions Scope 2",
        "description": "Indirect greenhouse gas emissions from purchased energy",
        "pillar": "E",
        "unit": "tCO2e",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["scope2_emissions", "indirect_emissions", "ghg_scope_2"]
    },
    {
        "indicator_code": "ENV_GHG_SCOPE3",
        "name": "GHG Emissions Scope 3",
        "description": "Indirect greenhouse gas emissions from value chain",
        "pillar": "E",
        "unit": "tCO2e",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["scope3_emissions", "value_chain_emissions", "ghg_scope_3"]
    },
    {
        "indicator_code": "ENV_ENERGY_CONSUMPTION",
        "name": "Total Energy Consumption",
        "description": "Total energy consumed from all sources",
        "pillar": "E",
        "unit": "MWh",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["energy_total", "total_energy"]
    },
    {
        "indicator_code": "ENV_RENEWABLE_ENERGY_PCT",
        "name": "Renewable Energy Percentage",
        "description": "Percentage of energy from renewable sources",
        "pillar": "E",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["renewable_pct", "renewable_energy_ratio"]
    },
    {
        "indicator_code": "ENV_WATER_WITHDRAWAL",
        "name": "Water Withdrawal",
        "description": "Total water withdrawn from all sources",
        "pillar": "E",
        "unit": "m3",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["water_total", "total_water_withdrawal"]
    },
    {
        "indicator_code": "ENV_WATER_RECYCLED_PCT",
        "name": "Water Recycled Percentage",
        "description": "Percentage of water recycled and reused",
        "pillar": "E",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["water_recycling_rate"]
    },
    {
        "indicator_code": "ENV_WASTE_GENERATED",
        "name": "Total Waste Generated",
        "description": "Total waste generated from operations",
        "pillar": "E",
        "unit": "tonnes",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["total_waste", "waste_total"]
    },
    {
        "indicator_code": "ENV_WASTE_RECYCLED_PCT",
        "name": "Waste Recycled Percentage",
        "description": "Percentage of waste recycled",
        "pillar": "E",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["waste_recycling_rate", "recycling_rate"]
    },
    {
        "indicator_code": "ENV_HAZARDOUS_WASTE",
        "name": "Hazardous Waste",
        "description": "Total hazardous waste generated",
        "pillar": "E",
        "unit": "tonnes",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["hazardous_waste_total"]
    },
    {
        "indicator_code": "ENV_BIODIVERSITY_IMPACT",
        "name": "Biodiversity Impact Sites",
        "description": "Number of sites with significant biodiversity impact",
        "pillar": "E",
        "unit": "count",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["biodiversity_sites"]
    },
    {
        "indicator_code": "ENV_LAND_USE",
        "name": "Total Land Use",
        "description": "Total land area used or affected by operations",
        "pillar": "E",
        "unit": "hectares",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["land_area"]
    },
    {
        "indicator_code": "ENV_AIR_EMISSIONS_NOX",
        "name": "NOx Air Emissions",
        "description": "Nitrogen oxide emissions",
        "pillar": "E",
        "unit": "tonnes",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["nox_emissions"]
    },
    {
        "indicator_code": "ENV_AIR_EMISSIONS_SOX",
        "name": "SOx Air Emissions",
        "description": "Sulfur oxide emissions",
        "pillar": "E",
        "unit": "tonnes",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["sox_emissions"]
    },
    {
        "indicator_code": "ENV_SPILLS_INCIDENTS",
        "name": "Environmental Spills and Incidents",
        "description": "Number of significant environmental spills or incidents",
        "pillar": "E",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["spills_count", "environmental_incidents"]
    },
    
    # SOCIAL (S) INDICATORS
    {
        "indicator_code": "SOC_EMPLOYEE_COUNT",
        "name": "Total Employee Count",
        "description": "Total number of employees (FTE)",
        "pillar": "S",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["employee_total", "headcount"]
    },
    {
        "indicator_code": "SOC_GENDER_DIVERSITY_PCT",
        "name": "Gender Diversity Percentage",
        "description": "Percentage of female employees",
        "pillar": "S",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["female_pct", "women_percentage"]
    },
    {
        "indicator_code": "SOC_BOARD_DIVERSITY_PCT",
        "name": "Board Gender Diversity",
        "description": "Percentage of women on board of directors",
        "pillar": "S",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["board_women_pct", "female_board_members"]
    },
    {
        "indicator_code": "SOC_TRAINING_HOURS",
        "name": "Training Hours per Employee",
        "description": "Average training hours per employee per year",
        "pillar": "S",
        "unit": "hours",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["avg_training_hours", "training_per_employee"]
    },
    {
        "indicator_code": "SOC_EMPLOYEE_TURNOVER_PCT",
        "name": "Employee Turnover Rate",
        "description": "Percentage of employees who left during the period",
        "pillar": "S",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["turnover_rate", "attrition_rate"]
    },
    {
        "indicator_code": "SOC_INJURY_RATE",
        "name": "Lost Time Injury Frequency Rate",
        "description": "Number of lost-time injuries per million hours worked",
        "pillar": "S",
        "unit": "rate",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["ltifr", "injury_frequency_rate"]
    },
    {
        "indicator_code": "SOC_FATALITIES",
        "name": "Workplace Fatalities",
        "description": "Number of work-related fatalities",
        "pillar": "S",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["fatality_count", "deaths"]
    },
    {
        "indicator_code": "SOC_HEALTH_SAFETY_INCIDENTS",
        "name": "Health and Safety Incidents",
        "description": "Total number of recordable health and safety incidents",
        "pillar": "S",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["safety_incidents", "recordable_incidents"]
    },
    {
        "indicator_code": "SOC_LIVING_WAGE_PCT",
        "name": "Living Wage Compliance",
        "description": "Percentage of employees earning at least living wage",
        "pillar": "S",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["living_wage_pct"]
    },
    {
        "indicator_code": "SOC_UNIONIZED_PCT",
        "name": "Unionized Workers Percentage",
        "description": "Percentage of employees covered by collective bargaining",
        "pillar": "S",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["union_coverage", "collective_bargaining_pct"]
    },
    {
        "indicator_code": "SOC_HUMAN_RIGHTS_VIOLATIONS",
        "name": "Human Rights Violations",
        "description": "Number of identified human rights violations",
        "pillar": "S",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["hr_violations"]
    },
    {
        "indicator_code": "SOC_SUPPLY_CHAIN_AUDITS",
        "name": "Supply Chain Social Audits",
        "description": "Number of suppliers audited for social criteria",
        "pillar": "S",
        "unit": "count",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["supplier_audits"]
    },
    {
        "indicator_code": "SOC_COMMUNITY_INVESTMENT",
        "name": "Community Investment",
        "description": "Total investment in community development programs",
        "pillar": "S",
        "unit": "currency",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["community_spend"]
    },
    {
        "indicator_code": "SOC_CUSTOMER_SATISFACTION",
        "name": "Customer Satisfaction Score",
        "description": "Average customer satisfaction rating",
        "pillar": "S",
        "unit": "score",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["csat", "customer_score"]
    },
    {
        "indicator_code": "SOC_DATA_BREACHES",
        "name": "Data Privacy Breaches",
        "description": "Number of substantiated data privacy breaches",
        "pillar": "S",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["privacy_breaches", "data_incidents"]
    },
    
    # GOVERNANCE (G) INDICATORS
    {
        "indicator_code": "GOV_BOARD_INDEPENDENCE_PCT",
        "name": "Board Independence",
        "description": "Percentage of independent board members",
        "pillar": "G",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["independent_directors_pct"]
    },
    {
        "indicator_code": "GOV_BOARD_MEETINGS",
        "name": "Board Meeting Frequency",
        "description": "Number of board meetings per year",
        "pillar": "G",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["board_meetings_count"]
    },
    {
        "indicator_code": "GOV_BOARD_ATTENDANCE_PCT",
        "name": "Board Meeting Attendance",
        "description": "Average board meeting attendance rate",
        "pillar": "G",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["attendance_rate"]
    },
    {
        "indicator_code": "GOV_AUDIT_COMMITTEE_INDEPENDENCE",
        "name": "Audit Committee Independence",
        "description": "Percentage of independent members on audit committee",
        "pillar": "G",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["audit_independence_pct"]
    },
    {
        "indicator_code": "GOV_ETHICS_VIOLATIONS",
        "name": "Ethics Code Violations",
        "description": "Number of substantiated ethics violations",
        "pillar": "G",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["ethics_breaches"]
    },
    {
        "indicator_code": "GOV_CORRUPTION_INCIDENTS",
        "name": "Corruption and Bribery Incidents",
        "description": "Number of confirmed corruption or bribery incidents",
        "pillar": "G",
        "unit": "count",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["corruption_cases", "bribery_incidents"]
    },
    {
        "indicator_code": "GOV_WHISTLEBLOWER_REPORTS",
        "name": "Whistleblower Reports",
        "description": "Number of whistleblower reports received",
        "pillar": "G",
        "unit": "count",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["whistleblower_count"]
    },
    {
        "indicator_code": "GOV_ANTI_CORRUPTION_TRAINING_PCT",
        "name": "Anti-Corruption Training Coverage",
        "description": "Percentage of employees trained on anti-corruption",
        "pillar": "G",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["corruption_training_pct"]
    },
    {
        "indicator_code": "GOV_POLITICAL_CONTRIBUTIONS",
        "name": "Political Contributions",
        "description": "Total monetary value of political contributions",
        "pillar": "G",
        "unit": "currency",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["political_spend"]
    },
    {
        "indicator_code": "GOV_REGULATORY_FINES",
        "name": "Regulatory Fines and Penalties",
        "description": "Total monetary value of fines for non-compliance",
        "pillar": "G",
        "unit": "currency",
        "data_type": "numeric",
        "is_required": True,
        "aliases": ["fines_total", "penalties"]
    },
    {
        "indicator_code": "GOV_TAX_RATE_EFFECTIVE",
        "name": "Effective Tax Rate",
        "description": "Effective corporate tax rate paid",
        "pillar": "G",
        "unit": "percent",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["tax_rate"]
    },
    {
        "indicator_code": "GOV_SUSTAINABILITY_REPORTING",
        "name": "Sustainability Reporting Framework",
        "description": "Framework used for sustainability reporting (GRI, SASB, etc.)",
        "pillar": "G",
        "unit": "text",
        "data_type": "text",
        "is_required": False,
        "aliases": ["reporting_framework"]
    },
    {
        "indicator_code": "GOV_ESG_COMMITTEE_EXISTS",
        "name": "ESG Committee Existence",
        "description": "Whether board-level ESG committee exists",
        "pillar": "G",
        "unit": "boolean",
        "data_type": "boolean",
        "is_required": True,
        "aliases": ["esg_committee"]
    },
    {
        "indicator_code": "GOV_EXECUTIVE_COMPENSATION_RATIO",
        "name": "CEO Pay Ratio",
        "description": "Ratio of CEO compensation to median employee compensation",
        "pillar": "G",
        "unit": "ratio",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["ceo_pay_ratio", "pay_equity_ratio"]
    },
    {
        "indicator_code": "GOV_SHAREHOLDER_ENGAGEMENT",
        "name": "Shareholder Engagement Score",
        "description": "Score indicating level of shareholder engagement",
        "pillar": "G",
        "unit": "score",
        "data_type": "numeric",
        "is_required": False,
        "aliases": ["engagement_score"]
    },
]
