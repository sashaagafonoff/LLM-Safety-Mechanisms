# scripts/gatherers/update_models.py (REFACTORED)
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any
from model_gatherer import ModelGatherer

class ModelUpdater:
    """
    REFACTORED MODEL UPDATER
    
    Builds models.json from provider_configs.json using real data extraction.
    No more relying on old crappy data - everything comes from curated configs
    and live documentation extraction.
    """
    
    def __init__(self, models_json_path: str = None):
        if models_json_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.models_json_path = os.path.join(project_root, 'data', 'models.json')
        else:
            self.models_json_path = models_json_path
            
        print(f"📄 Target models file: {self.models_json_path}")
        
        # Initialize the working model gatherer
        self.gatherer = ModelGatherer()
        self.available_providers = list(self.gatherer.provider_configs.keys())
        
        print(f"📋 Available providers: {self.available_providers}")
    
    def build_models_from_config(self, specific_providers: List[str] = None):
        """
        Build models.json from scratch using provider_configs.json
        
        This is the main method that:
        1. Gathers models from each provider using real extraction
        2. Builds a complete models.json from scratch
        3. No dependency on old/existing models.json data
        """
        
        # Step 1: Backup existing models.json if it exists
        backup_path = self._create_backup()
        
        # Step 2: Determine which providers to process
        if specific_providers:
            # Validate specified providers
            invalid_providers = [p for p in specific_providers if p not in self.available_providers]
            if invalid_providers:
                print(f"❌ Invalid providers: {invalid_providers}")
                print(f"   Available: {self.available_providers}")
                return
            providers_to_process = specific_providers
        else:
            providers_to_process = self.available_providers
        
        print(f"\n🚀 BUILDING MODELS FROM CONFIG")
        print("=" * 60)
        print(f"Processing providers: {providers_to_process}")
        print("=" * 60)
        
        # Step 3: Gather models from each provider
        all_models = []
        provider_stats = {}
        
        for provider_name in providers_to_process:
            print(f"\n🔍 Processing {provider_name.upper()}...")
            
            try:
                # Use the working model gatherer to extract real data
                provider_models = self.gatherer.gather_provider_models(provider_name)
                
                # Convert to models.json format and add to collection
                for model_data in provider_models:
                    model_entry = self._convert_to_models_json_format(model_data)
                    all_models.append(model_entry)
                
                provider_stats[provider_name] = len(provider_models)
                print(f"✅ {provider_name}: {len(provider_models)} models processed")
                
            except Exception as e:
                print(f"❌ Error processing {provider_name}: {e}")
                provider_stats[provider_name] = 0
        
        # Step 4: Build the complete models.json structure
        models_data = {
            "models": all_models,
            "last_updated": datetime.now().isoformat(),
            "total_models": len(all_models),
            "providers": sorted(provider_stats.keys()),
            "build_info": {
                "method": "built_from_provider_configs",
                "extraction_date": datetime.now().isoformat(),
                "provider_stats": provider_stats
            }
        }
        
        # Step 5: Save the new models.json
        self._save_models(models_data)
        
        # Step 6: Report results
        self._report_build_results(models_data, provider_stats, backup_path)
    
    def update_specific_providers(self, provider_names: List[str]):
        """Update specific providers while preserving others"""
        
        # Load existing models.json
        existing_data = self._load_existing_models()
        if not existing_data.get('models'):
            print("📝 No existing models.json found - building from scratch")
            return self.build_models_from_config(provider_names)
        
        backup_path = self._create_backup()
        existing_models = existing_data['models']
        
        # Remove models from providers being updated
        filtered_models = [
            model for model in existing_models 
            if model['provider'] not in provider_names
        ]
        
        print(f"🔄 Updating providers: {provider_names}")
        print(f"   Keeping {len(filtered_models)} models from other providers")
        print(f"   Removing {len(existing_models) - len(filtered_models)} models from updating providers")
        
        # Add fresh models from specified providers
        for provider_name in provider_names:
            print(f"\n🔍 Refreshing {provider_name.upper()}...")
            
            try:
                provider_models = self.gatherer.gather_provider_models(provider_name)
                
                for model_data in provider_models:
                    model_entry = self._convert_to_models_json_format(model_data)
                    filtered_models.append(model_entry)
                
                print(f"✅ {provider_name}: {len(provider_models)} models added")
                
            except Exception as e:
                print(f"❌ Error updating {provider_name}: {e}")
        
        # Build updated models.json
        updated_data = {
            "models": filtered_models,
            "last_updated": datetime.now().isoformat(),
            "total_models": len(filtered_models),
            "providers": sorted(list(set(model['provider'] for model in filtered_models))),
            "update_info": {
                "method": "selective_provider_update",
                "updated_providers": provider_names,
                "update_date": datetime.now().isoformat()
            }
        }
        
        self._save_models(updated_data)
        self._report_update_results(existing_data, updated_data, provider_names, backup_path)
    
    def _convert_to_models_json_format(self, gatherer_model: Dict[str, Any]) -> Dict[str, Any]:
        """Convert model_gatherer output to models.json format"""
        
        # Build the model entry with only valid fields
        model_entry = {
            "name": gatherer_model["name"],
            "provider": gatherer_model["provider"], 
            "status": gatherer_model.get("status", "active"),
            "last_updated": gatherer_model["last_updated"],
            "safety_mechanisms": []  # Empty for now - will be populated by safety research
        }
        
        # Add optional fields if they exist and are valid
        if gatherer_model.get("context_window"):
            model_entry["context_window"] = gatherer_model["context_window"]
            
        if gatherer_model.get("capabilities") and isinstance(gatherer_model["capabilities"], list):
            model_entry["capabilities"] = gatherer_model["capabilities"]
            
        if gatherer_model.get("description") and len(gatherer_model["description"].strip()) > 0:
            model_entry["description"] = gatherer_model["description"].strip()
        
        return model_entry
    
    def _create_backup(self) -> str:
        """Create backup of existing models.json if it exists"""
        
        if not os.path.exists(self.models_json_path):
            print("ℹ️  No existing models.json found - creating new file")
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
                
            print(f"📖 Loaded existing models.json with {len(data.get('models', []))} models")
            return data
            
        except Exception as e:
            print(f"❌ Error loading existing models: {e}")
            return {"models": [], "last_updated": None}
    
    def _save_models(self, models_data: Dict[str, Any]):
        """Save models.json"""
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.models_json_path), exist_ok=True)
            
            # Save with pretty formatting
            with open(self.models_json_path, 'w', encoding='utf-8') as f:
                json.dump(models_data, f, indent=2, ensure_ascii=False)
                
            print(f"💾 Saved {len(models_data['models'])} models to {self.models_json_path}")
            
        except Exception as e:
            print(f"❌ Error saving models: {e}")
            raise
    
    def _report_build_results(self, models_data: Dict[str, Any], provider_stats: Dict[str, int], backup_path: str):
        """Report results of building models.json from scratch"""
        
        print(f"\n📊 BUILD COMPLETE")
        print("=" * 50)
        print(f"✅ Built models.json from scratch using provider_configs.json")
        print(f"   Total models: {models_data['total_models']}")
        print(f"   Providers: {len(models_data['providers'])}")
        
        if backup_path:
            print(f"   Previous version backed up to: {backup_path}")
        
        print(f"\n📋 PROVIDER BREAKDOWN:")
        total_extracted = 0
        for provider, count in sorted(provider_stats.items()):
            print(f"   • {provider}: {count} models")
            total_extracted += count
        
        print(f"\n🎯 DATA QUALITY:")
        models_with_context = len([m for m in models_data['models'] if m.get('context_window')])
        models_with_description = len([m for m in models_data['models'] if m.get('description')])
        models_with_capabilities = len([m for m in models_data['models'] if m.get('capabilities')])
        
        print(f"   Models with context windows: {models_with_context}/{total_extracted}")
        print(f"   Models with descriptions: {models_with_description}/{total_extracted}")
        print(f"   Models with capabilities: {models_with_capabilities}/{total_extracted}")
        
        print(f"\n🚀 Ready for safety mechanism research!")
    
    def _report_update_results(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                             updated_providers: List[str], backup_path: str):
        """Report results of selective provider update"""
        
        old_count = len(old_data.get('models', []))
        new_count = len(new_data.get('models', []))
        
        print(f"\n📊 UPDATE COMPLETE")
        print("=" * 50)
        print(f"✅ Updated providers: {', '.join(updated_providers)}")
        print(f"   Models before: {old_count}")
        print(f"   Models after: {new_count}")
        print(f"   Net change: {new_count - old_count:+d}")
        
        if backup_path:
            print(f"   Backup available: {backup_path}")


if __name__ == "__main__":
    import sys
    
    updater = ModelUpdater()
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "build":
            # Build from scratch
            if len(sys.argv) > 2:
                # Build specific providers
                providers = [p.lower() for p in sys.argv[2:]]
                updater.build_models_from_config(providers)
            else:
                # Build all providers
                updater.build_models_from_config()
        
        elif sys.argv[1].lower() == "update":
            # Update specific providers
            if len(sys.argv) > 2:
                providers = [p.lower() for p in sys.argv[2:]]
                updater.update_specific_providers(providers)
            else:
                print("Usage: python update_models.py update <provider1> <provider2> ...")
        else:
            # Treat as provider names for updating
            providers = [p.lower() for p in sys.argv[1:]]
            updater.update_specific_providers(providers)
    
    else:
        # Default: build from scratch
        print("🏗️  No arguments provided - building models.json from scratch")
        updater.build_models_from_config()