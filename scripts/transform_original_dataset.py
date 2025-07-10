import json
import re
from datetime import datetime
from collections import defaultdict

class DatasetTransformer:
    def __init__(self):
        # Load existing data
        with open('data/providers.json', 'r') as f:
            self.providers = {p['id']: p for p in json.load(f)}
        
        with open('data/categories.json', 'r') as f:
            self.categories = {c['name']: c for c in json.load(f)}
        
        with open('data/techniques.json', 'r') as f:
            self.techniques = {t['name']: t for t in json.load(f)}
        
        # Rating mapping from old codes to new system
        self.rating_map = {
            'HPV': 'high',    # High, Published, Verified
            'HPU': 'high',    # High, Published, Unverified
            'HPC': 'high',    # High, Published, Claimed
            'HRV': 'high',    # High, Research, Verified
            'MPV': 'medium',  # Medium, Published, Verified
            'MPU': 'medium',  # Medium, Published, Unverified
            'MPC': 'medium',  # Medium, Published, Claimed
            'MRC': 'medium',  # Medium, Research, Claimed
            'MBC': 'medium',  # Medium, Basic, Claimed
            'MBV': 'medium',  # Medium, Basic, Verified
            'LPU': 'low',     # Low, Published, Unverified
            'LPC': 'low',     # Low, Published, Claimed
            'MRV': 'medium',  # Medium, Research, Verified
        }
        
        # Severity band mapping (second letter of rating code)
        self.severity_map = {
            'P': 'P',  # Published/Primary
            'R': 'B',  # Research/Benchmarked
            'B': 'C',  # Basic/Claimed
        }
        
        # Evidence level mapping (third letter)
        self.evidence_level_map = {
            'V': 'primary',    # Verified
            'U': 'secondary',  # Unverified
            'C': 'claimed',    # Claimed
        }
        
        # Provider ID mapping
        self.provider_id_map = {
            'OpenAI': 'openai',
            'Anthropic': 'anthropic',
            'Google': 'google',
            'Microsoft': 'microsoft',
            'Meta': 'meta',
            'Amazon': 'amazon',
            'Cohere': 'cohere',
            'Mistral': 'mistral',
            'Stability AI': 'stability-ai',
            'Hugging Face': 'hugging-face',
            'Baidu': 'baidu',
            'Alibaba': 'alibaba'
        }
        
        # Category name normalization
        self.category_map = {
            'Pre-training Safety': 'Pre-training Safety',
            'Alignment Methods': 'Alignment Methods',
            'Inference Safeguards': 'Inference Safeguards',
            'Governance & Oversight': 'Governance & Oversight',
            'Transparency': 'Transparency',
            'Novel/Advanced Features': 'Novel/Advanced Features'
        }
        
        self.evidence_counter = defaultdict(int)
    
    def normalize_technique_name(self, name):
        """Normalize technique names for matching"""
        # Remove parentheses content
        name = re.sub(r'\s*\([^)]*\)', '', name)
        # Normalize spaces
        name = ' '.join(name.split())
        return name.strip()
    
    def find_technique_id(self, technique_name, category_name):
        """Find the technique ID from our schema"""
        normalized_name = self.normalize_technique_name(technique_name)
        
        # Direct match
        for tech_name, tech in self.techniques.items():
            if self.normalize_technique_name(tech_name) == normalized_name:
                return tech['id']
        
        # Fuzzy match - look for key terms
        key_terms = {
            'CSAM': 'tech-csam-detection',
            'Copyright': 'tech-copyright-filtering',
            'Bias Detection': 'tech-bias-detection-training',
            'PII': 'tech-pii-reduction',
            'RLHF': 'tech-rlhf',
            'Constitutional AI': 'tech-constitutional-ai',
            'Safety Reward': 'tech-safety-reward-modeling',
            'Adversarial Training': 'tech-adversarial-training',
            'Red Team Data': 'tech-red-team-data',
            'Input Content Classification': 'tech-input-classification',
            'Output Content Filtering': 'tech-output-filtering',
            'Prompt Injection': 'tech-prompt-injection-protection',
            'Real-time Safety': 'tech-realtime-monitoring',
            'Contextual Safety': 'tech-contextual-safety',
            'Multi-stage': 'tech-multistage-pipeline',
            'PII Detection & Redaction': 'tech-pii-detection-inference',
            'Configurable Safety': 'tech-configurable-policies',
            'Audit Logging': 'tech-audit-logging',
            'Capability Threshold': 'tech-capability-monitoring',
            'External Red Team': 'tech-red-teaming',
            'Safety Level Classifications': 'tech-capability-monitoring',
            'Independent Safety Advisory': 'tech-safety-advisory',
            'Incident Reporting': 'tech-incident-reporting',
            'Usage Monitoring': 'tech-usage-monitoring',
            'Capability Evaluation': 'tech-capability-monitoring',
            'Red Team Exercises': 'tech-red-teaming',
            'Regulatory Compliance': 'tech-regulatory-compliance',
            'Academic Partnerships': 'tech-academic-partnerships',
            'Comprehensive Safety Documentation': 'tech-safety-documentation',
            'Model Cards': 'tech-model-cards',
            'Safety Research Publications': 'tech-safety-research',
            'Policy & Compliance Documentation': 'tech-policy-documentation',
            'Watermarking': 'tech-watermarking',
            'Training Data Filtering': 'tech-training-data-filtering',
            'Fine-tuning for Domain Safety': 'tech-fine-tuning-safety',
            'Community Feedback': 'tech-community-feedback',
            'Open Source Safety Tools': 'tech-opensource-tools',
            'Enterprise Security Integration': 'tech-enterprise-integration',
            'Sovereignty': 'tech-sovereignty-options',
            'Government Oversight': 'tech-government-oversight',
            'Community Governance': 'tech-community-governance',
            'Responsible release': 'tech-responsible-release',
            'Safety benchmarks': 'tech-safety-benchmarks',
            'Community Evaluation': 'tech-community-evaluation'
        }
        
        for key, tech_id in key_terms.items():
            if key.lower() in technique_name.lower():
                return tech_id
        
        # If still not found, create a new technique ID
        print(f"Warning: No technique ID found for '{technique_name}' in category '{category_name}'")
        return None
    
    def get_model_ids(self, provider_id):
        """Get model IDs for a provider"""
        # This would need to be expanded based on your models.json
        model_map = {
            'openai': ['model-gpt-4o'],
            'anthropic': ['model-claude-3-opus', 'model-claude-3-sonnet'],
            'google': ['model-gemini-pro'],
            'meta': ['model-llama-3-70b'],
            'amazon': ['model-titan-text-express'],
            'microsoft': [],  # Uses OpenAI models
            'cohere': [],
            'mistral': [],
        }
        return model_map.get(provider_id, [])
    
    def parse_rating_code(self, rating_code):
        """Parse the three-letter rating code"""
        if len(rating_code) == 3:
            rating = self.rating_map.get(rating_code, 'medium')
            severity = self.severity_map.get(rating_code[1], 'C')
            evidence_level = self.evidence_level_map.get(rating_code[2], 'claimed')
            
            # Determine rating criteria based on code
            criteria = {
                'publiclyDocumented': rating_code[1] in ['P', 'R'],
                'independentlyVerified': rating_code[2] == 'V',
                'quantitativeMetrics': rating_code[0] == 'H' and rating_code[1] in ['P', 'R'],
                'automatedTest': False  # Can't determine from code
            }
            
            return rating, severity, evidence_level, criteria
        else:
            # Default values
            return 'medium', 'C', 'claimed', {
                'publiclyDocumented': True,
                'independentlyVerified': False,
                'quantitativeMetrics': False,
                'automatedTest': False
            }
    
    def transform_evidence(self, provider_name, category_name, technique_name, technique_data):
        """Transform a single technique entry to evidence format"""
        provider_id = self.provider_id_map.get(provider_name)
        if not provider_id:
            print(f"Warning: Unknown provider '{provider_name}'")
            return None
        
        technique_id = self.find_technique_id(technique_name, category_name)
        if not technique_id:
            return None
        
        # Parse rating
        rating_code = technique_data.get('rating', 'MPC')
        rating, severity, evidence_level, criteria = self.parse_rating_code(rating_code)
        
        # Fix typo in lastUpdated
        last_updated = technique_data.get('lastUpdated') or technique_data.get('lasTupdated', '2024-01-01')
        
        # Generate evidence ID
        self.evidence_counter[provider_id] += 1
        evidence_id = f"ev-{provider_id}-{self.evidence_counter[provider_id]:04d}"
        
        # Determine document type from URL
        url = technique_data.get('url', '')
        doc_type = 'documentation'
        if 'arxiv.org' in url:
            doc_type = 'research-paper'
        elif 'system-card' in url or 'model-card' in url:
            doc_type = 'system-card'
        elif '/blog/' in url or '/news/' in url:
            doc_type = 'blog-post'
        elif '/policies' in url:
            doc_type = 'policy'
        
        evidence = {
            "id": evidence_id,
            "providerId": provider_id,
            "techniqueId": technique_id,
            "modelIds": self.get_model_ids(provider_id),
            "rating": rating,
            "severityBand": severity,
            "ratingCriteria": criteria,
            "summary": technique_data.get('summary', ''),
            "evidenceLevel": evidence_level,
            "sourceUrls": [{
                "url": url,
                "documentType": doc_type,
                "lastVerified": datetime.now().strftime('%Y-%m-%d'),
                "sourceHash": "0" * 64,
                "relevantSection": ""
            }],
            "implementationDate": last_updated,
            "lastReviewed": datetime.now().strftime('%Y-%m-%d'),
            "reviewFrequency": "P6M" if rating == 'high' else "P12M",
            "reviewer": "dataset-import",
            "evaluationMetrics": [],
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": f"Imported from original dataset with rating code: {rating_code}"
        }
        
        return evidence
    
    def process_dataset(self, original_data):
        """Process the entire original dataset"""
        all_evidence = []
        stats = defaultdict(int)
        
        for provider_name, categories in original_data.items():
            if not isinstance(categories, dict):
                continue
                
            for category_name, techniques in categories.items():
                if not isinstance(techniques, dict):
                    continue
                    
                for technique_name, technique_data in techniques.items():
                    if not isinstance(technique_data, dict):
                        continue
                    
                    evidence = self.transform_evidence(
                        provider_name, 
                        category_name, 
                        technique_name, 
                        technique_data
                    )
                    
                    if evidence:
                        all_evidence.append(evidence)
                        stats[evidence['providerId']] += 1
                    else:
                        print(f"Skipped: {provider_name} / {category_name} / {technique_name}")
        
        # Print statistics
        print("\n📊 Import Statistics:")
        for provider, count in sorted(stats.items()):
            print(f"  {provider}: {count} evidence records")
        print(f"  Total: {len(all_evidence)} evidence records")
        
        return all_evidence

def main():
    # Read the original dataset
    print("🔄 Reading original dataset...")
    
    # You'll need to paste your original dataset into a file or modify this
    # to read from wherever you have it stored
    original_file = 'data/original_safety_mechanisms.json'
    
    try:
        with open(original_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Please save your original dataset to '{original_file}'")
        return
    
    # Transform the data
    transformer = DatasetTransformer()
    new_evidence = transformer.process_dataset(original_data)
    
    # Load existing evidence (if any)
    try:
        with open('data/evidence.json', 'r') as f:
            existing_evidence = json.load(f)
    except:
        existing_evidence = []
    
    # Merge (or replace)
    if existing_evidence:
        response = input("\nExisting evidence found. Replace (r) or Merge (m)? ")
        if response.lower() == 'r':
            all_evidence = new_evidence
        else:
            # Merge, avoiding duplicates
            existing_ids = {e['id'] for e in existing_evidence}
            for evidence in new_evidence:
                if evidence['id'] not in existing_ids:
                    existing_evidence.append(evidence)
            all_evidence = existing_evidence
    else:
        all_evidence = new_evidence
    
    # Save the evidence
    with open('data/evidence.json', 'w', encoding='utf-8') as f:
        json.dump(all_evidence, f, indent=2)
    
    print(f"\n✅ Saved {len(all_evidence)} evidence records to data/evidence.json")
    
    # Update stats
    import subprocess
    subprocess.run(['python', 'scripts/generate_report.py'])

if __name__ == "__main__":
    main()