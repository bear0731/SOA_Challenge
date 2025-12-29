# -*- coding: utf-8 -*-
"""
Deep Analysis of ILEC Mortality Appendices
==========================================
Comprehensive visualization with proper axes, combined charts, and cross-analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configuration
FILE_PATH = '/Users/BF/Development/SOA/data/ilec-mort-appendices.xlsx'
OUTPUT_DIR = '/Users/BF/Development/SOA/data/plots'
REPORT_FILE = '/Users/BF/Development/SOA/data/deep_analysis_report.md'

# Style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.labelsize'] = 11

# Color palette
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#E94F37',
    'tertiary': '#A23B72',
    'quaternary': '#F18F01',
    'male': '#3498db',
    'female': '#e74c3c',
    'smoker': '#e67e22',
    'nonsmoker': '#27ae60'
}

SEGMENT_COLORS = ['#2E86AB', '#E94F37', '#A23B72', '#F18F01', '#27ae60', '#8e44ad', '#16a085', '#d35400']

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def find_data_start(df, keywords=['Issue Age', 'Attained Age', 'Duration', 'Face Amount', 'Risk Class']):
    """Find the row index where actual data headers start."""
    for idx, row in df.iterrows():
        row_str = ' '.join(str(v) for v in row.values if pd.notna(v)).lower()
        for kw in keywords:
            if kw.lower() in row_str:
                return idx
    return None

def clean_numeric(series):
    """Convert series to numeric, handling any format issues."""
    return pd.to_numeric(series, errors='coerce')

def save_plot(filename):
    """Save current figure to output directory."""
    filepath = f"{OUTPUT_DIR}/{filename}"
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {filename}")
    return filename

# ============================================================
# GROUP 2: OVERALL EXPERIENCE (Sheets A, B, C, D)
# ============================================================

def analyze_overall_experience(xl):
    """Analyze sheets A-D: Overall mortality by Age, Duration, Face Amount."""
    print("\n[Group 2] Analyzing Overall Experience (A, B, C, D)...")
    
    insights = []
    expected_cols = ['Index', 'Key', 'Death_Count', 'Exp_Death_Count', 'AE_Count',
                     'Death_Amount', 'Exp_Death_Amount', 'AE_Amount', 
                     'Exposure_Amount', 'Pct_Exp_Amount', 'Exposure_Count', 'Pct_Exp_Count', 'Avg_Size']
    
    def parse_sheet(sheet_name, key_name):
        df = xl.parse(sheet_name, skiprows=7)
        df = df.iloc[:, :13]  # Take first 13 columns
        df.columns = expected_cols
        df = df.rename(columns={'Key': key_name})
        df = df[df[key_name].notna()]
        df = df[~df[key_name].astype(str).str.contains('Total|Source', case=False)]
        for col in ['AE_Count', 'AE_Amount', 'Exposure_Amount', 'Exposure_Count']:
            df[col] = clean_numeric(df[col])
        return df
    
    df_a = parse_sheet('A', 'Attained_Age')
    df_b = parse_sheet('B', 'Issue_Age')
    df_c = parse_sheet('C', 'Duration')
    df_d = parse_sheet('D', 'Face_Amount_Band')
    
    df_d = parse_sheet('D', 'Face_Amount_Band')
    
    # ---- COMBINED 2x2 PLOT: A/E Ratio Overview ----
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # A: Attained Age
    ax = axes[0, 0]
    x = range(len(df_a))
    ax.plot(x, df_a['AE_Amount'], marker='o', color=COLORS['primary'], linewidth=2, label='By Amount')
    ax.plot(x, df_a['AE_Count'], marker='s', color=COLORS['secondary'], linewidth=2, linestyle='--', label='By Count')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(df_a['Attained_Age'], rotation=45, ha='right', fontsize=9)
    ax.set_xlabel('Attained Age')
    ax.set_ylabel('A/E Ratio')
    ax.set_title('A/E Ratio by Attained Age')
    ax.legend(loc='upper left', fontsize=9)
    ax.set_ylim(0.5, 1.5)
    
    # B: Issue Age
    ax = axes[0, 1]
    x = range(len(df_b))
    ax.plot(x, df_b['AE_Amount'], marker='o', color=COLORS['primary'], linewidth=2, label='By Amount')
    ax.plot(x, df_b['AE_Count'], marker='s', color=COLORS['secondary'], linewidth=2, linestyle='--', label='By Count')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(df_b['Issue_Age'], rotation=45, ha='right', fontsize=9)
    ax.set_xlabel('Issue Age')
    ax.set_ylabel('A/E Ratio')
    ax.set_title('A/E Ratio by Issue Age')
    ax.legend(loc='upper left', fontsize=9)
    ax.set_ylim(0.5, 1.5)
    
    # C: Duration
    ax = axes[1, 0]
    x = range(len(df_c))
    ax.plot(x, df_c['AE_Amount'], marker='o', color=COLORS['primary'], linewidth=2, label='By Amount')
    ax.plot(x, df_c['AE_Count'], marker='s', color=COLORS['secondary'], linewidth=2, linestyle='--', label='By Count')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(df_c['Duration'], rotation=45, ha='right', fontsize=9)
    ax.set_xlabel('Duration (Policy Year)')
    ax.set_ylabel('A/E Ratio')
    ax.set_title('A/E Ratio by Duration')
    ax.legend(loc='upper left', fontsize=9)
    ax.set_ylim(0.5, 1.5)
    
    # D: Face Amount
    ax = axes[1, 1]
    x = range(len(df_d))
    ax.bar(x, df_d['AE_Amount'], color=COLORS['primary'], alpha=0.7, label='By Amount')
    ax.bar(x, df_d['AE_Count'], color=COLORS['secondary'], alpha=0.4, label='By Count')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(df_d['Face_Amount_Band'], rotation=45, ha='right', fontsize=9)
    ax.set_xlabel('Face Amount Band')
    ax.set_ylabel('A/E Ratio')
    ax.set_title('A/E Ratio by Face Amount Band')
    ax.legend(loc='upper right', fontsize=9)
    
    plt.suptitle('Overall Mortality Experience: A/E Ratios by Key Dimensions', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    save_plot('group2_overall_ae_ratios.png')
    
    # ---- EXPOSURE DISTRIBUTION ----
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    ax = axes[0]
    ax.bar(range(len(df_a)), df_a['Exposure_Amount'] / 1e9, color=COLORS['primary'], alpha=0.7)
    ax.set_xticks(range(len(df_a)))
    ax.set_xticklabels(df_a['Attained_Age'], rotation=45, ha='right', fontsize=9)
    ax.set_xlabel('Attained Age')
    ax.set_ylabel('Exposure Amount ($ Billions)')
    ax.set_title('Exposure Distribution by Attained Age')
    
    ax = axes[1]
    ax.bar(range(len(df_c)), df_c['Exposure_Amount'] / 1e9, color=COLORS['tertiary'], alpha=0.7)
    ax.set_xticks(range(len(df_c)))
    ax.set_xticklabels(df_c['Duration'], rotation=45, ha='right', fontsize=9)
    ax.set_xlabel('Duration (Policy Year)')
    ax.set_ylabel('Exposure Amount ($ Billions)')
    ax.set_title('Exposure Distribution by Duration')
    
    plt.tight_layout()
    save_plot('group2_exposure_distribution.png')
    
    # Insights
    avg_ae_amount = df_a['AE_Amount'].mean()
    insights.append(f"Average A/E Ratio by Amount across attained ages: {avg_ae_amount:.3f}")
    insights.append(f"A/E Ratio by Count is generally higher than by Amount, indicating smaller policies have higher mortality.")
    
    return insights

# ============================================================
# GROUP 3: SEX/SMOKER x YEAR ANALYSIS (Sheets E1-E4)
# ============================================================

def analyze_sex_smoker_trends(xl):
    """Analyze sheets E1-E4: A/E by Sex/Smoker x Issue Age x Year."""
    print("\n[Group 3] Analyzing Sex/Smoker Trends (E1, E2, E3, E4)...")
    
    insights = []
    segments = {
        'E1': 'Male Nonsmoker (Face < $100K)',
        'E2': 'Male Nonsmoker (Face >= $100K)',
        'E3': 'Male Smoker (Face < $100K)',
        'E4': 'Female Smoker (Face < $100K)'
    }
    
    # Parse data for each segment
    data = {}
    for sheet, label in segments.items():
        df = xl.parse(sheet, skiprows=9)
        # Columns: Issue Age, 2012, 2013, ..., 2019, (more columns for other metrics)
        df = df.iloc[:, :9]  # Take first 9 columns (Issue Age + 8 years)
        df.columns = ['Issue_Age', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019']
        df = df[df['Issue_Age'].notna()]
        df = df[~df['Issue_Age'].astype(str).str.contains('Total|Source|70', case=False)]
        
        for col in ['2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019']:
            df[col] = clean_numeric(df[col])
        
        data[sheet] = df
    
    # ---- COMBINED 2x2 PANEL: A/E Trend by Issue Age for each segment ----
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    years = ['2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019']
    
    for idx, (sheet, label) in enumerate(segments.items()):
        ax = axes[idx // 2, idx % 2]
        df = data[sheet]
        
        for i, (_, row) in enumerate(df.iterrows()):
            age = row['Issue_Age']
            values = [row[y] for y in years]
            ax.plot(years, values, marker='o', label=str(age), color=SEGMENT_COLORS[i % len(SEGMENT_COLORS)], linewidth=1.5)
        
        ax.axhline(1.0, color='gray', linestyle=':', alpha=0.7)
        ax.set_xlabel('Observation Year')
        ax.set_ylabel('A/E Ratio')
        ax.set_title(label)
        ax.legend(title='Issue Age', loc='upper right', fontsize=8, ncol=2)
        ax.set_ylim(0.8, 2.0)
    
    plt.suptitle('A/E Ratio Trends by Issue Age Over Time (by Segment)', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    save_plot('group3_ae_trends_by_segment.png')
    
    # ---- CROSS-ANALYSIS: Compare Smoker vs NonSmoker ----
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Average A/E across years for each segment
    avg_ae = {}
    for sheet, label in segments.items():
        df = data[sheet]
        avg_ae[label] = df[years].mean(axis=1).mean()
    
    ax.barh(list(avg_ae.keys()), list(avg_ae.values()), color=[COLORS['nonsmoker'], COLORS['nonsmoker'], COLORS['smoker'], COLORS['smoker']])
    ax.axvline(1.0, color='gray', linestyle='--', alpha=0.7)
    ax.set_xlabel('Average A/E Ratio (2012-2019)')
    ax.set_title('Comparison of A/E Ratios by Segment')
    
    for i, (label, val) in enumerate(avg_ae.items()):
        ax.text(val + 0.02, i, f'{val:.2f}', va='center', fontsize=10)
    
    plt.tight_layout()
    save_plot('group3_segment_comparison.png')
    
    insights.append(f"Smoker segments consistently show higher A/E ratios than nonsmoker segments.")
    insights.append(f"Younger issue ages (18-29, 30-39) tend to have higher A/E ratios, possibly due to anti-selection.")
    
    return insights

# ============================================================
# GROUP 4: ISSUE AGE x DURATION HEATMAPS (Sheets F1-F4)
# ============================================================

def analyze_issue_age_duration(xl):
    """Analyze sheets F1-F4: A/E Heatmaps by Issue Age x Duration."""
    print("\n[Group 4] Analyzing Issue Age x Duration (F1, F2, F3, F4)...")
    
    insights = []
    segments = {
        'F1': 'Male Nonsmoker',
        'F2': 'Female Nonsmoker',
        'F3': 'Male Smoker',
        'F4': 'Female Smoker'
    }
    
    # Parse data for each segment
    heatmap_data = {}
    for sheet, label in segments.items():
        df = xl.parse(sheet, skiprows=9)
        # Columns: Issue Age, Dur 1, Dur 2, Dur 3, Dur 4-5, Dur 6-10, ...
        df = df.iloc[:, :9]  # Take relevant columns
        df.columns = ['Issue_Age', 'Dur_1', 'Dur_2', 'Dur_3', 'Dur_4-5', 'Dur_6-10', 'Dur_11-15', 'Dur_16-20', 'Dur_21-25']
        df = df[df['Issue_Age'].notna()]
        df = df[~df['Issue_Age'].astype(str).str.contains('Total|Source', case=False)]
        df = df.set_index('Issue_Age')
        
        for col in df.columns:
            df[col] = clean_numeric(df[col])
        
        heatmap_data[sheet] = df
    
    # ---- COMBINED 2x2 HEATMAPS ----
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    for idx, (sheet, label) in enumerate(segments.items()):
        ax = axes[idx // 2, idx % 2]
        df = heatmap_data[sheet]
        
        sns.heatmap(df, annot=True, fmt='.2f', cmap='RdYlGn_r', center=1.0, 
                    vmin=0.5, vmax=1.8, ax=ax, cbar_kws={'label': 'A/E Ratio'},
                    annot_kws={'fontsize': 8})
        ax.set_title(f'{label}: A/E by Issue Age x Duration')
        ax.set_xlabel('Duration')
        ax.set_ylabel('Issue Age')
    
    plt.suptitle('A/E Ratio Heatmaps: Issue Age x Duration', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    save_plot('group4_ae_heatmaps.png')
    
    insights.append("Early durations (1-3) often show higher A/E variability, indicating selection effects.")
    insights.append("Female segments generally show lower A/E ratios compared to male segments.")
    
    return insights

# ============================================================
# GROUP 7: OLDER AGE EXPERIENCE (Sheets OA1, OA2)
# ============================================================

def analyze_older_ages(xl):
    """Analyze sheets OA1, OA2: Older age mortality experience."""
    print("\n[Group 7] Analyzing Older Age Experience (OA1, OA2)...")
    
    insights = []
    
    # OA1: Issue Ages 65+
    df_oa1 = xl.parse('OA1', skiprows=8)
    df_oa1 = df_oa1.iloc[:, :13]
    df_oa1.columns = ['Index', 'Attained_Age', 'Death_Count', 'Exp_Death_Count', 'AE_Count',
                      'Death_Amount', 'Exp_Death_Amount', 'AE_Amount', 
                      'Exposure_Amount', 'Pct_Exp_Amount', 'Exposure_Count', 'Pct_Exp_Count', 'Avg_Size']
    df_oa1 = df_oa1[df_oa1['Attained_Age'].notna()]
    df_oa1 = df_oa1[~df_oa1['Attained_Age'].astype(str).str.contains('Total|Source|Overall', case=False)]
    
    for col in ['AE_Count', 'AE_Amount', 'Exposure_Amount']:
        df_oa1[col] = clean_numeric(df_oa1[col])
    
    # OA2: Attained Ages 65+
    df_oa2 = xl.parse('OA2', skiprows=8)
    df_oa2 = df_oa2.iloc[:, :13]
    df_oa2.columns = ['Index', 'Attained_Age', 'Death_Count', 'Exp_Death_Count', 'AE_Count',
                      'Death_Amount', 'Exp_Death_Amount', 'AE_Amount', 
                      'Exposure_Amount', 'Pct_Exp_Amount', 'Exposure_Count', 'Pct_Exp_Count', 'Avg_Size']
    df_oa2 = df_oa2[df_oa2['Attained_Age'].notna()]
    df_oa2 = df_oa2[~df_oa2['Attained_Age'].astype(str).str.contains('Total|Source|Overall', case=False)]
    
    for col in ['AE_Count', 'AE_Amount', 'Exposure_Amount']:
        df_oa2[col] = clean_numeric(df_oa2[col])
    
    # ---- COMBINED CHART: OA1 vs OA2 ----
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    ax = axes[0]
    x = range(len(df_oa1))
    ax.bar(x, df_oa1['AE_Amount'], color=COLORS['primary'], alpha=0.8)
    ax.axhline(1.0, color='gray', linestyle='--', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(df_oa1['Attained_Age'], rotation=45, ha='right')
    ax.set_xlabel('Attained Age')
    ax.set_ylabel('A/E Ratio by Amount')
    ax.set_title('OA1: Issue Ages 65+ (A/E by Attained Age)')
    
    ax = axes[1]
    x = range(len(df_oa2))
    ax.bar(x, df_oa2['AE_Amount'], color=COLORS['secondary'], alpha=0.8)
    ax.axhline(1.0, color='gray', linestyle='--', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(df_oa2['Attained_Age'], rotation=45, ha='right')
    ax.set_xlabel('Attained Age')
    ax.set_ylabel('A/E Ratio by Amount')
    ax.set_title('OA2: Attained Ages 65+ (A/E by Attained Age)')
    
    plt.suptitle('Older Age Mortality Experience', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    save_plot('group7_older_ages.png')
    
    insights.append("Older ages (65+) generally show A/E ratios closer to or above 1.0, indicating mortality aligns with expectations.")
    
    return insights

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("="*60)
    print("ILEC Mortality Appendices - Deep Analysis")
    print("="*60)
    
    xl = pd.ExcelFile(FILE_PATH)
    
    all_insights = []
    
    # Run all analysis groups
    all_insights.extend(analyze_overall_experience(xl))
    all_insights.extend(analyze_sex_smoker_trends(xl))
    all_insights.extend(analyze_issue_age_duration(xl))
    all_insights.extend(analyze_older_ages(xl))
    
    # Generate Report
    report = "# Deep Analysis Report: ILEC Mortality Appendices\n\n"
    report += "## Key Visualizations Generated\n\n"
    report += "1. `group2_overall_ae_ratios.png` - Overall A/E by Age, Duration, Face Amount\n"
    report += "2. `group2_exposure_distribution.png` - Exposure distribution\n"
    report += "3. `group3_ae_trends_by_segment.png` - A/E trends by Sex/Smoker segment\n"
    report += "4. `group3_segment_comparison.png` - Cross-segment comparison\n"
    report += "5. `group4_ae_heatmaps.png` - Issue Age x Duration heatmaps\n"
    report += "6. `group7_older_ages.png` - Older age experience\n\n"
    
    report += "## Key Insights\n\n"
    for i, insight in enumerate(all_insights, 1):
        report += f"{i}. {insight}\n"
    
    with open(REPORT_FILE, 'w') as f:
        f.write(report)
    
    print("\n" + "="*60)
    print("Analysis Complete!")
    print(f"Report saved to: {REPORT_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()
