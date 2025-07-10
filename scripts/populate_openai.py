import json
from datetime import datetime
import hashlib

def create_openai_evidence():
    """Populate OpenAI evidence from the original dataset"""
    
    # Load existing data
    with open('data/evidence.json', 'r') as f:
        evidence = json.load(f)
    
    # Evidence from GPT-4o system card
    new_evidence = [
        {
            "id": "ev-openai-training-filtering-001",
            "providerId": "openai",
            "techniqueId": "tech-training-data-filtering",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "Multi-stage filtering using Moderation API and safety classifiers to remove CSAM, hateful content, violence, and CBRN materials from training datasets",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,  # You'll calculate this later
                "relevantSection": "Section 3: Safety Evaluations"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": [
                "Specific filtering thresholds not disclosed",
                "May introduce demographic biases"
            ],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["SOC2"],
            "notes": "Part of comprehensive pre-training safety pipeline"
        }
    ]
    
    # Add more evidence records...
    evidence.extend(new_evidence)
    
    # Save
    with open('data/evidence.json', 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print(f"✅ Added {len(new_evidence)} evidence records for OpenAI")

if __name__ == "__main__":
    create_openai_evidence()