import json
import jsonschema
from pathlib import Path
import sys


def load_json(filepath):
    """Load JSON file with proper error handling"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        return None
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None


def validate_dataset():
    """Validate all data files against schema"""
    # Use Path for cross-platform compatibility
    project_root = Path(__file__).parent.parent

    # Load schema
    schema_path = project_root / "schema" / "llm-safety-v1.1.0.json"
    schema = load_json(schema_path)
    if not schema:
        return False

    # Load all data files
    data_files = {
        "providers": "data/providers.json",
        "models": "data/models.json",
        "categories": "data/categories.json",
        "techniques": "data/techniques.json",
        "evidence": "data/evidence.json",
        "riskAreas": "data/risk_areas.json",
    }

    dataset = {
        "version": "1.0.0",
        "lastUpdated": "2024-01-01T00:00:00Z",
        "generatedAt": "2024-01-01T00:00:00Z",
        "datasetHash": "0" * 64,  # Placeholder
    }

    # Load each data file
    all_valid = True
    for key, filepath in data_files.items():
        full_path = project_root / filepath
        data = load_json(full_path)
        if data is None:
            all_valid = False
            continue
        dataset[key] = data
        print(f"✅ Loaded {key}: {len(data)} records")

    # Validate against schema
    try:
        jsonschema.validate(dataset, schema)
        print("\n✅ Dataset validates against schema!")
    except jsonschema.ValidationError as e:
        print(f"\n❌ Schema validation failed: {e.message}")
        print(f"   Path: {' -> '.join(str(p) for p in e.path)}")
        all_valid = False

    return all_valid


if __name__ == "__main__":
    if validate_dataset():
        print("\n🎉 All validations passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Validation failed!")
        sys.exit(1)
