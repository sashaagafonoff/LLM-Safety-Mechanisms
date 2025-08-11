# scripts/gatherers/alibaba_gatherer.py
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelInfo:
    name: str
    provider: str
    status: str
    last_updated: str
    context_window: Optional[int] = None
    capabilities: Optional[List[str]] = None
    description: Optional[str] = None
    api_name: Optional[str] = None
    display_name: Optional[str] = None

class AlibabaGatherer:
    def __init__(self):
        self.models = {}
        
        # Known Alibaba models as of early 2025
        self.known_models = {
            "qwen2.5-72b": {
                "context_window": 131072,
                "description": "Latest large Qwen model with 72B parameters",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "code-generation", "multilingual"]
            },
            "qwen2.5-32b": {
                "context_window": 131072,
                "description": "Mid-size Qwen model with 32B parameters",
                "capabilities": ["text-generation", "conversation", "code-generation", "multilingual"]
            },
            "qwen2.5-14b": {
                "context_window": 131072,
                "description": "Efficient Qwen model with 14B parameters",
                "capabilities": ["text-generation", "conversation", "code-generation", "cost-effective", "multilingual"]
            },
            "qwen2.5-7b": {
                "context_window": 131072,
                "description": "Compact Qwen model with 7B parameters",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective", "multilingual"]
            },
            "qwen2.5-3b": {
                "context_window": 131072,
                "description": "Small Qwen model optimized for efficiency",
                "capabilities": ["text-generation", "conversation", "fast-response", "edge-deployment", "multilingual"]
            },
            "qwen2.5-1.5b": {
                "context_window": 131072,
                "description": "Ultra-compact Qwen model for resource-constrained environments",
                "capabilities": ["text-generation", "conversation", "edge-deployment", "multilingual"]
            },
            "qwen2.5-0.5b": {
                "context_window": 131072,
                "description": "Smallest Qwen model for edge applications",
                "capabilities": ["text-generation", "edge-deployment", "iot", "multilingual"]
            },
            "qwen2-vl-72b": {
                "context_window": 32768,
                "description": "Qwen vision-language model with 72B parameters",
                "capabilities": ["multimodal", "vision", "text-generation", "image-analysis", "conversation"]
            },
            "qwen2-vl-7b": {
                "context_window": 32768,
                "description": "Efficient Qwen vision-language model",
                "capabilities": ["multimodal", "vision", "text-generation", "image-analysis", "cost-effective"]
            },
            "qwen2-math-72b": {
                "context_window": 65536,
                "description": "Specialized Qwen model for mathematical reasoning",
                "capabilities": ["mathematical-reasoning", "problem-solving", "scientific-computing", "text-generation"]
            },
            "qwen-coder-32b": {
                "context_window": 131072,
                "description": "Specialized Qwen model for code generation",
                "capabilities": ["code-generation", "programming", "debugging", "code-completion"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all Alibaba models"""
        print("🔍 Gathering Alibaba models...")
        
        try:
            self._load_known_models()
            models_list = list(self.models.values())
            print(f"✅ Found {len(models_list)} unique Alibaba models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering Alibaba models: {e}")
            return []
    
    def _load_known_models(self):
        """Load known Alibaba models as baseline"""
        print("📚 Loading known Alibaba models...")
        
        for model_name, model_info in self.known_models.items():
            display_name = model_name.replace("-", " ").replace("qwen", "Qwen").title()
            
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="alibaba",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=display_name
            )

if __name__ == "__main__":
    gatherer = AlibabaGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()