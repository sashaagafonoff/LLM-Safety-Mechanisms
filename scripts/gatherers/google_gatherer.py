# scripts/gatherers/google_gatherer.py
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

class GoogleGatherer:
    def __init__(self):
        self.documentation_urls = [
            "https://ai.google.dev/models/gemini",
            "https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/overview"
        ]
        self.models = {}
        
        # Known Google models as of early 2025
        self.known_models = {
            "gemini-2.0-flash-exp": {
                "context_window": 1000000,
                "description": "Latest experimental Gemini 2.0 model with enhanced capabilities",
                "capabilities": ["text-generation", "conversation", "multimodal", "code-generation", "complex-reasoning"]
            },
            "gemini-1.5-pro": {
                "context_window": 2000000,
                "description": "Most capable Gemini model with 2M token context window",
                "capabilities": ["text-generation", "conversation", "multimodal", "code-generation", "complex-reasoning", "long-context"]
            },
            "gemini-1.5-flash": {
                "context_window": 1000000,
                "description": "Fast and versatile Gemini model optimized for speed",
                "capabilities": ["text-generation", "conversation", "multimodal", "code-generation", "fast-response"]
            },
            "gemini-1.5-flash-8b": {
                "context_window": 1000000,
                "description": "Smaller, more efficient version of Gemini 1.5 Flash",
                "capabilities": ["text-generation", "conversation", "multimodal", "fast-response", "cost-effective"]
            },
            "gemini-1.0-pro": {
                "context_window": 32768,
                "description": "Previous generation Gemini Pro model",
                "capabilities": ["text-generation", "conversation", "code-generation"]
            },
            "gemini-pro-vision": {
                "context_window": 16384,
                "description": "Gemini model optimized for vision tasks",
                "capabilities": ["text-generation", "multimodal", "vision", "image-analysis"]
            },
            "text-embedding-004": {
                "context_window": 2048,
                "description": "Google's text embedding model",
                "capabilities": ["text-embeddings", "semantic-search", "similarity"]
            },
            "text-embedding-gecko": {
                "context_window": 2048,
                "description": "Efficient embedding model for semantic tasks",
                "capabilities": ["text-embeddings", "semantic-search", "cost-effective"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all Google models"""
        print("🔍 Gathering Google models...")
        
        try:
            # Scrape documentation for updates
            scraped_models = self._scrape_documentation()
            
            # Use known models as base
            self._load_known_models()
            
            # Update with any scraped information
            if scraped_models:
                print(f"📋 Found {len(scraped_models)} models from documentation")
                for scraped_model in scraped_models:
                    self._update_with_scraped_info(scraped_model)
            else:
                print("📋 Using known model list as fallback")
            
            models_list = list(self.models.values())
            print(f"✅ Found {len(models_list)} unique Google models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering Google models: {e}")
            self._load_known_models()
            models_list = list(self.models.values())
            return [model.__dict__ for model in models_list]
    
    def _load_known_models(self):
        """Load known Google models as baseline"""
        print("📚 Loading known Google models...")
        
        for model_name, model_info in self.known_models.items():
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="google",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=model_name.replace("-", " ").title()
            )
    
    def _scrape_documentation(self) -> List[Dict[str, Any]]:
        """Scrape Google documentation for model information"""
        scraped_models = []
        
        for url in self.documentation_urls:
            try:
                print(f"📋 Scraping: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    models = self._extract_models_from_page(soup, url)
                    scraped_models.extend(models)
                else:
                    print(f"⚠️  Failed to access {url}: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
        
        return scraped_models
    
    def _extract_models_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract model information from documentation page"""
        models = []
        page_text = soup.get_text().lower()
        
        # Google model patterns
        patterns = [
            r'gemini-[0-9]+\.[0-9]+(?:-[a-z]+)+(?:-[a-z0-9]+)?',  # gemini-1.5-pro, gemini-2.0-flash-exp
            r'gemini-[a-z]+-[a-z]+',                              # gemini-pro-vision
            r'text-embedding-[a-z0-9]+',                          # text-embedding-004
            r'palm-[0-9]+',                                       # palm-2 (legacy)
            r'text-bison-[0-9]+',                                 # text-bison models
            r'code-bison-[0-9]+',                                 # code-bison models
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            for match in matches:
                models.append({
                    'name': match,
                    'source': 'text_extraction'
                })
        
        return models
    
    def _update_with_scraped_info(self, scraped_model: Dict[str, Any]):
        """Update known model with scraped information"""
        model_name = scraped_model['name']
        
        if model_name in self.models:
            model = self.models[model_name]
            model.last_updated = datetime.now().isoformat()
            print(f"🔄 Updated {model_name} with scraped info")

if __name__ == "__main__":
    gatherer = GoogleGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()