# -*- coding: utf-8 -*-
"""
LLM Module

Handles LLM integration for report generation using Azure OpenAI.
"""

import os
from typing import Optional
from pathlib import Path

# Load environment variables from .env (optional)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on environment variables

# Check for langchain
try:
    from langchain_openai import AzureChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False


class LLMClient:
    """
    LLM client for generating reports using Azure OpenAI.
    
    Uses LangChain's AzureChatOpenAI.
    """
    
    def __init__(
        self,
        deployment_name: str = "9h00100-service-gpt-4o-2",
        api_version: str = "2025-02-01-preview",
        temperature: float = 0.7
    ):
        self.deployment_name = deployment_name
        self.api_version = api_version
        self.temperature = temperature
        self.client = None
        self._initialized = False
    
    def initialize(self) -> 'LLMClient':
        """Initialize the LLM client."""
        if self._initialized:
            return self
        
        if not HAS_LANGCHAIN:
            print("⚠ langchain-openai not installed")
            return self
        
        try:
            self.client = AzureChatOpenAI(
                openai_api_version=self.api_version,
                deployment_name=self.deployment_name,
                temperature=self.temperature
            )
            self._initialized = True
            print(f"✓ LLM initialized: {self.deployment_name}")
        except Exception as e:
            print(f"⚠ LLM initialization failed: {e}")
        
        return self
    
    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str,
        max_retries: int = 3
    ) -> str:
        """
        Generate response from LLM.
        
        Args:
            system_prompt: System context
            user_prompt: User query
            max_retries: Number of retries on failure
            
        Returns:
            Generated text response
        """
        if not self._initialized or not self.client:
            return self._mock_response(user_prompt)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        for attempt in range(max_retries):
            try:
                response = self.client.invoke(messages)
                return response.content
            except Exception as e:
                print(f"⚠ LLM call failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return f"[LLM Error: {e}]"
        
        return "[LLM call failed]"
    
    def _mock_response(self, user_prompt: str) -> str:
        """Generate mock response when LLM not available."""
        return """## 風險評估報告

### 1. 預測摘要
根據模型預測，此保單的死亡率顯著高於整體人群平均。

### 2. 主要風險因子
- **年齡**: 高齡是主要風險驅動因子
- **吸菸狀態**: 吸菸進一步增加風險

### 3. 人群比較
此保單持有人位於人群風險分布的較高端。

### 4. 模型校準
模型整體校準良好，A/E Ratio 接近 1.0。

### 5. 免責聲明
此預測基於歷史資料模式，僅供參考，不應作為核保決策的唯一依據。

---
*[Mock Response - LLM not available]*
"""


# Factory function
def create_llm_client(
    deployment_name: str = "9h00100-service-gpt-4o-2",
    api_version: str = "2025-02-01-preview",
    temperature: float = 0.7
) -> LLMClient:
    """Factory function to create and initialize LLM client."""
    return LLMClient(deployment_name, api_version, temperature).initialize()
