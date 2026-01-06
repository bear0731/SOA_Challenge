# -*- coding: utf-8 -*-
"""
Report Generator (Refactored)

Generates structured explanation reports for mortality predictions.
Uses modular architecture: knowledge.py, matcher.py, predictor.py, llm.py.
"""

import json
from typing import Dict, Any, Optional, List

from .config import FEATURES, NUMERICAL_FEATURES, CATEGORICAL_FEATURES, REPORT_CONFIG
from .knowledge import KnowledgeBase, get_knowledge_base
from .matcher import SegmentMatcher
from .predictor import MortalityPredictor, create_predictor
from .prompts import SYSTEM_BASE, DISCLAIMERS
from .validator import validator
from .llm import LLMClient, create_llm_client


class ReportGenerator:
    """
    Generates structured explanation reports for mortality predictions.
    
    Architecture:
    - KnowledgeBase: Loads EDA, Calibration, SHAP, Segments
    - SegmentMatcher: Matches input to Coverage/Spotlight segments
    - MortalityPredictor: Predicts mortality rate and calculates SHAP
    - LLMClient: Generates natural language reports
    
    Usage:
        generator = ReportGenerator()
        report = generator.generate(input_record)
    """
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        load_model: bool = True,
        load_llm: bool = True
    ):
        # Load knowledge base
        self.kb = get_knowledge_base(knowledge_base_path)
        
        # Create matcher
        self.matcher = SegmentMatcher(self.kb)
        
        # Create predictor (optional - for full pipeline)
        self.predictor = None
        if load_model:
            try:
                self.predictor = create_predictor()
            except Exception as e:
                print(f"⚠ Predictor not loaded: {e}")
        
        # Create LLM client
        self.llm = None
        if load_llm:
            try:
                self.llm = create_llm_client()
            except Exception as e:
                print(f"⚠ LLM not loaded: {e}")
    
    # =========================================================================
    # Main Generation
    # =========================================================================
    
    def generate(
        self,
        input_record: Dict[str, Any],
        prediction: Optional[float] = None,
        shap_values: Optional[Dict[str, float]] = None,
        coverage_leaf_id: Optional[int] = None,
        spotlight_leaf_id: Optional[int] = None
    ) -> Dict:
        """
        Generate explanation report.
        
        Args:
            input_record: Feature values
            prediction: Pre-computed prediction (or will predict)
            shap_values: Pre-computed SHAP values (or will calculate)
            coverage_leaf_id: Coverage tree leaf ID
            spotlight_leaf_id: Spotlight tree leaf ID
        
        Returns:
            Complete report dict with prompts
        """
        # 1. Predict if not provided
        if prediction is None or shap_values is None:
            if self.predictor:
                prediction, shap_values = self.predictor.predict(input_record)
            else:
                # Mock values
                prediction = 0.01
                shap_values = {f: 0.0 for f in FEATURES}
        
        # 2. Get overall rate
        overall_rate = self.kb.get_overall_rate()
        relative_risk = prediction / overall_rate if overall_rate > 0 else 1.0
        
        # 3. Match segments
        coverage_segment = self.matcher.match_coverage(coverage_leaf_id) if coverage_leaf_id else None
        spotlight_segment = self.matcher.match_spotlight(spotlight_leaf_id) if spotlight_leaf_id else None
        
        # 4. Calculate context
        percentile_context = self._calculate_percentiles(input_record)
        category_context = self._calculate_categories(input_record)
        
        # 5. Sort SHAP by importance
        sorted_shap = sorted(
            shap_values.items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        )[:REPORT_CONFIG['top_shap_features']]
        
        # 6. Get base value
        base_value = self.predictor.get_base_value() if self.predictor else 0.0097
        
        # 7. Build report
        report = {
            "input": input_record,
            "prediction": {
                "mortality_rate": round(prediction, 6),
                "relative_risk": round(relative_risk, 2),
                "interpretation": self._interpret_rr(relative_risk)
            },
            "shap_analysis": {
                "base_value": round(base_value, 6),
                "top_drivers": [
                    {
                        "feature": feat,
                        "value": input_record.get(feat),
                        "shap_value": round(shap, 6),
                        "direction": "increases" if shap > 0 else "decreases",
                        "interpretation": self._interpret_shap(feat, shap)
                    }
                    for feat, shap in sorted_shap
                ]
            },
            "population_context": {
                "percentiles": percentile_context,
                "categories": category_context
            },
            "calibration": {
                "overall_ae": self.kb.overall_ae,
                "interpretation": self._interpret_calibration()
            },
            "coverage_segment": coverage_segment,
            "spotlight_alert": spotlight_segment,
            "global_feature_importance": self._get_global_importance()
        }
        
        # 8. Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(report)
        
        report["prompts"] = {
            "system": system_prompt,
            "user": user_prompt
        }
        
        return report
    
    def generate_report(
        self,
        input_record: Dict[str, Any],
        prediction: Optional[float] = None,
        shap_values: Optional[Dict[str, float]] = None,
        coverage_leaf_id: Optional[int] = None,
        spotlight_leaf_id: Optional[int] = None
    ) -> Dict:
        """
        Generate complete report with LLM explanation.
        
        Returns:
            Report dict with 'llm_report' field containing generated text
        """
        # Get structured report with prompts
        report = self.generate(
            input_record, prediction, shap_values,
            coverage_leaf_id, spotlight_leaf_id
        )
        
        # Generate LLM response
        if self.llm:
            llm_response = self.llm.generate(
                report['prompts']['system'],
                report['prompts']['user']
            )
            
            # Validate and auto-correct
            is_valid, issues = validator.validate(llm_response)
            if not is_valid:
                llm_response = validator.auto_correct(llm_response)
                report['validation_issues'] = issues
            
            report['llm_report'] = llm_response
        else:
            report['llm_report'] = "[LLM not available]"
        
        return report
    
    # =========================================================================
    # Context Calculation (using knowledge base)
    # =========================================================================
    
    def _calculate_percentiles(self, input_record: Dict) -> List[Dict]:
        """Calculate percentile context for numerical features."""
        if not self.kb.numerical_summary:
            return []
        
        results = []
        for feature in NUMERICAL_FEATURES:
            if feature in input_record and feature in self.kb.numerical_summary:
                value = input_record[feature]
                desc = self._get_percentile_description(feature, value)
                pctl = self._get_percentile(feature, value)
                results.append({
                    "feature": feature,
                    "value": value,
                    "percentile": pctl,
                    "description": desc
                })
        return results
    
    def _get_percentile(self, feature: str, value: float) -> int:
        """Get approximate percentile for a value."""
        pcts = self.kb.numerical_summary[feature]['percentiles']
        for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
            if value <= pcts.get(str(p), float('inf')):
                return p
        return 99
    
    def _get_percentile_description(self, feature: str, value: float) -> str:
        """Convert a value to percentile description for LLM."""
        pcts = self.kb.numerical_summary[feature]['percentiles']
        
        for p in sorted([int(k) for k in pcts.keys()]):
            if value <= pcts[str(p)]:
                if p <= 10:
                    return f"{feature}={value} is in the bottom {p}% (low)"
                elif p <= 25:
                    return f"{feature}={value} is below average ({p}th percentile)"
                elif p <= 75:
                    return f"{feature}={value} is typical ({p}th percentile)"
                elif p <= 90:
                    return f"{feature}={value} is above average ({p}th percentile)"
                else:
                    return f"{feature}={value} is in top {100-p}% (high)"
        
        return f"{feature}={value} is in the top 1% (extreme)"
    
    def _calculate_categories(self, input_record: Dict) -> List[Dict]:
        """Get category context."""
        if not self.kb.categorical_summary:
            return []
        
        results = []
        for feature in ['Sex', 'Smoker_Status', 'Insurance_Plan', 'Preferred_Class']:
            if feature in input_record and feature in self.kb.categorical_summary:
                value = str(input_record[feature])
                desc = self._get_category_description(feature, value)
                dist = self.kb.categorical_summary[feature].get('distribution', {})
                pct = dist.get(value, {}).get('percentage', 0) if value in dist else 0
                results.append({
                    "feature": feature,
                    "value": value,
                    "population_pct": pct,
                    "description": desc
                })
        return results
    
    def _get_category_description(self, feature: str, value: str) -> str:
        """Get category description with population percentage."""
        dist = self.kb.categorical_summary[feature].get('distribution', {})
        if value in dist:
            pct = dist[value].get('percentage', 0)
            return f"{feature}={value} ({pct:.1f}% of population)"
        return f"{feature}={value} (unknown category)"
    
    # =========================================================================
    # Interpretation Helpers
    # =========================================================================
    
    def _interpret_rr(self, rr: float) -> str:
        """Interpret relative risk value."""
        if rr < 0.5:
            return "Significantly lower than population average"
        elif rr < 0.85:
            return "Lower than population average"
        elif rr <= 1.15:
            return "Around population average"
        elif rr <= 2.0:
            return "Higher than population average"
        else:
            return f"Significantly higher than population average ({rr:.1f}x)"
    
    def _interpret_shap(self, feature: str, shap_value: float) -> str:
        """Interpret SHAP value."""
        direction = "increases" if shap_value > 0 else "decreases"
        magnitude = abs(shap_value)
        
        if magnitude < 0.001:
            impact = "minimal"
        elif magnitude < 0.01:
            impact = "moderate"
        else:
            impact = "significant"
        
        return f"{impact} impact, {direction} predicted mortality"
    
    def _interpret_calibration(self) -> str:
        """Interpret overall calibration."""
        if not self.kb.overall_ae:
            return "Calibration data not available"
        
        ae = self.kb.overall_ae.get('overall_ae', 1.0)
        if 0.95 <= ae <= 1.05:
            return f"Model is well-calibrated (A/E = {ae:.2f})"
        elif ae > 1.05:
            return f"Model tends to underestimate (A/E = {ae:.2f})"
        else:
            return f"Model tends to overestimate (A/E = {ae:.2f})"
    
    def _get_global_importance(self) -> List[Dict]:
        """Get top global feature importance."""
        if not self.kb.global_shap:
            return []
        return self.kb.global_shap.get('feature_importance', [])[:5]
    
    # =========================================================================
    # Prompt Building
    # =========================================================================
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with global knowledge."""
        sections = [SYSTEM_BASE]
        
        # EDA summary
        if self.kb.numerical_summary:
            sections.append("\n## 數值特徵統計")
            sections.append(json.dumps(self.kb.numerical_summary, indent=2, ensure_ascii=False))
        
        if self.kb.categorical_summary:
            sections.append("\n## 類別特徵分布")
            sections.append(json.dumps(self.kb.categorical_summary, indent=2, ensure_ascii=False))
        
        # Calibration
        if self.kb.overall_ae:
            sections.append("\n## 模型校準")
            sections.append(json.dumps(self.kb.overall_ae, indent=2, ensure_ascii=False))
        
        # Global SHAP
        if self.kb.global_shap:
            sections.append("\n## 全域特徵重要性 (SHAP)")
            importance = self.kb.global_shap.get('feature_importance', [])[:5]
            sections.append(json.dumps(importance, indent=2, ensure_ascii=False))
        
        return "\n".join(sections)
    
    def _build_user_prompt(self, report: Dict) -> str:
        """Build user prompt with specific record context."""
        sections = []
        
        # Input
        sections.append("## 查詢資料")
        sections.append(json.dumps(report['input'], indent=2, ensure_ascii=False, default=str))
        
        # Prediction
        sections.append("\n## 預測結果")
        sections.append(f"- 預測死亡率: {report['prediction']['mortality_rate']:.6f}")
        sections.append(f"- Relative Risk: {report['prediction']['relative_risk']}x")
        sections.append(f"- 解讀: {report['prediction']['interpretation']}")
        
        # SHAP
        sections.append("\n## SHAP 特徵貢獻")
        for driver in report['shap_analysis']['top_drivers']:
            sign = "+" if driver['shap_value'] > 0 else ""
            sections.append(f"- {driver['feature']}: {driver['value']} → SHAP={sign}{driver['shap_value']:.4f} ({driver['interpretation']})")
        
        # Population context
        sections.append("\n## 人群定位")
        for p in report['population_context']['percentiles']:
            sections.append(f"- {p['description']}")
        for c in report['population_context']['categories']:
            sections.append(f"- {c['description']}")
        
        # Segments (using matcher's context generator)
        segment_context = self.matcher.get_segment_context(
            report['coverage_segment'],
            report['spotlight_alert']
        )
        if segment_context and segment_context != "無匹配區段":
            sections.append(f"\n{segment_context}")
        
        # Task
        sections.append("\n---")
        sections.append("請根據以上資訊，用繁體中文撰寫一份完整的風險評估報告。")
        sections.append("報告應包含：預測摘要、主要風險因子、人群比較、模型校準說明、以及專業免責聲明。")
        
        return "\n".join(sections)
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate_report(self, report_text: str) -> tuple:
        """Validate generated report."""
        return validator.validate(report_text)
    
    def auto_correct_report(self, report_text: str) -> str:
        """Auto-correct common issues."""
        return validator.auto_correct(report_text)


# =============================================================================
# Factory function
# =============================================================================

def create_generator(
    kb_path: Optional[str] = None, 
    load_model: bool = True,
    load_llm: bool = True
) -> ReportGenerator:
    """Factory function to create ReportGenerator."""
    return ReportGenerator(kb_path, load_model, load_llm)
