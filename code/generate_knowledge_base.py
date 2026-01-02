import pandas as pd
import numpy as np
import json
import os
import shutil

# Configuration
KB_DIR = "../knowledge_base"
EXTERNAL_KB_DIR = f"{KB_DIR}/external_knowledge"
OUTPUT_EDA = f"{KB_DIR}/eda_summary.json"
OUTPUT_SHAP = f"{KB_DIR}/shap_analysis.json"
OUTPUT_SEGMENTS = f"{KB_DIR}/risk_segments.json"

# Ensure directories exist
os.makedirs(EXTERNAL_KB_DIR, exist_ok=True)

def generate_synthetic_data(n_samples=10000):
    """Generates synthetic mortality data for demonstration."""
    np.random.seed(42)
    
    data = {
        'issue_age': np.random.randint(20, 80, n_samples),
        'duration': np.random.randint(1, 30, n_samples),
        'face_amount': np.random.exponential(500000, n_samples),
        'smoker_status': np.random.choice(['Smoker', 'Non-Smoker'], n_samples, p=[0.15, 0.85]),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'preferred_class': np.random.choice(['Super Pref', 'Pref', 'Standard'], n_samples, p=[0.2, 0.3, 0.5])
    }
    
    df = pd.DataFrame(data)
    
    # Simulate Target (Mortality Rate) based on logic
    # Base rate
    base_rate = 0.001
    
    # Factors
    age_factor = np.exp((df['issue_age'] - 40) * 0.08)
    smoker_factor = np.where(df['smoker_status'] == 'Smoker', 2.5, 1.0)
    duration_factor = np.where(df['duration'] <= 2, 0.5, 1.0) # Selection effect
    
    df['expected_mortality'] = base_rate * age_factor * smoker_factor * duration_factor
    
    # Add some noise for "Actual"
    df['actual_mortality'] = df['expected_mortality'] * np.random.normal(1.0, 0.2, n_samples)
    df['actual_death'] = np.random.binomial(1, np.clip(df['actual_mortality'], 0, 1))
    
    return df

def generate_eda_summary(df):
    """Calculates distribution stats and correlation."""
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
    for col in ['smoker_status', 'gender', 'preferred_class']:
        counts = df[col].value_counts(normalize=True).to_dict()
        avg_target = df.groupby(col)['actual_death'].mean().to_dict()
        summary["categorical_features"][col] = {
            "distribution": counts,
            "avg_target_by_group": avg_target
        }
        
    return summary

def generate_shap_analysis(df):
    """Simulates SHAP values (Global importance and Local examples)."""
    print("Generating SHAP Analysis...")
    
    # In a real scenario, we would interpret the model. Here we mock it based on our synthetic logic.
    # Logic: Age >> Smoker > Duration > Others
    
    global_importance = {
        "issue_age": 0.45,
        "smoker_status": 0.25,
        "duration": 0.15,
        "face_amount": 0.05,
        "preferred_class": 0.05,
        "gender": 0.05
    }
    
    # Create some template local explanations
    local_explanations = [
        {
            "id": "sample_high_risk",
            "features": {"issue_age": 75, "smoker_status": "Smoker", "duration": 20},
            "prediction": 0.05,
            "shap_values": {
                "issue_age": 0.03,
                "smoker_status": 0.015,
                "duration": 0.005,
                "base_value": 0.0
            }
        },
        {
            "id": "sample_low_risk",
            "features": {"issue_age": 25, "smoker_status": "Non-Smoker", "duration": 1},
            "prediction": 0.0002,
            "shap_values": {
                "issue_age": -0.01,
                "smoker_status": -0.005,
                "duration": -0.005,
                "base_value": 0.02
            }
        }
    ]
    
    return {
        "global_feature_importance": global_importance,
        "local_examples": local_explanations
    }

def generate_risk_segments(df):
    """Identifies specific cohorts with high/low A/E or interesting patterns."""
    print("Identifying Risk Segments...")
    
    # Mocking identification of segments
    segments = [
        {
            "id": "seg_young_select",
            "name": "Young & New Policyholders",
            "condition": "issue_age < 35 and duration <= 2",
            "ae_ratio": 0.92,
            "description": "Mortality is significantly lower (~8% below expectation). Strong selection effect observed.",
            "key_drivers": ["duration", "issue_age"]
        },
        {
            "id": "seg_old_smoker",
            "name": "Elderly Smokers",
            "condition": "issue_age > 65 and smoker_status == 'Smoker'",
            "ae_ratio": 1.15,
            "description": "Observed mortality is 15% higher than predicted. Potential model underestimation of smoker impact at older ages.",
            "key_drivers": ["issue_age", "smoker_status"]
        }
    ]
    
    return segments

def generate_external_knowledge():
    """Creates Markdown files for external context."""
    print("Generating External Knowledge Documents...")
    
    doc1 = """# COVID-19 Impact on Mortality (2020-2021)
    
During the years 2020 and 2021, general population mortality increased significantly due to the COVID-19 pandemic. 
Key observations for insured populations:
*   **Older Age Groups (65+)**: Experienced the highest excess mortality.
*   **Direct vs Indirect**: While direct COVID deaths were high, indirect excess mortality (delayed medical care) was also observed.
*   **Model Adjustment**: Historical models trained on pre-2020 data tends to UNDERESTIMATE mortality in these calendar years.
    """
    
    doc2 = """# Preferred Class Definitions and Trends
    
The 'Preferred' classification system was introduced to segment risks better.
*   **Super Pref**: Excellent health, verified by blood/urine profiles. Mortality approx 60% of Standard.
*   **Standard**: Average health.
*   **Trend**: Over time, the strictness of 'Super Pref' criteria has fluctuated, potentially causing 'class creep' where newer policies have slightly different risk profiles than older ones.
    """
    
    with open(f"{EXTERNAL_KB_DIR}/doc_covid_impact.md", "w") as f:
        f.write(doc1)
        
    with open(f"{EXTERNAL_KB_DIR}/doc_preferred_class.md", "w") as f:
        f.write(doc2)

def main():
    print("Starting Knowledge Base Generation...")
    
    # 1. Generate Data
    df = generate_synthetic_data()
    
    # 2. EDA
    eda_summary = generate_eda_summary(df)
    with open(OUTPUT_EDA, "w") as f:
        json.dump(eda_summary, f, indent=2)
        
    # 3. SHAP
    shap_data = generate_shap_analysis(df)
    with open(OUTPUT_SHAP, "w") as f:
        json.dump(shap_data, f, indent=2)
        
    # 4. Risk Segments
    segments = generate_risk_segments(df)
    with open(OUTPUT_SEGMENTS, "w") as f:
        json.dump(segments, f, indent=2)
        
    # 5. External Knowledge
    generate_external_knowledge()
    
    print(f"Artifacts generated successfully in {KB_DIR}")

if __name__ == "__main__":
    main()
