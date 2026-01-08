# -*- coding: utf-8 -*-
"""
Prompt Builder

Builds complete system prompt with full knowledge base context.
"""

import json
from pathlib import Path
from typing import Optional

from .config import KNOWLEDGE_BASE_DIR


def load_json(path: Path) -> dict:
    """Load JSON file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def load_text(path: Path) -> str:
    """Load text file safely."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except:
        return ""


def build_system_prompt() -> str:
    """
    Build complete system prompt with all knowledge base context.
    
    Returns:
        Full system prompt string
    """
    kb_path = KNOWLEDGE_BASE_DIR
    sections = []
    
    # =========================================================================
    # 1. Core Actuarial Principles
    # =========================================================================
    sections.append("""# Actuarial Mortality Analysis System

You are an actuarial assistant generating mortality analysis reports compliant with ASOP standards.

## Core Principles
1. Model predicts **mortality RATE** (expected deaths per exposure), NOT probability
2. Use **associative language** (e.g., "associated with"), avoid causal claims
3. All values must **cite evidence sources** from the data
4. Reports must comply with **ASOP 23/25/41/56** standards

## Response Format
- Respond in ENGLISH only
- Use precise numeric formatting (see below)
- Generate structured JSON matching ActuarialInsights schema

## Numeric Formatting
- Mortality rate: 6 decimal places (0.009666)
- A/E Ratio: 2-4 decimal places (0.9989)
- SHAP value: signed, 4 decimal places (+0.0352)
- Percentile: ordinal format (90th percentile)
- Relative Risk: 2 decimals + 'x' suffix (6.08x)
""")
    
    # =========================================================================
    # 2. Model Contract
    # =========================================================================
    contract = load_json(kb_path / 'contracts' / 'model_contract.json')
    if contract:
        sections.append(f"""
---
## Model Specification

**Model**: {contract.get('model_type', 'LightGBM')}
**Purpose**: {contract.get('purpose', 'Mortality prediction')}
**Training Period**: {contract.get('training_period', '2009-2019')}

### Limitations
{chr(10).join('- ' + lim for lim in contract.get('limitations', []))}

### ASOP Compliance
{chr(10).join('- ' + c for c in contract.get('asop_compliance', []))}
""")
    
    # =========================================================================
    # 3. EDA Summary
    # =========================================================================
    numerical = load_json(kb_path / 'eda' / 'numerical_summary.json')
    categorical = load_json(kb_path / 'eda' / 'categorical_summary.json')
    
    if numerical:
        sections.append("""
---
## Data Distribution (EDA)

### Numerical Features""")
        for feat, stats in numerical.items():
            interp = stats.get('interpretation', {})
            sections.append(f"""
**{feat}**:
- Mean: {stats.get('mean', 'N/A')}, Std: {stats.get('std', 'N/A')}
- Range: [{stats.get('min', 0)}, {stats.get('max', 0)}]
- Interpretation: {interp.get('typical', 'N/A')}
- Extreme: {interp.get('extreme', 'N/A')}""")
    
    if categorical:
        sections.append("""
### Categorical Features""")
        for feat, stats in categorical.items():
            if 'value_counts' in stats:
                top_values = list(stats['value_counts'].items())[:3]
                top_str = ', '.join([f"{v[0]}:{v[1]:.1%}" for v in top_values])
                sections.append(f"- **{feat}**: {top_str}")
    
    # =========================================================================
    # 4. Calibration Data
    # =========================================================================
    overall_ae = load_json(kb_path / 'calibration' / 'overall_ae.json')
    yearly_ae = load_json(kb_path / 'calibration' / 'yearly_ae.json')
    
    if overall_ae:
        sections.append(f"""
---
## Model Calibration

**Overall A/E Ratio**: {overall_ae.get('overall_ae', 0.9989):.4f}
- Total Actual Deaths: {overall_ae.get('total_actual_deaths', 0):,}
- Total Expected Deaths: {overall_ae.get('total_expected_deaths', 0):,.0f}
- Interpretation: {overall_ae.get('interpretation', 'Well-calibrated')}
- Data Period: {overall_ae.get('data_period', '2009-2019')}
""")
    
    if yearly_ae:
        sections.append("### Yearly A/E Trend")
        for year, ae in list(yearly_ae.items())[:5]:
            sections.append(f"- {year}: A/E = {ae:.4f}" if isinstance(ae, float) else f"- {year}: {ae}")
    
    # =========================================================================
    # 5. SHAP Feature Importance
    # =========================================================================
    global_shap = load_json(kb_path / 'shap' / 'global_importance.json')
    if global_shap:
        sections.append("""
---
## Feature Importance (SHAP)

Global feature importance ranking:""")
        features = global_shap.get('features', global_shap)
        if isinstance(features, list):
            for i, item in enumerate(features[:8], 1):
                if isinstance(item, dict):
                    sections.append(f"{i}. {item.get('feature')}: {item.get('importance', item.get('mean_abs_shap', 0)):.4f}")
                else:
                    sections.append(f"{i}. {item}")
        elif isinstance(features, dict):
            sorted_feats = sorted(features.items(), key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True)
            for i, (feat, val) in enumerate(sorted_feats[:8], 1):
                sections.append(f"{i}. {feat}: {val:.4f}" if isinstance(val, (int, float)) else f"{i}. {feat}")
    
    # =========================================================================
    # 6. EDA Insights (from insight.md if exists)
    # =========================================================================
    insight_text = load_text(kb_path / 'eda' / 'insight.md')
    if insight_text:
        sections.append(f"""
---
## Key EDA Insights

{insight_text}
""")
    
    # =========================================================================
    # 7. Segment Overview
    # =========================================================================
    coverage = load_json(kb_path / 'segments' / 'coverage_registry.json')
    spotlight = load_json(kb_path / 'segments' / 'spotlight_summary.json')
    
    if coverage:
        sections.append(f"""
---
## Risk Segmentation

### Coverage Segments
- Total segments: {coverage.get('n_segments', 16)}
- Purpose: {coverage.get('purpose', 'Baseline risk classification')}
- Overall mortality rate: {coverage.get('overall_rate', 0.009666):.6f}
""")
    
    if spotlight:
        sections.append(f"""
### Spotlight Segments (Anomalies)
- Total anomaly segments: {spotlight.get('n_segments', 61)}
- Purpose: Identify statistically anomalous high/low risk groups
""")
    
    # =========================================================================
    # 8. Methodology
    # =========================================================================
    methodology_readme = load_text(kb_path / 'methodology' / 'README.md')
    if methodology_readme:
        sections.append(f"""
---
## Methodology Overview

{methodology_readme[:500]}...
""")
    
    # =========================================================================
    # 9. Key Metrics Definitions
    # =========================================================================
    sections.append("""
---
## Key Metrics Reference

| Metric | Formula | Interpretation |
|:-------|:--------|:---------------|
| A/E Ratio | Actual Deaths / Expected Deaths | =1.0: calibrated, >1.0: underestimate, <1.0: overestimate |
| Relative Risk (RR) | Segment Rate / Overall Rate | =1.0: average, >1.0: higher risk, <1.0: lower risk |
| Credibility | Based on exposure size | High: >50K, Medium: 10-50K, Low: <10K |
| SHAP Value | Feature contribution to prediction | +: increases mortality, -: decreases mortality |

## Language Guidelines
✓ Use: "associated with", "model estimates", "expected deaths", "based on historical data"
✗ Avoid: "death probability", "will die", "definitely", "certainly", "causes"
""")
    
    return "\n".join(sections)


def get_prompt_stats(prompt: str) -> dict:
    """Get statistics about the prompt."""
    lines = prompt.split('\n')
    chars = len(prompt)
    words = len(prompt.split())
    est_tokens = chars // 3  # Rough estimate
    
    return {
        'lines': len(lines),
        'characters': chars,
        'words': words,
        'estimated_tokens': est_tokens
    }


# Cache the built prompt
_cached_prompt = None

def get_full_system_prompt(force_rebuild: bool = False) -> str:
    """Get the full system prompt (cached)."""
    global _cached_prompt
    if _cached_prompt is None or force_rebuild:
        _cached_prompt = build_system_prompt()
    return _cached_prompt
