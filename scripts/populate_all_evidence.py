import json
from datetime import datetime

def populate_all_evidence():
    """Populate all evidence from the original dataset"""
    
    # First, ensure we have all categories
    categories_to_add = [
        {
            "id": "cat-novel-features",
            "name": "Novel/Advanced Features",
            "description": "Innovative or unique safety features",
            "phase": "deployment",
            "parentCategoryId": None,
            "riskAreaIds": [1, 2, 3, 4, 5, 6, 7]
        }
    ]
    
    with open('data/categories.json', 'r') as f:
        categories = json.load(f)
    
    for cat in categories_to_add:
        if not any(c['id'] == cat['id'] for c in categories):
            categories.append(cat)
    
    with open('data/categories.json', 'w') as f:
        json.dump(categories, f, indent=2)
    
    # Add all missing techniques
    techniques_to_add = [
        # More alignment techniques
        {
            "id": "tech-adversarial-training",
            "name": "Adversarial Training",
            "categoryId": "cat-alignment",
            "description": "Training with adversarial examples to improve robustness",
            "implementationMethods": ["AdversarialRedTeam"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Cannot cover all attack vectors"],
            "aliases": ["Adversarial Robustness Training"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 4]
        },
        {
            "id": "tech-red-team-data",
            "name": "Red Team Data Integration",
            "categoryId": "cat-alignment",
            "description": "Incorporating red team findings into training data",
            "implementationMethods": ["AdversarialRedTeam", "HumanModeration"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Limited by red team scope"],
            "aliases": [],
            "requiredTechniqueIds": ["tech-red-teaming"],
            "riskAreaIds": [1, 2, 4, 5]
        },
        # More inference safeguards
        {
            "id": "tech-realtime-monitoring",
            "name": "Real-time Safety Monitoring",
            "categoryId": "cat-inference-safeguards",
            "description": "Live monitoring of model outputs for safety violations",
            "implementationMethods": ["ExternalSafetyService", "EmbeddedClassifier"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Latency impact", "May miss context"],
            "aliases": ["Live Safety Monitoring"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5]
        },
        {
            "id": "tech-contextual-safety",
            "name": "Contextual Safety Assessment",
            "categoryId": "cat-inference-safeguards",
            "description": "Context-aware safety evaluation considering conversation history",
            "implementationMethods": ["EmbeddedClassifier", "RetrievalAugmentation"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Complex contexts challenging"],
            "aliases": [],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 5]
        },
        {
            "id": "tech-multistage-pipeline",
            "name": "Multi-stage Safety Pipeline",
            "categoryId": "cat-inference-safeguards",
            "description": "Multiple layers of safety checks at different stages",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Increased complexity", "Potential for conflicts"],
            "aliases": [],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5]
        },
        {
            "id": "tech-pii-detection-inference",
            "name": "PII Detection & Redaction",
            "categoryId": "cat-inference-safeguards",
            "description": "Real-time detection and redaction of personal information",
            "implementationMethods": ["RuleBased", "EmbeddedClassifier"],
            "governingStandards": ["GDPR", "CCPA"],
            "licence": None,
            "knownLimitations": ["Context-dependent PII hard to catch"],
            "aliases": ["PII Redaction"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [3]
        },
        {
            "id": "tech-configurable-policies",
            "name": "Configurable Safety Policies",
            "categoryId": "cat-inference-safeguards",
            "description": "User or admin configurable safety thresholds and policies",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Requires user expertise"],
            "aliases": [],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5]
        },
        {
            "id": "tech-audit-logging",
            "name": "Audit Logging",
            "categoryId": "cat-inference-safeguards",
            "description": "Comprehensive logging of safety-relevant events",
            "implementationMethods": ["Other"],
            "governingStandards": ["SOC2", "ISO27001"],
            "licence": None,
            "knownLimitations": ["Storage requirements", "Privacy concerns"],
            "aliases": ["Safety Audit Trail"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [7]
        },
        # Governance techniques
        {
            "id": "tech-safety-advisory",
            "name": "Independent Safety Advisory",
            "categoryId": "cat-governance",
            "description": "External advisory board for safety oversight",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Advisory only, not binding"],
            "aliases": ["Safety Board"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        },
        {
            "id": "tech-incident-reporting",
            "name": "Incident Reporting Systems",
            "categoryId": "cat-governance",
            "description": "Formal systems for reporting and tracking safety incidents",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Depends on reporting culture"],
            "aliases": [],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5]
        },
        {
            "id": "tech-usage-monitoring",
            "name": "Usage Monitoring & Analytics",
            "categoryId": "cat-governance",
            "description": "Monitoring usage patterns for safety insights",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Privacy considerations"],
            "aliases": [],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5]
        },
        {
            "id": "tech-regulatory-compliance",
            "name": "Regulatory Compliance Frameworks",
            "categoryId": "cat-governance",
            "description": "Frameworks for compliance with AI regulations",
            "implementationMethods": ["Other"],
            "governingStandards": ["EU AI Act", "NIST AI RMF"],
            "licence": None,
            "knownLimitations": ["Varies by jurisdiction"],
            "aliases": [],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        },
        {
            "id": "tech-academic-partnerships",
            "name": "Academic Partnerships",
            "categoryId": "cat-governance",
            "description": "Collaborations with academic institutions for safety research",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Research timeline constraints"],
            "aliases": ["University Collaborations"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        },
        # Transparency techniques
        {
            "id": "tech-model-cards",
            "name": "Model Cards & Technical Specs",
            "categoryId": "cat-transparency",
            "description": "Standardized documentation of model capabilities and limitations",
            "implementationMethods": ["Other"],
            "governingStandards": ["Model Cards Framework"],
            "licence": None,
            "knownLimitations": ["May not cover all aspects"],
            "aliases": ["Model Documentation"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [7]
        },
        {
            "id": "tech-safety-research",
            "name": "Safety Research Publications",
            "categoryId": "cat-transparency",
            "description": "Publishing safety research and methodologies",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["May not include proprietary methods"],
            "aliases": [],
            "requiredTechniqueIds": [],
            "riskAreaIds": [7]
        },
        {
            "id": "tech-policy-documentation",
            "name": "Policy & Compliance Documentation",
            "categoryId": "cat-transparency",
            "description": "Public documentation of safety policies and compliance measures",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["May be high-level"],
            "aliases": [],
            "requiredTechniqueIds": [],
            "riskAreaIds": [7]
        },
        # Novel features
        {
            "id": "tech-watermarking",
            "name": "Watermarking Technology",
            "categoryId": "cat-novel-features",
            "description": "Embedding detectable patterns in AI-generated content",
            "implementationMethods": ["Other"],
            "governingStandards": [],
            "licence": None,
            "knownLimitations": ["Can be removed or spoofed"],
            "aliases": ["AI Watermarking", "SynthID"],
            "requiredTechniqueIds": [],
            "riskAreaIds": [5, 7]
        }
    ]
    
    with open('data/techniques.json', 'r') as f:
        techniques = json.load(f)
    
    for tech in techniques_to_add:
        if not any(t['id'] == tech['id'] for t in techniques):
            techniques.append(tech)
    
    with open('data/techniques.json', 'w') as f:
        json.dump(techniques, f, indent=2)
    
    print(f"✅ Added {len(techniques_to_add)} techniques")
    
    # Now add all the evidence from your original data
    evidence_to_add = [
        # OpenAI - MORE EVIDENCE
        {
            "providerId": "openai",
            "techniqueId": "tech-csam-detection",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Automated detection and removal of child sexual abuse material using specialized classifiers during pre-training data preparation",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://openai.com/policies/usage-policies",
                "documentType": "policy",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Prohibited Usage"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": ["Detection rates not disclosed"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["NCMEC"],
            "notes": "Part of comprehensive content filtering"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-copyright-filtering",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Fingerprinting system to remove opted-out images from training data, building on DALL-E 3 opt-out mechanism",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Section 2.1"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Only for opted-out content"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["DMCA"],
            "notes": "Extends DALL-E 3 opt-out system"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-bias-detection-training",
            "modelIds": ["model-gpt-4o"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Advanced data filtering processes to reduce biased content, though specific bias detection methods not fully detailed",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Safety Evaluations"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Specific methods not disclosed"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-pii-reduction",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Advanced data filtering processes to reduce personal information from training data using automated detection systems",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Data Processing"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": ["Cannot catch all PII"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["GDPR", "CCPA"],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-adversarial-training",
            "modelIds": ["model-gpt-4o"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Red team data integration and adversarial testing during training, though specific methods not detailed",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Red Teaming"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Methods not fully disclosed"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-red-team-data",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "100+ external red teamers across 45 languages and 29 countries, data integrated into training process",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "External Red Teaming"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Extensive red team network"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-input-classification",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Layered policy engine with system prompt → model → content filter pipeline, including specialized voice classifiers",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Safety Pipeline"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Multi-layer approach"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-output-filtering",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Multi-stage content filtering with moderation API applied to both text and audio outputs",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Output Moderation"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Includes audio moderation"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-prompt-injection-protection",
            "modelIds": ["model-gpt-4o"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "System prompt protections and multi-layer filtering, though specific prompt injection defenses not detailed",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Safety Mitigations"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Specific defenses not disclosed"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-realtime-monitoring",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Real-time monitoring and enforcement with product-level mitigations including streaming audio analysis",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Real-time Voice"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Includes voice monitoring"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-contextual-safety",
            "modelIds": ["model-gpt-4o"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Context-aware safety evaluation, particularly for voice interactions, though implementation not detailed",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Voice Safety"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Implementation details limited"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-multistage-pipeline",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Comprehensive safety pipeline spanning pre-training, post-training, product development, and policy enforcement",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Safety Architecture"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "End-to-end approach"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-pii-detection-inference",
            "modelIds": ["model-gpt-4o"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "PII detection capabilities integrated into content filtering systems for personal information protection",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://openai.com/policies/usage-policies",
                "documentType": "policy",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Privacy"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Details not specified"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["GDPR", "CCPA"],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-configurable-policies",
            "modelIds": ["model-gpt-4o"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Usage policies and moderation tools provided to users, with transparency reports and configurable settings",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://openai.com/policies/usage-policies",
                "documentType": "policy",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Usage Policies"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Limited configurability"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-audit-logging",
            "modelIds": ["model-gpt-4o"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Usage monitoring and incident reporting systems for tracking and analyzing safety incidents",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Monitoring"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["SOC2"],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-capability-monitoring",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "Preparedness Framework with pre-defined capability thresholds and deployment decisions based on risk assessments",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/openai-preparedness-framework-beta.pdf",
                "documentType": "policy",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Full Document"
            }],
            "implementationDate": "2023-10-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Industry-leading framework"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-safety-advisory",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Safety Advisory Group providing independent oversight and recommendations on deployment decisions",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Governance"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P12M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-incident-reporting",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": True,
                "automatedTest": True
            },
            "summary": "Systematic incident reporting and analysis with internal tracking and external disclosure mechanisms",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Incident Response"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-usage-monitoring",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": True,
                "automatedTest": True
            },
            "summary": "Comprehensive usage monitoring with analytics for detecting patterns of misuse and safety incidents",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Usage Analytics"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P3M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-regulatory-compliance",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Compliance with voluntary White House commitments and development of internal governance frameworks",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://openai.com/index/our-approach-to-ai-safety",
                "documentType": "blog-post",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Commitments"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["White House Commitments"],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-academic-partnerships",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Collaboration with academic institutions and independent research organizations for safety evaluation",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "External Collaboration"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P12M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-model-cards",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "Technical documentation including model architecture, training methodology, and safety evaluation results",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://cdn.openai.com/gpt-4o-system-card.pdf",
                "documentType": "system-card",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Full Document"
            }],
            "implementationDate": "2024-08-08",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P12M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Comprehensive system card"
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-safety-research",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Regular publication of safety research, evaluation methodologies, and lessons learned from deployment",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://openai.com/research",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Safety Research"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P12M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "openai",
            "techniqueId": "tech-policy-documentation",
            "modelIds": ["model-gpt-4o"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Comprehensive usage policies, terms of service, and compliance documentation publicly available",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://openai.com/policies",
                "documentType": "policy",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "All Policies"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        
        # Google evidence
        {
            "providerId": "google",
            "techniqueId": "tech-watermarking",
            "modelIds": ["model-gemini-pro"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": True,
                "automatedTest": True
            },
            "summary": "SynthID watermarking technology for AI-generated image and audio content identification",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://deepmind.google/science/synthid/",
                "documentType": "documentation",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Technology Overview"
            }],
            "implementationDate": "2023-08-29",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Limited to certain content types"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Industry-leading watermarking"
        },
        {
            "providerId": "google",
            "techniqueId": "tech-regulatory-compliance",
            "modelIds": ["model-gemini-pro"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "EU AI Act compliance measures with transparency registers and regulatory reporting mechanisms",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://blog.google/technology/ai/google-ai-act-preparation/",
                "documentType": "blog-post",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Compliance Measures"
            }],
            "implementationDate": "2024-02-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": ["EU AI Act"],
            "notes": "Proactive compliance"
        },
        {
            "providerId": "google",
            "techniqueId": "tech-multistage-pipeline",
            "modelIds": ["model-gemini-pro"],
            "rating": "medium",
            "severityBand": "C",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": False,
                "quantitativeMetrics": False,
                "automatedTest": True
            },
            "summary": "Multi-stage safety layers including toxicity detection, policy checks, and SynthID watermarking",
            "evidenceLevel": "secondary",
            "sourceUrls": [{
                "url": "https://deepmind.google/discover/blog/advancing-geminis-security-safeguards/",
                "documentType": "blog-post",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Safety Architecture"
            }],
            "implementationDate": "2024-02-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        {
            "providerId": "google",
            "techniqueId": "tech-academic-partnerships",
            "modelIds": ["model-gemini-pro"],
            "rating": "high",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Academic partnerships for AI safety research and independent evaluation of safety measures",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://deepmind.google/research/",
                "documentType": "documentation",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Collaborations"
            }],
            "implementationDate": "2024-01-01",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P12M",
            "reviewer": "initial-import",
            "knownLimitations": [],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        
        # Meta additional evidence
        {
            "providerId": "meta",
            "techniqueId": "tech-output-filtering",
            "modelIds": ["model-llama-3-70b"],
            "rating": "medium",
            "severityBand": "P",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": False,
                "automatedTest": False
            },
            "summary": "Llama Guard output filtering with contextual moderation and open source validation",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Output Moderation"
            }],
            "implementationDate": "2023-12-07",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Requires separate inference"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": "Open source implementation"
        },
        {
            "providerId": "meta",
            "techniqueId": "tech-bias-detection-training",
            "modelIds": ["model-llama-3-70b"],
            "rating": "medium",
            "severityBand": "B",
            "ratingCriteria": {
                "publiclyDocumented": True,
                "independentlyVerified": True,
                "quantitativeMetrics": True,
                "automatedTest": False
            },
            "summary": "Bias detection and mitigation with community-driven evaluation and open source validation",
            "evidenceLevel": "primary",
            "sourceUrls": [{
                "url": "https://arxiv.org/abs/2307.09288",
                "documentType": "research-paper",
                "lastVerified": "2024-12-19",
                "sourceHash": "0" * 64,
                "relevantSection": "Section 5.2: Bias Evaluation"
            }],
            "implementationDate": "2023-07-18",
            "lastReviewed": "2024-12-19",
            "reviewFrequency": "P6M",
            "reviewer": "initial-import",
            "knownLimitations": ["Community-dependent validation"],
            "deploymentScope": "all-users",
            "geographicRestrictions": [],
            "complianceStandards": [],
            "notes": ""
        },
        
        # Add more for other providers...
    ]
    
    # Load existing evidence
    with open('data/evidence.json', 'r') as f:
        evidence = json.load(f)
    
    # Add new evidence
    added = 0
    for new_evidence in evidence_to_add:
        # Check if already exists
        exists = any(
            e['providerId'] == new_evidence['providerId'] and 
            e['techniqueId'] == new_evidence['techniqueId']
            for e in evidence
        )
        
        if not exists:
            # Generate ID
            count = len([e for e in evidence if e['providerId'] == new_evidence['providerId']])
            new_evidence['id'] = f"ev-{new_evidence['providerId']}-{count+1:04d}"
            
            evidence.append(new_evidence)
            added += 1
    
    # Save
    with open('data/evidence.json', 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print(f"✅ Added {added} new evidence records")
    
    # Generate updated stats
    import subprocess
    subprocess.run([sys.executable, "scripts/generate_report.py"])
    
    # Show new stats
    with open('data/stats.json', 'r') as f:
        stats = json.load(f)
    
    print(f"\n📊 Updated Stats:")
    print(f"  Providers: {stats['providers']}")
    print(f"  Models: {stats['models']}")
    print(f"  Categories: {stats['categories']}")
    print(f"  Techniques: {stats['techniques']}")
    print(f"  Evidence: {stats['evidence']}")
    print(f"\n  Coverage:")
    for provider, count in stats['coverage'].items():
        print(f"    {provider}: {count}")

if __name__ == "__main__":
    import sys
    populate_all_evidence()