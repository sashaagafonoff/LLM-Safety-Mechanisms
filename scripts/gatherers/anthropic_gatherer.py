# scripts/gatherers/anthropic_gatherer.py
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

class AnthropicGatherer:
    def __init__(self):
        self.base_url = "https://docs.anthropic.com/claude/docs/models-overview"
        self.models = {}  # Use dict to avoid duplicates
        
    def gather_models(self) -> List[Dict[str, Any]]:
        """Main method to gather all Anthropic models"""
        print("🔍 Gathering Anthropic models...")
        
        try:
            response = requests.get(self.base_url, timeout=15)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract from different table types
            self._extract_availability_table(soup)
            self._extract_model_id_table(soup) 
            self._extract_capabilities_table(soup)
            self._extract_pricing_table(soup)
            
            # Convert to list and clean up
            models_list = list(self.models.values())
            self._post_process_models(models_list)
            
            print(f"✅ Found {len(models_list)} unique Anthropic models")
            return [model.__dict__ for model in models_list]
            
        except Exception as e:
            print(f"❌ Error gathering Anthropic models: {e}")
            return []
    
    def _extract_availability_table(self, soup):
        """Extract from model availability table (API/Bedrock/Vertex)"""
        tables = soup.find_all('table')
        
        for table in tables:
            headers = [th.get_text().strip().lower() for th in table.find_all('th')]
            
            if 'model' in headers and any('api' in h or 'bedrock' in h for h in headers):
                print(f"📋 Processing availability table")
                
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                    if len(cells) > 0 and cells[0]:  # First cell should be model name
                        model_name = self._clean_model_name(cells[0])
                        if model_name:
                            self._add_or_update_model(model_name, {
                                'display_name': cells[0],
                                'availability': cells[1:] if len(cells) > 1 else []
                            })
    
    def _extract_model_id_table(self, soup):
        """Extract from model ID mapping table"""
        tables = soup.find_all('table')
        
        for table in tables:
            headers = [th.get_text().strip().lower() for th in table.find_all('th')]
            
            if 'model id' in ' '.join(headers) or 'alias' in headers:
                print(f"📋 Processing model ID table")
                
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                    if len(cells) >= 2:
                        display_name = cells[0]
                        api_name = cells[-1]  # Usually last column
                        
                        if self._is_valid_api_name(api_name):
                            model_name = self._clean_model_name(display_name)
                            if model_name:
                                self._add_or_update_model(model_name, {
                                    'api_name': api_name,
                                    'display_name': display_name
                                })
    
    def _extract_capabilities_table(self, soup):
        """Extract from capabilities comparison table"""
        tables = soup.find_all('table')
        
        for table in tables:
            headers = [th.get_text().strip() for th in table.find_all('th')]
            
            # Look for tables with model names as headers
            model_headers = [h for h in headers if 'claude' in h.lower()]
            
            if len(model_headers) >= 2:  # Multiple Claude models as headers
                print(f"📋 Processing capabilities table")
                
                rows = table.find_all('tr')
                for row in rows:
                    cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                    if len(cells) > 1 and cells[0].lower() in ['context window', 'max tokens', 'context']:
                        # This row contains context window info
                        for i, model_header in enumerate(model_headers):
                            if i + 1 < len(cells):
                                context_text = cells[i + 1]
                                context_window = self._extract_context_window(context_text)
                                
                                model_name = self._clean_model_name(model_header)
                                if model_name and context_window:
                                    self._add_or_update_model(model_name, {
                                        'context_window': context_window,
                                        'display_name': model_header
                                    })
    
    def _extract_pricing_table(self, soup):
        """Extract additional info from pricing tables"""
        tables = soup.find_all('table')
        
        for table in tables:
            headers = [th.get_text().strip().lower() for th in table.find_all('th')]
            
            if 'input tokens' in ' '.join(headers) or 'output tokens' in ' '.join(headers):
                print(f"📋 Processing pricing table (for model validation)")
                # Use this to validate our model list, don't extract pricing for now
                pass
    
    def _clean_model_name(self, raw_name: str) -> str:
        """Clean and standardize model names"""
        if not raw_name:
            return ""
            
        # Remove extra whitespace and common prefixes
        name = raw_name.strip()
        
        # Skip if it doesn't contain "claude"
        if 'claude' not in name.lower():
            return ""
            
        # Prefer API names over display names for uniqueness
        if name.startswith('claude-'):
            return name
            
        # Convert display names to a standard format
        name = name.lower()
        name = re.sub(r'claude\s+', 'claude-', name)
        name = re.sub(r'\s+', '-', name)
        
        return name
    
    def _is_valid_api_name(self, name: str) -> bool:
        """Check if this looks like a valid API model name"""
        return bool(name and name.startswith('claude-') and re.search(r'\d', name))
    
    def _extract_context_window(self, text: str) -> Optional[int]:
        """Extract context window size from text"""
        if not text:
            return None
            
        # Look for patterns like "200K", "200,000", "200000"
        patterns = [
            r'(\d+)k\b',  # 200K
            r'(\d+),(\d+)',  # 200,000  
            r'(\d{3,})'  # 200000 (3+ digits)
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                if pattern == r'(\d+)k\b':
                    return int(matches[0]) * 1000
                elif pattern == r'(\d+),(\d+)':
                    return int(matches[0][0] + matches[0][1])
                else:
                    num = int(matches[0])
                    if num >= 1000:  # Only accept reasonable context window sizes
                        return num
        
        return None

    def _infer_context_window(self, model_name: str) -> Optional[int]:
        """Infer context window from model name if extraction fails"""
        model_lower = model_name.lower()
        
        # Known context windows for Claude model families
        if any(x in model_lower for x in ['claude-4', 'claude-3-5', 'claude-3-7']):
            return 200000  # 200K tokens
        elif 'claude-3-haiku' in model_lower:
            return 200000  # 200K tokens (updated in newer versions)
        elif 'claude-3' in model_lower:
            return 200000  # 200K tokens
        elif 'claude-2' in model_lower:
            return 100000  # 100K tokens
        elif 'claude-instant' in model_lower:
            return 100000  # 100K tokens
            
        return None  # Unknown, let extraction handle it
    
    def _add_or_update_model(self, model_name: str, data: Dict[str, Any]):
        """Add or update model information"""
        if not model_name:
            return
            
        if model_name not in self.models:
            self.models[model_name] = ModelInfo(
                name=model_name,
                provider="anthropic",
                status="active",
                last_updated=datetime.now().isoformat()
            )
        
        # Update with new data
        model = self.models[model_name]
        for key, value in data.items():
            if hasattr(model, key) and value:
                setattr(model, key, value)
    
    def _post_process_models(self, models: List[ModelInfo]):
        """Clean up and validate models after extraction"""
        for model in models:
            # Use API name as primary name if available
            if model.api_name and self._is_valid_api_name(model.api_name):
                model.name = model.api_name
            
            # Add basic capabilities based on model type
            if not model.capabilities:
                model.capabilities = self._infer_capabilities(model.name)
            
            # Add description if missing
            if not model.description:
                model.description = self._generate_description(model.name)
                
            # Infer context window if missing
            if not model.context_window:
                model.context_window = self._infer_context_window(model.name)
    
    def _infer_capabilities(self, model_name: str) -> List[str]:
        """Infer basic capabilities from model name"""
        capabilities = ["text-generation", "conversation"]
        
        if "opus" in model_name.lower():
            capabilities.extend(["complex-reasoning", "creative-writing", "code-generation"])
        elif "sonnet" in model_name.lower():
            capabilities.extend(["balanced-performance", "code-generation"])
        elif "haiku" in model_name.lower():
            capabilities.extend(["fast-response", "simple-tasks"])
            
        return capabilities
    
    def _generate_description(self, model_name: str) -> str:
        """Generate basic description from model name"""
        if "opus" in model_name.lower():
            return "Most capable Claude model for complex tasks"
        elif "sonnet" in model_name.lower():
            return "Balanced Claude model for most use cases"
        elif "haiku" in model_name.lower():
            return "Fast and efficient Claude model"
        else:
            return "Claude language model"

if __name__ == "__main__":
    gatherer = AnthropicGatherer()
    models = gatherer.gather_models()
    
    print(f"\n📊 FINAL RESULTS: {len(models)} models")
    for model in models:
        print(f"  🤖 {model['name']}")
        if model.get('api_name'):
            print(f"     API: {model['api_name']}")
        if model.get('context_window'):
            print(f"     Context: {model['context_window']:,} tokens")
        if model.get('capabilities'):
            print(f"     Capabilities: {', '.join(model['capabilities'][:3])}")
        print()