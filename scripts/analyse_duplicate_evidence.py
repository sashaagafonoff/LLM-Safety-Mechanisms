#!/usr/bin/env python3
"""
Evidence Duplicate Detection Script
Comprehensive analysis of duplicates in the evidence collection
"""

import json
import hashlib
from collections import defaultdict
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime

def load_evidence_data():
    """Load evidence data from the repository"""
    try:
        with open('data/evidence.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ evidence.json not found. Run from repo root directory.")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing evidence.json: {e}")
        return []

def generate_content_hash(item: Dict[str, Any]) -> str:
    """Generate hash based on content (excluding metadata)"""
    # Use core content fields that shouldn't vary for the same evidence
    content_fields = {
        'providerId': item.get('providerId', ''),
        'techniqueId': item.get('techniqueId', ''),
        'summary': item.get('summary', ''),
        'rating': item.get('rating', ''),
        'implementationDate': item.get('implementationDate', ''),
    }
    
    # Sort modelIds to handle array order differences
    if 'modelIds' in item and isinstance(item['modelIds'], list):
        content_fields['modelIds'] = sorted(item['modelIds'])
    
    content_str = json.dumps(content_fields, sort_keys=True)
    return hashlib.md5(content_str.encode()).hexdigest()

def generate_similarity_key(item: Dict[str, Any]) -> str:
    """Generate key for finding similar (not necessarily identical) evidence"""
    return f"{item.get('providerId', 'unknown')}_{item.get('techniqueId', 'unknown')}"

def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    if not text:
        return ""
    return text.lower().strip().replace('\n', ' ').replace('\r', '')

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Simple text similarity based on word overlap"""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def find_exact_duplicates(evidence: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Find exact duplicates based on content hash"""
    content_hash_groups = defaultdict(list)
    
    for item in evidence:
        content_hash = generate_content_hash(item)
        content_hash_groups[content_hash].append(item)
    
    # Return only groups with more than one item
    return {k: v for k, v in content_hash_groups.items() if len(v) > 1}

def find_id_duplicates(evidence: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Find entries with duplicate IDs"""
    id_groups = defaultdict(list)
    
    for item in evidence:
        evidence_id = item.get('id', 'no-id')
        id_groups[evidence_id].append(item)
    
    return {k: v for k, v in id_groups.items() if len(v) > 1}

def find_similar_evidence(evidence: List[Dict[str, Any]], similarity_threshold: float = 0.8) -> List[Tuple[Dict[str, Any], Dict[str, Any], float]]:
    """Find evidence entries that are very similar but not exact duplicates"""
    similar_pairs = []
    similarity_groups = defaultdict(list)
    
    # Group by provider + technique for efficiency
    for item in evidence:
        key = generate_similarity_key(item)
        similarity_groups[key].append(item)
    
    # Compare within each group
    for group_items in similarity_groups.values():
        if len(group_items) < 2:
            continue
            
        for i, item1 in enumerate(group_items):
            for item2 in group_items[i+1:]:
                # Skip if they're exact duplicates (handled elsewhere)
                if item1.get('id') == item2.get('id'):
                    continue
                
                # Compare summaries
                summary1 = item1.get('summary', '')
                summary2 = item2.get('summary', '')
                similarity = calculate_text_similarity(summary1, summary2)
                
                if similarity >= similarity_threshold:
                    similar_pairs.append((item1, item2, similarity))
    
    return sorted(similar_pairs, key=lambda x: x[2], reverse=True)

def analyze_duplicate_patterns(evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in duplicate data"""
    patterns = {
        'by_provider': defaultdict(int),
        'by_technique': defaultdict(int),
        'by_reviewer': defaultdict(int),
        'by_evidence_level': defaultdict(int),
        'rating_inconsistencies': [],
        'date_inconsistencies': []
    }
    
    # Group by provider + technique to find inconsistencies
    provider_technique_groups = defaultdict(list)
    for item in evidence:
        key = f"{item.get('providerId', 'unknown')}_{item.get('techniqueId', 'unknown')}"
        provider_technique_groups[key].append(item)
    
    for group_items in provider_technique_groups.values():
        if len(group_items) < 2:
            continue
            
        # Check for rating inconsistencies
        ratings = set(item.get('rating', 'unknown') for item in group_items)
        if len(ratings) > 1:
            patterns['rating_inconsistencies'].append({
                'provider': group_items[0].get('providerId'),
                'technique': group_items[0].get('techniqueId'),
                'ratings': list(ratings),
                'items': [item.get('id') for item in group_items]
            })
        
        # Check for date inconsistencies
        dates = set(item.get('implementationDate', 'unknown') for item in group_items)
        if len(dates) > 1:
            patterns['date_inconsistencies'].append({
                'provider': group_items[0].get('providerId'),
                'technique': group_items[0].get('techniqueId'),
                'dates': list(dates),
                'items': [item.get('id') for item in group_items]
            })
    
    # Count duplicates by various fields
    for item in evidence:
        patterns['by_provider'][item.get('providerId', 'unknown')] += 1
        patterns['by_technique'][item.get('techniqueId', 'unknown')] += 1
        patterns['by_reviewer'][item.get('reviewer', 'unknown')] += 1
        patterns['by_evidence_level'][item.get('evidenceLevel', 'unknown')] += 1
    
    return patterns

def generate_deduplication_report(evidence: List[Dict[str, Any]]) -> str:
    """Generate comprehensive deduplication report"""
    report = []
    report.append("# Evidence Collection Duplicate Analysis Report")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total Evidence Items: {len(evidence)}")
    report.append("")
    
    # Find exact duplicates
    exact_duplicates = find_exact_duplicates(evidence)
    report.append(f"## 1. Exact Duplicates: {len(exact_duplicates)} groups")
    if exact_duplicates:
        total_duplicate_items = sum(len(group) for group in exact_duplicates.values())
        report.append(f"Total duplicate items: {total_duplicate_items}")
        report.append("")
        
        for i, (hash_key, group) in enumerate(exact_duplicates.items(), 1):
            report.append(f"### Duplicate Group {i} ({len(group)} items)")
            report.append(f"Content Hash: {hash_key}")
            
            for item in group:
                report.append(f"- ID: `{item.get('id', 'no-id')}`")
                report.append(f"  - Provider: {item.get('providerId', 'unknown')}")
                report.append(f"  - Technique: {item.get('techniqueId', 'unknown')}")
                report.append(f"  - Summary: {item.get('summary', 'no summary')[:100]}...")
                report.append(f"  - Reviewer: {item.get('reviewer', 'unknown')}")
                report.append("")
    else:
        report.append("✅ No exact duplicates found!")
        report.append("")
    
    # Find ID duplicates
    id_duplicates = find_id_duplicates(evidence)
    report.append(f"## 2. ID Duplicates: {len(id_duplicates)} groups")
    if id_duplicates:
        for duplicate_id, group in id_duplicates.items():
            report.append(f"### Duplicate ID: `{duplicate_id}` ({len(group)} items)")
            for item in group:
                report.append(f"- Provider: {item.get('providerId')}, Technique: {item.get('techniqueId')}")
            report.append("")
    else:
        report.append("✅ No ID duplicates found!")
        report.append("")
    
    # Find similar evidence
    similar_evidence = find_similar_evidence(evidence)
    report.append(f"## 3. Similar Evidence: {len(similar_evidence)} pairs")
    if similar_evidence:
        for item1, item2, similarity in similar_evidence[:10]:  # Show top 10
            report.append(f"### Similarity: {similarity:.2%}")
            report.append(f"**Item 1:** `{item1.get('id')}`")
            report.append(f"- Summary: {item1.get('summary', '')[:100]}...")
            report.append(f"**Item 2:** `{item2.get('id')}`")
            report.append(f"- Summary: {item2.get('summary', '')[:100]}...")
            report.append("")
    else:
        report.append("✅ No highly similar evidence found!")
        report.append("")
    
    # Analyze patterns
    patterns = analyze_duplicate_patterns(evidence)
    report.append("## 4. Duplicate Patterns Analysis")
    
    if patterns['rating_inconsistencies']:
        report.append(f"### Rating Inconsistencies: {len(patterns['rating_inconsistencies'])}")
        for inconsistency in patterns['rating_inconsistencies'][:5]:  # Show top 5
            report.append(f"- {inconsistency['provider']} + {inconsistency['technique']}")
            report.append(f"  Ratings: {inconsistency['ratings']}")
            report.append(f"  Items: {inconsistency['items']}")
        report.append("")
    
    if patterns['date_inconsistencies']:
        report.append(f"### Date Inconsistencies: {len(patterns['date_inconsistencies'])}")
        for inconsistency in patterns['date_inconsistencies'][:5]:  # Show top 5
            report.append(f"- {inconsistency['provider']} + {inconsistency['technique']}")
            report.append(f"  Dates: {inconsistency['dates']}")
            report.append(f"  Items: {inconsistency['items']}")
        report.append("")
    
    # Summary and recommendations
    report.append("## 5. Recommendations")
    
    total_issues = len(exact_duplicates) + len(id_duplicates) + len(similar_evidence)
    if total_issues == 0:
        report.append("🎉 **No major duplication issues found!** Your evidence collection is clean.")
    else:
        report.append("### Action Items:")
        if exact_duplicates:
            report.append(f"1. **Remove {sum(len(g)-1 for g in exact_duplicates.values())} exact duplicate entries**")
        if id_duplicates:
            report.append(f"2. **Fix {len(id_duplicates)} ID conflicts**")
        if similar_evidence:
            report.append(f"3. **Review {len(similar_evidence)} similar evidence pairs for potential consolidation**")
        if patterns['rating_inconsistencies']:
            report.append(f"4. **Resolve {len(patterns['rating_inconsistencies'])} rating inconsistencies**")
    
    return "\n".join(report)

def generate_deduplication_script(evidence: List[Dict[str, Any]]) -> str:
    """Generate a script to automatically remove duplicates"""
    exact_duplicates = find_exact_duplicates(evidence)
    
    if not exact_duplicates:
        return "# No exact duplicates found - no deduplication needed!"
    
    # Find items to keep (first item in each duplicate group)
    items_to_remove = set()
    for group in exact_duplicates.values():
        # Keep the first item, remove the rest
        for item in group[1:]:
            items_to_remove.add(item.get('id'))
    
    script = []
    script.append("#!/usr/bin/env python3")
    script.append('"""')
    script.append("Automated Evidence Deduplication Script")
    script.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    script.append(f"Will remove {len(items_to_remove)} duplicate items")
    script.append('"""')
    script.append("")
    script.append("import json")
    script.append("")
    script.append("# IDs to remove (duplicates)")
    script.append(f"ITEMS_TO_REMOVE = {sorted(list(items_to_remove))}")
    script.append("")
    script.append("def deduplicate_evidence():")
    script.append('    with open("data/evidence.json", "r", encoding="utf-8") as f:')
    script.append("        evidence = json.load(f)")
    script.append("")
    script.append("    original_count = len(evidence)")
    script.append('    evidence = [item for item in evidence if item.get("id") not in ITEMS_TO_REMOVE]')
    script.append("    new_count = len(evidence)")
    script.append("")
    script.append('    with open("data/evidence.json", "w", encoding="utf-8") as f:')
    script.append("        json.dump(evidence, f, indent=2, ensure_ascii=False)")
    script.append("")
    script.append('    print(f"✅ Removed {original_count - new_count} duplicate items")')
    script.append('    print(f"📊 Evidence collection: {original_count} → {new_count} items")')
    script.append("")
    script.append('if __name__ == "__main__":')
    script.append("    deduplicate_evidence()")
    
    return "\n".join(script)

def main():
    """Main function"""
    print("🔍 Loading evidence data...")
    evidence = load_evidence_data()
    
    if not evidence:
        return
    
    print(f"📊 Loaded {len(evidence)} evidence items")
    print("🔍 Analyzing for duplicates...")
    
    # Generate report
    report = generate_deduplication_report(evidence)
    
    # Save report
    with open("evidence_duplicate_analysis.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("📄 Report saved to: evidence_duplicate_analysis.md")
    
    # Generate deduplication script if needed
    exact_duplicates = find_exact_duplicates(evidence)
    if exact_duplicates:
        script = generate_deduplication_script(evidence)
        with open("deduplicate_evidence.py", "w", encoding="utf-8") as f:
            f.write(script)
        print("🔧 Deduplication script saved to: deduplicate_evidence.py")
    
    # Print summary
    print("\n" + "="*50)
    print("DUPLICATE ANALYSIS SUMMARY")
    print("="*50)
    
    id_duplicates = find_id_duplicates(evidence)
    similar_evidence = find_similar_evidence(evidence)
    
    print(f"📋 Total Evidence Items: {len(evidence)}")
    print(f"🔄 Exact Duplicates: {len(exact_duplicates)} groups")
    print(f"🆔 ID Duplicates: {len(id_duplicates)} groups") 
    print(f"🔗 Similar Evidence: {len(similar_evidence)} pairs")
    
    if exact_duplicates or id_duplicates or similar_evidence:
        print(f"\n⚠️  Issues found! Review the detailed report.")
        if exact_duplicates:
            print(f"   Run 'python deduplicate_evidence.py' to remove exact duplicates")
    else:
        print(f"\n✅ No duplication issues found!")

if __name__ == "__main__":
    main()