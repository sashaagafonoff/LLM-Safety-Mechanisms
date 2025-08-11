# scripts/gatherers/openai_gatherer.py (updated version)
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

class OpenAIGatherer:
    def __init__(self):
        self.documentation_urls = [
            "https://platform.openai.com/docs/models",
        ]
        self.models = {}
        
        # Known OpenAI models as fallback (current as of early 2025)
        self.known_models = {
            "gpt-4o": {
                "context_window": 128000,
                "description": "Most advanced GPT-4 model, optimized for chat and complex tasks",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "code-generation", "multimodal"]
            },
            "gpt-4o-mini": {
                "context_window": 128000,
                "description": "Smaller, faster version of GPT-4o",
                "capabilities": ["text-generation", "conversation", "code-generation", "fast-response"]
            },
            "gpt-4-turbo": {
                "context_window": 128000,
                "description": "Latest GPT-4 Turbo model with improved performance",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "code-generation", "multimodal"]
            },
            "gpt-4": {
                "context_window": 8192,
                "description": "Most capable GPT-4 model for complex, multi-step tasks",
                "capabilities": ["text-generation", "conversation", "complex-reasoning", "code-generation"]
            },
            "gpt-3.5-turbo": {
                "context_window": 16385,
                "description": "Most capable GPT-3.5 model and optimized for chat",
                "capabilities": ["text-generation", "conversation", "code-generation", "fast-response", "cost-effective"]
            },
            "dall-e-3": {
                "context_window": None,
                "description": "Most advanced image generation model",
                "capabilities": ["image-generation", "creative-ai"]
            },
            "dall-e-2": {
                "context_window": None,
                "description": "Image generation model",
                "capabilities": ["image-generation", "creative-ai"]
            },
            "whisper-1": {
                "context_window": None,
                "description": "Speech recognition model",
                "capabilities": ["speech-to-text", "transcription", "audio-processing"]
            },
            "tts-1": {
                "context_window": None,
                "description": "Text-to-speech model",
                "capabilities": ["text-to-speech", "voice-synthesis"]
            },
            "tts-1-hd": {
                "context_window": None,
                "description": "Higher quality text-to-speech model",
                "capabilities": ["text-to-speech", "voice-synthesis", "high-quality"]
            },
            "text-embedding-3-large": {
                "context_window": 8191,
                "description": "Most capable embedding model",
                "capabilities": ["text-embeddings", "semantic-search", "similarity"]
            },
            "text-embedding-3-small": {
                "context_window": 8191,
                "description": "Smaller, more efficient embedding model",
                "capabilities": ["text-embeddings", "semantic-search", "cost-effective"]
            },
            "text-embedding-ada-002": {
                "context_window": 8191,
                "description": "Previous generation embedding model",
                "capabilities": ["text-embeddings", "semantic-search"]
            }
        }
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all OpenAI models"""
        print("🔍 Gathering OpenAI models...")
        
        try:
            # Try to scrape documentation for updates
            scraped_models = self._scrape_documentation()
            
            # Use known models as base, update with scraped info
            self._load_known_models()
            
            # Update with any scraped information
            if scraped_models:
                print(f"📋 Found {len(scraped_models)} models from documentation")
                for scraped_model in scraped_models:
                    self._update_with_scraped_info(scraped_model)
            else:
                print("📋 Using known model list as fallback")
            
            # Convert to list and clean up
            models_list = list(self.models.values())
            
            print(f"✅ Found {len(models_list)} unique OpenAI models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering OpenAI models: {e}")
            # Still return known models even if scraping fails
            self._load_known_models()
            models_list = list(self.models.values())
            return [model.__dict__ for model in models_list]
    
    def _load_known_models(self):
        """Load known OpenAI models as baseline"""
        print("📚 Loading known OpenAI models...")
        
        for model_name, model_info in self.known_models.items():
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="openai",
                status="active",
                last_updated=datetime.now().isoformat(),
                context_window=model_info.get("context_window"),
                capabilities=model_info.get("capabilities"),
                description=model_info.get("description"),
                api_name=model_name,
                display_name=model_name.upper()
            )
    
    def _scrape_documentation(self) -> List[Dict[str, Any]]:
        """Scrape OpenAI documentation for model information"""
        scraped_models = []
        
        for url in self.documentation_urls:
            try:
                print(f"📋 Scraping: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract model information from various page elements
                    models = self._extract_models_from_page(soup, url)
                    scraped_models.extend(models)
                    
                else:
                    print(f"⚠️  Failed to access {url}: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
        
        return scraped_models
    
    def _extract_models_from_page(self, soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
        """Extract model information from a documentation page"""
        models = []
        
        # Method 1: Look for code blocks with model names
        code_blocks = soup.find_all(['code', 'pre'])
        for code in code_blocks:
            text = code.get_text()
            model_matches = self._find_models_in_text(text)
            models.extend(model_matches)
        
        # Method 2: Look for tables
        tables = soup.find_all('table')
        for table in tables:
            table_models = self._extract_from_table(table)
            models.extend(table_models)
        
        # Method 3: Look in headings and paragraphs
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li']):
            text = element.get_text()
            model_matches = self._find_models_in_text(text)
            models.extend(model_matches)
        
        # Remove duplicates
        unique_models = []
        seen_names = set()
        for model in models:
            if model['name'] not in seen_names:
                unique_models.append(model)
                seen_names.add(model['name'])
        
        return unique_models
    
    def _find_models_in_text(self, text: str) -> List[Dict[str, Any]]:
        """Find OpenAI model names in text"""
        models = []
        
        # Improved patterns for OpenAI models
        patterns = [
            r'gpt-4o(?:-mini|-2024-\d{2}-\d{2})?',          # gpt-4o, gpt-4o-mini, gpt-4o-2024-08-06
            r'gpt-4(?:-turbo)?(?:-2024-\d{2}-\d{2})?',      # gpt-4, gpt-4-turbo, gpt-4-2024-04-09
            r'gpt-3\.5-turbo(?:-\d{4}-\d{2}-\d{2})?',       # gpt-3.5-turbo, gpt-3.5-turbo-0125
            r'dall-e-[23]',                                 # dall-e-2, dall-e-3
            r'whisper-1',                                    # whisper-1
            r'tts-1(?:-hd)?',                               # tts-1, tts-1-hd
            r'text-embedding-(?:3-(?:large|small)|ada-002)' # text-embedding-3-large, etc.
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                models.append({
                    'name': match.lower(),
                    'source': 'text_extraction'
                })
        
        return models
    
    def _extract_from_table(self, table) -> List[Dict[str, Any]]:
        """Extract model information from HTML table"""
        models = []
        
        try:
            rows = table.find_all('tr')
            if len(rows) < 2:  # Need at least header + 1 data row
                return models
            
            # Get headers
            header_row = rows[0]
            headers = [th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])]
            
            # Look for model-related tables
            if not any(keyword in ' '.join(headers) for keyword in ['model', 'name', 'gpt']):
                return models
            
            # Process data rows
            for row in rows[1:]:
                cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                if cells:
                    # Look for model names in first few columns
                    for cell in cells[:3]:  # Check first 3 columns
                        model_matches = self._find_models_in_text(cell)
                        models.extend(model_matches)
                        
        except Exception as e:
            print(f"⚠️  Error processing table: {e}")
        
        return models
    
    def _update_with_scraped_info(self, scraped_model: Dict[str, Any]):
        """Update known model with scraped information"""
        model_name = scraped_model['name']
        
        if model_name in self.models:
            # Update existing model with any new information
            model = self.models[model_name]
            model.last_updated = datetime.now().isoformat()
            print(f"🔄 Updated {model_name} with scraped info")
        else:
            # Add new model found in documentation
            print(f"➕ Found new model in docs: {model_name}")
            # But don't add it without proper validation - OpenAI docs might mention experimental models

if __name__ == "__main__":
    gatherer = OpenAIGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()