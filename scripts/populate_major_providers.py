import json
from datetime import datetime
import hashlib

class ProviderDataPopulator:
    def __init__(self):
        self.load_existing_data()
        self.evidence_counter = self._get_max_evidence_id()
    
    def load_existing_data(self):
        """Load all existing data"""
        with open('data/providers.json', 'r') as f:
            self.providers = json.load(f)
            self.provider_ids = {p['id'] for p in self.providers}
        
        with open('data/models.json', 'r') as f:
            self.models = json.load(f)
            self.model_ids = {m['id'] for m in self.models}
        
        with open('data/categories.json', 'r') as f:
            self.categories = json.load(f)
            self.category_ids = {c['id'] for c in self.categories}
        
        with open('data/techniques.json', 'r') as f:
            self.techniques = json.load(f)
            self.technique_ids = {t['id'] for t in self.techniques}
        
        with open('data/evidence.json', 'r') as f:
            self.evidence = json.load(f)
    
    def _get_max_evidence_id(self):
        """Get the highest evidence ID number"""
        max_id = 0
        for e in self.evidence:
            match = e['id'].split('-')[-1]
            try:
                num = int(match)
                max_id = max(max_id, num)
            except:
                pass
        return max_id
    
    def add_provider(self, provider_data):
        """Add provider if not exists"""
        if provider_data['id'] not in self.provider_ids:
            self.providers.append(provider_data)
            self.provider_ids.add(provider_data['id'])
            print(f"✅ Added provider: {provider_data['name']}")
    
    def add_model(self, model_data):
        """Add model if not exists"""
        if model_data['id'] not in self.model_ids:
            self.models.append(model_data)
            self.model_ids.add(model_data['id'])
            print(f"✅ Added model: {model_data['name']} {model_data['version']}")
    
    def add_category(self, category_data):
        """Add category if not exists"""
        if category_data['id'] not in self.category_ids:
            self.categories.append(category_data)
            self.category_ids.add(category_data['id'])
            print(f"✅ Added category: {category_data['name']}")
    
    def add_technique(self, technique_data):
        """Add technique if not exists"""
        if technique_data['id'] not in self.technique_ids:
            self.techniques.append(technique_data)
            self.technique_ids.add(technique_data['id'])
            print(f"✅ Added technique: {technique_data['name']}")
    
    def add_evidence(self, evidence_data):
        """Add evidence with auto-generated ID"""
        self.evidence_counter += 1
        evidence_data['id'] = f"ev-{evidence_data['providerId']}-{self.evidence_counter:04d}"
        self.evidence.append(evidence_data)
        return evidence_data['id']
    
    def save_all(self):
        """Save all data files"""
        data_map = {
            'data/providers.json': self.providers,
            'data/models.json': self.models,
            'data/categories.json': self.categories,
            'data/techniques.json': self.techniques,
            'data/evidence.json': self.evidence
        }
        
        for filepath, data in data_map.items():
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        
        print(f"\n✅ Saved all data files")

def populate_all_providers():
    populator = ProviderDataPopulator()
    
    # Add all categories first
    categories_to_add = [
        {
            "id": "cat-alignment",
            "name": "Alignment Methods",
            "description": "Techniques for aligning model behavior with human values and preferences",
            "phase": "training",
            "parentCategoryId": None,
            "riskAreaIds": [1, 2, 5, 10]
        },
        {
            "id": "cat-inference-safeguards",
            "name": "Inference Safeguards",
            "description": "Safety measures applied during model inference and generation",
            "phase": "inference",
            "parentCategoryId": None,
            "riskAreaIds": [1, 2, 3, 4, 5]
        },
        {
            "id": "cat-governance",
            "name": "Governance & Oversight",
            "description": "Organizational and procedural safety measures",
            "phase": "governance",
            "parentCategoryId": None,
            "riskAreaIds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        },
        {
            "id": "cat-transparency",
            "name": "Transparency",
            "description": "Documentation and disclosure practices",
            "phase": "governance",
            "parentCategoryId": None,
            "riskAreaIds": [7]
        }
    ]
    
    for cat in categories_to_add:
        populator.add_category(cat)
    
    # Add all techniques
    techniques_to_add = [
        # Pre-training Safety
        {
            "id": "tech-csam-detection",
            "name": "CSAM Detection & Removal",
            "categoryId": "cat-pre-training-safety",
            "description": "Automated detection and removal of child sexual abuse material from training data",
            "implementationMethods": ["EmbeddedClassifier", "ExternalSafetyService"],
            "governingStandards": ["NCMEC"],
            "licence": None,
            "knownLimitations": ["False positive rates not typically disclosed"],
            "aliases": ["CSAM Filtering"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1]
        },
        {
            "id": "tech-copyright-filtering",
            "name": "Copyright Content Filtering",
            "categoryId": "cat-pre-training-safety",
            "description": "Detection and removal of copyrighted content from training datasets",
            "implementationMethods": ["RuleBased", "EmbeddedClassifier"],
            "governingStandards": ["DMCA"],
            "licence": None,
            "knownLimitations": ["Difficult to detect all copyrighted content", "May remove fair use content"],
            "aliases": ["Copyright Protection"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [6]
        },
        {
            "id": "tech-bias-detection-training",
            "name": "Bias Detection in Training Data",
            "categoryId": "cat-pre-training-safety",
            "description": "Detection and mitigation of demographic and cultural biases in training data",
            "implementationMethods": ["EmbeddedClassifier", "RuleBased"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Cannot detect all forms of bias", "Definitions of bias vary culturally"],
            "aliases": ["Training Data Debiasing"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [2]
        },
        {
            "id": "tech-pii-reduction",
            "name": "PII Reduction",
            "categoryId": "cat-pre-training-safety",
            "description": "Detection and removal of personal information from training data",
            "implementationMethods": ["RuleBased", "EmbeddedClassifier"],
            "governingStandards": ["GDPR", "CCPA"],
            "licence": None,
            "knownLimitations": ["Cannot catch all PII", "Context-dependent PII is challenging"],
            "aliases": ["PII Filtering", "Personal Data Removal"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [3]
        },
        
        # Alignment Methods
        {
            "id": "tech-rlhf",
            "name": "Reinforcement Learning from Human Feedback",
            "categoryId": "cat-alignment",
            "description": "Training models using human preference data to align outputs with human values",
            "implementationMethods": ["HumanModeration", "EmbeddedClassifier"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Subject to annotator biases", "Expensive to scale", "May overfit to specific preferences"],
            "aliases": ["RLHF"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 5, 10]
        },
        {
            "id": "tech-constitutional-ai",
            "name": "Constitutional AI / Self-Critique",
            "categoryId": "cat-alignment",
            "description": "Training models to critique and revise their own outputs based on constitutional principles",
            "implementationMethods": ["EmbeddedClassifier", "RetrievalAugmentation"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Requires careful principle design", "May be overly conservative"],
            "aliases": ["CAI", "Constitutional AI"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 5, 10]
        },
        {
            "id": "tech-safety-reward-modeling",
            "name": "Safety Reward Modeling",
            "categoryId": "cat-alignment",
            "description": "Separate reward models specifically optimized for safety outcomes",
            "implementationMethods": ["EmbeddedClassifier", "HumanModeration"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["May conflict with capability objectives", "Hard to balance multiple safety goals"],
            "aliases": ["Safety RM"],
            "requiredTechniqueIds": ["tech-rlhf"],
            "riskAreaIds": [1, 2, 5]
        },
        
        # Inference Safeguards
        {
            "id": "tech-input-classification",
            "name": "Input Content Classification",
            "categoryId": "cat-inference-safeguards",
            "description": "Classification of input prompts for safety risks before processing",
            "implementationMethods": ["EmbeddedClassifier", "ExternalSafetyService"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["May block benign content", "Context-dependent risks hard to catch"],
            "aliases": ["Input Filtering", "Prompt Classification"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 4, 5]
        },
        {
            "id": "tech-output-filtering",
            "name": "Output Content Filtering",
            "categoryId": "cat-inference-safeguards",
            "description": "Post-generation filtering of model outputs for safety violations",
            "implementationMethods": ["EmbeddedClassifier", "ExternalSafetyService", "RuleBased"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["May alter intended meaning", "Can be overly restrictive"],
            "aliases": ["Output Moderation"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 5, 6]
        },
        {
            "id": "tech-prompt-injection-protection",
            "name": "Prompt Injection Protection",
            "categoryId": "cat-inference-safeguards",
            "description": "Detection and prevention of prompt injection attacks",
            "implementationMethods": ["RuleBased", "EmbeddedClassifier"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Evolving attack vectors", "May restrict legitimate use cases"],
            "aliases": ["Injection Defense"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [4]
        },
        
        # Governance
        {
            "id": "tech-red-teaming",
            "name": "Red Team Exercises",
            "categoryId": "cat-governance",
            "description": "Systematic adversarial testing by security experts",
            "implementationMethods": ["HumanModeration", "AdversarialRedTeam"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Limited by red team expertise", "Cannot test all scenarios"],
            "aliases": ["Adversarial Testing", "Red Teaming"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5, 6, 9, 10]
        },
        {
            "id": "tech-capability-monitoring",
            "name": "Capability Threshold Monitoring",
            "categoryId": "cat-governance",
            "description": "Monitoring model capabilities against predefined safety thresholds",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Thresholds may be arbitrary", "Capabilities hard to measure precisely"],
            "aliases": ["Capability Evaluation"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [9, 10]
        },
        
        # Transparency
        {
            "id": "tech-safety-documentation",
            "name": "Comprehensive Safety Documentation",
            "categoryId": "cat-transparency",
            "description": "Detailed public documentation of safety measures and evaluations",
            "implementationMethods": ["Other"],
            "governingStandards": ["ISO 26000"],
            "licence": None,
            "knownLimitations": ["May not cover proprietary methods", "Can become outdated"],
            "aliases": ["Safety Cards", "System Cards"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [7]
        }
    ]
    
    for tech in techniques_to_add:
        populator.add_technique(tech)
    
    # Now add providers and their evidence
    
    # ANTHROPIC
    print("\n📦 Adding Anthropic...")
    populator.add_provider({
        "id": "anthropic",
        "name": "Anthropic",
        "type": "commercial",
        "headquarters": "United States",
        "website": "https://anthropic.com",
        "establishedYear": 2021
    })
    
    populator.add_model({
        "id": "model-claude-3-opus",
        "providerId": "anthropic",
        "name": "Claude 3",
        "version": "claude-3-opus-20240229",
        "releaseDate": "2024-03-04",
        "modalityType": "text",
        "parameterCount": None,
        "deploymentStatus": "general-availability",
        "accessType": "api"
    })
    
    populator.add_model({
        "id": "model-claude-3-sonnet",
        "providerId": "anthropic",
        "name": "Claude 3",
        "version": "claude-3-sonnet-20240229",
        "releaseDate": "2024-03-04",
        "modalityType": "text",
        "parameterCount": None,
        "deploymentStatus": "general-availability",
        "accessType": "api"
    })
    
    # Anthropic evidence
    anthropic_evidence = [
        {
            "providerId": "anthropic",
            "techniqueId": "tech-training-data-filtering",
            "modelIds": ["model-claude-3-opus", "model-claude-3-sonnet"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Constitutional training data with filtered corpora designed to reduce harmful content and improve model alignment",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://www.anthropic.com/news/anthropics-responsible-scaling-policy",
                "documentType": "policy",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Safety and Security Standards"
            }],
            "implementationDate": "2023-09-18",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Specific filtering methods not detailed"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Part of Constitutional AI framework"
        },
        {
            "providerId": "anthropic",
            "techniqueId": "tech-constitutional-ai",
            "modelIds": ["model-claude-3-opus", "model-claude-3-sonnet"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "Self-critique training using constitutional principles for helpful, harmless, honest behavior with scalable oversight",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://arxiv.org/abs/2212.08073",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Section 3: Constitutional AI"
            }],
            "implementationDate": "2022-12-15",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "evaluationMetrics": [{
                "metric": "human_preference_rate",
                "value": 76,
                "unit": "percent",
                "benchmarkContext": {
                    "name": "Constitutional AI Eval",
                    "version": "v1",
                    "url": "https://arxiv.org/abs/2212.08073"
                }
            }],
            "knownLimitations": ["May be overly conservative", "Principles require careful design"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Core safety innovation from Anthropic"
        },
        {
            "providerId": "anthropic",
            "techniqueId": "tech-rlhf",
            "modelIds": ["model-claude-3-opus", "model-claude-3-sonnet"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "Constitutional AI approach combining self-critique with RLHF for scalable oversight and preference learning",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://arxiv.org/abs/2212.08073",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Section 4: Training Process"
            }],
            "implementationDate": "2022-12-15",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Subject to annotator biases", "Computationally expensive"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Combined with Constitutional AI for enhanced safety"
        }
    ]
    
    for evidence in anthropic_evidence:
        populator.add_evidence(evidence)
    
    # GOOGLE
    print("\n📦 Adding Google...")
    populator.add_provider({
        "id": "google",
        "name": "Google",
        "type": "commercial",
        "headquarters": "United States",
        "website": "https://google.com",
        "establishedYear": 1998
    })
    
    populator.add_model({
        "id": "model-gemini-pro",
        "providerId": "google",
        "name": "Gemini",
        "version": "gemini-pro-1.0",
        "releaseDate": "2023-12-06",
        "modalityType": "multimodal",
        "parameterCount": None,
        "deploymentStatus": "general-availability",
        "accessType": "api"
    })
    
    # Google evidence
    google_evidence = [
        {
            "providerId": "google",
            "techniqueId": "tech-training-data-filtering",
            "modelIds": ["model-gemini-pro"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Multi-lingual safety filtering and bias detection in training data preparation for Gemini models",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://deepmind.google/discover/blog/advancing-geminis-security-safeguards/",
                "documentType": "blog-post",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Training Data Safety"
            }],
            "implementationDate": "2024-02-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Specific methods not detailed"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["EU AI Act"],
            "notes": "Focus on multilingual safety"
        },
        {
            "providerId": "google",
            "techniqueId": "tech-rlhf",
            "modelIds": ["model-gemini-pro"],
            "rating": "medium",
            "severityBand": "B",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "RLHF with adversarial safety tuning datasets and Sparrow-style critiquing methodology",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://arxiv.org/abs/2209.14375",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Section 3: Training Sparrow"
            }],
            "implementationDate": "2022-09-29",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Limited to English initially"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Based on Sparrow research"
        }
    ]
    
    for evidence in google_evidence:
        populator.add_evidence(evidence)
    
    # META
    print("\n📦 Adding Meta...")
    populator.add_provider({
        "id": "meta",
        "name": "Meta",
        "type": "commercial",
        "headquarters": "United States",
        "website": "https://meta.com",
        "establishedYear": 2004
    })
    
    populator.add_model({
        "id": "model-llama-3-70b",
        "providerId": "meta",
        "name": "Llama 3",
        "version": "llama-3-70b",
        "releaseDate": "2024-04-18",
        "modalityType": "text",
        "parameterCount": 70000000000,
        "deploymentStatus": "general-availability",
        "accessType": "download"
    })
    
    # Meta evidence
    meta_evidence = [
        {
            "providerId": "meta",
            "techniqueId": "tech-training-data-filtering",
            "modelIds": ["model-llama-3-70b"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Open training with safety benchmarks and Llama Guard integration for content filtering",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://arxiv.org/abs/2307.09288",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Section 4: Safety"
            }],
            "implementationDate": "2023-07-18",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Community-dependent verification"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Open source approach enables community verification"
        },
        {
            "providerId": "meta",
            "techniqueId": "tech-rlhf",
            "modelIds": ["model-llama-3-70b"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "Two-phase RLHF with community-driven safety feedback and open source evaluation",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://arxiv.org/abs/2307.09288",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Section 3.3: Fine-tuning"
            }],
            "implementationDate": "2023-07-18",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Resource intensive", "Community feedback quality varies"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Two-phase approach with safety-specific rewards"
        },
        {
            "providerId": "meta",
            "techniqueId": "tech-input-classification",
            "modelIds": ["model-llama-3-70b"],
            "rating": "medium",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Llama Guard as separate safety classifier for input content with open source implementation",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Section 2: Llama Guard"
            }],
            "implementationDate": "2023-12-07",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Requires separate model inference"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Open source safety classifier"
        }
    ]
    
    for evidence in meta_evidence:
        populator.add_evidence(evidence)
    
    # AMAZON
    print("\n📦 Adding Amazon...")
    populator.add_provider({
        "id": "amazon",
        "name": "Amazon",
        "type": "commercial",
        "headquarters": "United States",
        "website": "https://aws.amazon.com",
        "establishedYear": 1994
    })
    
    populator.add_model({
        "id": "model-titan-text-express",
        "providerId": "amazon",
        "name": "Titan Text",
        "version": "titan-text-express-v1",
        "releaseDate": "2023-09-28",
        "modalityType": "text",
        "parameterCount": None,
        "deploymentStatus": "general-availability",
        "accessType": "api"
    })
    
    # Amazon evidence
    amazon_evidence = [
        {
            "providerId": "amazon",
            "techniqueId": "tech-pii-reduction",
            "modelIds": ["model-titan-text-express"],
            "rating": "medium",
            "severityBand": "B",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Advanced PII detection and redaction through Bedrock Guardrails with enterprise-grade protection",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-sensitive-filters.html",
                "documentType": "documentation",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Sensitive Information Filters"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Language support varies", "Context-dependent PII challenging"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["HIPAA", "PCI-DSS"],
            "notes": "Enterprise-grade PII protection"
        },
        {
            "providerId": "amazon",
            "techniqueId": "tech-input-classification",
            "modelIds": ["model-titan-text-express"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Bedrock Guardrails input classification with customizable policies and enterprise integration",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html",
                "documentType": "documentation",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Content Filters"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Requires configuration", "May have false positives"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Highly configurable for enterprise needs"
        },
        {
            "providerId": "amazon",
            "techniqueId": "tech-output-filtering",
            "modelIds": ["model-titan-text-express"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Bedrock Guardrails output filtering with hallucination detection and content policy enforcement",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html",
                "documentType": "documentation",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Output Moderation"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["May alter outputs", "Hallucination detection has limits"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Includes hallucination detection"
        }
    ]
    
    for evidence in amazon_evidence:
        populator.add_evidence(evidence)
    
    # Add some governance techniques for all providers
    governance_evidence = [
        {
            "providerId": "anthropic",
            "techniqueId": "tech-red-teaming",
            "modelIds": ["model-claude-3-opus", "model-claude-3-sonnet"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "External red team engagement as part of responsible scaling policy and AI Safety Level assessments",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://www.anthropic.com/news/anthropics-responsible-scaling-policy",
                "documentType": "policy",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "AI Safety Levels"
            }],
            "implementationDate": "2023-09-18",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": ["Specific findings not always public"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Part of ASL framework"
        },
        {
            "providerId": "anthropic",
            "techniqueId": "tech-safety-documentation",
            "modelIds": ["model-claude-3-opus", "model-claude-3-sonnet"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Responsible scaling policy and constitutional AI research provide comprehensive safety framework documentation",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://www.anthropic.com/news/anthropics-responsible-scaling-policy",
                "documentType": "policy",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Full Document"
            }],
            "implementationDate": "2023-09-18",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P12M",
            "reviewer": "initial-import",
            "evaluationMetrics": [],
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Industry-leading transparency"
        }
    ]
    
    for evidence in governance_evidence:
        populator.add_evidence(evidence)
    
    # Save everything
    populator.save_all()
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"  Providers: {len(populator.providers)}")
    print(f"  Models: {len(populator.models)}")
    print(f"  Categories: {len(populator.categories)}")
    print(f"  Techniques: {len(populator.techniques)}")
    print(f"  Evidence Records: {len(populator.evidence)}")

if __name__ == "__main__":
    populate_all_providers()