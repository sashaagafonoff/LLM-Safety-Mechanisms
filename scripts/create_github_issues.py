import json
import subprocess
from collections import defaultdict

def get_missing_evidence():
    """Identify missing provider-technique combinations"""
    
    # Load data
    with open('data/providers.json', 'r') as f:
        providers = json.load(f)
    
    with open('data/techniques.json', 'r') as f:
        techniques = json.load(f)
    
    with open('data/evidence.json', 'r') as f:
        evidence = json.load(f)
    
    # Build coverage matrix
    coverage = defaultdict(set)
    for e in evidence:
        coverage[e['providerId']].add(e['techniqueId'])
    
    # Find gaps
    missing = []
    priority_techniques = [
        'tech-csam-detection',
        'tech-bias-detection-training', 
        'tech-pii-reduction',
        'tech-prompt-injection-protection',
        'tech-capability-monitoring'
    ]
    
    for provider in providers:
        if provider['id'] in ['stability-ai', 'hugging-face', 'baidu', 'alibaba']:
            continue  # Skip these for now
            
        for technique in techniques:
            if technique['id'] not in coverage[provider['id']]:
                priority = 'high' if technique['id'] in priority_techniques else 'medium'
                missing.append({
                    'provider': provider,
                    'technique': technique,
                    'priority': priority
                })
    
    return missing

def create_issue_commands(missing_evidence):
    """Generate GitHub CLI commands to create issues"""
    
    commands = []
    
    # Group by provider
    by_provider = defaultdict(list)
    for item in missing_evidence:
        by_provider[item['provider']['name']].append(item)
    
    # Create batch issues per provider
    for provider_name, items in by_provider.items():
        if len(items) > 5:  # Create a batch issue
            techniques_list = '\n'.join([f"- [ ] {item['technique']['name']}" for item in items[:10]])
            
            title = f"[Evidence Needed] {provider_name} - Multiple Techniques"
            body = f"""## Provider: {provider_name}

We need evidence for the following safety techniques:

{techniques_list}

## How to Contribute

1. Check the provider's official documentation:
   - System/Model cards
   - Safety documentation
   - Research papers
   - API documentation

2. For each technique found:
   - Fork the repository
   - Run `python scripts/extract_evidence.py` to get a template
   - Fill in the evidence with sources
   - Submit a PR

## Priority Techniques
Focus on these first:
- CSAM Detection & Removal
- Bias Detection in Training Data
- PII Reduction
- Prompt Injection Protection

Label: `evidence`, `help wanted`, `{provider_name.lower().replace(' ', '-')}`
"""
            
            cmd = f'''gh issue create --title "{title}" --body "{body}" --label "evidence,help wanted"'''
            commands.append(cmd)
    
    # Create individual issues for high-priority gaps
    for item in missing_evidence:
        if item['priority'] == 'high' and len(by_provider[item['provider']['name']]) <= 5:
            provider = item['provider']
            technique = item['technique']
            
            title = f"[Evidence] Add {provider['name']} {technique['name']} evidence"
            body = f"""## Provider
Provider: {provider['name']} (`{provider['id']}`)

## Technique
Technique: {technique['name']} (`{technique['id']}`)
Category: {technique['categoryId']}

## Description
{technique['description']}

## Suggested Sources
- {provider['website']}/safety
- {provider['website']}/docs
- arXiv papers from {provider['name']}
- Official blog posts

## Evidence Template
```json
{{
  "providerId": "{provider['id']}",
  "techniqueId": "{technique['id']}",
  "modelIds": [],
  "rating": "medium",
  "severityBand": "C",
  "summary": "",
  "evidenceLevel": "claimed",
  "sourceUrls": [{{
    "url": "",
    "documentType": "documentation",
    "lastVerified": "2024-12-19",
    "sourceHash": {"0" * 64},
    "relevantSection": ""
  }}]
}}
```

Label: `evidence`, `help wanted`, `good first issue`
"""
            
            cmd = f'''gh issue create --title "{title}" --body "{body}" --label "evidence,help wanted,good first issue"'''
            commands.append(cmd)
    
    return commands

def main():
    missing = get_missing_evidence()
    print(f"Found {len(missing)} missing evidence combinations\n")
    
    # Generate commands
    commands = create_issue_commands(missing)
    
    # Save commands to file
    with open('create_issues.sh', 'w') as f:
        f.write('#!/bin/bash\n\n')
        f.write('# GitHub CLI commands to create issues\n')
        f.write('# Run: gh auth login (if not authenticated)\n')
        f.write('# Then: bash create_issues.sh\n\n')
        
        for i, cmd in enumerate(commands[:10]):  # Limit to 10 to avoid spam
            f.write(f"echo 'Creating issue {i+1}/{len(commands[:10])}...'\n")
            f.write(cmd + '\n')
            f.write('sleep 2  # Rate limiting\n\n')
    
    print(f"Generated {len(commands)} issue commands")
    print("Run: bash create_issues.sh")
    print("(Limited to first 10 to avoid spam)")

if __name__ == "__main__":
    main()