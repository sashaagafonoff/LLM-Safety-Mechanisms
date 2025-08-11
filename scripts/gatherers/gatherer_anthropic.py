#!/usr/bin/env python3
"""
Anthropic-specific model gatherer.
Fetches model information from Anthropic's documentation and API.
"""

import re
import json
from typing import List, Dict, Optional, Set
from datetime import datetime

from model_gatherer_base import BaseModelGatherer, ModelInfo

class AnthropicModelGatherer(BaseModelGatherer):
    """Gatherer for Anthropic Claude models"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("anthropic", "Anthropic")
        self.api_key = api_key
        
    def get_source_urls(self) -> Dict[str, str]:
        """Return source URLs for Anthropic models"""
        return {
            "docs": "https://docs.anthropic.com/en/docs/about-claude/models",
            "api_docs": "https://docs.anthropic.com/en/api/getting-started",
            "pricing": "https://www.anthropic.com/pricing"
        }
    
    def fetch_models(self) -> List[ModelInfo]:
        """Fetch current Claude models from Anthropic's sources"""
        all_models = []
        
        # Try documentation
        docs_url = self.get_source_urls()['docs']
        html_content = self.fetch_url(docs_url)
        
        if html_content:
            models = self._parse_documentation(html_content)
            all_models.extend(models)
        
        # Try pricing page as it often lists current models
        pricing_url = self.get_source_urls()['pricing']
        pricing_html = self.fetch_url(pricing_url)
        
        if pricing_html:
            pricing_models = self._parse_pricing_page(pricing_html)
            # Merge with existing, avoiding duplicates
            existing_versions = {m.version for m in all_models}
            for model in pricing_models:
                if model.version not in existing_versions:
                    all_models.append(model)
        
        if not all_models:
            self.logger.warning("No models found from any source")
        else:
            self.logger.info(f"Found {len(all_models)} total models")
        
        return all_models
    
    def _parse_documentation(self, html_content: str) -> List[ModelInfo]:
        """Parse any Claude model references from documentation"""
        models = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all strings that look like Claude model identifiers
            # These typically follow pattern: claude-[variant]-[version]-[date]
            # But we discover the pattern, not assume it
            
            model_versions = self._extract_model_versions(soup)
            
            # For each version found, try to extract surrounding context
            for version in model_versions:
                model_info = self._extract_model_info(version, soup)
                if model_info:
                    models.append(model_info)
            
            self.logger.info(f"Parsed {len(models)} models from documentation")
            
        except ImportError:
            self.logger.error("BeautifulSoup not installed. Install with: pip install beautifulsoup4")
        except Exception as e:
            self.logger.error(f"Error parsing documentation: {e}")
        
        return models
    
    def _extract_model_versions(self, soup) -> Set[str]:
        """Extract all potential model version strings from HTML"""
        versions = set()
        
        # Look for patterns in code blocks (where API identifiers are shown)
        for code in soup.find_all(['code', 'pre']):
            text = code.get_text().strip()
            # Match claude model patterns - more flexible regex
            matches = re.findall(r'claude-[a-z0-9\-\.]+', text)
            for match in matches:
                # Remove version suffixes like -v1, -v2
                clean_match = re.sub(r'-v\d+
    
    def _extract_model_info(self, version: str, soup) -> Optional[ModelInfo]:
        """Extract model information for a given version string"""
        
        # Parse the version string
        # Examples: claude-opus-4-1-20250805, claude-3-5-sonnet-20241022
        parts = version.split('-')
        
        variant = None
        version_nums = []
        release_date = None
        
        i = 1  # Skip 'claude' at index 0
        while i < len(parts):
            part = parts[i]
            
            # Check if it's a variant name
            if part in ['opus', 'sonnet', 'haiku']:
                variant = part.capitalize()
                i += 1
            # Check if it's a date (8 digits)
            elif len(part) == 8 and part.isdigit():
                release_date = f"{part[:4]}-{part[4:6]}-{part[6:]}"
                i += 1
            # Check if it's part of a version number
            elif part.isdigit() or (len(part) <= 2 and part.replace('.', '').isdigit()):
                # Look ahead to see if next part is also a number (like 4-1 for 4.1)
                if i + 1 < len(parts) and parts[i + 1].isdigit() and len(parts[i + 1]) <= 2:
                    version_nums.append(f"{part}.{parts[i + 1]}")
                    i += 2
                else:
                    version_nums.append(part)
                    i += 1
            else:
                # Skip suffixes like v1, v2, etc.
                i += 1
        
        if not variant or not release_date:
            return None
        
        # Build the name and display version
        if version_nums:
            # Format like "Claude Opus 4.1" or "Claude 3.5 Sonnet"
            version_str = '.'.join(version_nums) if len(version_nums) == 1 else version_nums[0]
            name = f"Claude {variant} {version_str}"
            display = f"{variant} {version_str}"
            family = f"Claude {version_str.split('.')[0]}"
        else:
            # Old format without version numbers
            name = f"Claude {variant}"
            display = variant
            family = "Claude 3"
        
        return ModelInfo(
            id=f"model-{version}",
            providerId=self.provider_id,
            name=name,
            family=family,
            version=version,
            displayVersion=display,
            releaseDate=release_date,
            modalityType="text",
            deploymentStatus="general-availability",
            contextWindow=200000
        )
    
    def _parse_pricing_page(self, html_content: str) -> List[ModelInfo]:
        """Parse the pricing page which often has current model list"""
        models = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Pricing pages often have model names in a structured format
            # Look for pricing tables or cards
            
            # Find elements that might contain model information
            model_elements = []
            
            # Check for pricing cards
            for element in soup.find_all(['div', 'section'], class_=re.compile(r'pricing|model|tier', re.I)):
                text = element.get_text()
                if 'claude' in text.lower():
                    model_elements.append(element)
            
            # Parse each element for model info
            for element in model_elements:
                model = self._parse_pricing_element(element)
                if model:
                    models.append(model)
            
        except Exception as e:
            self.logger.error(f"Error parsing pricing page: {e}")
        
        return models
    
    def _parse_pricing_element(self, element) -> Optional[ModelInfo]:
        """Parse a pricing element for model information"""
        text = element.get_text()
        
        # Look for model identifiers
        version_match = re.search(r'claude-[\w\-\.]+', text)
        if not version_match:
            return None
        
        version = version_match.group()
        
        # Try to extract pricing info which can help identify the model
        price_match = re.search(r'\$?([\d\.]+)\s*(?:\/|per)\s*(?:1M|million)', text, re.I)
        
        # Extract what we can from the text
        return self._extract_model_info(version, element)
    
    def _find_context_window_near(self, version: str, soup) -> Optional[int]:
        """Try to find context window size near a version string"""
        # Look for patterns like "200k", "200,000 tokens", etc.
        text = soup.get_text()
        
        # Find the version in the text and look nearby
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-200):idx+200]
            
            # Look for context window patterns
            patterns = [
                r'(\d+)[kK]\s*(?:tokens|context)',
                r'(\d{1,3}),?(\d{3})\s*(?:tokens|context)',
                r'context.*?(\d+)[kK]',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, nearby_text)
                if match:
                    if 'k' in pattern.lower():
                        return int(match.group(1)) * 1000
                    else:
                        return int(match.group(1) + match.group(2))
        
        return None
    
    def _find_status_near(self, version: str, soup) -> Optional[str]:
        """Try to determine deployment status from context"""
        text = soup.get_text()
        
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-100):idx+100].lower()
            
            if 'deprecated' in nearby_text:
                return 'deprecated'
            elif 'preview' in nearby_text or 'beta' in nearby_text:
                return 'preview'
            elif 'coming soon' in nearby_text or 'announced' in nearby_text:
                return 'announced'
        
        return None
    
    def _find_release_date_near(self, version: str, soup) -> Optional[str]:
        """Try to find a release date near the version string"""
        text = soup.get_text()
        
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-200):idx+200]
            
            # Look for date patterns
            date_patterns = [
                r'(?:released?|available|launched?)\s*(?:on\s*)?(\w+\s+\d{1,2},?\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, nearby_text, re.I)
                if match:
                    date_str = match.group(1)
                    # Try to parse and normalize the date
                    try:
                        # Try various formats
                        for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                            try:
                                dt = datetime.strptime(date_str.replace(',', ''), fmt)
                                return dt.strftime('%Y-%m-%d')
                            except ValueError:
                                continue
                    except:
                        pass
        
        return None


# Standalone execution for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path if running standalone
    sys.path.insert(0, str(Path(__file__).parent))
    
    from model_gatherer_base import ModelDataManager
    
    print("="*60)
    print("ANTHROPIC MODEL GATHERER")
    print("="*60)
    
    # Initialize gatherer
    gatherer = AnthropicModelGatherer()
    
    # Show sources
    print("\nSources:")
    for name, url in gatherer.get_source_urls().items():
        print(f"  {name}: {url}")
    
    # Fetch models
    print("\nFetching models from Anthropic's documentation...")
    models = gatherer.fetch_models()
    
    if models:
        print(f"\nFound {len(models)} models:")
        for model in models:
            print(f"\n  {model.name}")
            print(f"    Version: {model.version}")
            print(f"    Display: {model.displayVersion}")
            print(f"    Released: {model.releaseDate}")
            print(f"    Status: {model.deploymentStatus}")
            if model.contextWindow:
                print(f"    Context: {model.contextWindow:,} tokens")
    else:
        print("\nNo models found. This could mean:")
        print("  1. The documentation structure has changed")
        print("  2. Network/connection issues")
        print("  3. The parser needs updating")
    
    # Offer to update if models were found
    if models:
        response = input("\nUpdate data/models.json with these models? (y/n): ")
        if response.lower() == 'y':
            manager = ModelDataManager()
            stats = manager.update_provider_models("anthropic", models)
            print(f"\nUpdate complete:")
            print(f"  Added: {stats['added']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Unchanged: {stats['unchanged']}")
            print(f"  Discontinued: {stats['removed']}"), '', match)
                # Remove @ suffixes (AWS/GCP format)
                clean_match = clean_match.split('@')[0]
                # Filter out obvious non-models but be less restrictive
                if 'latest' not in clean_match and len(clean_match) > 8:
                    versions.add(clean_match)
        
        # Also check table cells directly
        for cell in soup.find_all(['td']):
            # Look for code elements within cells
            for code in cell.find_all('code'):
                text = code.get_text().strip()
                if text.startswith('claude-'):
                    # Remove parenthetical aliases
                    text = text.split('(')[0].strip()
                    # Remove version suffixes
                    text = re.sub(r'-v\d+
    
    def _extract_model_info(self, version: str, soup) -> Optional[ModelInfo]:
        """Extract model information for a given version string"""
        
        # Parse the version string
        # Examples: claude-opus-4-1-20250805, claude-3-5-sonnet-20241022
        parts = version.split('-')
        
        variant = None
        version_nums = []
        release_date = None
        
        i = 1  # Skip 'claude' at index 0
        while i < len(parts):
            part = parts[i]
            
            # Check if it's a variant name
            if part in ['opus', 'sonnet', 'haiku']:
                variant = part.capitalize()
                i += 1
            # Check if it's a date (8 digits)
            elif len(part) == 8 and part.isdigit():
                release_date = f"{part[:4]}-{part[4:6]}-{part[6:]}"
                i += 1
            # Check if it's part of a version number
            elif part.isdigit() or (len(part) <= 2 and part.replace('.', '').isdigit()):
                # Look ahead to see if next part is also a number (like 4-1 for 4.1)
                if i + 1 < len(parts) and parts[i + 1].isdigit() and len(parts[i + 1]) <= 2:
                    version_nums.append(f"{part}.{parts[i + 1]}")
                    i += 2
                else:
                    version_nums.append(part)
                    i += 1
            else:
                # Skip suffixes like v1, v2, etc.
                i += 1
        
        if not variant or not release_date:
            return None
        
        # Build the name and display version
        if version_nums:
            # Format like "Claude Opus 4.1" or "Claude 3.5 Sonnet"
            version_str = '.'.join(version_nums) if len(version_nums) == 1 else version_nums[0]
            name = f"Claude {variant} {version_str}"
            display = f"{variant} {version_str}"
            family = f"Claude {version_str.split('.')[0]}"
        else:
            # Old format without version numbers
            name = f"Claude {variant}"
            display = variant
            family = "Claude 3"
        
        return ModelInfo(
            id=f"model-{version}",
            providerId=self.provider_id,
            name=name,
            family=family,
            version=version,
            displayVersion=display,
            releaseDate=release_date,
            modalityType="text",
            deploymentStatus="general-availability",
            contextWindow=200000
        )
    
    def _parse_pricing_page(self, html_content: str) -> List[ModelInfo]:
        """Parse the pricing page which often has current model list"""
        models = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Pricing pages often have model names in a structured format
            # Look for pricing tables or cards
            
            # Find elements that might contain model information
            model_elements = []
            
            # Check for pricing cards
            for element in soup.find_all(['div', 'section'], class_=re.compile(r'pricing|model|tier', re.I)):
                text = element.get_text()
                if 'claude' in text.lower():
                    model_elements.append(element)
            
            # Parse each element for model info
            for element in model_elements:
                model = self._parse_pricing_element(element)
                if model:
                    models.append(model)
            
        except Exception as e:
            self.logger.error(f"Error parsing pricing page: {e}")
        
        return models
    
    def _parse_pricing_element(self, element) -> Optional[ModelInfo]:
        """Parse a pricing element for model information"""
        text = element.get_text()
        
        # Look for model identifiers
        version_match = re.search(r'claude-[\w\-\.]+', text)
        if not version_match:
            return None
        
        version = version_match.group()
        
        # Try to extract pricing info which can help identify the model
        price_match = re.search(r'\$?([\d\.]+)\s*(?:\/|per)\s*(?:1M|million)', text, re.I)
        
        # Extract what we can from the text
        return self._extract_model_info(version, element)
    
    def _find_context_window_near(self, version: str, soup) -> Optional[int]:
        """Try to find context window size near a version string"""
        # Look for patterns like "200k", "200,000 tokens", etc.
        text = soup.get_text()
        
        # Find the version in the text and look nearby
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-200):idx+200]
            
            # Look for context window patterns
            patterns = [
                r'(\d+)[kK]\s*(?:tokens|context)',
                r'(\d{1,3}),?(\d{3})\s*(?:tokens|context)',
                r'context.*?(\d+)[kK]',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, nearby_text)
                if match:
                    if 'k' in pattern.lower():
                        return int(match.group(1)) * 1000
                    else:
                        return int(match.group(1) + match.group(2))
        
        return None
    
    def _find_status_near(self, version: str, soup) -> Optional[str]:
        """Try to determine deployment status from context"""
        text = soup.get_text()
        
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-100):idx+100].lower()
            
            if 'deprecated' in nearby_text:
                return 'deprecated'
            elif 'preview' in nearby_text or 'beta' in nearby_text:
                return 'preview'
            elif 'coming soon' in nearby_text or 'announced' in nearby_text:
                return 'announced'
        
        return None
    
    def _find_release_date_near(self, version: str, soup) -> Optional[str]:
        """Try to find a release date near the version string"""
        text = soup.get_text()
        
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-200):idx+200]
            
            # Look for date patterns
            date_patterns = [
                r'(?:released?|available|launched?)\s*(?:on\s*)?(\w+\s+\d{1,2},?\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, nearby_text, re.I)
                if match:
                    date_str = match.group(1)
                    # Try to parse and normalize the date
                    try:
                        # Try various formats
                        for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                            try:
                                dt = datetime.strptime(date_str.replace(',', ''), fmt)
                                return dt.strftime('%Y-%m-%d')
                            except ValueError:
                                continue
                    except:
                        pass
        
        return None


# Standalone execution for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path if running standalone
    sys.path.insert(0, str(Path(__file__).parent))
    
    from model_gatherer_base import ModelDataManager
    
    print("="*60)
    print("ANTHROPIC MODEL GATHERER")
    print("="*60)
    
    # Initialize gatherer
    gatherer = AnthropicModelGatherer()
    
    # Show sources
    print("\nSources:")
    for name, url in gatherer.get_source_urls().items():
        print(f"  {name}: {url}")
    
    # Fetch models
    print("\nFetching models from Anthropic's documentation...")
    models = gatherer.fetch_models()
    
    if models:
        print(f"\nFound {len(models)} models:")
        for model in models:
            print(f"\n  {model.name}")
            print(f"    Version: {model.version}")
            print(f"    Display: {model.displayVersion}")
            print(f"    Released: {model.releaseDate}")
            print(f"    Status: {model.deploymentStatus}")
            if model.contextWindow:
                print(f"    Context: {model.contextWindow:,} tokens")
    else:
        print("\nNo models found. This could mean:")
        print("  1. The documentation structure has changed")
        print("  2. Network/connection issues")
        print("  3. The parser needs updating")
    
    # Offer to update if models were found
    if models:
        response = input("\nUpdate data/models.json with these models? (y/n): ")
        if response.lower() == 'y':
            manager = ModelDataManager()
            stats = manager.update_provider_models("anthropic", models)
            print(f"\nUpdate complete:")
            print(f"  Added: {stats['added']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Unchanged: {stats['unchanged']}")
            print(f"  Discontinued: {stats['removed']}"), '', text)
                    # Remove @ suffixes
                    text = text.split('@')[0]
                    if 'latest' not in text and len(text) > 8:
                        versions.add(text)
        
        # Filter out obvious non-models
        filtered_versions = set()
        for v in versions:
            # Skip if it contains common non-model suffixes
            skip_patterns = ['api', 'sdk', 'python', 'node', 'docs', 'example', 'latest']
            if not any(pattern in v.lower() for pattern in skip_patterns):
                # Skip versions that end with just -0 or -20 (incomplete dates)
                if not re.search(r'-\d{1,2}
    
    def _extract_model_info(self, version: str, soup) -> Optional[ModelInfo]:
        """Extract model information for a given version string"""
        
        # Parse the version string
        # Examples: claude-opus-4-1-20250805, claude-3-5-sonnet-20241022
        parts = version.split('-')
        
        variant = None
        version_nums = []
        release_date = None
        
        i = 1  # Skip 'claude' at index 0
        while i < len(parts):
            part = parts[i]
            
            # Check if it's a variant name
            if part in ['opus', 'sonnet', 'haiku']:
                variant = part.capitalize()
                i += 1
            # Check if it's a date (8 digits)
            elif len(part) == 8 and part.isdigit():
                release_date = f"{part[:4]}-{part[4:6]}-{part[6:]}"
                i += 1
            # Check if it's part of a version number
            elif part.isdigit() or (len(part) <= 2 and part.replace('.', '').isdigit()):
                # Look ahead to see if next part is also a number (like 4-1 for 4.1)
                if i + 1 < len(parts) and parts[i + 1].isdigit() and len(parts[i + 1]) <= 2:
                    version_nums.append(f"{part}.{parts[i + 1]}")
                    i += 2
                else:
                    version_nums.append(part)
                    i += 1
            else:
                # Skip suffixes like v1, v2, etc.
                i += 1
        
        if not variant or not release_date:
            return None
        
        # Build the name and display version
        if version_nums:
            # Format like "Claude Opus 4.1" or "Claude 3.5 Sonnet"
            version_str = '.'.join(version_nums) if len(version_nums) == 1 else version_nums[0]
            name = f"Claude {variant} {version_str}"
            display = f"{variant} {version_str}"
            family = f"Claude {version_str.split('.')[0]}"
        else:
            # Old format without version numbers
            name = f"Claude {variant}"
            display = variant
            family = "Claude 3"
        
        return ModelInfo(
            id=f"model-{version}",
            providerId=self.provider_id,
            name=name,
            family=family,
            version=version,
            displayVersion=display,
            releaseDate=release_date,
            modalityType="text",
            deploymentStatus="general-availability",
            contextWindow=200000
        )
    
    def _parse_pricing_page(self, html_content: str) -> List[ModelInfo]:
        """Parse the pricing page which often has current model list"""
        models = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Pricing pages often have model names in a structured format
            # Look for pricing tables or cards
            
            # Find elements that might contain model information
            model_elements = []
            
            # Check for pricing cards
            for element in soup.find_all(['div', 'section'], class_=re.compile(r'pricing|model|tier', re.I)):
                text = element.get_text()
                if 'claude' in text.lower():
                    model_elements.append(element)
            
            # Parse each element for model info
            for element in model_elements:
                model = self._parse_pricing_element(element)
                if model:
                    models.append(model)
            
        except Exception as e:
            self.logger.error(f"Error parsing pricing page: {e}")
        
        return models
    
    def _parse_pricing_element(self, element) -> Optional[ModelInfo]:
        """Parse a pricing element for model information"""
        text = element.get_text()
        
        # Look for model identifiers
        version_match = re.search(r'claude-[\w\-\.]+', text)
        if not version_match:
            return None
        
        version = version_match.group()
        
        # Try to extract pricing info which can help identify the model
        price_match = re.search(r'\$?([\d\.]+)\s*(?:\/|per)\s*(?:1M|million)', text, re.I)
        
        # Extract what we can from the text
        return self._extract_model_info(version, element)
    
    def _find_context_window_near(self, version: str, soup) -> Optional[int]:
        """Try to find context window size near a version string"""
        # Look for patterns like "200k", "200,000 tokens", etc.
        text = soup.get_text()
        
        # Find the version in the text and look nearby
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-200):idx+200]
            
            # Look for context window patterns
            patterns = [
                r'(\d+)[kK]\s*(?:tokens|context)',
                r'(\d{1,3}),?(\d{3})\s*(?:tokens|context)',
                r'context.*?(\d+)[kK]',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, nearby_text)
                if match:
                    if 'k' in pattern.lower():
                        return int(match.group(1)) * 1000
                    else:
                        return int(match.group(1) + match.group(2))
        
        return None
    
    def _find_status_near(self, version: str, soup) -> Optional[str]:
        """Try to determine deployment status from context"""
        text = soup.get_text()
        
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-100):idx+100].lower()
            
            if 'deprecated' in nearby_text:
                return 'deprecated'
            elif 'preview' in nearby_text or 'beta' in nearby_text:
                return 'preview'
            elif 'coming soon' in nearby_text or 'announced' in nearby_text:
                return 'announced'
        
        return None
    
    def _find_release_date_near(self, version: str, soup) -> Optional[str]:
        """Try to find a release date near the version string"""
        text = soup.get_text()
        
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-200):idx+200]
            
            # Look for date patterns
            date_patterns = [
                r'(?:released?|available|launched?)\s*(?:on\s*)?(\w+\s+\d{1,2},?\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, nearby_text, re.I)
                if match:
                    date_str = match.group(1)
                    # Try to parse and normalize the date
                    try:
                        # Try various formats
                        for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                            try:
                                dt = datetime.strptime(date_str.replace(',', ''), fmt)
                                return dt.strftime('%Y-%m-%d')
                            except ValueError:
                                continue
                    except:
                        pass
        
        return None


# Standalone execution for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path if running standalone
    sys.path.insert(0, str(Path(__file__).parent))
    
    from model_gatherer_base import ModelDataManager
    
    print("="*60)
    print("ANTHROPIC MODEL GATHERER")
    print("="*60)
    
    # Initialize gatherer
    gatherer = AnthropicModelGatherer()
    
    # Show sources
    print("\nSources:")
    for name, url in gatherer.get_source_urls().items():
        print(f"  {name}: {url}")
    
    # Fetch models
    print("\nFetching models from Anthropic's documentation...")
    models = gatherer.fetch_models()
    
    if models:
        print(f"\nFound {len(models)} models:")
        for model in models:
            print(f"\n  {model.name}")
            print(f"    Version: {model.version}")
            print(f"    Display: {model.displayVersion}")
            print(f"    Released: {model.releaseDate}")
            print(f"    Status: {model.deploymentStatus}")
            if model.contextWindow:
                print(f"    Context: {model.contextWindow:,} tokens")
    else:
        print("\nNo models found. This could mean:")
        print("  1. The documentation structure has changed")
        print("  2. Network/connection issues")
        print("  3. The parser needs updating")
    
    # Offer to update if models were found
    if models:
        response = input("\nUpdate data/models.json with these models? (y/n): ")
        if response.lower() == 'y':
            manager = ModelDataManager()
            stats = manager.update_provider_models("anthropic", models)
            print(f"\nUpdate complete:")
            print(f"  Added: {stats['added']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Unchanged: {stats['unchanged']}")
            print(f"  Discontinued: {stats['removed']}"), v):
                    filtered_versions.add(v)
        
        self.logger.info(f"Found potential versions: {filtered_versions}")
        return filtered_versions
    
    def _extract_model_info(self, version: str, soup) -> Optional[ModelInfo]:
        """Extract model information for a given version string"""
        
        # Parse the version string
        # Examples: claude-opus-4-1-20250805, claude-3-5-sonnet-20241022
        parts = version.split('-')
        
        variant = None
        version_nums = []
        release_date = None
        
        i = 1  # Skip 'claude' at index 0
        while i < len(parts):
            part = parts[i]
            
            # Check if it's a variant name
            if part in ['opus', 'sonnet', 'haiku']:
                variant = part.capitalize()
                i += 1
            # Check if it's a date (8 digits)
            elif len(part) == 8 and part.isdigit():
                release_date = f"{part[:4]}-{part[4:6]}-{part[6:]}"
                i += 1
            # Check if it's part of a version number
            elif part.isdigit() or (len(part) <= 2 and part.replace('.', '').isdigit()):
                # Look ahead to see if next part is also a number (like 4-1 for 4.1)
                if i + 1 < len(parts) and parts[i + 1].isdigit() and len(parts[i + 1]) <= 2:
                    version_nums.append(f"{part}.{parts[i + 1]}")
                    i += 2
                else:
                    version_nums.append(part)
                    i += 1
            else:
                # Skip suffixes like v1, v2, etc.
                i += 1
        
        if not variant or not release_date:
            return None
        
        # Build the name and display version
        if version_nums:
            # Format like "Claude Opus 4.1" or "Claude 3.5 Sonnet"
            version_str = '.'.join(version_nums) if len(version_nums) == 1 else version_nums[0]
            name = f"Claude {variant} {version_str}"
            display = f"{variant} {version_str}"
            family = f"Claude {version_str.split('.')[0]}"
        else:
            # Old format without version numbers
            name = f"Claude {variant}"
            display = variant
            family = "Claude 3"
        
        return ModelInfo(
            id=f"model-{version}",
            providerId=self.provider_id,
            name=name,
            family=family,
            version=version,
            displayVersion=display,
            releaseDate=release_date,
            modalityType="text",
            deploymentStatus="general-availability",
            contextWindow=200000
        )
    
    def _parse_pricing_page(self, html_content: str) -> List[ModelInfo]:
        """Parse the pricing page which often has current model list"""
        models = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Pricing pages often have model names in a structured format
            # Look for pricing tables or cards
            
            # Find elements that might contain model information
            model_elements = []
            
            # Check for pricing cards
            for element in soup.find_all(['div', 'section'], class_=re.compile(r'pricing|model|tier', re.I)):
                text = element.get_text()
                if 'claude' in text.lower():
                    model_elements.append(element)
            
            # Parse each element for model info
            for element in model_elements:
                model = self._parse_pricing_element(element)
                if model:
                    models.append(model)
            
        except Exception as e:
            self.logger.error(f"Error parsing pricing page: {e}")
        
        return models
    
    def _parse_pricing_element(self, element) -> Optional[ModelInfo]:
        """Parse a pricing element for model information"""
        text = element.get_text()
        
        # Look for model identifiers
        version_match = re.search(r'claude-[\w\-\.]+', text)
        if not version_match:
            return None
        
        version = version_match.group()
        
        # Try to extract pricing info which can help identify the model
        price_match = re.search(r'\$?([\d\.]+)\s*(?:\/|per)\s*(?:1M|million)', text, re.I)
        
        # Extract what we can from the text
        return self._extract_model_info(version, element)
    
    def _find_context_window_near(self, version: str, soup) -> Optional[int]:
        """Try to find context window size near a version string"""
        # Look for patterns like "200k", "200,000 tokens", etc.
        text = soup.get_text()
        
        # Find the version in the text and look nearby
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-200):idx+200]
            
            # Look for context window patterns
            patterns = [
                r'(\d+)[kK]\s*(?:tokens|context)',
                r'(\d{1,3}),?(\d{3})\s*(?:tokens|context)',
                r'context.*?(\d+)[kK]',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, nearby_text)
                if match:
                    if 'k' in pattern.lower():
                        return int(match.group(1)) * 1000
                    else:
                        return int(match.group(1) + match.group(2))
        
        return None
    
    def _find_status_near(self, version: str, soup) -> Optional[str]:
        """Try to determine deployment status from context"""
        text = soup.get_text()
        
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-100):idx+100].lower()
            
            if 'deprecated' in nearby_text:
                return 'deprecated'
            elif 'preview' in nearby_text or 'beta' in nearby_text:
                return 'preview'
            elif 'coming soon' in nearby_text or 'announced' in nearby_text:
                return 'announced'
        
        return None
    
    def _find_release_date_near(self, version: str, soup) -> Optional[str]:
        """Try to find a release date near the version string"""
        text = soup.get_text()
        
        if version in text:
            idx = text.index(version)
            nearby_text = text[max(0, idx-200):idx+200]
            
            # Look for date patterns
            date_patterns = [
                r'(?:released?|available|launched?)\s*(?:on\s*)?(\w+\s+\d{1,2},?\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, nearby_text, re.I)
                if match:
                    date_str = match.group(1)
                    # Try to parse and normalize the date
                    try:
                        # Try various formats
                        for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                            try:
                                dt = datetime.strptime(date_str.replace(',', ''), fmt)
                                return dt.strftime('%Y-%m-%d')
                            except ValueError:
                                continue
                    except:
                        pass
        
        return None


# Standalone execution for testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add parent directory to path if running standalone
    sys.path.insert(0, str(Path(__file__).parent))
    
    from model_gatherer_base import ModelDataManager
    
    print("="*60)
    print("ANTHROPIC MODEL GATHERER")
    print("="*60)
    
    # Initialize gatherer
    gatherer = AnthropicModelGatherer()
    
    # Show sources
    print("\nSources:")
    for name, url in gatherer.get_source_urls().items():
        print(f"  {name}: {url}")
    
    # Fetch models
    print("\nFetching models from Anthropic's documentation...")
    models = gatherer.fetch_models()
    
    if models:
        print(f"\nFound {len(models)} models:")
        for model in models:
            print(f"\n  {model.name}")
            print(f"    Version: {model.version}")
            print(f"    Display: {model.displayVersion}")
            print(f"    Released: {model.releaseDate}")
            print(f"    Status: {model.deploymentStatus}")
            if model.contextWindow:
                print(f"    Context: {model.contextWindow:,} tokens")
    else:
        print("\nNo models found. This could mean:")
        print("  1. The documentation structure has changed")
        print("  2. Network/connection issues")
        print("  3. The parser needs updating")
    
    # Offer to update if models were found
    if models:
        response = input("\nUpdate data/models.json with these models? (y/n): ")
        if response.lower() == 'y':
            manager = ModelDataManager()
            stats = manager.update_provider_models("anthropic", models)
            print(f"\nUpdate complete:")
            print(f"  Added: {stats['added']}")
            print(f"  Updated: {stats['updated']}")
            print(f"  Unchanged: {stats['unchanged']}")
            print(f"  Discontinued: {stats['removed']}")