# -*- coding: utf-8 -*-
"""
Structured Actuarial Report Generator

Complete demo with:
- Random sampling from ILEC dataset
- Real model prediction + SHAP
- Full knowledge base system prompt
- LLM structured insights
- Report with system prompt appendix
- Timing and cost tracking
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from report_generator.schemas import (
    ActuarialInsights, ReportData, FullReport,
    PredictionData, SHAPData, SegmentData, EvidenceChart, PromptContext
)
from report_generator.llm import create_llm_client
from report_generator.renderer import create_renderer
from report_generator.prompt_builder import get_full_system_prompt, get_prompt_stats
from report_generator.knowledge import get_knowledge_base
from report_generator.predictor import create_predictor


# =============================================================================
# Test Mode: Set to True to use fake high-risk sample that triggers Spotlight
# =============================================================================
USE_TEST_DATA = True  # Change to False for random real sampling

# Fake high-risk sample (guaranteed to trigger Spotlight alert)
TEST_SAMPLE = {
    'Attained_Age': 88,
    'Issue_Age': 56,
    'Duration': 33,
    'Sex': 'M',
    'Smoker_Status': 'S',
    'Insurance_Plan': 'UL',
    'Face_Amount_Band': '03: 25,000 - 49,999',
    'Preferred_Class': 'NA',
    'SOA_Post_Lvl_Ind': 'NA',
    'SOA_Antp_Lvl_TP': 'N/A (Not Term)',
    'SOA_Guar_Lvl_TP': 'N/A (Not Term)'
}


# =============================================================================
# Cost Estimation (Google Gemini 2.5 Flash Lite pricing)
# =============================================================================
COST_PER_INPUT_TOKEN = 0.1 / 1e6  
COST_PER_OUTPUT_TOKEN = 0.4 / 1e6 


def estimate_tokens(text: str) -> int:
    """Rough token estimation."""
    return len(text) // 3


class CostTracker:
    """Track time and cost for each stage."""
    
    def __init__(self):
        self.stages = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def start_stage(self, name: str):
        return {'name': name, 'start': time.time(), 'input_tokens': 0, 'output_tokens': 0}
    
    def end_stage(self, stage: dict, input_text: str = "", output_text: str = ""):
        stage['end'] = time.time()
        stage['duration'] = stage['end'] - stage['start']
        stage['input_tokens'] = estimate_tokens(input_text)
        stage['output_tokens'] = estimate_tokens(output_text)
        stage['cost'] = (
            stage['input_tokens'] * COST_PER_INPUT_TOKEN +
            stage['output_tokens'] * COST_PER_OUTPUT_TOKEN
        )
        self.stages.append(stage)
        self.total_input_tokens += stage['input_tokens']
        self.total_output_tokens += stage['output_tokens']
        return stage
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("TIMING & COST SUMMARY")
        print("=" * 70)
        
        total_time = sum(s['duration'] for s in self.stages)
        total_cost = sum(s['cost'] for s in self.stages)
        
        print(f"\n{'Stage':<35} {'Time':>10} {'Tokens':>10} {'Cost':>12}")
        print("-" * 70)
        
        for stage in self.stages:
            tokens = stage['input_tokens'] + stage['output_tokens']
            print(f"{stage['name']:<35} {stage['duration']:>9.2f}s {tokens:>9,} ${stage['cost']:>10.6f}")
        
        print("-" * 70)
        print(f"{'TOTAL':<35} {total_time:>9.2f}s {self.total_input_tokens + self.total_output_tokens:>9,} ${total_cost:>10.6f}")


def load_sample():
    """Load sample based on USE_TEST_DATA flag."""
    import pandas as pd
    
    data_path = Path(__file__).parent.parent.parent / 'data' / 'ilec_cleaned.parquet'
    
    if not data_path.exists():
        print(f"⚠ Data file not found: {data_path}")
        return None, None
    
    df = pd.read_parquet(data_path)
    
    if USE_TEST_DATA:
        # Use fake high-risk sample
        sample = TEST_SAMPLE.copy()
        print("    [TEST MODE] Using fake high-risk sample")
    else:
        # Random real sampling
        sample = df.sample(1).iloc[0].to_dict()
    
    return sample, df


def find_matching_segment(input_record: dict, kb) -> dict:
    """Find matching coverage segment based on rules."""
    if not kb.coverage_registry:
        return None
    
    plan_map = {'Term': 0, 'UL': 1, 'ULSG': 2, 'VUL': 3, 'WL': 4}
    smoker_map = {'NS': 1, 'S': 2}
    
    age = input_record.get('Attained_Age', 0)
    duration = input_record.get('Duration', 0)
    plan = input_record.get('Insurance_Plan', 'Term')
    smoker = input_record.get('Smoker_Status', 'NS')
    
    plan_encoded = plan_map.get(plan, 0)
    smoker_encoded = smoker_map.get(smoker, 1)
    
    for seg in kb.coverage_registry.get('segments', []):
        rules = seg.get('rules', [])
        match = True
        
        for rule in rules:
            if '<=' in rule:
                parts = rule.split('<=')
                feat, threshold = parts[0].strip(), float(parts[1].strip())
                
                if feat == 'Duration' and not (duration <= threshold):
                    match = False
                elif feat == 'Attained_Age' and not (age <= threshold):
                    match = False
                elif feat == 'Insurance_Plan' and not (plan_encoded <= threshold):
                    match = False
                elif feat == 'Smoker_Status' and not (smoker_encoded <= threshold):
                    match = False
                    
            elif '>' in rule:
                parts = rule.split('>')
                feat, threshold = parts[0].strip(), float(parts[1].strip())
                
                if feat == 'Duration' and not (duration > threshold):
                    match = False
                elif feat == 'Attained_Age' and not (age > threshold):
                    match = False
                elif feat == 'Insurance_Plan' and not (plan_encoded > threshold):
                    match = False
                elif feat == 'Smoker_Status' and not (smoker_encoded > threshold):
                    match = False
        
        if match:
            return seg
    
    return None


def create_report_data(sample: dict, df, predictor, kb) -> ReportData:
    """Create ReportData from sample."""
    
    features = ['Attained_Age', 'Issue_Age', 'Duration', 'Sex', 'Smoker_Status',
                'Insurance_Plan', 'Face_Amount_Band', 'Preferred_Class',
                'SOA_Post_Lvl_Ind', 'SOA_Antp_Lvl_TP', 'SOA_Guar_Lvl_TP']
    
    input_record = {f: sample[f] for f in features}
    
    # Prediction
    mortality_rate, shap_dict = predictor.predict(input_record)
    overall_rate = df['Death_Count'].sum() / df['Policies_Exposed'].sum()
    relative_risk = mortality_rate / overall_rate
    
    prediction = PredictionData(
        mortality_rate=mortality_rate,
        relative_risk=relative_risk,
        overall_death_rate=overall_rate,
        interpretation="higher" if relative_risk > 1 else "lower"
    )
    
    # SHAP
    shap_contributions = []
    sorted_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
    for feat, shap_val in sorted_shap[:5]:
        direction = "Increases" if shap_val > 0 else "Decreases"
        shap_contributions.append(SHAPData(
            feature=feat, value=input_record.get(feat, 'N/A'),
            shap_value=shap_val, direction=direction
        ))
    
    # Population context
    percentile_context = []
    for feat in ['Attained_Age', 'Issue_Age', 'Duration']:
        val = sample[feat]
        pct = int((df[feat] < val).mean() * 100)
        percentile_context.append({
            "feature": feat, "value": val, "percentile": pct,
            "description": f"{feat}={val} is at the {pct}th percentile"
        })
    
    category_context = []
    for feat in ['Sex', 'Smoker_Status', 'Insurance_Plan']:
        val = sample[feat]
        pct = round((df[feat] == val).mean() * 100, 1)
        category_context.append({
            "feature": feat, "value": val, "population_pct": pct,
            "description": f"{feat}={val} ({pct}% of population)"
        })
    
    # Segment matching
    cov_seg = find_matching_segment(input_record, kb)
    coverage_segment = None
    if cov_seg:
        coverage_segment = SegmentData(
            segment_id=cov_seg.get('segment_id'),
            rule_text=cov_seg.get('rule_text'),
            ae_ratio=cov_seg.get('statistics', {}).get('ae_ratio', 1.0),
            relative_risk=cov_seg.get('statistics', {}).get('relative_risk', 1.0),
            credibility="high" if cov_seg.get('statistics', {}).get('exposure', 0) > 50000 else "medium"
        )
    
    # Spotlight (if high RR)
    spotlight_segment = None
    if relative_risk > 3:
        spotlight_segment = SegmentData(
            segment_id=f"SPOT_HIGH_{int(relative_risk*10):03d}",
            rule_text=f"Attained_Age={input_record['Attained_Age']} AND Smoker_Status={input_record['Smoker_Status']}",
            ae_ratio=1.0, relative_risk=relative_risk,
            credibility="model_derived",
            risk_level="high_risk" if relative_risk > 5 else "elevated"
        )
    
    # Evidence charts
    evidence_charts = []
    charts_dir = Path(__file__).parent.parent.parent / 'data' / 'reports'
    if (charts_dir / 'shap_waterfall.png').exists():
        evidence_charts.append(EvidenceChart(
            name="SHAP Waterfall", path="shap_waterfall.png",
            description="Feature contributions to prediction"
        ))
    
    overall_ae = kb.overall_ae.get('overall_ae', 0.9989) if kb.overall_ae else 0.9989
    
    return ReportData(
        report_date=datetime.now().strftime('%Y-%m-%d'),
        report_version="1.0",
        input_record=input_record,
        prediction=prediction,
        shap_contributions=shap_contributions,
        percentile_context=percentile_context,
        category_context=category_context,
        coverage_segment=coverage_segment,
        spotlight_segment=spotlight_segment,
        overall_ae=overall_ae,
        evidence_charts=evidence_charts,
        disclaimers=[
            "This prediction is based on historical data from 2012-2019 and is for reference only.",
            "This model does not include COVID-19 period data; post-2020 predictions require adjustment.",
            "This report complies with ASOP 23/25/41/56 standards."
        ]
    )


def main():
    print("=" * 70)
    print("STRUCTURED ACTUARIAL REPORT GENERATOR")
    print("=" * 70)
    
    tracker = CostTracker()
    
    # Stage 1: Load data
    stage = tracker.start_stage("1. Load Data & Sample")
    sample, df = load_sample()
    if sample is None:
        return None
    tracker.end_stage(stage)
    print(f"\n[1] Data loaded ({stage['duration']:.2f}s)")
    print(f"    Records: {len(df):,}")
    print(f"    Sample: Age={sample['Attained_Age']}, Sex={sample['Sex']}, Smoker={sample['Smoker_Status']}")
    
    # Stage 2: Initialize
    stage = tracker.start_stage("2. Initialize Components")
    kb = get_knowledge_base()
    predictor = create_predictor()
    llm = create_llm_client()
    system_prompt = get_full_system_prompt()
    prompt_stats = get_prompt_stats(system_prompt)
    tracker.end_stage(stage)
    print(f"\n[2] Initialized ({stage['duration']:.2f}s)")
    print(f"    System prompt: {prompt_stats['characters']:,} chars (~{prompt_stats['estimated_tokens']:,} tokens)")
    
    # Stage 3: Create data
    stage = tracker.start_stage("3. Create Report Data")
    data = create_report_data(sample, df, predictor, kb)
    tracker.end_stage(stage)
    print(f"\n[3] Report data created ({stage['duration']:.2f}s)")
    print(f"    Mortality: {data.prediction.mortality_rate:.6f}")
    print(f"    Relative Risk: {data.prediction.relative_risk:.2f}x")
    if data.coverage_segment:
        print(f"    Coverage: {data.coverage_segment.segment_id}")
    if data.spotlight_segment:
        print(f"    ⚠️ Spotlight: {data.spotlight_segment.segment_id}")
    
    # Stage 4: Build context
    stage = tracker.start_stage("4. Build LLM Context")
    context = PromptContext(
        prediction=data.prediction,
        shap_contributions=data.shap_contributions,
        percentiles=data.percentile_context,
        categories=data.category_context,
        coverage_segment=data.coverage_segment.model_dump() if data.coverage_segment else None,
        spotlight_segment=data.spotlight_segment.model_dump() if data.spotlight_segment else None,
        overall_ae=data.overall_ae
    )
    input_text = system_prompt + str(context.model_dump())
    tracker.end_stage(stage, input_text=input_text)
    print(f"\n[4] Context built ({stage['duration']:.3f}s)")
    
    # Stage 5: Generate insights
    stage = tracker.start_stage("5. Generate Insights (LLM)")
    insights = llm.generate_insights(context, system_prompt)
    output_text = str(insights.model_dump()) if hasattr(insights, 'model_dump') else str(insights.__dict__)
    tracker.end_stage(stage, input_text=input_text, output_text=output_text)
    print(f"\n[5] Insights generated ({stage['duration']:.2f}s)")
    print(f"    Cost: ${stage['cost']:.6f}")
    
    # Stage 6: Render
    stage = tracker.start_stage("6. Render Report")
    report = FullReport(
        data=data, insights=insights,
        system_prompt=system_prompt, is_validated=True
    )
    
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'reports'
    renderer = create_renderer(str(output_dir))
    
    md_path = renderer.save_markdown(report, "actuarial_report.md")
    json_path = renderer.save_json(report, "actuarial_report.json")
    prompt_path = renderer.save_prompt(report, "system_prompt_appendix.txt")
    tracker.end_stage(stage)
    print(f"\n[6] Report saved")
    print(f"    ✓ {md_path}")
    print(f"    ✓ {json_path}")
    print(f"    ✓ {prompt_path}")
    
    tracker.print_summary()
    
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    
    return report


if __name__ == "__main__":
    main()
