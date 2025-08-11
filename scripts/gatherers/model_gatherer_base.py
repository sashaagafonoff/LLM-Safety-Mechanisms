# scripts/gatherers/model_gatherer_base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ModelInfo:
    name: str
    provider: str
    status: str
    last_updated: str
    context_window: int = None
    capabilities: List[str] = None
    description: str = None
    api_name: str = None
    display_name: str = None

class ModelGathererBase(ABC):
    """Base class for all model gatherers"""
    
    @abstractmethod
    def gather_models(self) -> List[Dict[str, Any]]:
        """Gather models from this provider and return as list of dicts"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider identifier (e.g., 'anthropic', 'openai')"""
        pass
    
    def validate_model_info(self, model_dict: Dict[str, Any]) -> bool:
        """Validate that model info meets minimum requirements"""
        required_fields = ["name", "provider", "status", "last_updated"]
        return all(field in model_dict for field in required_fields)