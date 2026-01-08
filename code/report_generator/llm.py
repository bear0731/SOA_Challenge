# -*- coding: utf-8 -*-
"""
LLM Module with Structured Output

Handles LLM integration for report generation using Google Gemini
with Pydantic structured output.
"""

import os
from typing import Optional, Type, TypeVar
from pathlib import Path

# Load environment variables from .env (optional)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Check for pydantic schemas
try:
    from .schemas import ActuarialInsights, PromptContext, SHAPExplanation, HAS_PYDANTIC
except ImportError:
    HAS_PYDANTIC = False
    ActuarialInsights = None
    PromptContext = None
    SHAPExplanation = None

# Check for langchain-google-genai
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

# Type variable for structured output
T = TypeVar('T')


class LLMClient:
    """
    LLM client for generating structured actuarial insights using Google Gemini.
    
    Uses Pydantic for structured output validation.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash-lite",
        temperature: float = 0.3
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.client = None
        self._initialized = False
    
    def initialize(self) -> 'LLMClient':
        """Initialize the LLM client."""
        if self._initialized:
            return self
        
        if not HAS_GOOGLE:
            print("⚠ langchain-google-genai not installed")
            print("  Install with: pip install langchain-google-genai")
            return self
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("⚠ GOOGLE_API_KEY not found in environment")
            return self
        
        try:
            self.client = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                google_api_key=api_key
            )
            self._initialized = True
            print(f"✓ LLM initialized: {self.model_name}")
        except Exception as e:
            print(f"⚠ LLM initialization failed: {e}")
        
        return self
    
    def generate_insights(
        self, 
        context: PromptContext,
        system_prompt: str
    ) -> ActuarialInsights:
        """
        Generate structured actuarial insights.
        
        Args:
            context: Data context for the report
            system_prompt: System instructions
            
        Returns:
            ActuarialInsights Pydantic model
        """
        if not self._initialized or not self.client:
            return self._mock_insights(context)
        
        # Build user prompt from context
        user_prompt = self._build_context_prompt(context)
        
        # Combine prompts
        full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        
        try:
            # Try structured output first
            structured_llm = self.client.with_structured_output(ActuarialInsights)
            response = structured_llm.invoke(full_prompt)
            return response
        except Exception as e:
            print(f"⚠ Structured output failed: {e}")
            print("  Falling back to JSON parsing...")
            
            # Fallback: regular generation + parse
            return self._fallback_generate(full_prompt)
    
    def _build_context_prompt(self, context: PromptContext) -> str:
        """Build user prompt from context data."""
        lines = []
        
        # Prediction
        lines.append("## 預測數據")
        lines.append(f"- 預測死亡率: {context.prediction.mortality_rate:.6f}")
        lines.append(f"- Relative Risk (RR): {context.prediction.relative_risk:.2f}x")
        lines.append(f"- 整體平均死亡率: {context.prediction.overall_death_rate:.6f}")
        
        # SHAP
        lines.append("\n## SHAP 特徵貢獻")
        for s in context.shap_contributions[:5]:
            sign = "+" if s.shap_value > 0 else ""
            lines.append(f"- {s.feature}: {s.value} → SHAP={sign}{s.shap_value:.4f} ({s.direction})")
        
        # Population context
        lines.append("\n## 人群比較")
        for p in context.percentiles:
            lines.append(f"- {p.get('description', str(p))}")
        for c in context.categories:
            lines.append(f"- {c.get('description', str(c))}")
        
        # Segments
        if context.coverage_segment:
            seg = context.coverage_segment
            lines.append(f"\n## 所屬區段")
            lines.append(f"- Segment: {seg.get('segment_id')}")
            lines.append(f"- A/E: {seg.get('statistics', {}).get('ae_ratio')}")
            lines.append(f"- RR: {seg.get('statistics', {}).get('relative_risk')}")
        
        if context.spotlight_segment:
            seg = context.spotlight_segment
            lines.append(f"\n## ⚠️ 異常區段")
            lines.append(f"- Segment: {seg.get('segment_id')}")
            lines.append(f"- Risk Level: {seg.get('risk_level')}")
            lines.append(f"- RR: {seg.get('statistics', {}).get('relative_risk')}")
        
        # Calibration
        lines.append(f"\n## 模型校準")
        lines.append(f"- Overall A/E: {context.overall_ae:.4f}")
        
        # Task
        lines.append("\n---")
        lines.append("請根據以上數據，生成結構化的精算解釋。")
        lines.append("回覆必須是有效的 JSON，符合 ActuarialInsights schema。")
        
        return "\n".join(lines)
    
    def _fallback_generate(self, prompt: str) -> ActuarialInsights:
        """Fallback: regular generation with JSON parsing."""
        import json
        
        try:
            response = self.client.invoke(prompt)
            content = response.content
            
            # Try to extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "{" in content:
                start = content.index("{")
                end = content.rindex("}") + 1
                json_str = content[start:end]
            else:
                raise ValueError("No JSON found in response")
            
            data = json.loads(json_str)
            return ActuarialInsights(**data)
        except Exception as e:
            print(f"⚠ Fallback parsing failed: {e}")
            return self._mock_insights(None)
    
    def _mock_insights(self, context: Optional[PromptContext]) -> ActuarialInsights:
        """Generate mock insights when LLM not available."""
        from .schemas import SHAPExplanation
        
        return ActuarialInsights(
            summary="此保單的預測死亡率顯著高於整體人群平均。主要風險因子為高齡及吸菸狀態。建議進行進一步精算審查。",
            risk_interpretation="根據模型預測，此保單的 Relative Risk 顯示風險水平高於平均。這與保單持有人的年齡和風險特徵相關。",
            shap_explanations=[
                SHAPExplanation(
                    feature="Attained_Age",
                    value="75",
                    direction="增加",
                    explanation="高齡是死亡率上升的主要驅動因子"
                ),
                SHAPExplanation(
                    feature="Smoker_Status",
                    value="S",
                    direction="增加",
                    explanation="吸菸與較高死亡率相關"
                )
            ],
            calibration_note="模型整體 A/E Ratio 接近 1.0，表示模型校準良好。",
            segment_insight=None,
            recommendations=[
                "建議對高風險區段進行額外核保審查",
                "建議持續監控此類保單的經驗發展"
            ]
        )
    
    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str,
        max_retries: int = 3
    ) -> str:
        """
        Legacy method: Generate unstructured text response.
        
        For backward compatibility.
        """
        if not self._initialized or not self.client:
            return "[LLM not available]"
        
        combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
        
        for attempt in range(max_retries):
            try:
                response = self.client.invoke(combined_prompt)
                return response.content
            except Exception as e:
                print(f"⚠ LLM call failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return f"[LLM Error: {e}]"
        
        return "[LLM call failed]"


def create_llm_client(
    model_name: str = "gemini-2.0-flash",
    temperature: float = 0.3
) -> LLMClient:
    """Factory function to create and initialize LLM client."""
    return LLMClient(model_name, temperature).initialize()
