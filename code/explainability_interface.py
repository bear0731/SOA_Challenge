import sys
import json
import numpy as np
import pandas as pd # Needed if we load real model, here we mock
from rag_engine import KnowledgeBase

class ModelExplainer:
    def __init__(self, kb_dir="../knowledge_base"):
        self.rag = KnowledgeBase(kb_dir)
        
    def _predict_mortality(self, input_data):
        """
        Mocks the LightGBM prediction logic based on the synthetic data logic 
        from generate_knowledge_base.py
        """
        # Logic: Base * AgeFactor * SmokerFactor * DurationFactor
        base_rate = 0.001
        age = input_data.get('issue_age', 40)
        dur = input_data.get('duration', 5)
        smoker = input_data.get('smoker_status', 'Non-Smoker')
        
        age_factor = np.exp((age - 40) * 0.08)
        smoker_factor = 2.5 if smoker == 'Smoker' else 1.0
        duration_factor = 0.5 if dur <= 2 else 1.0
        
        rate = base_rate * age_factor * smoker_factor * duration_factor
        return rate

    def construct_llm_prompt(self, input_data, prediction, context):
        """
        Assembles the System Prompt and User Query.
        """
        
        system_prompt = f"""You are an actuarial model explainer assistant.
Your goal is to explain a mortality rate of {prediction:.6f} for a specific policyholder.

Use the provided Context Information to justify the prediction.
- Cite the "EDA Stats" to benchmark if values are high/low.
- Explain "Risk Segments" if the user falls into one.
- Use "SHAP Drivers" to mention key features.
- Reference "External Knowledge" if relevant to the profile.

Context Information:
{json.dumps(context, indent=2)}
"""

        user_query = f"""
        Profile:
        {json.dumps(input_data, indent=2)}
        
        Task: Explain why this mortality rate is predicted. Is it high or low risk? What are the main drivers?
        """
        
        return system_prompt, user_query

    def explain_single_case(self, input_data):
        # 1. Prediction
        pred = self._predict_mortality(input_data)
        
        # 2. Retrieval
        context = self.rag.find_relevant_context(input_data)
        
        # 3. Prompting
        sys_prompt, user_msg = self.construct_llm_prompt(input_data, pred, context)
        
        return {
            "prediction_mortality_rate": pred,
            "retrieved_context_summary": {k: len(v) for k,v in context.items()},
            "final_llm_prompt": sys_prompt + "\n" + user_msg
        }

if __name__ == "__main__":
    explainer = ModelExplainer()
    
    # Test Case 1: High Risk (Old Smoker)
    test_case_1 = {
        "issue_age": 72,
        "duration": 15,
        "smoker_status": "Smoker",
        "preferred_class": "Standard",
        "face_amount": 50000
    }
    
    print("--- Test Case 1: Elderly Smoker ---")
    result1 = explainer.explain_single_case(test_case_1)
    print(f"Predicted Rate: {result1['prediction_mortality_rate']:.5f}")
    print("Prompt Preview (First 500 chars):")
    print(result1['final_llm_prompt'][:500])
    print("-" * 50)

    # Test Case 2: Low Risk (Young Non-Smoker)
    test_case_2 = {
        "issue_age": 28,
        "duration": 1,
        "smoker_status": "Non-Smoker",
        "preferred_class": "Super Pref",
        "face_amount": 1000000
    }
    
    print("\n--- Test Case 2: Young Select ---")
    result2 = explainer.explain_single_case(test_case_2)
    print(f"Predicted Rate: {result2['prediction_mortality_rate']:.5f}")
    # print(result2['final_llm_prompt']) # Uncomment to see full prompt
