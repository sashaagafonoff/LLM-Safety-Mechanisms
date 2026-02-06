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
        evidence_data = json.load(f)
        sources = evidence_data.get('sources', [])

    with open('data/model_technique_map.json', 'r') as f:
        technique_map = json.load(f)

    # Build source-to-provider mapping
    source_providers = {}
    for source in sources:
        source_providers[source.get('url', '')] = source.get('provider')
        source_providers[source.get('id', '')] = source.get('provider')

    # Calculate statistics from technique_map
    provider_techniques = defaultdict(set)
    technique_sources = defaultdict(list)

    for source_key, detected_techniques in technique_map.items():
        # Find provider for this source
        provider = None
        for source in sources:
            if source.get('url') == source_key or source.get('id') == source_key:
                provider = source.get('provider')
                break

        if not provider:
            continue

        # Track techniques per provider
        for tech in detected_techniques:
            tech_id = tech.get('techniqueId')
            if tech_id:
                provider_techniques[provider].add(tech_id)
                technique_sources[tech_id].append({
                    'provider': provider,
                    'source': source_key,
                    'confidence': tech.get('confidence', 'Unknown')
                })

    # Generate report
    report = ["# LLM Safety Mechanisms - Dataset Summary\n"]
    report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    # Overall statistics
    report.append("## 📊 Overall Statistics\n")
    report.append(f"- **Providers**: {len(providers)}")
    report.append(f"- **Models**: {len(models)}")
    report.append(f"- **Categories**: {len(categories)}")
    report.append(f"- **Techniques**: {len(techniques)}")
    report.append(f"- **Source Documents**: {len(sources)}")
    report.append(f"- **Techniques Detected**: {len(technique_sources)}\n")

    # Coverage by category
    report.append("## 🎯 Coverage by Category\n")
    report.append("| Category | Total Techniques | Detected in Sources |")
    report.append("|----------|------------------|---------------------|")

    for cat_id, cat in sorted(categories.items(), key=lambda x: x[1]['name']):
        tech_count = len([t for t in techniques.values() if t['categoryId'] == cat_id])
        detected_count = len([t_id for t_id in technique_sources.keys()
                             if techniques.get(t_id, {}).get('categoryId') == cat_id])
        report.append(f"| {cat['name']} | {tech_count} | {detected_count} |")

    report.append("")

    # Provider breakdown
    report.append("## 🏢 Provider Breakdown\n")

    for provider_id in ['openai', 'anthropic', 'google', 'meta', 'amazon', 'microsoft',
                        'deepseek', 'xai', 'cohere', 'mistral', 'alibaba', 'nvidia', 'tii']:
        if provider_id not in providers:
            continue

        provider = providers[provider_id]
        provider_sources = [s for s in sources if s.get('provider') == provider_id]
        techniques_detected = provider_techniques.get(provider_id, set())

        report.append(f"### {provider['name']}\n")
        report.append(f"- **Type**: {provider['type']}")
        report.append(f"- **Source Documents**: {len(provider_sources)}")
        report.append(f"- **Techniques Detected**: {len(techniques_detected)}")

        if techniques_detected:
            # Count confidence levels
            confidence_counts = defaultdict(int)
            for tech_id in techniques_detected:
                detections = [d for d in technique_sources[tech_id]
                            if d['provider'] == provider_id]
                for det in detections:
                    confidence_counts[det['confidence']] += 1

            if confidence_counts:
                report.append("\n**Detection Confidence**:")
                for conf in ['High', 'Medium', 'Low']:
                    if conf in confidence_counts:
                        report.append(f"- {conf}: {confidence_counts[conf]}")

        report.append("")

    # Technique coverage matrix
    report.append("## 📋 Technique Coverage Matrix\n")
    report.append("| Technique | OpenAI | Anthropic | Google | Meta | Amazon |")
    report.append("|-----------|--------|-----------|---------|------|---------|")

    # Get techniques that have been detected
    detected_technique_ids = sorted(technique_sources.keys())

    for tech_id in detected_technique_ids:
        if tech_id not in techniques:
            continue

        tech = techniques[tech_id]
        row = [tech['name'][:30]]  # Truncate long names

        for provider_id in ['openai', 'anthropic', 'google', 'meta', 'amazon']:
            detections = [d for d in technique_sources[tech_id]
                         if d['provider'] == provider_id]
            if detections:
                # Use highest confidence
                confidences = [d['confidence'] for d in detections]
                if 'High' in confidences:
                    row.append('✅ High')
                elif 'Medium' in confidences:
                    row.append('🟡 Med')
                else:
                    row.append('🟠 Low')
            else:
                row.append('—')

        report.append(f"| {' | '.join(row)} |")

    report.append("")

    # Recent sources
    report.append("## 📚 Recent Source Documents\n")
    recent_sources = sorted(sources,
                          key=lambda s: s.get('date_added', ''),
                          reverse=True)[:10]

    report.append("| Provider | Document | Type | Date Added |")
    report.append("|----------|----------|------|------------|")

    for s in recent_sources:
        provider_name = providers.get(s.get('provider'), {}).get('name', s.get('provider', 'Unknown'))
        title = s.get('title', 'Unknown')[:50]
        doc_type = s.get('type', 'Unknown')
        date_added = s.get('date_added', 'N/A')
        report.append(f"| {provider_name} | {title} | {doc_type} | {date_added} |")

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
        "sources": len(sources),
        "techniques_detected": len(technique_sources),
        "coverage": {
            p_id: len(provider_techniques[p_id])
            for p_id in providers.keys()
        }
    }

    with open('data/stats.json', 'w') as f:
        json.dump(stats, f, indent=2)

    print("✅ Generated SUMMARY.md")
    print(f"📊 Total source documents: {len(sources)}")
    print(f"🔍 Techniques detected: {len(technique_sources)}")

if __name__ == "__main__":
    generate_summary()
