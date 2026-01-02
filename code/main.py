import sys
import json
import numpy as np
import pandas as pd
from rag_retriever import KnowledgeBase

class ExplanationSystem:
    def __init__(self):
        self.rag = KnowledgeBase()
        self.system_context = self.rag.get_system_context()

    def _mock_predict(self, input_data):
        """
        Mocks the LightGBM prediction logic based on the synthetic data logic.
        """
        base_rate = 0.001
        age = input_data.get('issue_age', 40)
        dur = input_data.get('duration', 5)
        smoker = input_data.get('smoker_status', 'Non-Smoker')
        pref = input_data.get('preferred_class', 'Standard')
        
        age_factor = np.exp((age - 40) * 0.08)
        smoker_factor = 2.5 if smoker == 'Smoker' else 1.0
        duration_factor = 0.5 if dur <= 2 else 1.0
        
        pref_factor_map = {'Super Pref': 0.6, 'Classic Pref': 0.8, 'Standard': 1.0, 'Substandard': 1.5}
        pref_factor = pref_factor_map.get(pref, 1.0)
        
        rate = base_rate * age_factor * smoker_factor * duration_factor * pref_factor
        return rate

    def construct_system_prompt(self):
        """
        Builds the System Prompt with Global Data Context.
        """
        eda = self.system_context['eda_summary']
        return f"""You are an expert Actuarial Model Assistant. 
Your goal is to explain mortality model predictions to reviewers.

# GLOBAL DATA CONTEXT (What is "Normal"?)
Use these statistics to judge if a user's values are high or low.

## Numerical Features (Mean / P90)
{json.dumps(eda['numerical_features'], indent=2)}

## Categorical Features (Distribution)
{json.dumps(eda['categorical_features'], indent=2)}

# INSTRUCTIONS
1. Always cite the "Global Data Context" to benchmark the user. (e.g. "Age 75 is well above the p90 of 74").
2. If the user falls into a "Risk Segment", explain why their risk is High/Low using the provided A/E ratio.
3. Use the SHAP values to explain the specific drivers of the prediction.
4. If "External Knowledge" is provided (e.g. COVID), use it to add qualitative context.
"""

    def construct_user_prompt(self, input_data, prediction, context):
        """
        Builds the User Prompt with Specific Retrieval Context.
        """
        return f"""
# TASK
Explain the predicted mortality rate of **{prediction:.6f}** for the following policyholder.

# POLICYHOLDER PROFILE
{json.dumps(input_data, indent=2)}

# RETRIEVED CONTEXT (Specific to this case)

## 1. Risk Segments (Cohorts)
{json.dumps(context['matched_risk_segments'], indent=2)}

## 2. External Knowledge (Domain Context)
{json.dumps(context['relevant_external_docs'], indent=2)}

## 3. SHAP Analysis (Drivers)
{json.dumps(context['shap_context'], indent=2)}

# QUESTION
Why is this rate predicted? Is it reasonable?
"""

    def run(self, input_data):
        # 1. Predict
        pred = self._mock_predict(input_data)
        
        # 2. Retrieve
        query_ctx = self.rag.get_query_context(input_data)
        
        # 3. Prompt
        sys_prompt = self.construct_system_prompt()
        user_prompt = self.construct_user_prompt(input_data, pred, query_ctx)
        
        return {
            "prediction": pred,
            "final_system_prompt": sys_prompt,
            "final_user_prompt": user_prompt
        }

if __name__ == "__main__":
    app = ExplanationSystem()
    
    # Test Case: Elderly Smoker (High Risk)
    print(">>> RUNNING TEST CASE: Elderly Smoker")
    case = {
        "issue_age": 72, 
        "smoker_status": "Smoker", 
        "preferred_class": "Standard",
        "duration": 10
    }
    result = app.run(case)
    
    print(f"Prediction: {result['prediction']:.6f}")
    print("\n--- SYSTEM PROMPT (Preview) ---")
    print(result['final_system_prompt'][:600])
    print("\n--- USER PROMPT (Full) ---")
    print(result['final_user_prompt'])
