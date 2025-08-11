# scripts/gatherers/baidu_gatherer.py
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

class BaiduGatherer:
    def __init__(self):
        self.models = {}
        
        # Known Baidu models as of early 2025
        self.known_models = {
            "ernie-4.0-8k": {
                "context_window": 8192,
                "description": "Latest ERNIE 4.0 model with enhanced capabilities",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "multilingual", "chinese-optimized"]
            },
            "ernie-4.0-turbo-8k": {
                "context_window": 8192,
                "description": "Faster version of ERNIE 4.0",
                "capabilities": ["text-generation", "conversation", "fast-response", "multilingual", "chinese-optimized"]
            },
            "ernie-3.5-8k": {
                "context_window": 8192,
                "description": "ERNIE 3.5 model optimized for various tasks",
                "capabilities": ["text-generation", "conversation", "code-generation", "multilingual", "chinese-optimized"]
            },
            "ernie-3.5-128k": {
                "context_window": 131072,
                "description": "ERNIE 3.5 with extended context window",
                "capabilities": ["text-generation", "conversation", "long-context", "multilingual", "chinese-optimized"]
            },
            "ernie-lite-8k": {
                "context_window": 8192,
                "description": "Lightweight ERNIE model for efficient processing",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective", "chinese-optimized"]
            },
            "ernie-speed-8k": {
                "context_window": 8192,
                "description": "High-speed ERNIE model optimized for quick responses",
                "capabilities": ["text-generation", "conversation", "fast-response", "real-time", "chinese-optimized"]
            },
            "ernie-tiny-8k": {
                "context_window": 8192,
                "description": "Ultra-compact ERNIE model",
                "capabilities": ["text-generation", "edge-deployment", "cost-effective", "chinese-optimized"]
            },
            "ernie-vision": {
                "context_window": 2048,
                "description": "ERNIE model with vision capabilities",
                "capabilities": ["multimodal", "vision", "text-generation", "image-analysis", "chinese-optimized"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all Baidu models"""
        print("🔍 Gathering Baidu models...")
        
        try:
            self._load_known_models()
            models_list = list(self.models.values())
            print(f"✅ Found {len(models_list)} unique Baidu models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering Baidu models: {e}")
            return []
    
    def _load_known_models(self):
        """Load known Baidu models as baseline"""
        print("📚 Loading known Baidu models...")
        
        for model_name, model_info in self.known_models.items():
            display_name = model_name.replace("-", " ").upper()
            
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="baidu",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=display_name
            )

if __name__ == "__main__":
    gatherer = BaiduGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()