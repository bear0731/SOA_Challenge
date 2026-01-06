# -*- coding: utf-8 -*-
"""
Predictor Module

Handles LightGBM prediction and SHAP value calculation.
"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import math

# Optional imports (may not be available in all environments)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

from .config import LGBM_MODEL_PATH, FEATURES, CATEGORICAL_FEATURES


class MortalityPredictor:
    """
    Handles mortality prediction and SHAP explanation.
    
    Uses LightGBM model for prediction and SHAP for feature attribution.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = Path(model_path) if model_path else LGBM_MODEL_PATH
        self.model = None
        self.explainer = None
        self.encoders: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self) -> 'MortalityPredictor':
        """Load the model and create SHAP explainer."""
        if self._loaded:
            return self
        
        if not HAS_LIGHTGBM:
            print("⚠ LightGBM not installed - using mock predictions")
            return self
        
        try:
            self.model = lgb.Booster(model_file=str(self.model_path))
            print(f"✓ Model loaded: {self.model.num_trees()} trees")
            
            if HAS_SHAP:
                self.explainer = shap.TreeExplainer(self.model)
                print("✓ SHAP explainer created")
            else:
                print("⚠ SHAP not installed - using mock SHAP values")
            
            self._loaded = True
        except Exception as e:
            print(f"⚠ Error loading model: {e}")
        
        return self
    
    def predict(self, features: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Make prediction and calculate SHAP values.
        
        Args:
            features: Dict of feature values
            
        Returns:
            (prediction, shap_values_dict)
        """
        if not self._loaded or self.model is None:
            return self._mock_predict(features)
        
        # Prepare feature vector
        X = self._prepare_features(features)
        
        # Predict
        prediction = self.model.predict([X])[0]
        
        # SHAP values
        if self.explainer:
            shap_values = self.explainer.shap_values(np.array([X]))[0]
            shap_dict = dict(zip(FEATURES, shap_values))
        else:
            shap_dict = self._mock_shap(features)
        
        return prediction, shap_dict
    
    def _prepare_features(self, features: Dict) -> List:
        """Prepare feature vector for prediction."""
        from sklearn.preprocessing import LabelEncoder
        
        X = []
        for feat in FEATURES:
            val = features.get(feat, 0)
            
            if feat in CATEGORICAL_FEATURES:
                # Encode categorical
                if feat not in self.encoders:
                    self.encoders[feat] = LabelEncoder()
                    # Fit on the single value (not ideal but works for demo)
                    self.encoders[feat].fit([str(val)])
                
                try:
                    val = self.encoders[feat].transform([str(val)])[0]
                except ValueError:
                    val = 0  # Unknown category
            
            X.append(val)
        
        return X
    
    def _mock_predict(self, features: Dict) -> Tuple[float, Dict[str, float]]:
        """Generate mock prediction when model not available."""
        # Simple mock based on age
        age = features.get('Attained_Age', 50)
        smoker = features.get('Smoker_Status', 'NS')
        
        base_rate = 0.001
        age_factor = math.exp((age - 40) * 0.08)
        smoker_factor = 2.5 if smoker == 'S' else 1.0
        
        prediction = base_rate * age_factor * smoker_factor
        prediction = min(prediction, 1.0)  # Cap at 1.0
        
        shap_dict = self._mock_shap(features)
        
        return prediction, shap_dict
    
    def _mock_shap(self, features: Dict) -> Dict[str, float]:
        """Generate mock SHAP values."""
        age = features.get('Attained_Age', 50)
        smoker = features.get('Smoker_Status', 'NS')
        duration = features.get('Duration', 10)
        
        return {
            'Attained_Age': (age - 50) * 0.001,
            'Duration': (duration - 10) * 0.0005,
            'Smoker_Status': 0.015 if smoker == 'S' else -0.005,
            'Issue_Age': 0.005,
            'Face_Amount_Band': -0.002,
            'Insurance_Plan': -0.001,
            'Sex': 0.001,
            'Preferred_Class': -0.003,
            'SOA_Post_Lvl_Ind': 0.0001,
            'SOA_Antp_Lvl_TP': 0.0,
            'SOA_Guar_Lvl_TP': 0.0,
        }
    
    def get_base_value(self) -> float:
        """Get SHAP base value (expected value)."""
        if self.explainer:
            return float(self.explainer.expected_value)
        return 0.0097  # Default overall rate


def create_predictor(model_path: Optional[str] = None) -> MortalityPredictor:
    """Factory function for MortalityPredictor."""
    return MortalityPredictor(model_path).load()
