# -*- coding: utf-8 -*-
"""
Report Generator Package

Generates structured explanation reports for mortality predictions.
"""

from .config import (
    KNOWLEDGE_BASE_DIR,
    FEATURES,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    REPORT_CONFIG,
)

from .knowledge import KnowledgeBase, get_knowledge_base
from .matcher import SegmentMatcher, create_matcher
from .predictor import MortalityPredictor, create_predictor
from .llm import LLMClient, create_llm_client
from .generator import ReportGenerator, create_generator
from .validator import ReportValidator, validator
from .prompts import SYSTEM_BASE, REPORT_STRUCTURE, DISCLAIMERS

__all__ = [
    # Config
    'KNOWLEDGE_BASE_DIR',
    'FEATURES',
    'CATEGORICAL_FEATURES', 
    'NUMERICAL_FEATURES',
    'REPORT_CONFIG',
    # Knowledge
    'KnowledgeBase',
    'get_knowledge_base',
    # Matcher
    'SegmentMatcher',
    'create_matcher',
    # Predictor
    'MortalityPredictor',
    'create_predictor',
    # LLM
    'LLMClient',
    'create_llm_client',
    # Generator
    'ReportGenerator',
    'create_generator',
    # Validator
    'ReportValidator',
    'validator',
    # Prompts
    'SYSTEM_BASE',
    'REPORT_STRUCTURE',
    'DISCLAIMERS',
]
