import json
from collections import defaultdict
from datetime import datetime

def generate_summary():
    """Generate a comprehensive markdown summary"""
    
    # Load all data
    with open('data/providers.json', 'r') as f:
        providers = {p['id']: p for p in json.load(f)}
    
    with open('data/models.json', 'r') as f:
        models = json.load(f)
    
    with open('data/categories.json', 'r') as f:
        categories = {c['id']: c for c in json.load(f)}
    
    with open('data/techniques.json', 'r') as f:
        techniques = {t['id']: t for t in json.load(f)}
    
    with open('data/evidence.json', 'r') as f:
        evidence = json.load(f)
    
    # Calculate statistics
    evidence_by_provider = defaultdict(list)
    evidence_by_technique = defaultdict(list)
    evidence_by_category = defaultdict(list)
    
    for e in evidence:
        evidence_by_provider[e['providerId']].append(e)
        evidence_by_technique[e['techniqueId']].append(e)
        tech = techniques.get(e['techniqueId'])
        if tech:
            evidence_by_category[tech['categoryId']].append(e)
    
    # Generate report
    report = ["# LLM Safety Mechanisms - Dataset Summary\n"]
    report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    
    # Overall statistics
    report.append("## 📊 Overall Statistics\n")
    report.append(f"- **Providers**: {len(providers)}")
    report.append(f"- **Models**: {len(models)}")
    report.append(f"- **Categories**: {len(categories)}")
    report.append(f"- **Techniques**: {len(techniques)}")
    report.append(f"- **Evidence Records**: {len(evidence)}\n")
    
    # Coverage by category
    report.append("## 🎯 Coverage by Category\n")
    report.append("| Category | Techniques | Evidence Records |")
    report.append("|----------|------------|------------------|")
    
    for cat_id, cat in sorted(categories.items(), key=lambda x: x[1]['name']):
        tech_count = len([t for t in techniques.values() if t['categoryId'] == cat_id])
        evidence_count = len(evidence_by_category.get(cat_id, []))
        report.append(f"| {cat['name']} | {tech_count} | {evidence_count} |")
    
    report.append("")
    
    # Provider breakdown
    report.append("## 🏢 Provider Breakdown\n")
    
    for provider_id in ['openai', 'anthropic', 'google', 'meta', 'amazon']:
        if provider_id not in providers:
            continue
            
        provider = providers[provider_id]
        p_evidence = evidence_by_provider[provider_id]
        p_models = [m for m in models if m['providerId'] == provider_id]
        
        report.append(f"### {provider['name']}\n")
        report.append(f"- **Type**: {provider['type']}")
        report.append(f"- **Models**: {len(p_models)}")
        report.append(f"- **Evidence Records**: {len(p_evidence)}")
        report.append(f"- **Techniques Covered**: {len(set(e['techniqueId'] for e in p_evidence))}")
        
        # Rating breakdown
        ratings = defaultdict(int)
        for e in p_evidence:
            ratings[e['rating']] += 1
        
        if ratings:
            report.append("\n**Implementation Ratings**:")
            for rating in ['high', 'medium', 'low', 'not-implemented', 'planned']:
                if rating in ratings:
                    report.append(f"- {rating.title()}: {ratings[rating]}")
        
        # Evidence quality
        severity_bands = defaultdict(int)
        for e in p_evidence:
            severity_bands[e.get('severityBand', 'U')] += 1
        
        if severity_bands:
            report.append("\n**Evidence Quality**:")
            band_names = {'P': 'Primary', 'B': 'Benchmarked', 'C': 'Claimed', 'V': 'Volunteered', 'U': 'Unverified'}
            for band in ['P', 'B', 'C', 'V', 'U']:
                if band in severity_bands:
                    report.append(f"- {band_names[band]}: {severity_bands[band]}")
        
        report.append("")
    
    # Technique coverage matrix
    report.append("## 📋 Technique Coverage Matrix\n")
    report.append("| Technique | OpenAI | Anthropic | Google | Meta | Amazon |")
    report.append("|-----------|--------|-----------|---------|------|---------|")
    
    # Get unique techniques that have evidence
    technique_ids = sorted(set(e['techniqueId'] for e in evidence))
    
    for tech_id in technique_ids:
        if tech_id not in techniques:
            continue
            
        tech = techniques[tech_id]
        row = [tech['name']]
        
        for provider_id in ['openai', 'anthropic', 'google', 'meta', 'amazon']:
            provider_evidence = [e for e in evidence_by_technique[tech_id] 
                               if e['providerId'] == provider_id]
            if provider_evidence:
                rating = provider_evidence[0]['rating']
                if rating == 'high':
                    row.append('✅ High')
                elif rating == 'medium':
                    row.append('🟡 Med')
                elif rating == 'low':
                    row.append('🟠 Low')
                else:
                    row.append('❓ ' + rating[:3])
            else:
                row.append('—')
        
        report.append(f"| {' | '.join(row)} |")
    
    report.append("")
    
    # Recent updates
    report.append("## 🔄 Recent Updates\n")
    recent_evidence = sorted(evidence, 
                           key=lambda e: e.get('lastReviewed', ''), 
                           reverse=True)[:10]
    
    report.append("| Provider | Technique | Last Reviewed | Rating |")
    report.append("|----------|-----------|---------------|--------|")
    
    for e in recent_evidence:
        provider_name = providers.get(e['providerId'], {}).get('name', e['providerId'])
        tech_name = techniques.get(e['techniqueId'], {}).get('name', e['techniqueId'])
        report.append(f"| {provider_name} | {tech_name} | {e.get('lastReviewed', 'N/A')} | {e['rating']} |")
    
    # Save report
    report_text = '\n'.join(report)
    
    with open('SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    # Also save a simple stats file
    stats = {
        "generated": datetime.now().isoformat(),
        "providers": len(providers),
        "models": len(models),
        "categories": len(categories),
        "techniques": len(techniques),
        "evidence": len(evidence),
        "coverage": {
            p_id: len(evidence_by_provider[p_id]) 
            for p_id in providers.keys()
        }
    }
    
    with open('data/stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("✅ Generated SUMMARY.md")
    print(f"📊 Total evidence records: {len(evidence)}")

if __name__ == "__main__":
    generate_summary()