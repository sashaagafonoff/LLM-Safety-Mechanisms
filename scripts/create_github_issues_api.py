import json
import requests
from collections import defaultdict
import time

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
        self.owner = "YOUR_GITHUB_USERNAME"  # Change this!
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
    
    def create_batch_issues(self):
        """Create issues for missing evidence"""
        missing = self.get_missing_evidence()
        print(f"Found {len(missing)} missing evidence combinations\n")
        
        # Group by provider
        by_provider = defaultdict(list)
        for item in missing:
            by_provider[item['provider']['name']].append(item)
        
        issues_created = []
        
        # Create one issue per provider with multiple techniques
        for provider_name, items in by_provider.items():
            if len(items) > 3:  # Create a batch issue
                techniques_list = '\n'.join([f"- [ ] {item['technique']['name']} (`{item['technique']['id']}`)" 
                                           for item in items[:10]])
                
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

## Resources
- Provider website: {items[0]['provider']['website']}
- Check their /safety or /docs pages
- Search for "{provider_name} safety" on arXiv

Thank you for contributing! 🙏"""
                
                labels = ["evidence", "help wanted", provider_name.lower().replace(' ', '-')]
                url = self.create_issue(title, body, labels)
                if url:
                    issues_created.append(url)
                    time.sleep(2)  # Rate limiting
        
        return issues_created

def main():
    print("GitHub Issue Creator")
    print("="*60)
    print("\nThis script can create GitHub issues for missing evidence.")
    print("\nOption 1: Generate issue content (no token needed)")
    print("Option 2: Create issues via API (requires personal access token)")
    print("\nTo use Option 2:")
    print("1. Go to: https://github.com/settings/tokens/new")
    print("2. Create a token with 'repo' scope")
    print("3. Set environment variable: $env:GITHUB_TOKEN = 'your_token_here'")
    print("   Or pass it when running the script")
    
    import os
    token = os.environ.get('GITHUB_TOKEN')
    
    if not token:
        print("\n⚠️  No GITHUB_TOKEN found. Will display issues instead of creating them.")
        response = input("\nContinue? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Update with your username!
    creator = GitHubIssueCreator(token)
    creator.owner = input("\nEnter your GitHub username: ") or "YOUR_USERNAME"
    
    print(f"\nWill create issues in: {creator.owner}/{creator.repo}")
    
    if token:
        response = input("\nCreate issues via API? (y/n): ")
        if response.lower() != 'y':
            return
    
    issues = creator.create_batch_issues()
    
    if token and issues:
        print(f"\n✅ Created {len(issues)} issues!")
        for url in issues:
            print(f"  - {url}")
    else:
        print("\n📋 Issue content displayed above. Copy and create manually on GitHub.")

if __name__ == "__main__":
    main()