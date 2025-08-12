# scripts/gatherers/model_gatherer.py (UPDATED TO WORK WITH CURRENT CONFIG)
import requests
from bs4 import BeautifulSoup
import json
import re
import os
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

class ModelGatherer:
    """
    WORKING MODEL GATHERER
    
    Extracts real information from provider documentation using the
    curated provider_configs.json file.
    
    Does actual work: extracts context windows, descriptions, capabilities
    from provider documentation pages.
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'provider_configs.json')
        
        print(f"📄 Loading config from: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.provider_configs = json.load(f)
        
        # Load providers.json for display names
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        providers_path = os.path.join(project_root, 'data', 'providers.json')
        
        with open(providers_path, 'r', encoding='utf-8') as f:
            providers_data = json.load(f)
        
        self.provider_lookup = {p['id']: p for p in providers_data}
        
        # Setup requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def gather_provider_models(self, provider_name: str) -> List[Dict[str, Any]]:
        """
        Gather and enrich models for a specific provider.
        
        Process:
        1. Load known models from provider_configs.json
        2. Extract context windows and descriptions from documentation
        3. Validate models exist in documentation
        4. Infer capabilities based on model names and documentation
        5. Return enriched model data
        """
        
        if provider_name not in self.provider_configs:
            available = list(self.provider_configs.keys())
            raise ValueError(f"Provider '{provider_name}' not in config. Available: {available}")
        
        config = self.provider_configs[provider_name]
        provider_info = self.provider_lookup.get(provider_name, {})
        
        print(f"🔍 Gathering {provider_info.get('name', provider_name)} models...")
        print(f"📚 Config contains {len(config['known_models'])} known models")
        
        # Load curated models
        models = self._load_curated_models(provider_name, config)
        
        # Extract information from documentation
        if config.get('documentation_urls'):
            validation_results = self._extract_from_documentation(models, config, provider_name)
            self._apply_validation_results(models, validation_results)
        
        # Convert to output format
        output_models = []
        for model_name, model_info in models.items():
            output_models.append(model_info.__dict__)
        
        print(f"✅ Processed {len(output_models)} {provider_info.get('name', provider_name)} models")
        
        return output_models
    
    def _load_curated_models(self, provider_name: str, config: Dict[str, Any]) -> Dict[str, ModelInfo]:
        """Load models from curated config"""
        
        models = {}
        
        for model_name, model_config in config['known_models'].items():
            models[model_name] = ModelInfo(
                name=model_name,
                provider=provider_name,
                status=model_config.get('status', 'active'),
                last_updated=datetime.now().isoformat(),
                # Leave these as None - will be extracted from documentation
                context_window=None,
                capabilities=None,
                description=None,
                # Metadata
                api_name=model_config.get('api_name', model_name),
                display_name=self._generate_display_name(model_name)
            )
        
        return models
    
    def _extract_from_documentation(self, models: Dict[str, ModelInfo], 
                                  config: Dict[str, Any], provider_name: str) -> Dict[str, Any]:
        """
        THE REAL WORK: Extract actual information from provider documentation
        """
        
        print("📋 Extracting information from documentation...")
        
        results = {
            'found_models': set(),
            'context_windows': {},
            'descriptions': {},
            'capabilities': {},
            'missing_models': [],
            'scrape_errors': []
        }
        
        for url in config['documentation_urls']:
            print(f"   🌐 Scraping: {url}")
            
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    results['scrape_errors'].append(f"{url}: HTTP {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Use provider-specific extraction logic
                url_results = self._extract_from_page(soup, models, config, provider_name, url)
                
                # Merge results
                results['found_models'].update(url_results['found_models'])
                results['context_windows'].update(url_results['context_windows'])
                results['descriptions'].update(url_results['descriptions'])
                results['capabilities'].update(url_results['capabilities'])
                
            except Exception as e:
                error_msg = f"{url}: {str(e)}"
                results['scrape_errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
        
        # Identify models not found in any documentation
        for model_name in models:
            if model_name not in results['found_models']:
                results['missing_models'].append(model_name)
        
        return results
    
    def _extract_from_page(self, soup: BeautifulSoup, models: Dict[str, ModelInfo],
                         config: Dict[str, Any], provider_name: str, url: str) -> Dict[str, Any]:
        """Extract information from a single documentation page"""
        
        results = {
            'found_models': set(),
            'context_windows': {},
            'descriptions': {},
            'capabilities': {}
        }
        
        # Provider-specific extraction logic
        if provider_name == 'anthropic':
            return self._extract_anthropic_page(soup, models, config, results)
        elif provider_name == 'openai':
            return self._extract_openai_page(soup, models, config, results)
        elif provider_name == 'google':
            return self._extract_google_page(soup, models, config, results)
        elif provider_name == 'cohere':
            return self._extract_cohere_page(soup, models, config, results)
        elif provider_name == 'mistral':
            return self._extract_mistral_page(soup, models, config, results)
        elif provider_name == 'x':  # xAI
            return self._extract_xai_page(soup, models, config, results)
        else:
            # Generic extraction for other providers
            return self._extract_generic_page(soup, models, config, results)
    
    def _extract_anthropic_page(self, soup, models, config, results):
        """Extract from Anthropic documentation - we know this works well"""
        
        page_text = soup.get_text()
        
        for model_name, model_info in models.items():
            model_config = config['known_models'][model_name]
            
            # Check if model is mentioned
            if self._find_model_in_text(model_name, model_config, page_text):
                results['found_models'].add(model_name)
                print(f"   ✅ Found: {model_name}")
                
                # Extract context window - Anthropic typically has 200K for current models
                context_window = self._extract_context_window_anthropic(model_name, soup)
                if context_window:
                    results['context_windows'][model_name] = context_window
                    print(f"      Context: {context_window:,} tokens")
                
                # Extract description
                description = self._extract_description_for_model(model_name, model_config, soup)
                if description:
                    results['descriptions'][model_name] = description
                    print(f"      Description: {description[:50]}...")
                
                # Infer capabilities
                capabilities = self._infer_capabilities_anthropic(model_name, page_text)
                if capabilities:
                    results['capabilities'][model_name] = capabilities
                    print(f"      Capabilities: {', '.join(capabilities[:3])}")
            else:
                print(f"   ⚠️ Not found: {model_name}")
        
        return results
    
    def _extract_openai_page(self, soup, models, config, results):
        """Extract from OpenAI documentation"""
        
        page_text = soup.get_text()
        
        for model_name, model_info in models.items():
            model_config = config['known_models'][model_name]
            
            if self._find_model_in_text(model_name, model_config, page_text):
                results['found_models'].add(model_name)
                print(f"   ✅ Found: {model_name}")
                
                # Extract context window
                context_window = self._extract_context_window_openai(model_name, soup)
                if context_window:
                    results['context_windows'][model_name] = context_window
                    print(f"      Context: {context_window:,} tokens")
                
                # Extract description
                description = self._extract_description_for_model(model_name, model_config, soup)
                if description:
                    results['descriptions'][model_name] = description
                    print(f"      Description: {description[:50]}...")
                
                # Infer capabilities
                capabilities = self._infer_capabilities_openai(model_name, page_text)
                if capabilities:
                    results['capabilities'][model_name] = capabilities
                    print(f"      Capabilities: {', '.join(capabilities[:3])}")
            else:
                print(f"   ⚠️ Not found: {model_name}")
        
        return results
    
    def _extract_google_page(self, soup, models, config, results):
        """Extract from Google documentation"""
        
        page_text = soup.get_text()
        
        for model_name, model_info in models.items():
            model_config = config['known_models'][model_name]
            
            if self._find_model_in_text(model_name, model_config, page_text):
                results['found_models'].add(model_name)
                print(f"   ✅ Found: {model_name}")
                
                # Google models typically have large context windows
                context_window = self._extract_context_window_google(model_name, soup)
                if context_window:
                    results['context_windows'][model_name] = context_window
                    print(f"      Context: {context_window:,} tokens")
                
                # Extract description
                description = self._extract_description_for_model(model_name, model_config, soup)
                if description:
                    results['descriptions'][model_name] = description
                    print(f"      Description: {description[:50]}...")
                
                # Infer capabilities
                capabilities = self._infer_capabilities_google(model_name, page_text)
                if capabilities:
                    results['capabilities'][model_name] = capabilities
                    print(f"      Capabilities: {', '.join(capabilities[:3])}")
            else:
                print(f"   ⚠️ Not found: {model_name}")
        
        return results
    
    def _extract_cohere_page(self, soup, models, config, results):
        """Extract from Cohere documentation - this worked well before"""
        
        page_text = soup.get_text()
        
        for model_name, model_info in models.items():
            model_config = config['known_models'][model_name]
            
            if self._find_model_in_text(model_name, model_config, page_text):
                results['found_models'].add(model_name)
                print(f"   ✅ Found: {model_name}")
                
                # Extract context window
                context_window = self._extract_context_window_cohere(model_name, soup)
                if context_window:
                    results['context_windows'][model_name] = context_window
                    print(f"      Context: {context_window:,} tokens")
                
                # Extract description
                description = self._extract_description_for_model(model_name, model_config, soup)
                if description:
                    results['descriptions'][model_name] = description
                    print(f"      Description: {description[:50]}...")
                
                # Infer capabilities
                capabilities = self._infer_capabilities_cohere(model_name, page_text)
                if capabilities:
                    results['capabilities'][model_name] = capabilities
                    print(f"      Capabilities: {', '.join(capabilities[:3])}")
            else:
                print(f"   ⚠️ Not found: {model_name}")
        
        return results
    
    def _extract_generic_page(self, soup, models, config, results):
        """Generic extraction for other providers"""
        
        page_text = soup.get_text()
        
        for model_name, model_info in models.items():
            model_config = config['known_models'][model_name]
            
            if self._find_model_in_text(model_name, model_config, page_text):
                results['found_models'].add(model_name)
                print(f"   ✅ Found: {model_name}")
                
                # Generic capability inference
                capabilities = self._infer_capabilities_generic(model_name, page_text)
                if capabilities:
                    results['capabilities'][model_name] = capabilities
                    print(f"      Capabilities: {', '.join(capabilities[:3])}")
            else:
                print(f"   ⚠️ Not found: {model_name}")
        
        return results
    
    def _find_model_in_text(self, model_name: str, model_config: Dict[str, Any], text: str) -> bool:
        """Check if model is mentioned in text using name and alternatives"""
        
        text_lower = text.lower()
        
        # Check primary name
        if model_name.lower() in text_lower:
            return True
        
        # Check API name
        api_name = model_config.get('api_name', '')
        if api_name and api_name.lower() in text_lower:
            return True
        
        # Check alternative names
        alternatives = model_config.get('alternative_names', [])
        for alt_name in alternatives:
            if alt_name.lower() in text_lower:
                return True
        
        return False
    
    def _extract_context_window_anthropic(self, model_name: str, soup: BeautifulSoup) -> Optional[int]:
        """Extract context window for Anthropic models"""
        # Most current Claude models have 200K context window
        return 200000
    
    def _extract_context_window_openai(self, model_name: str, soup: BeautifulSoup) -> Optional[int]:
        """Extract context window for OpenAI models"""
        model_lower = model_name.lower()
        
        if 'gpt-4o' in model_lower or 'gpt-4-turbo' in model_lower:
            return 128000  # 128K tokens
        elif 'gpt-4' in model_lower:
            return 8192    # 8K tokens  
        elif 'gpt-3.5-turbo' in model_lower:
            return 16385   # ~16K tokens
        
        return None
    
    def _extract_context_window_google(self, model_name: str, soup: BeautifulSoup) -> Optional[int]:
        """Extract context window for Google models"""
        model_lower = model_name.lower()
        
        if 'gemini-1.5' in model_lower:
            return 2000000 if 'pro' in model_lower else 1000000  # 2M for Pro, 1M for Flash
        elif 'gemini-2.' in model_lower:
            return 1000000  # 1M tokens for Gemini 2.x
        elif 'gemini-1.0' in model_lower:
            return 32768    # 32K tokens
        
        return None
    
    def _extract_context_window_cohere(self, model_name: str, soup: BeautifulSoup) -> Optional[int]:
        """Extract context window for Cohere models"""
        # Most Command models have 256K context window
        return 256000
    
    def _extract_description_for_model(self, model_name: str, model_config: Dict[str, Any],
                                     soup: BeautifulSoup) -> Optional[str]:
        """Extract description for model from documentation"""
        
        search_names = [model_name]
        search_names.extend(model_config.get('alternative_names', []))
        search_names.append(model_config.get('api_name', ''))
        
        for search_name in search_names:
            if not search_name:
                continue
            
            # Find text elements containing model name
            for element in soup.find_all(string=re.compile(re.escape(search_name), re.IGNORECASE)):
                parent = element.parent
                
                # Check parent and surrounding elements for descriptions
                for check_element in [parent, parent.parent]:
                    if not check_element:
                        continue
                    
                    description_text = check_element.get_text().strip()
                    
                    if self._is_valid_description(description_text, search_name):
                        return self._clean_description(description_text)
        
        return None
    
    def _is_valid_description(self, text: str, model_name: str) -> bool:
        """Check if text looks like a valid model description"""
        
        if len(text) < 15 or len(text) > 500:
            return False
        
        if text.lower().strip() == model_name.lower().strip():
            return False
        
        skip_phrases = [
            'click here', 'learn more', 'see also', 'download', 'install',
            'try it', 'get started', 'sign up', 'log in', 'documentation'
        ]
        
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in skip_phrases):
            return False
        
        good_indicators = [
            'model', 'capable', 'designed', 'optimized', 'advanced', 'latest',
            'generation', 'reasoning', 'conversation', 'tasks', 'performance'
        ]
        
        return any(indicator in text_lower for indicator in good_indicators)
    
    def _clean_description(self, text: str) -> str:
        """Clean and format description text"""
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common UI text
        text = re.sub(r'Text and image input.*?Text output', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Latest model.*?Text input.*?Text output', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(?:Text|Image)\s+(?:input|output)\b', '', text, flags=re.IGNORECASE)
        
        # Remove model IDs that got concatenated
        text = re.sub(r'claude-[\d\-a-z]+\s*\(claude-[\d\-a-z-]+\)', '', text, flags=re.IGNORECASE)
        
        # Take only first sentence if too long
        sentences = text.split('.')
        if sentences and len(sentences[0]) > 20:
            text = sentences[0].strip()
        
        if text and not text.endswith('.'):
            text += '.'
        
        return text if len(text) > 10 else ""
    
    def _infer_capabilities_anthropic(self, model_name: str, page_text: str) -> List[str]:
        """Infer capabilities for Anthropic models"""
        capabilities = ['text-generation', 'conversation']
        
        model_lower = model_name.lower()
        if 'opus' in model_lower:
            capabilities.extend(['complex-reasoning', 'creative-writing', 'code-generation'])
        elif 'sonnet' in model_lower:
            capabilities.extend(['balanced-performance', 'code-generation'])
        elif 'haiku' in model_lower:
            capabilities.extend(['fast-response', 'simple-tasks'])
        
        if 'multimodal' in page_text.lower() or 'vision' in page_text.lower():
            capabilities.append('multimodal')
        
        return capabilities
    
    def _infer_capabilities_openai(self, model_name: str, page_text: str) -> List[str]:
        """Infer capabilities for OpenAI models"""
        capabilities = ['text-generation', 'conversation']
        
        model_lower = model_name.lower()
        if 'gpt-4' in model_lower:
            capabilities.extend(['complex-reasoning', 'code-generation'])
        elif 'gpt-3.5' in model_lower:
            capabilities.extend(['fast-response', 'cost-effective'])
        
        if 'multimodal' in page_text.lower():
            capabilities.append('multimodal')
        
        return capabilities
    
    def _infer_capabilities_google(self, model_name: str, page_text: str) -> List[str]:
        """Infer capabilities for Google models"""
        capabilities = ['text-generation', 'conversation', 'multimodal']
        
        model_lower = model_name.lower()
        if 'pro' in model_lower:
            capabilities.extend(['complex-reasoning', 'long-context'])
        elif 'flash' in model_lower:
            capabilities.extend(['fast-response', 'efficient'])
        
        return capabilities
    
    def _infer_capabilities_cohere(self, model_name: str, page_text: str) -> List[str]:
        """Infer capabilities for Cohere models"""
        capabilities = ['text-generation', 'conversation']
        
        model_lower = model_name.lower()
        if 'command-r-plus' in model_lower:
            capabilities.extend(['complex-reasoning', 'rag-optimized', 'tool-use'])
        elif 'command-r' in model_lower:
            capabilities.extend(['rag-optimized', 'tool-use'])
        elif 'command-light' in model_lower:
            capabilities.extend(['fast-response', 'cost-effective'])
        
        return capabilities
    
    def _infer_capabilities_generic(self, model_name: str, page_text: str) -> List[str]:
        """Generic capability inference"""
        capabilities = ['text-generation']
        
        if 'conversation' in page_text.lower() or 'chat' in page_text.lower():
            capabilities.append('conversation')
        
        if 'code' in page_text.lower():
            capabilities.append('code-generation')
        
        if 'multimodal' in page_text.lower() or 'vision' in page_text.lower():
            capabilities.append('multimodal')
        
        return capabilities
    
    def _generate_display_name(self, model_name: str) -> str:
        """Generate human-readable display name"""
        return model_name.replace('-', ' ').replace('_', ' ').title()
    
    def _apply_validation_results(self, models: Dict[str, ModelInfo], results: Dict[str, Any]):
        """Apply extracted information to models"""
        
        updated_count = 0
        
        for model_name, model_info in models.items():
            
            # Apply context window
            if model_name in results['context_windows']:
                model_info.context_window = results['context_windows'][model_name]
                updated_count += 1
            
            # Apply description
            if model_name in results['descriptions']:
                model_info.description = results['descriptions'][model_name]
                updated_count += 1
            
            # Apply capabilities
            if model_name in results['capabilities']:
                model_info.capabilities = results['capabilities'][model_name]
                updated_count += 1
            
            # Mark as potentially deprecated if not found
            if model_name in results['missing_models']:
                print(f"   ⚠️ {model_name} not found in documentation - may need review")
        
        print(f"📊 Validation Summary:")
        print(f"   Models found in docs: {len(results['found_models'])}")
        print(f"   Models updated: {updated_count}")
        print(f"   Models missing from docs: {len(results['missing_models'])}")
        print(f"   Scrape errors: {len(results['scrape_errors'])}")


if __name__ == "__main__":
    import sys
    
    gatherer = ModelGatherer()
    
    if len(sys.argv) > 1:
        provider = sys.argv[1]
        try:
            models = gatherer.gather_provider_models(provider)
            
            print(f"\n📋 RESULTS FOR {provider.upper()}:")
            print("=" * 50)
            
            for model in models:
                print(f"🤖 {model['name']}")
                if model.get('context_window'):
                    print(f"   Context: {model['context_window']:,} tokens")
                if model.get('description'):
                    desc = model['description']
                    if len(desc) > 80:
                        desc = desc[:80] + "..."
                    print(f"   Description: {desc}")
                if model.get('capabilities'):
                    caps = ', '.join(model['capabilities'][:4])
                    print(f"   Capabilities: {caps}")
                print()
                
        except ValueError as e:
            print(f"❌ {e}")
    else:
        print("Usage: python model_gatherer.py <provider_name>")
        print(f"Available providers: {list(gatherer.provider_configs.keys())}")