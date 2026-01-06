# -*- coding: utf-8 -*-
"""
Report Generator CLI / Demo

Usage:
    python -m report_generator.main

Demonstrates the complete report generation pipeline with timing.
"""

import json
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def demo_report():
    """Generate a demo report with sample data and timing."""
    from report_generator import create_generator
    
    print("=" * 70)
    print("MORTALITY REPORT GENERATOR - DEMO")
    print("=" * 70)
    
    timings = {}
    
    # =========================================================================
    # Stage 1: Initialize Generator
    # =========================================================================
    print("\n[Stage 1] Initializing generator...")
    start = time.time()
    
    kb_path = Path(__file__).parent.parent.parent / 'knowledge_base'
    generator = create_generator(str(kb_path), load_model=False, load_llm=True)
    
    timings['init'] = time.time() - start
    print(f"  ✓ Completed in {timings['init']:.2f}s")
    
    # =========================================================================
    # Stage 2: Prepare Input
    # =========================================================================
    print("\n[Stage 2] Preparing input...")
    start = time.time()
    
    sample_record = {
        "Attained_Age": 75,
        "Issue_Age": 55,
        "Duration": 20,
        "Sex": "M",
        "Smoker_Status": "S",
        "Insurance_Plan": "Term",
        "Face_Amount_Band": "05: 100,000 - 249,999",
        "Preferred_Class": "2",
        "SOA_Post_Lvl_Ind": "NA",
        "SOA_Antp_Lvl_TP": "N/A (Not Term)",
        "SOA_Guar_Lvl_TP": "N/A (Not Term)"
    }
    
    prediction = 0.065
    shap_values = {
        "Attained_Age": 0.0352,
        "Duration": 0.0183,
        "Smoker_Status": 0.0156,
        "Issue_Age": 0.0089,
        "Face_Amount_Band": -0.0023,
        "Insurance_Plan": -0.0012,
        "Sex": 0.0008,
        "Preferred_Class": -0.0005,
        "SOA_Post_Lvl_Ind": 0.0001,
        "SOA_Antp_Lvl_TP": 0.0000,
        "SOA_Guar_Lvl_TP": 0.0000
    }
    
    coverage_leaf = 15
    spotlight_leaf = 96
    
    timings['prepare'] = time.time() - start
    print(f"  ✓ Completed in {timings['prepare']:.4f}s")
    
    print("\n" + "-" * 70)
    print("INPUT RECORD")
    print("-" * 70)
    print(json.dumps(sample_record, indent=2, ensure_ascii=False))
    
    # =========================================================================
    # Stage 3: Generate Structured Report
    # =========================================================================
    print("\n[Stage 3] Generating structured report...")
    start = time.time()
    
    report = generator.generate(
        input_record=sample_record,
        prediction=prediction,
        shap_values=shap_values,
        coverage_leaf_id=coverage_leaf,
        spotlight_leaf_id=spotlight_leaf
    )
    
    timings['structured'] = time.time() - start
    print(f"  ✓ Completed in {timings['structured']:.4f}s")
    
    # =========================================================================
    # Print System Prompt (Full)
    # =========================================================================
    print("\n" + "=" * 70)
    print("SYSTEM PROMPT (Full)")
    print("=" * 70)
    print(report['prompts']['system'])
    
    # =========================================================================
    # Print User Prompt
    # =========================================================================
    print("\n" + "=" * 70)
    print("USER PROMPT")
    print("=" * 70)
    print(report['prompts']['user'])
    
    # =========================================================================
    # Stage 4: Call LLM
    # =========================================================================
    print("\n[Stage 4] Calling LLM to generate report...")
    start = time.time()
    
    if generator.llm:
        llm_response = generator.llm.generate(
            report['prompts']['system'],
            report['prompts']['user']
        )
        report['llm_report'] = llm_response
    else:
        report['llm_report'] = "[LLM not available]"
    
    timings['llm'] = time.time() - start
    print(f"  ✓ Completed in {timings['llm']:.2f}s")
    
    # =========================================================================
    # Print LLM Report
    # =========================================================================
    print("\n" + "=" * 70)
    print("LLM GENERATED REPORT")
    print("=" * 70)
    print(report['llm_report'])
    
    # =========================================================================
    # Print Summary Statistics
    # =========================================================================
    print("\n" + "=" * 70)
    print("PREDICTION SUMMARY")
    print("=" * 70)
    print(json.dumps(report['prediction'], indent=2, ensure_ascii=False))
    
    if report.get('spotlight_alert'):
        print("\n⚠️  SPOTLIGHT ALERT:")
        seg = report['spotlight_alert']
        print(f"   Segment: {seg.get('segment_id')}")
        print(f"   Risk Level: {seg.get('risk_level')}")
        print(f"   Relative Risk: {seg.get('statistics', {}).get('relative_risk')}x")
    
    # =========================================================================
    # Timing Summary
    # =========================================================================
    print("\n" + "=" * 70)
    print("TIMING SUMMARY")
    print("=" * 70)
    total = sum(timings.values())
    for stage, t in timings.items():
        pct = (t / total) * 100
        print(f"  {stage:15s}: {t:6.2f}s ({pct:5.1f}%)")
    print(f"  {'TOTAL':15s}: {total:6.2f}s")
    
    # =========================================================================
    # Save Report
    # =========================================================================
    output_dir = Path(__file__).parent.parent.parent / 'data'
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'sample_report.json'
    
    # Add timing to report
    report['timings'] = timings
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n✓ Full report saved to: {output_path}")
    
    return report


if __name__ == "__main__":
    demo_report()
