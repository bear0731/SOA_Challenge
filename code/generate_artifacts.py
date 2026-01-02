import pandas as pd
import numpy as np
import json
import os

# Configuration
KB_DIR = "knowledge_base"
EXTERNAL_KB_DIR = f"{KB_DIR}/external_knowledge"
OUTPUT_EDA = f"{KB_DIR}/eda_summary.json"
OUTPUT_SHAP = f"{KB_DIR}/shap_analysis.json"
OUTPUT_SEGMENTS = f"{KB_DIR}/risk_segments.json"
OUTPUT_DICT = f"{KB_DIR}/data_dictionary.json"

def generate_synthetic_data(n_samples=10000):
    """Generates synthetic mortality data for demonstration."""
    np.random.seed(42)
    
    data = {
        'issue_age': np.random.randint(20, 80, n_samples),
        'duration': np.random.randint(1, 30, n_samples),
        'face_amount': np.random.exponential(500000, n_samples),
        'smoker_status': np.random.choice(['Smoker', 'Non-Smoker'], n_samples, p=[0.15, 0.85]),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'preferred_class': np.random.choice(['Super Pref', 'Classic Pref', 'Standard', 'Substandard'], n_samples, p=[0.1, 0.2, 0.5, 0.2]),
        'plan_type': np.random.choice(['Term 10', 'Term 20', 'Whole Life'], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Simulate Target (Mortality Rate) based on logic
    # Base rate
    base_rate = 0.001
    
    # Factors
    age_factor = np.exp((df['issue_age'] - 40) * 0.08)
    smoker_factor = np.where(df['smoker_status'] == 'Smoker', 2.5, 1.0)
    duration_factor = np.where(df['duration'] <= 2, 0.5, 1.0) # Selection effect
    pref_class_factor = df['preferred_class'].map({
        'Super Pref': 0.6, 'Classic Pref': 0.8, 'Standard': 1.0, 'Substandard': 1.5
    })
    
    df['expected_mortality'] = base_rate * age_factor * smoker_factor * duration_factor * pref_class_factor
    
    # Add some noise for "Actual"
    df['actual_mortality'] = df['expected_mortality'] * np.random.normal(1.0, 0.2, n_samples)
    
    # Simulate COVID impact (randomly increase mortality for older ages)
    covid_shock = (df['issue_age'] > 65) * np.random.choice([1.0, 1.3], n_samples, p=[0.7, 0.3])
    df['actual_mortality'] *= covid_shock
    
    df['actual_death'] = np.random.binomial(1, np.clip(df['actual_mortality'], 0, 1))
    
    return df

def generate_data_dictionary():
    """Generates Data Dictionary with definitions."""
    print("Generating Data Dictionary...")
    dictionary = {
        "issue_age": {"definition": "Age of the policyholder at policy issuance.", "type": "numerical", "unit": "years"},
        "duration": {"definition": "Number of years the policy has been in force.", "type": "numerical", "unit": "years"},
        "face_amount": {"definition": "The death benefit amount.", "type": "numerical", "unit": "USD"},
        "smoker_status": {"definition": "Tobacco usage status.", "type": "categorical", "values": ["Smoker", "Non-Smoker"]},
        "preferred_class": {"definition": "Underwriting health classification. 'Super Pref' is best health, 'Substandard' is high risk.", "type": "categorical"},
        "plan_type": {"definition": "Type of insurance product.", "type": "categorical"}
    }
    with open(OUTPUT_DICT, "w") as f:
        json.dump(dictionary, f, indent=2)

def generate_eda_summary(df):
    """Calculates distribution stats (Mean, Median, P90) and correlation."""
    print("Generating EDA Summary...")
    
    summary = {
        "numerical_features": {},
        "categorical_features": {}
    }
    
    # Numerical
    for col in ['issue_age', 'duration', 'face_amount']:
        summary["numerical_features"][col] = {
            "mean": float(df[col].mean()),
            "median": float(df[col].median()),
            "std": float(df[col].std()),
            "p90": float(df[col].quantile(0.9)),
            "corr_with_target": float(df[col].corr(df['actual_death']))
        }
        
    # Categorical
    for col in ['smoker_status', 'preferred_class', 'plan_type']:
        counts = df[col].value_counts(normalize=True).to_dict()
        avg_target = df.groupby(col)['actual_death'].mean().to_dict()
        summary["categorical_features"][col] = {
            "distribution": counts,
            "avg_target_by_group": avg_target
        }
        
    with open(OUTPUT_EDA, "w") as f:
        json.dump(summary, f, indent=2)

def generate_risk_segments(df):
    """Identifies High/Low risk cohorts and Model Interpretation."""
    print("Identifying Risk Segments...")
    
    # Mocking identification logic based on synthetic data logic
    segments = [
        {
            "id": "segment_high_risk_elderly",
            "name": "High Risk: Elderly Smokers",
            "condition": "issue_age > 65 and smoker_status == 'Smoker'",
            "ae_ratio": 1.25,
            "description": "Mortality significantly higher than base expectation (A/E 1.25). Likely influenced by COVID-19 impact in 2020-2021.",
            "key_drivers": ["issue_age", "smoker_status"],
            "avg_mortality": float(df[(df['issue_age'] > 65) & (df['smoker_status'] == 'Smoker')]['actual_death'].mean())
        },
        {
            "id": "segment_low_risk_young",
            "name": "Low Risk: Young Preferred",
            "condition": "issue_age < 35 and preferred_class == 'Super Pref'",
            "ae_ratio": 0.85,
            "description": "Very healthy cohort with extensive underwriting. Mortality is 15% better than standard expectation.",
            "key_drivers": ["issue_age", "preferred_class"],
            "avg_mortality": float(df[(df['issue_age'] < 35) & (df['preferred_class'] == 'Super Pref')]['actual_death'].mean())
        }
    ]
    
    with open(OUTPUT_SEGMENTS, "w") as f:
        json.dump(segments, f, indent=2)

def generate_shap_analysis(df):
    """Simulates SHAP values."""
    print("Generating SHAP Analysis...")
    
    # Mock Global Importance
    global_importance = {
        "issue_age": 0.45,
        "smoker_status": 0.25,
        "preferred_class": 0.15,
        "duration": 0.10,
        "face_amount": 0.03,
        "plan_type": 0.02
    }
    
    # Mock Local Example (Structure is key here for LLM)
    local_examples = [
        {
            "id": "sample_12345",
            "profile": "Age 75, Smoker",
            "shap_values": {
                "issue_age": {"value": 75, "shap": 0.03},
                "smoker_status": {"value": "Smoker", "shap": 0.015},
                "preferred_class": {"value": "Standard", "shap": 0.005},
                "base_value": 0.001
            }
        }
    ]
    
    data = {
        "global_feature_importance": global_importance,
        "local_examples": local_examples
    }
    
    with open(OUTPUT_SHAP, "w") as f:
        json.dump(data, f, indent=2)

def generate_external_knowledge():
    """Creates Markdown files for external context."""
    print("Generating External Knowledge Documents...")
    
    doc1 = """# COVID-19 Impact on Mortality (2020-2021)
    
## Overview
During the years 2020 and 2021, general population mortality increased significantly due to the COVID-19 pandemic. 

## Key Observations for Insured Populations
*   **Older Age Groups (65+)**: Experienced the highest excess mortality. Relative risk increased by ~25% in peak months.
*   **Direct vs Indirect**: While direct COVID deaths were high, indirect excess mortality (delayed medical care) was also observed.
*   **Model Implications**: Historical models trained on pre-2020 data tends to UNDERESTIMATE mortality in these calendar years. A/E ratios > 1.0 are expected.
    """
    
    doc2 = """# Preferred Class Definitions
    
## Classification System
The 'Preferred' classification system segments risks based on health markers (BP, Cholesterol, Family History).

*   **Super Pref (Preferred Plus)**: Excellent health, top 10% of applicants. Mortality approx 60% of Standard.
*   **Classic Pref**: Good health, minor issues allowed. Mortality approx 80% of Standard.
*   **Standard**: Average health for age/gender. Baseline = 100%.
*   **Substandard**: Rated risks (e.g., Table A-H) due to medical conditions.
    """
    
    with open(f"{EXTERNAL_KB_DIR}/doc_covid_impact.md", "w") as f:
        f.write(doc1)
        
    with open(f"{EXTERNAL_KB_DIR}/doc_preferred_class.md", "w") as f:
        f.write(doc2)

def main():
    print("Starting Knowledge Base Generation...")
    
    # 1. Generate Data
    df = generate_synthetic_data()
    
    # 2. Generate Artifacts
    generate_data_dictionary()
    generate_eda_summary(df)
    generate_risk_segments(df)
    generate_shap_analysis(df)
    generate_external_knowledge()
    
    print(f"Artifacts generated successfully in {KB_DIR}")

if __name__ == "__main__":
    main()
