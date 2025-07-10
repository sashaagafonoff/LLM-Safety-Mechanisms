import json
import re
from datetime import datetime

class EvidenceExtractor:
    def __init__(self):
        self.load_data()
    
    def load_data(self):
        """Load all necessary data files"""
        with open('data/providers.json', 'r') as f:
            self.providers = {p['id']: p for p in json.load(f)}
        
        with open('data/techniques.json', 'r') as f:
            self.techniques = {t['id']: t for t in json.load(f)}
        
        with open('data/models.json', 'r') as f:
            self.models = json.load(f)
    
    def create_evidence_template(self, provider_id, technique_id):
        """Generate evidence template for easy filling"""
        return {
            "id": f"ev-{provider_id}-{technique_id}-XXX",
            "providerId": provider_id,
            "techniqueId": technique_id,
            "modelIds": [],  # Fill with specific models
            "rating": "medium",  # Adjust based on evidence
            "severityBand": "C",  # C=Claimed, update when verified
            "ratingCriteria": {
                "publiclyDocumented": False,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "",  # Fill from source
            "evidenceLevel": "claimed",
            "sourceUrls": [{
                "url": "",  # Add URL
                "documentType": "blog-post",  # Update type
                "lastVerified": datetime.now().strftime('%Y-%m-%d'),
                "sourceHash": "0" * 64,
                "relevantSection": ""
            }],
            "implementationDate": None,
            "lastReviewed": datetime.now().strftime('%Y-%m-%d'),
            "reviewFrequency": "P6M",
            "reviewer": "manual-entry",
            "evaluationMetrics": [],
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        }
    
    def quick_add(self, provider_id, technique_id, url, summary):
        """Quick way to add evidence"""
        template = self.create_evidence_template(provider_id, technique_id)
        template['sourceUrls'][0]['url'] = url
        template['summary'] = summary
        
        # Generate unique ID
        existing = len([e for e in self.get_evidence() 
                       if e['providerId'] == provider_id 
                       and e['techniqueId'] == technique_id])
        template['id'] = f"ev-{provider_id}-{technique_id}-{existing+1:03d}"
        
        return template
    
    def get_evidence(self):
        with open('data/evidence.json', 'r') as f:
            return json.load(f)
    
    def save_evidence(self, evidence_list):
        with open('data/evidence.json', 'w') as f:
            json.dump(evidence_list, f, indent=2)

# Example usage
if __name__ == "__main__":
    extractor = EvidenceExtractor()
    
    # Create template for Anthropic Constitutional AI
    template = extractor.create_evidence_template("anthropic", "tech-constitutional-ai")
    print(json.dumps(template, indent=2))