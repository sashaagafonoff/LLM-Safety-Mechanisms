import json
from collections import defaultdict

def generate_summary():
    """Generate a markdown summary of the dataset"""
    # Load all data
    with open('data/providers.json', 'r') as f:
        providers = json.load(f)
    
    with open('data/evidence.json', 'r') as f:
        evidence = json.load(f)
    
    with open('data/techniques.json', 'r') as f:
        techniques = json.load(f)
    
    # Calculate statistics
    evidence_by_provider = defaultdict(list)
    for e in evidence:
        evidence_by_provider[e['providerId']].append(e)
    
    # Generate report
    report = ["# LLM Safety Mechanisms - Dataset Summary\n"]
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n")
    
    report.append("## Coverage Summary\n")
    report.append(f"- **Providers**: {len(providers)}")
    report.append(f"- **Techniques**: {len(techniques)}")
    report.append(f"- **Evidence Records**: {len(evidence)}\n")
    
    report.append("## Provider Breakdown\n")
    for provider in providers:
        p_id = provider['id']
        p_evidence = evidence_by_provider[p_id]
        report.append(f"### {provider['name']}")
        report.append(f"- Evidence Records: {len(p_evidence)}")
        report.append(f"- Techniques Covered: {len(set(e['techniqueId'] for e in p_evidence))}")
        
        # Rating breakdown
        ratings = defaultdict(int)
        for e in p_evidence:
            ratings[e['rating']] += 1
        
        report.append("- Ratings:")
        for rating, count in sorted(ratings.items()):
            report.append(f"  - {rating}: {count}")
        report.append("")
    
    # Save report
    with open('SUMMARY.md', 'w') as f:
        f.write('\n'.join(report))
    
    print("✅ Generated SUMMARY.md")

if __name__ == "__main__":
    generate_summary()