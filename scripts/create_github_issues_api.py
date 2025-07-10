import json
import requests
from collections import defaultdict
import time
import os

class GitHubIssueCreator:
    def __init__(self, token=None):
        """
        Initialize with a GitHub personal access token.
        Get one from: https://github.com/settings/tokens/new
        Needs 'repo' scope.
        """
        self.token = token
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        if token:
            self.headers['Authorization'] = f'token {token}'
        
        # Update these with your repo details
        self.owner = "sashaagafonoff"  # Your username
        self.repo = "LLM-Safety-Mechanisms"
        self.base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
    
    def create_issue(self, title, body, labels):
        """Create a single issue"""
        data = {
            'title': title,
            'body': body,
            'labels': labels
        }
        
        if not self.token:
            print(f"\n{'='*60}")
            print(f"Title: {title}")
            print(f"Labels: {', '.join(labels)}")
            print(f"Body:\n{body}")
            print(f"{'='*60}\n")
            return None
        
        response = requests.post(self.base_url, json=data, headers=self.headers)
        
        if response.status_code == 201:
            issue_data = response.json()
            print(f"✅ Created issue #{issue_data['number']}: {title}")
            return issue_data['html_url']
        else:
            print(f"❌ Failed to create issue: {response.status_code}")
            print(response.json())
            return None
    
    def get_missing_evidence(self):
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
            'tech-capability-monitoring',
            'tech-red-teaming',
            'tech-safety-reward-modeling'
        ]
        
        for provider in providers:
            # Skip platform providers for now
            if provider['id'] in ['stability-ai', 'hugging-face', 'baidu', 'alibaba']:
                continue
                
            for technique in techniques:
                if technique['id'] not in coverage[provider['id']]:
                    priority = 'high' if technique['id'] in priority_techniques else 'medium'
                    missing.append({
                        'provider': provider,
                        'technique': technique,
                        'priority': priority
                    })
        
        return missing
    
    def create_batch_issues(self, max_issues=10):
        """Create issues for missing evidence"""
        missing = self.get_missing_evidence()
        print(f"Found {len(missing)} missing evidence combinations\n")
        
        # Group by provider
        by_provider = defaultdict(list)
        for item in missing:
            by_provider[item['provider']['name']].append(item)
        
        issues_created = []
        issue_count = 0
        
        # Create one issue per provider with multiple techniques
        for provider_name, items in by_provider.items():
            if issue_count >= max_issues:
                break
                
            # Sort items by priority
            high_priority = [item for item in items if item['priority'] == 'high']
            medium_priority = [item for item in items if item['priority'] == 'medium']
            
            # Take top techniques
            selected_items = (high_priority[:7] + medium_priority[:3])[:10]
            
            if len(selected_items) > 0:
                techniques_list = '\n'.join([
                    f"- [ ] **{item['technique']['name']}** (`{item['technique']['id']}`) - Priority: {item['priority'].upper()}" 
                    for item in selected_items
                ])
                
                title = f"[Evidence Needed] {provider_name} - {len(selected_items)} Safety Techniques"
                body = f"""## Provider: {provider_name}

We need evidence for the following safety techniques:

{techniques_list}

## How to Contribute

1. **Check official documentation:**
   - {items[0]['provider']['website']}/safety
   - {items[0]['provider']['website']}/docs
   - System cards, model cards, or research papers
   - Blog posts or announcements

2. **For each technique found:**
   - Fork the repository
   - Run `python scripts/extract_evidence.py` to get a template
   - Fill in the evidence with sources
   - Submit a PR with title: "Add {provider_name} [technique] evidence"

3. **Evidence requirements:**
   - Must include primary source URL
   - Should include implementation date if known
   - Rate as high/medium/low based on documentation quality
   - Include specific quotes or section references

## Priority Techniques
Please focus on HIGH priority items first:
- CSAM Detection & Removal
- Bias Detection in Training Data  
- PII Reduction
- Prompt Injection Protection
- Red Team Exercises
- Capability Monitoring

## Example Evidence JSON
```json
{{
  "providerId": "{items[0]['provider']['id']}",
  "techniqueId": "tech-xxx",
  "modelIds": [],
  "rating": "medium",
  "severityBand": "C",
  "summary": "Brief description of implementation",
  "evidenceLevel": "primary",
  "sourceUrls": [{{
    "url": "https://...",
    "documentType": "system-card",
    "lastVerified": "2024-12-19",
    "sourceHash": "{"0" * 64}",
    "relevantSection": "Section X.Y"
  }}],
  "implementationDate": null,
  "lastReviewed": "2024-12-19",
  "reviewFrequency": "P6M",
  "reviewer": "contributor-github-username"
}}
```

Thank you for contributing to AI safety transparency! 🙏"""
                
                labels = ["evidence", "help wanted"]
                if len(high_priority) > 0:
                    labels.append("high-priority")
                if len(selected_items) <= 3:
                    labels.append("good first issue")
                
                url = self.create_issue(title, body, labels)
                if url:
                    issues_created.append(url)
                    issue_count += 1
                    time.sleep(2)  # Rate limiting
        
        # Also create a few individual high-priority issues
        high_priority_missing = [item for item in missing if item['priority'] == 'high'][:5]
        
        for item in high_priority_missing:
            if issue_count >= max_issues:
                break
                
            provider = item['provider']
            technique = item['technique']
            
            title = f"[High Priority] Add {provider['name']} - {technique['name']} evidence"
            body = f"""## High Priority Evidence Needed

**Provider:** {provider['name']} (`{provider['id']}`)  
**Technique:** {technique['name']} (`{technique['id']}`)  
**Category:** {technique['categoryId']}

## Description
{technique['description']}

## Why This Is High Priority
This is a critical safety technique that should be documented across all major providers.

## Suggested Sources
1. {provider['website']}/safety
2. {provider['website']}/docs
3. Search for: "{provider['name']} {technique['name']}"
4. Recent blog posts or announcements
5. Research papers by {provider['name']} team

## How to Contribute
1. Find evidence in official documentation
2. Fork this repository
3. Create evidence JSON using the template below
4. Submit PR with title: "Add {provider['name']} {technique['name']} evidence"

## Evidence Template
```json
{{
  "providerId": "{provider['id']}",
  "techniqueId": "{technique['id']}",
  "modelIds": [],
  "rating": "medium",
  "severityBand": "C",
  "summary": "",
  "evidenceLevel": "primary",
  "sourceUrls": [{{
    "url": "",
    "documentType": "documentation",
    "lastVerified": "2024-12-19",
    "sourceHash": "{"0" * 64}",
    "relevantSection": ""
  }}],
  "implementationDate": null,
  "lastReviewed": "2024-12-19",
  "reviewFrequency": "P6M",
  "reviewer": "your-github-username",
  "knownLimitations": [],
  "deploymentScope": "all-users",
  "geographicRestrictions": [],
  "complianceStandards": []
}}
```

Thank you for helping document AI safety practices! 🛡️"""
            
            labels = ["evidence", "help wanted", "high-priority", "good first issue"]
            
            url = self.create_issue(title, body, labels)
            if url:
                issues_created.append(url)
                issue_count += 1
                time.sleep(2)
        
        return issues_created

def main():
    print("GitHub Issue Creator for LLM Safety Mechanisms")
    print("="*60)
    
    # Get token from environment
    token = os.environ.get('GITHUB_TOKEN')
    
    if not token:
        print("\n⚠️  No GITHUB_TOKEN found in environment.")
        print("\nTo set it in PowerShell:")
        print('  $env:GITHUB_TOKEN = "ghp_YOUR_TOKEN_HERE"')
        print("\nTo create a token:")
        print("  1. Go to: https://github.com/settings/tokens/new")
        print("  2. Check the 'repo' scope")
        print("  3. Generate and copy the token")
        return
    
    creator = GitHubIssueCreator(token)
    
    print(f"\nWill create issues in: {creator.owner}/{creator.repo}")
    print("GitHub API rate limit: 5000 requests/hour")
    
    # Ask how many issues to create
    try:
        max_issues = int(input("\nHow many issues to create? (max 10 recommended): "))
        max_issues = min(max_issues, 20)  # Cap at 20 for safety
    except:
        max_issues = 5
    
    response = input(f"\nCreate up to {max_issues} issues? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    print("\nCreating issues...")
    issues = creator.create_batch_issues(max_issues)
    
    if issues:
        print(f"\n✅ Successfully created {len(issues)} issues!")
        print("\nCreated issues:")
        for i, url in enumerate(issues, 1):
            print(f"  {i}. {url}")
    else:
        print("\n❌ No issues were created. Check the error messages above.")

if __name__ == "__main__":
    main()