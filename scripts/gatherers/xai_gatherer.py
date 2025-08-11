# scripts/gatherers/xai_gatherer.py
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

class XaiGatherer:
    def __init__(self):
        self.documentation_urls = [
            "https://x.ai/",
            "https://docs.x.ai/api"
        ]
        self.models = {}
        
        # Known xAI models as of early 2025
        self.known_models = {
            "grok-2": {
                "context_window": 131072,
                "description": "Latest Grok model with improved reasoning capabilities",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "real-time-info", "humor"]
            },
            "grok-2-mini": {
                "context_window": 131072,
                "description": "Smaller, more efficient version of Grok-2",
                "capabilities": ["text-generation", "conversation", "fast-response", "real-time-info", "cost-effective"]
            },
            "grok-1.5": {
                "context_window": 128000,
                "description": "Previous generation Grok model with vision capabilities",
                "capabilities": ["text-generation", "conversation", "multimodal", "vision", "real-time-info"]
            },
            "grok-1.5v": {
                "context_window": 128000,
                "description": "Grok 1.5 with enhanced vision processing",
                "capabilities": ["text-generation", "multimodal", "vision", "image-analysis", "real-time-info"]
            },
            "grok-1": {
                "context_window": 65536,
                "description": "Original Grok model",
                "capabilities": ["text-generation", "conversation", "humor", "real-time-info"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all xAI models"""
        print("🔍 Gathering xAI models...")
        
        try:
            self._load_known_models()
            models_list = list(self.models.values())
            print(f"✅ Found {len(models_list)} unique xAI models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering xAI models: {e}")
            return []
    
    def _load_known_models(self):
        """Load known xAI models as baseline"""
        print("📚 Loading known xAI models...")
        
        for model_name, model_info in self.known_models.items():
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="xai",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=model_name.replace("-", " ").title()
            )

if __name__ == "__main__":
    gatherer = XaiGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()