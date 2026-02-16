"""
generate_report.py - Generate docs/SUMMARY.md, data/stats.json, and update README.md.

Writes to docs/SUMMARY.md only (single canonical location, served by GitHub Pages).
Also patches the "Dataset at a Glance" section of README.md with live stats.
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def generate_summary():
    """Generate a comprehensive markdown summary."""

    # Load all data
    with open('data/providers.json', 'r') as f:
        providers = {p['id']: p for p in json.load(f)}

    with open('data/models.json', 'r') as f:
        models_data = json.load(f)
        # models.json wraps the list in {"models": [...]}
        if isinstance(models_data, dict) and 'models' in models_data:
            models_list = models_data['models']
        elif isinstance(models_data, list):
            models_list = models_data
        else:
            models_list = []

    with open('data/categories.json', 'r') as f:
        categories = {c['id']: c for c in json.load(f)}

    with open('data/techniques.json', 'r') as f:
        techniques = {t['id']: t for t in json.load(f)}

    with open('data/evidence.json', 'r') as f:
        evidence_data = json.load(f)
        sources = evidence_data.get('sources', [])

    with open('data/model_technique_map.json', 'r') as f:
        technique_map = json.load(f)

    # Build lookups
    source_by_id = {s['id']: s for s in sources if 'id' in s}

    # Aggregate technique detections per provider from technique_map
    provider_techniques = defaultdict(lambda: defaultdict(list))
    technique_providers = defaultdict(lambda: defaultdict(list))
    all_detected_techniques = set()

    for doc_id, detected_techniques in technique_map.items():
        source = source_by_id.get(doc_id)
        if not source:
            continue
        provider_id = source.get('provider')
        if not provider_id:
            continue

        for tech in detected_techniques:
            if not tech.get('active', True):
                continue
            tech_id = tech.get('techniqueId')
            if not tech_id:
                continue
            all_detected_techniques.add(tech_id)
            detection = {
                'confidence': tech.get('confidence', 'Unknown'),
                'created_by': tech.get('created_by', 'unknown'),
                'doc_id': doc_id,
            }
            provider_techniques[provider_id][tech_id].append(detection)
            technique_providers[tech_id][provider_id].append(detection)

    # Count manual vs system detections per category
    category_manual = defaultdict(set)
    category_system = defaultdict(set)
    for tech_id in all_detected_techniques:
        cat_id = techniques.get(tech_id, {}).get('categoryId', '')
        for provider_id, detections in technique_providers[tech_id].items():
            for d in detections:
                if d['created_by'] == 'manual':
                    category_manual[cat_id].add(tech_id)
                else:
                    category_system[cat_id].add(tech_id)

    # Determine which providers have source documents
    providers_with_sources = set()
    for s in sources:
        p = s.get('provider')
        if p:
            providers_with_sources.add(p)

    # Order providers by source count descending, then alphabetical
    provider_order = sorted(
        providers_with_sources,
        key=lambda p: (-len([s for s in sources if s.get('provider') == p]),
                       providers.get(p, {}).get('name', p)),
    )

    # ================================================================
    # Build report
    # ================================================================
    report = ["# LLM Safety Mechanisms - Dataset Summary\n"]
    report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    # Separate active vs aspirational techniques
    active_techniques = {t_id: t for t_id, t in techniques.items()
                        if t.get('status') != 'aspirational'}
    aspirational_techniques = {t_id: t for t_id, t in techniques.items()
                              if t.get('status') == 'aspirational'}

    # --- Overall Statistics ---
    report.append("## Overall Statistics\n")
    report.append(f"- **Providers**: {len(providers_with_sources)}")
    report.append(f"- **Models tracked**: {len(models_list)}")
    report.append(f"- **Technique categories**: {len(categories)}")
    report.append(f"- **Active techniques in taxonomy**: {len(active_techniques)}")
    if aspirational_techniques:
        report.append(f"- **Aspirational techniques** (no provider evidence): "
                      f"{len(aspirational_techniques)}")
    report.append(f"- **Source documents**: {len(sources)}")
    active_detected = all_detected_techniques & set(active_techniques.keys())
    report.append(f"- **Techniques with detections**: "
                  f"{len(active_detected)} / {len(active_techniques)}")
    report.append("")

    # --- Coverage by Category ---
    report.append("## Coverage by Category\n")
    report.append("| Category | Techniques | System Detected | Manual Entry |")
    report.append("|----------|------------|-----------------|--------------|")

    for cat_id, cat in sorted(categories.items(), key=lambda x: x[1]['name']):
        tech_count = len([t for t in techniques.values()
                         if t['categoryId'] == cat_id])
        sys_count = len(category_system.get(cat_id, set()))
        manual_count = len(category_manual.get(cat_id, set()))
        report.append(f"| {cat['name']} | {tech_count} | "
                      f"{sys_count} | {manual_count} |")

    report.append("")

    # --- Provider Breakdown (tabular) ---
    report.append("## Provider Breakdown\n")
    report.append("| Provider | Type | Source Docs | Techniques | "
                  "Detection Confidence |")
    report.append("|----------|------|-------------|------------|"
                  "----------------------|")

    for provider_id in provider_order:
        if provider_id not in providers:
            continue
        provider = providers[provider_id]
        provider_sources = [s for s in sources
                          if s.get('provider') == provider_id]
        techs = provider_techniques.get(provider_id, {})
        tech_count = len(techs)

        # Confidence: use highest per technique
        conf = defaultdict(int)
        for tech_id, detections in techs.items():
            confidences = [d['confidence'] for d in detections]
            if 'High' in confidences:
                conf['H'] += 1
            elif 'Medium' in confidences:
                conf['M'] += 1
            else:
                conf['L'] += 1

        conf_str = (f"H:{conf.get('H', 0)} / "
                    f"M:{conf.get('M', 0)} / "
                    f"L:{conf.get('L', 0)}")

        report.append(
            f"| {provider['name']} | {provider['type']} | "
            f"{len(provider_sources)} | {tech_count} | {conf_str} |"
        )

    report.append("")

    # --- Technique Coverage Matrix (ALL providers) ---
    report.append("## Technique Coverage Matrix\n")

    header_names = []
    for p in provider_order:
        if p in providers:
            header_names.append(providers[p]['name'])

    report.append("| Technique | " + " | ".join(header_names) + " |")
    report.append("|-----------|" + "|".join(["---"] * len(header_names)) + "|")

    # Sort techniques by category then name
    sorted_techniques = sorted(
        techniques.values(),
        key=lambda t: (
            categories.get(t['categoryId'], {}).get('name', ''),
            t['name']
        )
    )

    for tech in sorted_techniques:
        tech_id = tech['id']
        is_aspirational = tech.get('status') == 'aspirational'

        if is_aspirational:
            row = [f"{tech['name']} *"]
            row.extend(['\u2014'] * len(provider_order))
        else:
            row = [tech['name']]
            for provider_id in provider_order:
                detections = technique_providers.get(tech_id, {}).get(
                    provider_id, [])
                if detections:
                    confidences = [d['confidence'] for d in detections]
                    if 'High' in confidences:
                        row.append('\u2705')
                    elif 'Medium' in confidences:
                        row.append('\U0001F7E1')
                    else:
                        row.append('\U0001F7E0')
                else:
                    row.append('\u2014')

        report.append(f"| {' | '.join(row)} |")

    report.append("")
    report.append("**Key:** \u2705 = High confidence | "
                  "\U0001F7E1 = Medium | "
                  "\U0001F7E0 = Low | "
                  "\u2014 = Not detected")
    if aspirational_techniques:
        report.append("")
        report.append("**\\*** Aspirational technique — no tracked provider "
                      "has documented production deployment.\n")
    else:
        report.append("")

    # --- Recent Source Documents ---
    report.append("## Recent Source Documents\n")
    recent_sources = sorted(
        sources,
        key=lambda s: s.get('date_added', ''),
        reverse=True
    )[:10]

    report.append("| Provider | Document | Type | URI | Date Added |")
    report.append("|----------|----------|------|-----|------------|")

    for s in recent_sources:
        provider_name = providers.get(
            s.get('provider'), {}
        ).get('name', s.get('provider', 'Unknown'))
        title = s.get('title', 'Unknown')
        doc_type = s.get('type', 'Unknown')
        date_added = s.get('date_added', 'N/A')
        uri = s.get('url', s.get('uri', ''))
        uri_display = uri if len(uri) <= 60 else uri[:57] + '...'
        report.append(f"| {provider_name} | {title} | {doc_type} | "
                      f"{uri_display} | {date_added} |")

    # Save report to docs/ only
    report_text = '\n'.join(report)

    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)
    with open(docs_dir / 'SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(report_text)

    # Save stats
    stats = {
        "generated": datetime.now().isoformat(),
        "providers": len(providers_with_sources),
        "models": len(models_list),
        "categories": len(categories),
        "techniques": len(techniques),
        "techniques_detected": len(all_detected_techniques),
        "sources": len(sources),
        "coverage": {
            p_id: len(provider_techniques.get(p_id, {}))
            for p_id in providers_with_sources
        }
    }

    with open('data/stats.json', 'w') as f:
        json.dump(stats, f, indent=2)

    # Count total technique-document links
    total_links = sum(
        len([t for t in techs if t.get('active', True)])
        for techs in technique_map.values()
    )

    # Update README
    update_readme(
        num_techniques=len(active_techniques),
        num_aspirational=len(aspirational_techniques),
        num_providers=len(providers_with_sources),
        num_sources=len(sources),
        num_links=total_links,
    )

    print("Generated docs/SUMMARY.md")
    print(f"  Providers: {len(providers_with_sources)}")
    print(f"  Models: {len(models_list)}")
    print(f"  Source documents: {len(sources)}")
    print(f"  Active techniques: {len(active_techniques)}"
          f" (+{len(aspirational_techniques)} aspirational)")
    print(f"  Techniques detected: "
          f"{len(active_detected)} / {len(active_techniques)}")
    print(f"  Technique-document links: {total_links}")


def update_readme(num_techniques, num_aspirational, num_providers,
                  num_sources, num_links):
    """Patch the 'Dataset at a Glance' section of README.md with live stats."""
    readme_path = Path('README.md')
    if not readme_path.exists():
        return

    text = readme_path.read_text(encoding='utf-8')

    # Build replacement lines
    new_glance = (
        f"- **{num_techniques} active safety techniques** across "
        f"**5 categories** (+{num_aspirational} aspirational)\n"
        f"- **{num_providers} providers** (OpenAI, Anthropic, Google, "
        f"Meta, Cohere, Mistral, xAI, and more)\n"
        f"- **{num_sources} source documents** (system cards, technical "
        f"reports, safety frameworks)\n"
        f"- **{num_links}+ technique-document links** with provenance "
        f"tracking"
    )

    # Match the glance block: lines starting with "- **" between
    # "## Dataset at a Glance" and the next "##" heading
    pattern = (
        r'(## Dataset at a Glance\s*\n\s*\n)'
        r'(- \*\*.*?)'
        r'(\n\s*\n## )'
    )
    replacement = r'\1' + new_glance + r'\3'

    new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)

    if new_text != text:
        readme_path.write_text(new_text, encoding='utf-8')
        print("Updated README.md (Dataset at a Glance)")
    else:
        print("README.md already up to date")


if __name__ == "__main__":
    generate_summary()
