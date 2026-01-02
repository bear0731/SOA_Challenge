import json
import os
import glob

class KnowledgeBase:
    def __init__(self, kb_dir="../knowledge_base"):
        self.kb_dir = kb_dir
        self.eda_summary = self._load_json("eda_summary.json")
        self.shap_analysis = self._load_json("shap_analysis.json")
        self.risk_segments = self._load_json("risk_segments.json")
        self.external_docs = self._load_external_docs()

    def _load_json(self, filename):
        path = os.path.join(self.kb_dir, filename)
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found.")
            return {}

    def _load_external_docs(self):
        docs = {}
        pattern = os.path.join(self.kb_dir, "external_knowledge", "*.md")
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            with open(filepath, "r") as f:
                docs[filename] = f.read()
        return docs

    def _check_condition(self, condition, data_point):
        """
        Evaluates a string condition against a data dict.
        WARNING: Uses eval() for prototype simplicity. Secure parsing needed for prod.
        """
        try:
            # Create a safe local scope with data values
            # Replace variable names in condition with data_point values is tricky 
            # without a parser.
            # Alternatively, simply inject variables into eval local scope.
            # Security risk acceptable for this prototype context.
            return eval(condition, {}, data_point)
        except Exception as e:
            # If data_point is missing keys required for condition
            return False

    def find_relevant_context(self, input_data):
        """
        Retrieves context based on a single data point input.
        input_data: dict, e.g., {'issue_age': 45, 'smoker_status': 'Smoker', ...}
        """
        context = {
            "eda_context": [],
            "risk_segment_context": [],
            "shap_context": [],
            "external_context": []
        }

        # 1. EDA Context: Compare input values to global stats
        if self.eda_summary:
            nums = self.eda_summary.get("numerical_features", {})
            for feat, val in input_data.items():
                if feat in nums:
                    stats = nums[feat]
                    # Logic: Flag if value deviates significantly
                    if val > stats["p90"]:
                        context["eda_context"].append(f"Feature '{feat}' value {val} is in the top 10% (p90={stats['p90']}).")
                    
            cats = self.eda_summary.get("categorical_features", {})
            for feat, val in input_data.items():
                if feat in cats:
                    group_data = cats[feat]
                    avg_mortality = group_data.get("avg_target_by_group", {}).get(str(val), "N/A")
                    context["eda_context"].append(f"Feature '{feat}'='{val}'. Group Avg Mortality: {avg_mortality}.")

        # 2. Risk Segments: Check membership
        if self.risk_segments:
            for segment in self.risk_segments:
                if self._check_condition(segment["condition"], input_data):
                    context["risk_segment_context"].append(segment)

        # 3. SHAP Context: Global importance + Local approximation
        if self.shap_analysis:
            # Always include top drivers globally
            global_imp = self.shap_analysis.get("global_feature_importance", {})
            top_3 = sorted(global_imp.items(), key=lambda x: x[1], reverse=True)[:3]
            context["shap_context"].append(f"Global Top Risk Drivers: {', '.join([x[0] for x in top_3])}.")
            
            # Simple heuristic matching for local examples (nearest neighbor could be better)
            # For now, just pass the logic description.

        # 4. External Knowledge: Keyword matching
        # Simple keywords for demo
        for doc_name, content in self.external_docs.items():
            # Example logic: if prediction year is 2020/2021 (if we had calendar year)
            # Here we just look for broad matches or include specific docs based on rules
            if "covid" in doc_name.lower():
               # Hypothetical trigger
               pass
            
            if "preferred" in doc_name.lower() and "preferred_class" in input_data:
                context["external_context"].append(f"Reference: {doc_name}\nSummary: {content[:200]}...")

        return context

# Test function
if __name__ == "__main__":
    rag = KnowledgeBase("../knowledge_base")
    sample_input = {
        "issue_age": 75,
        "duration": 5,
        "smoker_status": "Smoker",
        "preferred_class": "Standard",
        "face_amount": 100000
    }
    ctx = rag.find_relevant_context(sample_input)
    print(json.dumps(ctx, indent=2))
