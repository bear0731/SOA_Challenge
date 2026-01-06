# -*- coding: utf-8 -*-
"""
Post-Generation Validator

Validates and corrects LLM-generated reports.
"""

import re
from typing import List, Tuple


class ReportValidator:
    """Validates and corrects generated reports."""
    
    # =========================================================================
    # Prohibited Patterns
    # =========================================================================
    PROHIBITED_PATTERNS = [
        (r"probability of death", "mortality rate"),
        (r"will die", "expected deaths"),
        (r"causes? (higher|lower|increased|decreased) mortality", 
         "is associated with \\1 mortality"),
        (r"the model is certain", "the model estimates"),
        (r"definitely", "likely"),
        (r"100% chance", "high likelihood"),
    ]
    
    # =========================================================================
    # Required Patterns per Section
    # =========================================================================
    REQUIRED_PATTERNS = {
        "Key Risk Drivers": [r"[+-]?\d+\.\d{3,}"],  # Must have SHAP values
        "Population Context": [r"\d+(st|nd|rd|th) percentile"],  # Must have percentile
        "Model Calibration": [r"A/E.*\d+\.\d{2}"],  # Must have A/E ratio
    }
    
    # =========================================================================
    # Numeric Formatting Rules
    # =========================================================================
    NUMERIC_FORMATS = {
        "mortality_rate": {"decimals": 6},
        "ae_ratio": {"decimals": 2},
        "shap_value": {"decimals": 4, "sign": True},
        "percentile": {"format": "ordinal"},  # 92nd, not 92
    }
    
    def validate(self, report: str) -> Tuple[bool, List[str]]:
        """
        Validate a generated report.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check prohibited patterns
        for pattern, replacement in self.PROHIBITED_PATTERNS:
            if re.search(pattern, report, re.IGNORECASE):
                issues.append(f"Prohibited pattern found: '{pattern}'")
        
        # Check required patterns per section
        for section, patterns in self.REQUIRED_PATTERNS.items():
            if section in report:
                section_start = report.find(section)
                section_end = report.find("###", section_start + 1)
                section_text = report[section_start:section_end] if section_end > 0 else report[section_start:]
                
                for pattern in patterns:
                    if not re.search(pattern, section_text):
                        issues.append(f"Missing required pattern in '{section}': {pattern}")
        
        return len(issues) == 0, issues
    
    def auto_correct(self, report: str) -> str:
        """
        Auto-correct common issues in generated report.
        """
        corrected = report
        
        # Fix prohibited patterns
        for pattern, replacement in self.PROHIBITED_PATTERNS:
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def format_number(self, value: float, num_type: str) -> str:
        """Format a number according to rules."""
        fmt = self.NUMERIC_FORMATS.get(num_type, {"decimals": 2})
        
        if num_type == "percentile":
            # Convert to ordinal
            n = int(value)
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            if 11 <= n % 100 <= 13:
                suffix = 'th'
            return f"{n}{suffix}"
        
        decimals = fmt.get("decimals", 2)
        formatted = f"{value:.{decimals}f}"
        
        if fmt.get("sign") and value >= 0:
            formatted = "+" + formatted
        
        return formatted


# Singleton instance
validator = ReportValidator()
