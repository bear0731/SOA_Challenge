import unittest
import json
from explainability_interface import ModelExplainer

class TestExplainabilitySystem(unittest.TestCase):
    def setUp(self):
        self.explainer = ModelExplainer("../knowledge_base")

    def test_high_risk_segment_detection(self):
        """Test if 'Elderly Smoker' segment is correctly identified."""
        input_data = {
            "issue_age": 75,
            "duration": 15,
            "smoker_status": "Smoker",
            "preferred_class": "Standard"
        }
        result = self.explainer.explain_single_case(input_data)
        prompt = result['final_llm_prompt']
        
        # Check if Risk Segment logic was retrieved
        self.assertIn("Elderly Smokers", prompt)
        self.assertIn("seg_old_smoker", prompt)
        
        # Check if EDA stats were retrieved
        self.assertIn("p90", prompt)

    def test_low_risk_segment_detection(self):
        """Test if 'Young Select' segment is correctly identified."""
        input_data = {
            "issue_age": 25,
            "duration": 1,
            "smoker_status": "Non-Smoker",
            "preferred_class": "Super Pref"
        }
        result = self.explainer.explain_single_case(input_data)
        prompt = result['final_llm_prompt']
        
        self.assertIn("Young & New Policyholders", prompt)
        self.assertIn("seg_young_select", prompt)

    def test_external_knowledge_retrieval(self):
        """Test if external docs are pulled when relevat."""
        # 'preferred_class' keyword should trigger 'doc_preferred_class.md'
        input_data = {
            "issue_age": 40,
            "preferred_class": "Super Pref" 
        }
        result = self.explainer.explain_single_case(input_data)
        prompt = result['final_llm_prompt']
        
        self.assertIn("Preferred Class Definitions", prompt)

if __name__ == '__main__':
    unittest.main()
