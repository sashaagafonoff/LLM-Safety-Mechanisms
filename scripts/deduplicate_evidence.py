#!/usr/bin/env python3
"""
Automated Evidence Deduplication Script
Generated: 2025-07-24 23:40:17
Will remove 23 duplicate items
"""

import json

# IDs to remove (duplicates)
ITEMS_TO_REMOVE = ['ev-amazon-0005', 'ev-amazon-0009', 'ev-anthropic-0001', 'ev-anthropic-0007', 'ev-anthropic-0008', 'ev-anthropic-0022', 'ev-anthropic-0031', 'ev-google-0001', 'ev-google-0007', 'ev-google-0017', 'ev-google-0021', 'ev-google-0027', 'ev-meta-0001', 'ev-meta-0011', 'ev-meta-0012', 'ev-openai-0001', 'ev-openai-0002', 'ev-openai-0029', 'ev-openai-0030', 'ev-openai-0032', 'ev-openai-0033', 'ev-openai-0034', 'ev-openai-training-filtering-001']

def deduplicate_evidence():
    with open("data/evidence.json", "r", encoding="utf-8") as f:
        evidence = json.load(f)

    original_count = len(evidence)
    evidence = [item for item in evidence if item.get("id") not in ITEMS_TO_REMOVE]
    new_count = len(evidence)

    with open("data/evidence.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    print(f"✅ Removed {original_count - new_count} duplicate items")
    print(f"📊 Evidence collection: {original_count} → {new_count} items")

if __name__ == "__main__":
    deduplicate_evidence()