import json
import os
from pathlib import Path

# Ensure we're in the project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Create VERSION file
with open("VERSION", "w") as f:
    f.write("1.0.0\n")

# Create initial schema (save the full schema from earlier)
schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://safety.ai/schemas/llm-safety-mechanisms/v1.1.0",
    "title": "LLM Safety Mechanisms Dataset",
    # ... (include the full schema here)
}

with open("schema/llm-safety-v1.1.0.json", "w") as f:
    json.dump(schema, f, indent=2)

# Initialize data files
providers = [
    {
        "id": "openai",
        "name": "OpenAI",
        "type": "commercial",
        "headquarters": "United States",
        "website": "https://openai.com",
        "establishedYear": 2015,
    }
]

models = [
    {
        "id": "model-gpt-4o",
        "providerId": "openai",
        "name": "GPT-4",
        "version": "gpt-4o-2024-08-06",
        "releaseDate": "2024-08-06",
        "modalityType": "multimodal",
        "parameterCount": None,
        "deploymentStatus": "general-availability",
        "accessType": "api",
    }
]

categories = [
    {
        "id": "cat-pre-training-safety",
        "name": "Pre-training Safety",
        "description": "Safety measures applied during the initial training phase",
        "phase": "pre-training",
        "parentCategoryId": None,
        "riskAreaIds": [1, 2, 3],
    }
]

techniques = [
    {
        "id": "tech-training-data-filtering",
        "name": "Training Data Filtering",
        "categoryId": "cat-pre-training-safety",
        "description": "Systematic removal of harmful content from training datasets",
        "implementationMethods": ["RuleBased", "EmbeddedClassifier"],
        "governingStandards": [],
        "licence": None,
        "knownLimitations": ["May introduce demographic biases"],
        "aliases": ["Data Curation", "Dataset Cleaning"],
        "requiredTechniqueIds": [],
        "riskAreaIds": [1, 2, 6],
    }
]

risk_areas = [
    {
        "id": 1,
        "name": "Harmful Content",
        "description": "Violence, self-harm, CSAM, hate speech",
        "category": "safety",
    },
    {
        "id": 2,
        "name": "Bias & Fairness",
        "description": "Demographic biases, discrimination",
        "category": "fairness",
    },
    {
        "id": 3,
        "name": "Privacy & PII",
        "description": "Personal information leakage",
        "category": "privacy",
    },
    {
        "id": 4,
        "name": "Security & Misuse",
        "description": "Prompt injection, adversarial use",
        "category": "security",
    },
    {
        "id": 5,
        "name": "Misinformation",
        "description": "False or misleading information",
        "category": "reliability",
    },
    {
        "id": 6,
        "name": "Copyright & IP",
        "description": "Intellectual property violations",
        "category": "fairness",
    },
    {
        "id": 7,
        "name": "Transparency",
        "description": "Lack of interpretability",
        "category": "transparency",
    },
    {
        "id": 8,
        "name": "Environmental",
        "description": "Energy consumption, carbon footprint",
        "category": "reliability",
    },
    {
        "id": 9,
        "name": "Dual Use",
        "description": "Potential for harmful applications",
        "category": "security",
    },
    {
        "id": 10,
        "name": "Autonomy & Control",
        "description": "AI system autonomy risks",
        "category": "safety",
    },
]

evidence = []  # Start empty

# Write all data files
data_files = {
    "data/providers.json": providers,
    "data/models.json": models,
    "data/categories.json": categories,
    "data/techniques.json": techniques,
    "data/evidence.json": evidence,
    "data/risk_areas.json": risk_areas,
}

for filepath, data in data_files.items():
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

print("✅ Project initialized successfully!")
print(f"📁 Created in: {project_root}")
