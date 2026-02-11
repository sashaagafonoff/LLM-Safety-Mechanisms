#!/usr/bin/env python3
"""
Compare two model_technique_map.json files in a minimal, diffable format.

Usage:
    python scripts/compare_maps.py nlu.json llm.json
    python scripts/compare_maps.py --file1 data/map_nlu.json --file2 data/map_llm.json
"""

import json
import sys
from pathlib import Path


def normalize_map(data: dict) -> dict:
    """Extract just sorted technique IDs per document."""
    return {k: sorted([m["techniqueId"] for m in v]) for k, v in data.items()}


def print_normalized(data: dict, label: str = ""):
    """Print in a clean, diffable format."""
    if label:
        print(f"# {label}")
    for doc_id in sorted(data.keys()):
        techniques = data[doc_id]
        if techniques:
            for tech in techniques:
                print(f"{doc_id}|{tech}")
        else:
            print(f"{doc_id}|(none)")


def main():
    if len(sys.argv) == 2:
        # Single file - just normalize and print
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
        print_normalized(normalize_map(data))

    elif len(sys.argv) == 3:
        # Two files - show side by side diff
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data1 = normalize_map(json.load(f))
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            data2 = normalize_map(json.load(f))

        all_docs = sorted(set(data1.keys()) | set(data2.keys()))

        print(f"# Comparing: {sys.argv[1]} vs {sys.argv[2]}")
        print(f"# Format: doc_id|technique  [status]")
        print()

        for doc_id in all_docs:
            techs1 = set(data1.get(doc_id, []))
            techs2 = set(data2.get(doc_id, []))

            all_techs = sorted(techs1 | techs2)

            for tech in all_techs:
                in1, in2 = tech in techs1, tech in techs2
                if in1 and in2:
                    status = "="
                elif in1:
                    status = "<"  # only in file1
                else:
                    status = ">"  # only in file2
                print(f"{doc_id}|{tech}  [{status}]")

    else:
        print("Usage: compare_maps.py <file.json>")
        print("       compare_maps.py <file1.json> <file2.json>")
        sys.exit(1)


if __name__ == "__main__":
    main()
