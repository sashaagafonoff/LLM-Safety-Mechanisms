import json

def add_techniques():
    """Add the techniques from your original dataset"""
    
    techniques_to_add = [
        {
            "id": "tech-csam-detection",
            "name": "CSAM Detection & Removal",
            "categoryId": "cat-pre-training-safety",
            "description": "Automated detection and removal of child sexual abuse material",
            "implementationMethods": ["EmbeddedClassifier", "ExternalSafetyService"],
            "governingStandards": ["NCMEC"],
            "licence": None,
            "knownLimitations": ["False positive rates not disclosed"],
            "aliases": ["CSAM Filtering"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1]
        },
        {
            "id": "tech-rlhf",
            "name": "Reinforcement Learning from Human Feedback",
            "categoryId": "cat-alignment",
            "description": "Training models to align with human preferences through feedback",
            "implementationMethods": ["HumanModeration", "EmbeddedClassifier"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Subject to annotator biases", "Expensive to scale"],
            "aliases": ["RLHF"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 5]
        }
        # Add more...
    ]
    
    # First add the alignment category if needed
    with open('data/categories.json', 'r') as f:
        categories = json.load(f)
    
    if not any(c['id'] == 'cat-alignment' for c in categories):
        categories.append({
            "id": "cat-alignment",
            "name": "Alignment Methods",
            "description": "Techniques for aligning model behavior with human values",
            "phase": "training",
            "parentCategoryId": None,
            "riskAreaIds": [1, 2, 5, 10]
        })
        
        with open('data/categories.json', 'w') as f:
            json.dump(categories, f, indent=2)
    
    # Add techniques
    with open('data/techniques.json', 'r') as f:
        techniques = json.load(f)
    
    techniques.extend(techniques_to_add)
    
    with open('data/techniques.json', 'w') as f:
        json.dump(techniques, f, indent=2)
    
    print(f"✅ Added {len(techniques_to_add)} techniques")

if __name__ == "__main__":
    add_techniques()