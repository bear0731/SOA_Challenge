import json
import os
import glob

class KnowledgeBase:
    def __init__(self, kb_dir="knowledge_base"):
        self.kb_dir = kb_dir
        self.data_dictionary = self._load_json("data_dictionary.json")
        self.eda_summary = self._load_json("eda_summary.json")
        self.risk_segments = self._load_json("risk_segments.json")
        self.shap_analysis = self._load_json("shap_analysis.json")
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

    def get_system_context(self):
        """
        Returns the 'Global Data Picture' for the System Prompt.
        Includes EDA Summary and Data Dictionary.
        """
        return {
            "eda_summary": self.eda_summary,
            "data_dictionary": self.data_dictionary
        }

    def _check_condition(self, condition, data_point):
        """
        Evaluates a string condition against a data dict.
        WARNING: unsafe eval() used for prototype.
        """
        try:
            return eval(condition, {}, data_point)
        except Exception:
            return False

    def get_query_context(self, input_data):
        """
        Retrieves context specific to the input data point.
        """
        context = {
            "matched_risk_segments": [],
            "relevant_external_docs": [],
            "shap_context": {}
        }

        # 1. Match Risk Segments
        if self.risk_segments:
            for segment in self.risk_segments:
                if self._check_condition(segment["condition"], input_data):
                    context["matched_risk_segments"].append(segment)

        # 2. External Knowledge (Simple Keyword Matching)
        # In a real system, this would be semantic search.
        # print(f"DEBUG: Checking {len(self.external_docs)} docs against input {input_data}")
        for doc_name, content in self.external_docs.items():
            # print(f"DEBUG: key={doc_name}")
            # Example Logic: "COVID" doc if issue_age > 65 (vulnerable group)
            if "covid" in doc_name.lower():
                # print(f"DEBUG: Found covid doc. Age={input_data.get('issue_age', 0)}")
                if input_data.get("issue_age", 0) > 65:
                    context["relevant_external_docs"].append({"source": doc_name, "content": content})
            
            # Example Logic: "Preferred" doc if preferred_class is present
            if "preferred" in doc_name.lower():
                if "preferred_class" in input_data:
                    context["relevant_external_docs"].append({"source": doc_name, "content": content})

        # 3. SHAP Context (Global + mock local)
        if self.shap_analysis:
            context["shap_context"]["global_importance"] = self.shap_analysis.get("global_feature_importance", {})
            # Here we would normally plug in the Real Local SHAP values from the model.
            # For now, we leave a placeholder or retrieve the closest template.
            
        return context

if __name__ == "__main__":
    # Test
    kb = KnowledgeBase()
    
    # Test High Risk Input
    input_high = {"issue_age": 70, "smoker_status": "Smoker", "preferred_class": "Standard"}
    ctx_high = kb.get_query_context(input_high)
    print("--- High Risk Context ---")
    print(json.dumps(ctx_high["matched_risk_segments"], indent=2))
    print(f"External Docs: {len(ctx_high['relevant_external_docs'])}")

    # Test Low Risk Input
    input_low = {"issue_age": 25, "preferred_class": "Super Pref"}
    ctx_low = kb.get_query_context(input_low)
    print("\n--- Low Risk Context ---")
    print(json.dumps(ctx_low["matched_risk_segments"], indent=2))
