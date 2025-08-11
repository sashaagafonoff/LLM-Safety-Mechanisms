# scripts/gatherers/gather_models.py
import importlib
import os
from typing import List, Dict, Any
from update_models import ModelUpdater

class ModelGatherOrchestrator:
    def __init__(self):
        self.gatherers = []
        self.updater = ModelUpdater()
        
    def register_gatherer(self, gatherer_class):
        """Register a gatherer class"""
        self.gatherers.append(gatherer_class)
        
    def discover_gatherers(self):
        """Auto-discover gatherer modules in this directory"""
        current_dir = os.path.dirname(__file__)
        
        for filename in os.listdir(current_dir):
            if filename.endswith('_gatherer.py') and filename != 'model_gatherer_base.py':
                module_name = filename[:-3]  # Remove .py
                try:
                    module = importlib.import_module(module_name)
                    # Look for gatherer class (assumes naming convention)
                    class_name = ''.join(word.capitalize() for word in module_name.split('_'))
                    if hasattr(module, class_name):
                        gatherer_class = getattr(module, class_name)
                        self.register_gatherer(gatherer_class)
                        print(f"📦 Discovered gatherer: {class_name}")
                except ImportError as e:
                    print(f"⚠️  Could not import {module_name}: {e}")
    
    def gather_all_models(self):
        """Run all registered gatherers and update models.json"""
        if not self.gatherers:
            self.discover_gatherers()
            
        print("🚀 Starting model gathering process...")
        print(f"   Found {len(self.gatherers)} gatherers")
        
        # For now, just run Anthropic (can be extended later)
        from anthropic_gatherer import AnthropicGatherer
        gatherer = AnthropicGatherer()
        
        # Use existing update logic
        self.updater.update_anthropic_models()
        
        print("✅ Model gathering completed!")

if __name__ == "__main__":
    orchestrator = ModelGatherOrchestrator()
    orchestrator.gather_all_models()