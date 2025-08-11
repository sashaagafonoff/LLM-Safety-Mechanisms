#!/usr/bin/env python3
"""
Base model gathering system for LLM Safety Mechanisms dataset.
Provides core functionality for fetching model information from providers.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class ModelInfo:
    """Model information matching the schema"""
    id: str
    providerId: str
    name: str
    family: str
    version: str  # Full API version identifier
    displayVersion: str  # Human-readable version
    releaseDate: str
    modalityType: str
    deploymentStatus: str
    contextWindow: Optional[int] = None
    lastVerified: Optional[str] = None
    aliases: Optional[List[str]] = None
    
    def __post_init__(self):
        """Set defaults after initialization"""
        if not self.lastVerified:
            self.lastVerified = datetime.now().strftime('%Y-%m-%d')
    
    def to_dict(self) -> Dict:
        """Convert to dictionary, excluding None values"""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}

class BaseModelGatherer(ABC):
    """Abstract base class for provider-specific model gatherers"""
    
    def __init__(self, provider_id: str, provider_name: str):
        self.provider_id = provider_id
        self.provider_name = provider_name
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LLM-Safety-Mechanisms-Gatherer/1.0'
        })
    
    @abstractmethod
    def fetch_models(self) -> List[ModelInfo]:
        """Fetch all current models from the provider"""
        pass
    
    @abstractmethod
    def get_source_urls(self) -> Dict[str, str]:
        """Return dict of source URLs used for gathering"""
        pass
    
    def fetch_url(self, url: str, timeout: int = 10) -> Optional[str]:
        """Fetch content from URL with error handling"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def parse_date(self, date_str: str) -> str:
        """Parse various date formats to YYYY-MM-DD"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        # Already in correct format?
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            return date_str
        
        # Parse different formats
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d", 
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse date: {date_str}")
        return date_str

class ModelDataManager:
    """Manages reading and writing model data files"""
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.models_file = data_dir / "models.json"
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load_current_models(self) -> Dict[str, Any]:
        """Load existing models indexed by ID"""
        if not self.models_file.exists():
            return {}
        
        with open(self.models_file, 'r') as f:
            models = json.load(f)
        
        return {m['id']: m for m in models}
    
    def save_models(self, models: List[Dict]):
        """Save models to file"""
        # Sort for consistency
        models.sort(key=lambda x: (
            x.get('providerId', ''),
            x.get('family', ''),
            x.get('releaseDate', ''),
            x.get('version', '')
        ))
        
        with open(self.models_file, 'w') as f:
            json.dump(models, f, indent=2)
        
        self.logger.info(f"Saved {len(models)} models to {self.models_file}")
    
    def update_provider_models(self, provider_id: str, new_models: List[ModelInfo]) -> Dict:
        """Update models for a specific provider"""
        current_models = self.load_current_models()
        
        # Track statistics
        stats = {
            'added': 0,
            'updated': 0,
            'unchanged': 0,
            'removed': 0
        }
        
        # Process new models
        updated_ids = set()
        for model in new_models:
            model_dict = model.to_dict()
            model_id = model.id
            updated_ids.add(model_id)
            
            if model_id in current_models:
                # Check if actually changed (ignoring lastVerified)
                existing = current_models[model_id].copy()
                existing.pop('lastVerified', None)
                new_dict = model_dict.copy()
                new_dict.pop('lastVerified', None)
                
                if existing != new_dict:
                    current_models[model_id] = model_dict
                    stats['updated'] += 1
                    self.logger.info(f"Updated: {model.name} {model.displayVersion}")
                else:
                    # Update lastVerified even if unchanged
                    current_models[model_id]['lastVerified'] = model_dict['lastVerified']
                    stats['unchanged'] += 1
            else:
                current_models[model_id] = model_dict
                stats['added'] += 1
                self.logger.info(f"Added: {model.name} {model.displayVersion}")
        
        # Check for removed models (models that exist for this provider but weren't in the update)
        for model_id, model in list(current_models.items()):
            if model.get('providerId') == provider_id and model_id not in updated_ids:
                # Mark as discontinued rather than deleting
                if model.get('deploymentStatus') not in ['discontinued', 'deprecated']:
                    current_models[model_id]['deploymentStatus'] = 'discontinued'
                    current_models[model_id]['lastVerified'] = datetime.now().strftime('%Y-%m-%d')
                    stats['removed'] += 1
                    self.logger.info(f"Marked discontinued: {model.get('name')} {model.get('displayVersion', '')}")
        
        # Save all models
        self.save_models(list(current_models.values()))
        
        return stats