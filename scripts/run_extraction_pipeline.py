#!/usr/bin/env python3
"""
Extraction Pipeline - Runs NLU and LLM extraction in sequence.

This script orchestrates the two-stage extraction process:
1. NLU pass: Semantic embedding + cross-encoder verification
2. LLM pass: Claude API analysis with NLU context

The LLM pass builds on NLU findings (additive), can suggest deletions,
and manual annotations are always preserved.

Usage:
    python scripts/run_extraction_pipeline.py                    # Full pipeline
    python scripts/run_extraction_pipeline.py --nlu-only         # Just NLU pass
    python scripts/run_extraction_pipeline.py --llm-only         # Just LLM pass (uses existing NLU)
    python scripts/run_extraction_pipeline.py --id doc-id        # Process specific document
    python scripts/run_extraction_pipeline.py --model sonnet     # Use Sonnet instead of Haiku

Requirements:
    - sentence-transformers (for NLU)
    - anthropic package + ANTHROPIC_API_KEY (for LLM)
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try API_key.env first, then fall back to .env
    env_file = Path(__file__).parent.parent / "API_key.env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()  # Default .env in current directory
except ImportError:
    pass  # dotenv not installed, rely on environment variables

# Paths
DATA_DIR = Path("data")
OUTPUT_PATH = DATA_DIR / "model_technique_map.json"
NLU_OUTPUT_PATH = DATA_DIR / "map_nlu.json"
LLM_OUTPUT_PATH = DATA_DIR / "map_llm.json"
FLAT_TEXT_DIR = DATA_DIR / "flat_text"
PIPELINE_LOG_PATH = Path("cache/pipeline_log.json")


def load_existing_map() -> Dict[str, List[Dict]]:
    """Load existing model_technique_map.json if it exists."""
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def partition_by_source(existing: Dict[str, List[Dict]]) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Partition existing entries by their source.

    Returns dict with keys: 'manual', 'nlu', 'llm', 'legacy'
    Each value is a dict mapping doc_id -> list of technique entries
    """
    partitioned = {
        'manual': {},
        'nlu': {},
        'llm': {},
        'legacy': {}
    }

    for doc_id, techniques in existing.items():
        for tech in techniques:
            # Determine source from evidence entries
            source = 'legacy'  # Default for old format

            evidence = tech.get('evidence', [])
            if isinstance(evidence, list) and evidence:
                first_ev = evidence[0]
                if isinstance(first_ev, dict):
                    created_by = first_ev.get('created_by', '')
                    if created_by == 'manual':
                        source = 'manual'
                    elif created_by == 'nlu':
                        source = 'nlu'
                    elif created_by == 'llm':
                        source = 'llm'
                elif isinstance(first_ev, str):
                    if first_ev == 'Manual annotation':
                        source = 'manual'

            if doc_id not in partitioned[source]:
                partitioned[source][doc_id] = []
            partitioned[source][doc_id].append(tech)

    return partitioned


def merge_technique_lists(base: List[Dict], additions: List[Dict], source: str) -> List[Dict]:
    """
    Merge technique lists, avoiding duplicates.

    Deduplication is by techniqueId - if same technique exists,
    we add new evidence entries rather than replacing.
    """
    # Index existing by techniqueId
    by_id = {t['techniqueId']: t for t in base}

    for new_tech in additions:
        tech_id = new_tech['techniqueId']

        if tech_id in by_id:
            # Technique exists - merge evidence
            existing = by_id[tech_id]
            existing_texts = set()

            for ev in existing.get('evidence', []):
                if isinstance(ev, dict):
                    existing_texts.add(ev.get('text', ''))
                elif isinstance(ev, str):
                    existing_texts.add(ev)

            # Add new evidence that doesn't already exist
            for new_ev in new_tech.get('evidence', []):
                new_text = new_ev.get('text', '') if isinstance(new_ev, dict) else new_ev
                if new_text and new_text not in existing_texts:
                    if 'evidence' not in existing:
                        existing['evidence'] = []
                    existing['evidence'].append(new_ev)
                    existing_texts.add(new_text)
        else:
            # New technique - add it
            by_id[tech_id] = new_tech

    return list(by_id.values())


def apply_deletions(techniques: List[Dict], deletions: List[Dict]) -> List[Dict]:
    """
    Apply LLM-suggested deletions by marking techniques/evidence as inactive.
    """
    deletion_ids = {d['techniqueId'] for d in deletions}
    deletion_reasons = {d['techniqueId']: d.get('reasoning', '') for d in deletions}

    for tech in techniques:
        tech_id = tech['techniqueId']
        if tech_id in deletion_ids:
            # Mark as deleted at technique level
            tech['active'] = False
            tech['deleted_by'] = 'llm'
            tech['deletion_reason'] = deletion_reasons.get(tech_id, '')

            # Also mark all evidence as deleted
            for ev in tech.get('evidence', []):
                if isinstance(ev, dict):
                    ev['active'] = False
                    ev['deleted_by'] = 'llm'

    return techniques


def run_nlu_pass(specific_doc_id: Optional[str] = None) -> Dict[str, List[Dict]]:
    """Run NLU analysis and return results."""
    print("\n" + "=" * 70)
    print("STAGE 1: NLU ANALYSIS")
    print("=" * 70)

    # Import here to avoid requiring sentence-transformers when not using NLU
    try:
        from analyze_nlu import NLUAnalyzer, INPUT_DIR
    except ImportError as e:
        print(f"Error importing NLU analyzer: {e}")
        print("Make sure sentence-transformers is installed")
        sys.exit(1)

    analyzer = NLUAnalyzer()

    # Get files to process
    if specific_doc_id:
        files = [INPUT_DIR / f"{specific_doc_id}.txt"]
        if not files[0].exists():
            print(f"Error: File not found: {files[0]}")
            return {}
    else:
        files = sorted(INPUT_DIR.glob("*.txt"))
        files = [f for f in files if not f.name.startswith("temp_")]

    print(f"\nProcessing {len(files)} documents...")

    results = {}
    for i, file_path in enumerate(files, 1):
        doc_id = file_path.stem
        print(f"[{i}/{len(files)}] {doc_id}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            parts = content.split("-" * 20 + "\n", 1)
            body = parts[1] if len(parts) > 1 else content

        raw_matches = analyzer.analyze_document(body, doc_id)
        consolidated = analyzer._aggregate_results(raw_matches)

        results[doc_id] = consolidated
        print(f"   → {len(consolidated)} techniques found")

    # Save NLU-only results
    with open(NLU_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ NLU results saved to {NLU_OUTPUT_PATH}")

    return results


def run_llm_pass(nlu_results: Dict[str, List[Dict]],
                 model_name: str = "haiku",
                 specific_doc_id: Optional[str] = None) -> Dict[str, Dict]:
    """
    Run LLM analysis with NLU context and return results.

    Returns dict mapping doc_id -> {"additions": [...], "deletions": [...]}
    """
    print("\n" + "=" * 70)
    print("STAGE 2: LLM ANALYSIS")
    print("=" * 70)

    # Import here to avoid requiring anthropic when not using LLM
    try:
        from llm_assisted_extraction import LLMExtractor, FLAT_TEXT_DIR
    except ImportError as e:
        print(f"Error importing LLM extractor: {e}")
        print("Make sure anthropic is installed and ANTHROPIC_API_KEY is set")
        sys.exit(1)

    extractor = LLMExtractor(model_name=model_name, resume=False)

    # Get files to process
    if specific_doc_id:
        files = [(specific_doc_id, FLAT_TEXT_DIR / f"{specific_doc_id}.txt")]
    else:
        files = [(f.stem, f) for f in sorted(FLAT_TEXT_DIR.glob("*.txt"))]

    print(f"\nProcessing {len(files)} documents with {extractor.model}...")

    for i, (doc_id, file_path) in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] ", end="")

        # Get NLU results for this document
        nlu_for_doc = nlu_results.get(doc_id, [])

        # Process with NLU context
        extractor.process_document(doc_id, file_path, nlu_results=nlu_for_doc)

    # Get raw results with deletions
    raw_results = extractor.get_raw_results()

    # Save LLM-only results
    with open(LLM_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(raw_results, f, indent=2)
    print(f"\n✓ LLM results saved to {LLM_OUTPUT_PATH}")

    return raw_results


def merge_all_results(manual: Dict[str, List[Dict]],
                      nlu: Dict[str, List[Dict]],
                      llm: Dict[str, Dict]) -> Dict[str, List[Dict]]:
    """
    Merge all results: manual (preserved) + NLU + LLM additions - LLM deletions.
    """
    print("\n" + "=" * 70)
    print("MERGING RESULTS")
    print("=" * 70)

    all_doc_ids = set(manual.keys()) | set(nlu.keys()) | set(llm.keys())
    final = {}

    stats = {
        'manual_preserved': 0,
        'nlu_added': 0,
        'llm_added': 0,
        'llm_deleted': 0
    }

    for doc_id in sorted(all_doc_ids):
        doc_techniques = []

        # 1. Start with manual annotations (always preserved)
        if doc_id in manual:
            doc_techniques = manual[doc_id].copy()
            stats['manual_preserved'] += len(doc_techniques)

        # 2. Add NLU results
        if doc_id in nlu:
            before = len(doc_techniques)
            doc_techniques = merge_technique_lists(doc_techniques, nlu[doc_id], 'nlu')
            stats['nlu_added'] += len(doc_techniques) - before

        # 3. Add LLM additions and apply deletions
        if doc_id in llm:
            llm_result = llm[doc_id]

            if isinstance(llm_result, dict):
                additions = llm_result.get('additions', [])
                deletions = llm_result.get('deletions', [])
            else:
                # Legacy format
                additions = llm_result
                deletions = []

            # Add LLM findings
            before = len(doc_techniques)
            doc_techniques = merge_technique_lists(doc_techniques, additions, 'llm')
            stats['llm_added'] += len(doc_techniques) - before

            # Apply deletions (soft delete - marks as inactive)
            if deletions:
                doc_techniques = apply_deletions(doc_techniques, deletions)
                stats['llm_deleted'] += len(deletions)

        final[doc_id] = doc_techniques

    print(f"\nMerge statistics:")
    print(f"  Manual preserved: {stats['manual_preserved']}")
    print(f"  NLU added: {stats['nlu_added']}")
    print(f"  LLM added: {stats['llm_added']}")
    print(f"  LLM deletions: {stats['llm_deleted']}")

    return final


def save_final_results(results: Dict[str, List[Dict]]):
    """Save final merged results."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Count totals
    total_docs = len(results)
    total_techniques = sum(len(techs) for techs in results.values())
    active_techniques = sum(
        1 for techs in results.values()
        for t in techs if t.get('active', True)
    )

    print(f"\n✓ Final results saved to {OUTPUT_PATH}")
    print(f"  Documents: {total_docs}")
    print(f"  Total technique links: {total_techniques}")
    print(f"  Active links: {active_techniques}")


def save_pipeline_log(stats: Dict):
    """Save pipeline execution log."""
    PIPELINE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log = {
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    }

    with open(PIPELINE_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Run extraction pipeline (NLU + LLM)"
    )
    parser.add_argument(
        '--nlu-only',
        action='store_true',
        help='Run only NLU pass'
    )
    parser.add_argument(
        '--llm-only',
        action='store_true',
        help='Run only LLM pass (uses existing NLU results)'
    )
    parser.add_argument(
        '--id',
        type=str,
        help='Process only a specific document ID'
    )
    parser.add_argument(
        '--model',
        type=str,
        choices=['haiku', 'sonnet', 'sonnet-legacy', 'opus'],
        default='haiku',
        help='Claude model for LLM pass (default: haiku)'
    )
    parser.add_argument(
        '--preserve-manual',
        action='store_true',
        default=True,
        help='Preserve manual annotations (default: True)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("EXTRACTION PIPELINE")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")

    # Load existing results to preserve manual annotations
    existing = load_existing_map()
    partitioned = partition_by_source(existing)

    print(f"\nExisting data:")
    print(f"  Manual annotations: {sum(len(v) for v in partitioned['manual'].values())} techniques")
    print(f"  NLU detections: {sum(len(v) for v in partitioned['nlu'].values())} techniques")
    print(f"  LLM detections: {sum(len(v) for v in partitioned['llm'].values())} techniques")
    print(f"  Legacy format: {sum(len(v) for v in partitioned['legacy'].values())} techniques")

    # Run pipeline stages
    nlu_results = {}
    llm_results = {}

    if not args.llm_only:
        nlu_results = run_nlu_pass(specific_doc_id=args.id)
    else:
        # Load existing NLU results
        if NLU_OUTPUT_PATH.exists():
            with open(NLU_OUTPUT_PATH, 'r', encoding='utf-8') as f:
                nlu_results = json.load(f)
            print(f"\n✓ Loaded existing NLU results from {NLU_OUTPUT_PATH}")
        else:
            print(f"\n⚠️ No existing NLU results found at {NLU_OUTPUT_PATH}")

    if not args.nlu_only:
        llm_results = run_llm_pass(
            nlu_results,
            model_name=args.model,
            specific_doc_id=args.id
        )

    # Merge all results
    if not args.nlu_only and not args.llm_only:
        final = merge_all_results(
            manual=partitioned['manual'] if args.preserve_manual else {},
            nlu=nlu_results,
            llm=llm_results
        )
        save_final_results(final)
    elif args.nlu_only:
        # Just save NLU results as the main output
        final = merge_all_results(
            manual=partitioned['manual'] if args.preserve_manual else {},
            nlu=nlu_results,
            llm={}
        )
        save_final_results(final)
    elif args.llm_only:
        # Merge NLU + LLM results
        final = merge_all_results(
            manual=partitioned['manual'] if args.preserve_manual else {},
            nlu=nlu_results,
            llm=llm_results
        )
        save_final_results(final)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"Finished: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
