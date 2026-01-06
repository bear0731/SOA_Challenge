# -*- coding: utf-8 -*-
"""
Configuration for Report Generator
"""

from pathlib import Path

# =============================================================================
# Paths
# =============================================================================

# Base paths
ROOT_DIR = Path(__file__).parent.parent.parent
CODE_DIR = ROOT_DIR / 'code'
DATA_DIR = ROOT_DIR / 'data'
MODELS_DIR = ROOT_DIR / 'models'
KNOWLEDGE_BASE_DIR = ROOT_DIR / 'knowledge_base'

# Knowledge base sub-paths
EDA_DIR = KNOWLEDGE_BASE_DIR / 'eda'
CALIBRATION_DIR = KNOWLEDGE_BASE_DIR / 'calibration'
SEGMENTS_DIR = KNOWLEDGE_BASE_DIR / 'segments'
SHAP_DIR = KNOWLEDGE_BASE_DIR / 'shap'

# Model files
LGBM_MODEL_PATH = MODELS_DIR / 'lgbm_mortality_offset_poisson.txt'
YEAR_FACTORS_PATH = MODELS_DIR / 'year_factors_offset.csv'

# =============================================================================
# Model Features
# =============================================================================

FEATURES = [
    'Attained_Age', 'Issue_Age', 'Duration', 'Sex', 'Smoker_Status',
    'Insurance_Plan', 'Face_Amount_Band', 'Preferred_Class',
    'SOA_Post_Lvl_Ind', 'SOA_Antp_Lvl_TP', 'SOA_Guar_Lvl_TP'
]

CATEGORICAL_FEATURES = [
    'Sex', 'Smoker_Status', 'Insurance_Plan', 'Face_Amount_Band',
    'Preferred_Class', 'SOA_Post_Lvl_Ind', 'SOA_Antp_Lvl_TP', 'SOA_Guar_Lvl_TP'
]

NUMERICAL_FEATURES = ['Attained_Age', 'Issue_Age', 'Duration']

# =============================================================================
# LLM Configuration (Placeholder)
# =============================================================================

LLM_CONFIG = {
    "model": "gpt-4",  # or "gemini-pro"
    "temperature": 0.3,
    "max_tokens": 2000,
}

# =============================================================================
# Report Settings
# =============================================================================

REPORT_CONFIG = {
    "top_shap_features": 5,
    "rr_anomaly_threshold": 0.15,  # |RR - 1| > 15%
    "ae_calibrated_range": (0.95, 1.05),
}
