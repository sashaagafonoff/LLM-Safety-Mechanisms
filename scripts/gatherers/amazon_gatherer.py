# scripts/gatherers/amazon_gatherer.py
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

class AmazonGatherer:
    def __init__(self):
        self.documentation_urls = [
            "https://docs.aws.amazon.com/bedrock/latest/userguide/titan-models.html"
        ]
        self.models = {}
        
        # Known Amazon/AWS models (focusing on Amazon-developed Titan models)
        self.known_models = {
            "amazon.titan-text-premier-v1:0": {
                "context_window": 32000,
                "description": "Most advanced Amazon Titan text model",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "code-generation"]
            },
            "amazon.titan-text-express-v1": {
                "context_window": 8000,
                "description": "Fast and efficient Amazon Titan text model",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective"]
            },
            "amazon.titan-text-lite-v1": {
                "context_window": 4000,
                "description": "Lightweight Amazon Titan text model",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective"]
            },
            "amazon.titan-embed-text-v1": {
                "context_window": 8000,
                "description": "Amazon Titan text embedding model",
                "capabilities": ["text-embeddings", "semantic-search", "similarity"]
            },
            "amazon.titan-embed-text-v2:0": {
                "context_window": 8000,
                "description": "Improved Amazon Titan text embedding model",
                "capabilities": ["text-embeddings", "semantic-search", "similarity", "multilingual"]
            },
            "amazon.titan-image-generator-v1": {
                "context_window": None,
                "description": "Amazon Titan image generation model",
                "capabilities": ["image-generation", "creative-ai", "image-editing"]
            },
            "amazon.titan-image-generator-v2:0": {
                "context_window": None,
                "description": "Advanced Amazon Titan image generation model",
                "capabilities": ["image-generation", "creative-ai", "image-editing", "high-resolution"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all Amazon models"""
        print("🔍 Gathering Amazon models...")
        
        try:
            self._load_known_models()
            models_list = list(self.models.values())
            print(f"✅ Found {len(models_list)} unique Amazon models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering Amazon models: {e}")
            return []
    
    def _load_known_models(self):
        """Load known Amazon models as baseline"""
        print("📚 Loading known Amazon models...")
        
        for model_name, model_info in self.known_models.items():
            display_name = model_name.replace("amazon.titan-", "Titan ").replace("-v1", " v1").replace("-v2:0", " v2").title()
            
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="amazon",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=display_name
            )

if __name__ == "__main__":
    gatherer = AmazonGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()