#!/usr/bin/env python3
"""
Main script to gather and update model information from all providers.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from model_gatherer_base import ModelDataManager
from gatherer_anthropic import AnthropicModelGatherer

# Import other gatherers as they're created
# from gatherer_openai import OpenAIModelGatherer
# from gatherer_google import GoogleModelGatherer
# from gatherer_meta import MetaModelGatherer

def main():
    """Main execution function"""
    
    parser = argparse.ArgumentParser(description='Update LLM model information')
    parser.add_argument(
        '--provider',
        choices=['all', 'anthropic', 'openai', 'google', 'meta', 'amazon'],
        default='all',
        help='Which provider to update (default: all)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed logging'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("LLM MODEL INFORMATION GATHERER")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Initialize data manager
    manager = ModelDataManager()
    
    # Define available gatherers
    gatherers = {
        'anthropic': AnthropicModelGatherer,
        # 'openai': OpenAIModelGatherer,  # To be implemented
        # 'google': GoogleModelGatherer,   # To be implemented
        # 'meta': MetaModelGatherer,       # To be implemented
    }
    
    # Determine which providers to update
    if args.provider == 'all':
        providers_to_update = list(gatherers.keys())
    else:
        providers_to_update = [args.provider] if args.provider in gatherers else []
    
    if not providers_to_update:
        print(f"Error: No gatherer available for provider '{args.provider}'")
        return 1
    
    # Process each provider
    total_stats = {
        'added': 0,
        'updated': 0,
        'unchanged': 0,
        'removed': 0
    }
    
    for provider_id in providers_to_update:
        print(f"\n{'='*40}")
        print(f"Processing: {provider_id.upper()}")
        print('='*40)
        
        try:
            # Initialize gatherer
            gatherer_class = gatherers[provider_id]
            gatherer = gatherer_class()
            
            # Show source URLs
            sources = gatherer.get_source_urls()
            print(f"Sources:")
            for name, url in sources.items():
                print(f"  - {name}: {url}")
            
            # Fetch models
            print(f"\nFetching models...")
            models = gatherer.fetch_models()
            
            if not models:
                print("  No models found")
                continue
            
            print(f"  Found {len(models)} models")
            
            if args.verbose:
                for model in models:
                    print(f"    - {model.name} ({model.displayVersion}) - {model.deploymentStatus}")
            
            # Update database (unless dry run)
            if args.dry_run:
                print("\n[DRY RUN] Would update with:")
                for model in models:
                    print(f"  - {model.name} {model.displayVersion}")
                    print(f"    Version: {model.version}")
                    print(f"    Status: {model.deploymentStatus}")
            else:
                print(f"\nUpdating models.json...")
                stats = manager.update_provider_models(provider_id, models)
                
                # Update totals
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)
                
                # Show results
                print(f"Results:")
                print(f"  Added: {stats['added']}")
                print(f"  Updated: {stats['updated']}")
                print(f"  Unchanged: {stats['unchanged']}")
                print(f"  Marked discontinued: {stats['removed']}")
        
        except Exception as e:
            print(f"ERROR processing {provider_id}: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            continue
    
    # Show final summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total changes across all providers:")
    print(f"  Added: {total_stats['added']}")
    print(f"  Updated: {total_stats['updated']}")
    print(f"  Unchanged: {total_stats['unchanged']}")
    print(f"  Marked discontinued: {total_stats['removed']}")
    
    if args.dry_run:
        print("\n[DRY RUN] No changes were made")
    else:
        print(f"\nModels updated in: data/models.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())