# -*- coding: utf-8 -*-
"""
Report Renderer (English)

Renders structured report data to Markdown and PDF formats.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime
import json

from .schemas import FullReport, ReportData, ActuarialInsights


class ReportRenderer:
    """
    Renders structured report to various output formats.
    
    Combines fixed data (tables, charts, disclaimers) with 
    LLM-generated insights into a complete actuarial report.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path('.')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def render_markdown(self, report: FullReport) -> str:
        """Render complete report as Markdown."""
        data = report.data
        insights = report.insights
        
        sections = []
        
        # =====================================================================
        # Header
        # =====================================================================
        sections.append(f"""# Mortality Prediction Analysis Report

**Report Date**: {data.report_date}  
**Version**: {data.report_version}  

---
""")
        
        # =====================================================================
        # 1. Executive Summary (LLM-generated)
        # =====================================================================
        sections.append(f"""## 1. Executive Summary

{insights.summary}

---
""")
        
        # =====================================================================
        # 2. Prediction Results (Fixed Data)
        # =====================================================================
        sections.append(f"""## 2. Prediction Results

| Metric | Value | Description |
|:-------|:------|:------------|
| Predicted Mortality Rate | {data.prediction.mortality_rate:.6f} | Expected deaths per exposure-year |
| Relative Risk (RR) | {data.prediction.relative_risk:.2f}x | Relative to overall average |
| Overall Average Rate | {data.prediction.overall_death_rate:.6f} | Reference baseline |

**Risk Interpretation**: {insights.risk_interpretation}

---
""")
        
        # =====================================================================
        # 3. SHAP Analysis (Fixed table + LLM explanations)
        # =====================================================================
        shap_table = "| Feature | Value | SHAP Contribution | Direction |\n|:--------|:------|:------------------|:----------|\n"
        for s in data.shap_contributions[:5]:
            sign = "+" if s.shap_value > 0 else ""
            direction = "Increases" if s.shap_value > 0 else "Decreases"
            shap_table += f"| {s.feature} | {s.value} | {sign}{s.shap_value:.4f} | {direction} |\n"
        
        shap_explanations = ""
        for exp in insights.shap_explanations:
            shap_explanations += f"- **{exp.feature}** ({exp.value}): {exp.explanation}\n"
        
        sections.append(f"""## 3. Risk Factor Analysis (SHAP)

### 3.1 Feature Contribution Table
{shap_table}

### 3.2 Feature Explanations
{shap_explanations}

---
""")
        
        # =====================================================================
        # 4. Population Context (Fixed Data)
        # =====================================================================
        percentile_text = ""
        for p in data.percentile_context:
            percentile_text += f"- {p.get('description', p.get('feature'))}\n"
        
        category_text = ""
        for c in data.category_context:
            category_text += f"- {c.get('description', c.get('feature'))}\n"
        
        sections.append(f"""## 4. Population Context

### 4.1 Numerical Feature Percentiles
{percentile_text}

### 4.2 Categorical Feature Distribution
{category_text}

---
""")
        
        # =====================================================================
        # 5. Segment Analysis (Fixed + LLM insight)
        # =====================================================================
        segment_section = "## 5. Segment Analysis\n\n"
        
        if data.coverage_segment:
            seg = data.coverage_segment
            segment_section += f"""### 5.1 Coverage Segment (General Classification)

This policy belongs to the following risk segment based on key characteristics:

| Metric | Value |
|:-------|:------|
| Segment ID | {seg.segment_id} |
| Classification Rule | {seg.rule_text} |
| A/E Ratio | {seg.ae_ratio:.3f} |
| Relative Risk | {seg.relative_risk:.3f}x |
| Credibility | {seg.credibility} |

"""
        
        if data.spotlight_segment:
            seg = data.spotlight_segment
            segment_section += f"""### 5.2 ⚠️ Spotlight Alert (Anomaly Detection)

> **Note**: Spotlight segments identify statistically anomalous risk groups. This is an **additional warning**, not a contradiction to the Coverage segment.

| Metric | Value |
|:-------|:------|
| Segment ID | {seg.segment_id} |
| Classification Rule | {seg.rule_text} |
| Risk Level | {seg.risk_level} |
| Relative Risk | {seg.relative_risk:.2f}x |

"""
        
        if insights.segment_insight:
            segment_section += f"**Segment Interpretation**: {insights.segment_insight}\n"
        
        segment_section += "\n---\n"
        sections.append(segment_section)
        
        # =====================================================================
        # 6. Model Calibration (Fixed Data + LLM note)
        # =====================================================================
        sections.append(f"""## 6. Model Calibration

| Metric | Value |
|:-------|:------|
| Overall A/E Ratio | {data.overall_ae:.4f} |

{insights.calibration_note}

---
""")
        
        # =====================================================================
        # 7. Evidence Charts (Fixed paths)
        # =====================================================================
        if data.evidence_charts:
            chart_section = "## 7. Evidence Charts\n\n"
            for chart in data.evidence_charts:
                chart_section += f"### {chart.name}\n"
                chart_section += f"![{chart.name}]({chart.path})\n\n"
                chart_section += f"*{chart.description}*\n\n"
            chart_section += "---\n"
            sections.append(chart_section)
        
        # =====================================================================
        # 8. Recommendations (LLM-generated)
        # =====================================================================
        if insights.recommendations:
            rec_section = "## 8. Recommendations\n\n"
            for i, rec in enumerate(insights.recommendations, 1):
                rec_section += f"{i}. {rec}\n"
            rec_section += "\n---\n"
            sections.append(rec_section)
        
        # =====================================================================
        # 9. Disclaimers (Fixed)
        # =====================================================================
        disclaimer_section = "## 9. Disclaimers\n\n"
        for disc in data.disclaimers:
            disclaimer_section += f"> {disc}\n\n"
        sections.append(disclaimer_section)
        
        # =====================================================================
        # 10. Appendix: System Prompt (for transparency)
        # =====================================================================
        if report.system_prompt:
            sections.append(f"""
---

## Appendix A: System Prompt Used

<details>
<summary>Click to expand full system prompt ({len(report.system_prompt)} characters)</summary>

```
{report.system_prompt}
```

</details>
""")
        
        # =====================================================================
        # Footer
        # =====================================================================
        sections.append(f"""
---

*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*Compliant with ASOP 23/25/41/56 standards*
""")
        
        return "\n".join(sections)
    
    def save_prompt(self, report: FullReport, filename: str) -> str:
        """Save the system prompt to a text file."""
        if not report.system_prompt:
            return ""
        
        path = Path(self.output_dir) / filename
        with open(path, 'w', encoding='utf-8') as f:
            f.write(report.system_prompt)
        return str(path)
    
    def save_markdown(self, report: FullReport, filename: str = "report.md") -> Path:
        """Save report as Markdown file."""
        md_content = self.render_markdown(report)
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return output_path
    
    def render_pdf(self, report: FullReport, filename: str = "report.pdf") -> Optional[Path]:
        """
        Render report as PDF.
        
        Requires weasyprint: pip install weasyprint
        """
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            print("⚠ weasyprint not installed. Install with: pip install weasyprint")
            return None
        
        # Convert Markdown to HTML
        md_content = self.render_markdown(report)
        
        try:
            import markdown
            html_body = markdown.markdown(
                md_content, 
                extensions=['tables', 'fenced_code']
            )
        except ImportError:
            # Fallback: basic conversion
            html_body = f"<pre>{md_content}</pre>"
        
        # Wrap in HTML template
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        blockquote {{ 
            background: #f9f9f9; 
            border-left: 4px solid #e74c3c; 
            padding: 10px 20px; 
            margin: 10px 0;
        }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>
"""
        
        output_path = self.output_dir / filename
        HTML(string=html_content).write_pdf(output_path)
        return output_path
    
    def save_json(self, report: FullReport, filename: str = "report.json") -> Path:
        """Save report as JSON for API consumption."""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.model_dump(), f, indent=2, ensure_ascii=False, default=str)
        return output_path


def create_renderer(output_dir: Optional[str] = None) -> ReportRenderer:
    """Factory function for ReportRenderer."""
    return ReportRenderer(output_dir)
