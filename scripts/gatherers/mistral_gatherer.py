# scripts/gatherers/mistral_gatherer.py
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

class MistralGatherer:
    def __init__(self):
        self.models = {}
        
        # Known Mistral models as of early 2025
        self.known_models = {
            "mistral-large": {
                "context_window": 128000,
                "description": "Most capable Mistral model for complex tasks",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "code-generation", "multilingual"]
            },
            "mistral-medium": {
                "context_window": 32000,
                "description": "Balanced Mistral model for general use",
                "capabilities": ["text-generation", "conversation", "code-generation", "cost-effective"]
            },
            "mistral-small": {
                "context_window": 32000,
                "description": "Efficient Mistral model optimized for speed",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective"]
            },
            "mistral-tiny": {
                "context_window": 32000,
                "description": "Compact Mistral model for simple tasks",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective"]
            },
            "mixtral-8x7b": {
                "context_window": 32000,
                "description": "Mixture of Experts model with 8x7B architecture",
                "capabilities": ["text-generation", "conversation", "code-generation", "mixture-of-experts"]
            },
            "mixtral-8x22b": {
                "context_window": 65536,
                "description": "Large Mixture of Experts model with 8x22B architecture",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "code-generation", "mixture-of-experts"]
            },
            "codestral": {
                "context_window": 32000,
                "description": "Specialized Mistral model for code generation",
                "capabilities": ["code-generation", "programming", "debugging", "code-completion"]
            },
            "mistral-embed": {
                "context_window": 8192,
                "description": "Mistral embedding model for semantic tasks",
                "capabilities": ["text-embeddings", "semantic-search", "similarity"]
            },
            "mistral-7b-instruct": {
                "context_window": 32000,
                "description": "Instruction-tuned Mistral 7B model",
                "capabilities": ["text-generation", "conversation", "instruction-following", "cost-effective"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all Mistral models"""
        print("🔍 Gathering Mistral models...")
        
        try:
            self._load_known_models()
            models_list = list(self.models.values())
            print(f"✅ Found {len(models_list)} unique Mistral models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering Mistral models: {e}")
            return []
    
    def _load_known_models(self):
        """Load known Mistral models as baseline"""
        print("📚 Loading known Mistral models...")
        
        for model_name, model_info in self.known_models.items():
            display_name = model_name.replace("-", " ").title()
            
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="mistral",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=display_name
            )

if __name__ == "__main__":
    gatherer = MistralGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()