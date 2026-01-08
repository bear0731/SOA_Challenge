# -*- coding: utf-8 -*-
"""
Pydantic Schemas for Structured Report Output

Defines the exact structure for LLM-generated insights and fixed report data.
"""

from typing import List, Optional, Dict, Any
from datetime import date

# Check for pydantic
try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    # Provide fallback base class
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def model_dump(self):
            return self.__dict__
    def Field(*args, **kwargs):
        return kwargs.get('default', None)


# =============================================================================
# LLM-Generated Insights (Structured Output)
# =============================================================================

class SHAPExplanation(BaseModel):
    """Explanation for a single SHAP feature contribution."""
    feature: str = Field(description="特徵名稱")
    value: str = Field(description="特徵值")
    direction: str = Field(description="增加或降低死亡率")
    explanation: str = Field(description="一句話解釋此特徵對死亡率的影響")


class ActuarialInsights(BaseModel):
    """
    LLM-generated interpretive content only.
    
    這個 schema 定義 LLM 可以生成的內容範圍。
    固定數據（表格、圖表、免責聲明）不在此處。
    """
    
    # Executive Summary (2-3 句話)
    summary: str = Field(description="2-3 句話總結：預測結果、主要風險因子、風險水平")
    
    # Risk Interpretation
    risk_interpretation: str = Field(description="解釋此保單的風險水平，必須引用 Relative Risk (RR) 數值")
    
    # SHAP Explanations (top 5 features)
    shap_explanations: List[SHAPExplanation] = Field(description="解釋前 5 個最重要特徵的影響")
    
    # Model Calibration Interpretation
    calibration_note: str = Field(description="解釋 A/E Ratio 的含義，說明模型校準狀態")
    
    # Segment-Specific Insight
    segment_insight: Optional[str] = Field(default=None, description="如有異常區段(Spotlight)，說明該區段的風險特性")
    
    # Recommendations (max 3)
    recommendations: List[str] = Field(description="基於分析結果的建議事項")


# =============================================================================
# Fixed Report Data (Not LLM-generated)
# =============================================================================

class PredictionData(BaseModel):
    """固定的預測數據。"""
    mortality_rate: float
    relative_risk: float
    overall_death_rate: float
    interpretation: str


class SHAPData(BaseModel):
    """固定的 SHAP 數據。"""
    feature: str
    value: Any
    shap_value: float
    direction: str


class SegmentData(BaseModel):
    """固定的區段數據。"""
    segment_id: str
    rule_text: str
    ae_ratio: float
    relative_risk: float
    credibility: str
    risk_level: Optional[str] = None


class EvidenceChart(BaseModel):
    """證據圖表引用。"""
    name: str
    path: str
    description: str


class ReportData(BaseModel):
    """
    固定的報告數據（非 LLM 生成）。
    包含所有數據表格、圖表路徑、免責聲明。
    """
    
    # Metadata
    report_date: str
    report_version: str = "1.0"
    
    # Input Record
    input_record: Dict[str, Any]
    
    # Prediction
    prediction: PredictionData
    
    # SHAP (top 5)
    shap_contributions: List[SHAPData]
    
    # Population Context
    percentile_context: List[Dict[str, Any]]
    category_context: List[Dict[str, Any]]
    
    # Segments
    coverage_segment: Optional[SegmentData] = None
    spotlight_segment: Optional[SegmentData] = None
    
    # Calibration
    overall_ae: float
    yearly_ae: Optional[Dict[str, float]] = None
    
    # Evidence Charts (paths for PDF inclusion)
    evidence_charts: List[EvidenceChart] = Field(default_factory=list)
    
    # Fixed Disclaimers
    disclaimers: List[str]


# =============================================================================
# Full Report (Combined)
# =============================================================================

class FullReport(BaseModel):
    """
    完整報告 = 固定數據 + LLM 解釋。
    
    這個結構可以直接渲染為 Markdown 或 PDF。
    """
    
    # Fixed data
    data: ReportData
    
    # LLM-generated insights
    insights: ActuarialInsights
    
    # System prompt used (for transparency)
    system_prompt: Optional[str] = None
    
    # Validation status
    is_validated: bool = False
    validation_notes: List[str] = Field(default_factory=list)


# =============================================================================
# Prompt Context (Input to LLM)
# =============================================================================

class PromptContext(BaseModel):
    """
    傳給 LLM 的上下文資訊。
    LLM 根據此資訊生成 ActuarialInsights。
    """
    
    # Core prediction
    prediction: PredictionData
    
    # SHAP data for interpretation
    shap_contributions: List[SHAPData]
    
    # Context
    percentiles: List[Dict[str, Any]]
    categories: List[Dict[str, Any]]
    
    # Segment info
    coverage_segment: Optional[Dict[str, Any]] = None
    spotlight_segment: Optional[Dict[str, Any]] = None
    
    # Calibration
    overall_ae: float
