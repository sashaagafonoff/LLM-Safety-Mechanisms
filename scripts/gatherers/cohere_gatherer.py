# scripts/gatherers/cohere_gatherer.py
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

class CohereGatherer:
    def __init__(self):
        self.models = {}
        
        # Known Cohere models as of early 2025
        self.known_models = {
            "command-r-plus": {
                "context_window": 128000,
                "description": "Most capable Command model for complex tasks",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "rag-optimized", "tool-use"]
            },
            "command-r": {
                "context_window": 128000,
                "description": "Balanced Command model for general use",
                "capabilities": ["text-generation", "conversation", "rag-optimized", "tool-use", "cost-effective"]
            },
            "command-light": {
                "context_window": 4096,
                "description": "Lightweight Command model for simple tasks",
                "capabilities": ["text-generation", "conversation", "fast-response", "cost-effective"]
            },
            "command": {
                "context_window": 4096,
                "description": "Standard Command model",
                "capabilities": ["text-generation", "conversation", "general-purpose"]
            },
            "embed-v3": {
                "context_window": 512,
                "description": "Latest embedding model with improved performance",
                "capabilities": ["text-embeddings", "semantic-search", "similarity", "multilingual"]
            },
            "embed-english-v3": {
                "context_window": 512,
                "description": "English-optimized embedding model",
                "capabilities": ["text-embeddings", "semantic-search", "similarity", "english-optimized"]
            },
            "embed-multilingual-v3": {
                "context_window": 512,
                "description": "Multilingual embedding model",
                "capabilities": ["text-embeddings", "semantic-search", "similarity", "multilingual"]
            },
            "rerank-v3": {
                "context_window": 4096,
                "description": "Document reranking model for search applications",
                "capabilities": ["reranking", "search-optimization", "relevance-scoring"]
            },
            "rerank-english-v3": {
                "context_window": 4096,
                "description": "English-optimized reranking model",
                "capabilities": ["reranking", "search-optimization", "relevance-scoring", "english-optimized"]
            },
            "rerank-multilingual-v3": {
                "context_window": 4096,
                "description": "Multilingual reranking model",
                "capabilities": ["reranking", "search-optimization", "relevance-scoring", "multilingual"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all Cohere models"""
        print("🔍 Gathering Cohere models...")
        
        try:
            self._load_known_models()
            models_list = list(self.models.values())
            print(f"✅ Found {len(models_list)} unique Cohere models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering Cohere models: {e}")
            return []
    
    def _load_known_models(self):
        """Load known Cohere models as baseline"""
        print("📚 Loading known Cohere models...")
        
        for model_name, model_info in self.known_models.items():
            display_name = model_name.replace("-", " ").title()
            
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="cohere",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=display_name
            )

if __name__ == "__main__":
    gatherer = CohereGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()