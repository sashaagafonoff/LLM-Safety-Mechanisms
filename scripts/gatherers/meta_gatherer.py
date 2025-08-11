# scripts/gatherers/meta_gatherer.py
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

class MetaGatherer:
    def __init__(self):
        self.documentation_urls = [
            "https://llama.meta.com/",
            "https://github.com/meta-llama"
        ]
        self.models = {}
        
        # Known Meta models as of early 2025
        self.known_models = {
            "llama-3.3-70b": {
                "context_window": 128000,
                "description": "Latest Llama 3.3 model with 70B parameters",
                "capabilities": ["text-generation", "conversation", "code-generation", "complex-reasoning"]
            },
            "llama-3.2-90b": {
                "context_window": 128000,
                "description": "Large Llama 3.2 model with 90B parameters",
                "capabilities": ["text-generation", "conversation", "code-generation", "complex-reasoning", "multimodal"]
            },
            "llama-3.2-70b": {
                "context_window": 128000,
                "description": "Llama 3.2 model with 70B parameters",
                "capabilities": ["text-generation", "conversation", "code-generation", "complex-reasoning"]
            },
            "llama-3.2-11b": {
                "context_window": 128000,
                "description": "Mid-size Llama 3.2 model with vision capabilities",
                "capabilities": ["text-generation", "conversation", "multimodal", "vision", "code-generation"]
            },
            "llama-3.2-3b": {
                "context_window": 128000,
                "description": "Efficient Llama 3.2 model with 3B parameters",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective"]
            },
            "llama-3.2-1b": {
                "context_window": 128000,
                "description": "Compact Llama 3.2 model with 1B parameters",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective", "edge-deployment"]
            },
            "llama-3.1-405b": {
                "context_window": 128000,
                "description": "Largest Llama 3.1 model with 405B parameters",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "code-generation", "scientific-reasoning"]
            },
            "llama-3.1-70b": {
                "context_window": 128000,
                "description": "Large Llama 3.1 model with 70B parameters",
                "capabilities": ["text-generation", "conversation", "code-generation", "complex-reasoning"]
            },
            "llama-3.1-8b": {
                "context_window": 128000,
                "description": "Efficient Llama 3.1 model with 8B parameters",
                "capabilities": ["text-generation", "conversation", "code-generation", "cost-effective"]
            },
            "code-llama-34b": {
                "context_window": 100000,
                "description": "Specialized Llama model for code generation",
                "capabilities": ["code-generation", "programming", "debugging", "code-completion"]
            },
            "code-llama-13b": {
                "context_window": 100000,
                "description": "Mid-size Code Llama model",
                "capabilities": ["code-generation", "programming", "code-completion", "cost-effective"]
            },
            "code-llama-7b": {
                "context_window": 100000,
                "description": "Efficient Code Llama model",
                "capabilities": ["code-generation", "programming", "fast-response", "cost-effective"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all Meta models"""
        print("🔍 Gathering Meta models...")
        
        try:
            self._load_known_models()
            models_list = list(self.models.values())
            print(f"✅ Found {len(models_list)} unique Meta models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering Meta models: {e}")
            return []
    
    def _load_known_models(self):
        """Load known Meta models as baseline"""
        print("📚 Loading known Meta models...")
        
        for model_name, model_info in self.known_models.items():
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="meta",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=f"Llama {model_name.replace('llama-', '').replace('code-llama', 'Code Llama').upper()}"
            )

if __name__ == "__main__":
    gatherer = MetaGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()