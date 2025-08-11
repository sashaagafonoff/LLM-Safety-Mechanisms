# scripts/gatherers/update_models.py (updated for multiple providers)
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any
from anthropic_gatherer import AnthropicGatherer
from openai_gatherer import OpenAIGatherer

class ModelUpdater:
    def __init__(self, models_json_path: str = None):
        if models_json_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.models_json_path = os.path.join(project_root, 'data', 'models.json')
        else:
            self.models_json_path = models_json_path
            
        print(f"📄 Models file: {self.models_json_path}")
    
    def update_all_models(self):
        """Update models.json with latest models from all providers"""
        
        # Step 1: Backup existing models.json
        backup_path = self._create_backup()
        
        # Step 2: Load existing models
        existing_models = self._load_existing_models()
        
        # Step 3: Gather models from all providers
        print("\n" + "="*60)
        all_new_models = []
        
        # Gather Anthropic models
        print("🔍 Gathering Anthropic models...")
        anthropic_gatherer = AnthropicGatherer()
        anthropic_models = anthropic_gatherer.gather_models()
        all_new_models.extend(anthropic_models)
        
        # Gather OpenAI models
        print("\n🔍 Gathering OpenAI models...")
        openai_gatherer = OpenAIGatherer()
        openai_models = openai_gatherer.gather_models()
        all_new_models.extend(openai_models)
        
        print(f"\n📊 TOTAL GATHERED: {len(all_new_models)} models")
        print(f"   - Anthropic: {len(anthropic_models)}")
        print(f"   - OpenAI: {len(openai_models)}")
        
        # Step 4: Update the models data
        updated_models = self._merge_models(existing_models, all_new_models)
        
        # Step 5: Save updated models
        self._save_models(updated_models)
        
        # Step 6: Report changes
        self._report_changes(existing_models, updated_models, backup_path)
    
    def update_anthropic_models(self):
        """Update models.json with latest Anthropic models only"""
        backup_path = self._create_backup()
        existing_models = self._load_existing_models()
        
        print("\n" + "="*60)
        gatherer = AnthropicGatherer()
        new_anthropic_models = gatherer.gather_models()
        
        updated_models = self._merge_models(existing_models, new_anthropic_models)
        self._save_models(updated_models)
        self._report_changes(existing_models, updated_models, backup_path)
    
    def update_openai_models(self):
        """Update models.json with latest OpenAI models only"""
        backup_path = self._create_backup()
        existing_models = self._load_existing_models()
        
        print("\n" + "="*60)
        gatherer = OpenAIGatherer()
        new_openai_models = gatherer.gather_models()
        
        updated_models = self._merge_models(existing_models, new_openai_models)
        self._save_models(updated_models)
        self._report_changes(existing_models, updated_models, backup_path)
    
    def _create_backup(self) -> str:
        """Create backup of existing models.json"""
        if not os.path.exists(self.models_json_path):
            print("ℹ️  No existing models.json found - will create new file")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.models_json_path}.backup.{timestamp}"
        
        shutil.copy2(self.models_json_path, backup_path)
        print(f"💾 Backup created: {backup_path}")
        return backup_path
    
    def _load_existing_models(self) -> Dict[str, Any]:
        """Load existing models.json"""
        if not os.path.exists(self.models_json_path):
            return {"models": [], "last_updated": None}
            
        try:
            with open(self.models_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"📖 Loaded {len(data.get('models', []))} existing models")
            return data
            
        except Exception as e:
            print(f"❌ Error loading existing models: {e}")
            return {"models": [], "last_updated": None}
    
    def _merge_models(self, existing_data: Dict[str, Any], new_models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge new models with existing models"""
        
        existing_models = existing_data.get("models", [])
        
        # Create lookup for existing models by name
        existing_by_name = {model["name"]: model for model in existing_models}
        
        # Track changes by provider
        providers_processed = set(model["provider"] for model in new_models)
        changes = {provider: {"added": 0, "updated": 0, "retired": 0} for provider in providers_processed}
        
        # Process new models
        new_model_names_by_provider = {}
        for provider in providers_processed:
            new_model_names_by_provider[provider] = set()
        
        for new_model in new_models:
            model_name = new_model["name"]
            provider = new_model["provider"]
            new_model_names_by_provider[provider].add(model_name)
            
            if model_name in existing_by_name:
                # Update existing model
                existing_model = existing_by_name[model_name]
                if self._should_update_model(existing_model, new_model):
                    self._update_model_data(existing_model, new_model)
                    changes[provider]["updated"] += 1
            else:
                # Add new model
                existing_models.append(self._convert_to_models_json_format(new_model))
                changes[provider]["added"] += 1
        
        # Mark missing models as retired for each processed provider
        for model in existing_models:
            model_provider = model.get("provider")
            if (model_provider in providers_processed and 
                model["name"] not in new_model_names_by_provider[model_provider] and 
                model.get("status") != "retired"):
                model["status"] = "retired"
                model["last_updated"] = datetime.now().isoformat()
                changes[model_provider]["retired"] += 1
        
        print(f"\n📊 MERGE SUMMARY:")
        for provider, stats in changes.items():
            print(f"   {provider.upper()}:")
            print(f"     ➕ Added: {stats['added']} models")
            print(f"     🔄 Updated: {stats['updated']} models")
            print(f"     🚫 Retired: {stats['retired']} models")
        
        # Update metadata
        result = {
            "models": existing_models,
            "last_updated": datetime.now().isoformat(),
            "total_models": len(existing_models),
            "providers": sorted(list(set(model.get("provider", "unknown") for model in existing_models)))
        }
        
        return result
    
    def _should_update_model(self, existing: Dict[str, Any], new: Dict[str, Any]) -> bool:
        """Check if existing model should be updated with new data"""
        update_fields = ["context_window", "capabilities", "description", "api_name", "status"]
        
        for field in update_fields:
            if new.get(field) and new.get(field) != existing.get(field):
                return True
                
        return False
    
    def _update_model_data(self, existing: Dict[str, Any], new: Dict[str, Any]):
        """Update existing model with new data"""
        update_fields = ["context_window", "capabilities", "description", "status"]
        
        for field in update_fields:
            if new.get(field):
                existing[field] = new[field]
        
        existing["last_updated"] = new["last_updated"]
    
    def _convert_to_models_json_format(self, gatherer_model: Dict[str, Any]) -> Dict[str, Any]:
        """Convert gatherer model format to models.json format"""
        converted = {
            "name": gatherer_model["name"],
            "provider": gatherer_model["provider"],
            "status": gatherer_model["status"],
            "last_updated": gatherer_model["last_updated"]
        }
        
        # Add optional fields if present
        optional_fields = ["context_window", "capabilities", "description"]
        for field in optional_fields:
            if gatherer_model.get(field):
                converted[field] = gatherer_model[field]
        
        # Initialize empty safety mechanisms
        converted["safety_mechanisms"] = []
        
        return converted
    
    def _save_models(self, models_data: Dict[str, Any]):
        """Save updated models to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.models_json_path), exist_ok=True)
            
            with open(self.models_json_path, 'w', encoding='utf-8') as f:
                json.dump(models_data, f, indent=2, ensure_ascii=False)
                
            print(f"💾 Saved {len(models_data['models'])} models to {self.models_json_path}")
            
        except Exception as e:
            print(f"❌ Error saving models: {e}")
            raise
    
    def _report_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], backup_path: str):
        """Report what changed"""
        old_models = {m["name"]: m for m in old_data.get("models", [])}
        new_models = {m["name"]: m for m in new_data.get("models", [])}
        
        print(f"\n📋 CHANGE REPORT")
        print("="*50)
        
        # New models
        new_names = set(new_models.keys()) - set(old_models.keys())
        if new_names:
            print(f"\n➕ NEW MODELS ({len(new_names)}):")
            for name in sorted(new_names):
                model = new_models[name]
                print(f"   • {name} ({model.get('provider', 'unknown')})")
        
        # Updated models
        updated_names = []
        for name in set(old_models.keys()) & set(new_models.keys()):
            if old_models[name].get("last_updated") != new_models[name].get("last_updated"):
                updated_names.append(name)
        
        if updated_names:
            print(f"\n🔄 UPDATED MODELS ({len(updated_names)}):")
            for name in sorted(updated_names):
                print(f"   • {name}")
        
        # Retired models
        retired_names = []
        for name in new_models:
            old_status = old_models.get(name, {}).get("status")
            new_status = new_models[name].get("status")
            if old_status != "retired" and new_status == "retired":
                retired_names.append(name)
        
        if retired_names:
            print(f"\n🚫 RETIRED MODELS ({len(retired_names)}):")
            for name in sorted(retired_names):
                print(f"   • {name}")
        
        print(f"\n✅ Update completed successfully!")
        if backup_path:
            print(f"   Backup available at: {backup_path}")
        print(f"   Total models: {len(new_models)}")
        
        # Provider summary
        providers = {}
        for model in new_models.values():
            provider = model.get("provider", "unknown")
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"   Providers: {dict(providers)}")


if __name__ == "__main__":
    import sys
    
    updater = ModelUpdater()
    
    if len(sys.argv) > 1:
        provider = sys.argv[1].lower()
        if provider == "anthropic":
            updater.update_anthropic_models()
        elif provider == "openai":
            updater.update_openai_models()
        elif provider == "all":
            updater.update_all_models()
        else:
            print(f"Unknown provider: {provider}")
            print("Usage: python update_models.py [anthropic|openai|all]")
    else:
        # Default to all providers
        updater.update_all_models()