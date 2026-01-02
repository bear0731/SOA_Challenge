import unittest
import json
from main import ExplanationSystem

class TestQAExplanationSystem(unittest.TestCase):
    def setUp(self):
        self.app = ExplanationSystem()

    def test_high_risk_segment_context(self):
        """Test if 'Elderly Smoker' segment is correctly identified and injected."""
        case = {
            "issue_age": 75,
            "smoker_status": "Smoker",
            "preferred_class": "Standard",
            "duration": 10
        }
        result = self.app.run(case)
        user_prompt = result['final_user_prompt']
        
        # Check Segment Logic
        self.assertIn("Elderly Smokers", user_prompt)
        self.assertIn("ae_ratio", user_prompt)
        
        # Check SHAP Logic
        self.assertIn("global_importance", user_prompt)

    def test_external_knowledge_retrieval(self):
        """Test if 'COVID' doc is retrieved for elderly."""
        case = {
            "issue_age": 70,
            "smoker_status": "Non-Smoker"
        }
        result = self.app.run(case)
        user_prompt = result['final_user_prompt']
        
        self.assertIn("COVID", user_prompt)

    def test_system_prompt_eda_injection(self):
        """Test if EDA stats are in the System Prompt."""
        result = self.app.run({"issue_age": 40})
        sys_prompt = result['final_system_prompt']
        
        self.assertIn("GLOBAL DATA CONTEXT", sys_prompt)
        self.assertIn("Numerical Features", sys_prompt)
        self.assertIn("p90", sys_prompt)

if __name__ == '__main__':
    unittest.main()
