#!/usr/bin/env python3
"""Evaluate NLU pipeline against ground truth from manual reviews.

Runs NLU analysis on reviewed documents and compares results against
the manually-curated technique map to compute precision, recall, and F1.
Does NOT modify model_technique_map.json.
"""

import json
import os
import sys
from pathlib import Path

# Add scripts dir for imports
sys.path.insert(0, str(Path(__file__).parent))
from analyze_nlu import NLUAnalyzer

INPUT_DIR = Path("data/flat_text")
MAP_PATH = Path("data/model_technique_map.json")


def _load_no_safety_flags() -> set:
    """Load document IDs explicitly flagged as no_safety_content in evidence.json."""
    evidence_path = Path("data/evidence.json")
    if not evidence_path.exists():
        return set()
    with open(evidence_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    flagged = set()
    for source in data.get("sources", []):
        meta = source.get("content_metadata", {})
        if meta.get("no_safety_content", False):
            flagged.add(source.get("id", ""))
    return flagged


def load_ground_truth(map_path: Path) -> dict:
    """Load ground truth from manually reviewed entries in the technique map.

    Returns dict mapping doc_id -> {"techniques": set, "no_safety_data": bool}.
    Documents where all entries were rejected and none added manually are
    flagged as no_safety_data — these should be excluded from aggregate FP
    counts since any detection is by definition a false positive against an
    empty ground truth, which distorts precision metrics.

    Also respects the no_safety_content flag from evidence.json.
    """
    with open(map_path, "r", encoding="utf-8") as f:
        technique_map = json.load(f)

    no_safety_flags = _load_no_safety_flags()

    ground_truth = {}
    for doc_id, entries in technique_map.items():
        has_manual = False
        has_deleted = False
        for e in entries:
            if not e.get("active", True) and e.get("deleted_by") not in (None, "system"):
                has_deleted = True
            for ev in e.get("evidence", []):
                if ev.get("created_by") in ("manual", "sashaagafonoff"):
                    has_manual = True

        if has_manual or has_deleted:
            # This document has been manually reviewed
            active_techniques = set()
            for e in entries:
                if e.get("active", True):
                    active_techniques.add(e["techniqueId"])

            # Flag as no-safety if GT is empty OR explicitly marked in evidence.json
            is_no_safety = len(active_techniques) == 0 or doc_id in no_safety_flags

            ground_truth[doc_id] = {
                "techniques": active_techniques,
                "no_safety_data": is_no_safety,
            }

    return ground_truth


def run_nlu_on_doc(analyzer: "NLUAnalyzer", doc_id: str) -> set:
    """Run NLU analysis on a single document, return detected technique IDs."""
    txt_path = INPUT_DIR / f"{doc_id}.txt"
    if not txt_path.exists():
        print(f"  WARNING: No flat text for {doc_id}")
        return set()

    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()
        parts = content.split("-" * 20 + "\n", 1)
        body = parts[1] if len(parts) > 1 else content

    raw_matches = analyzer.analyze_document(body, doc_id)
    consolidated = analyzer._aggregate_results(raw_matches)
    return {entry["techniqueId"] for entry in consolidated}


def main():
    print("=" * 70)
    print("NLU EVALUATION AGAINST GROUND TRUTH")
    print("=" * 70)

    # Load ground truth
    ground_truth = load_ground_truth(MAP_PATH)
    safety_docs = {k: v for k, v in ground_truth.items() if not v["no_safety_data"]}
    no_safety_docs = {k: v for k, v in ground_truth.items() if v["no_safety_data"]}

    print(f"\nFound {len(ground_truth)} manually reviewed documents:")
    for doc_id, info in sorted(ground_truth.items()):
        flag = " [NO SAFETY DATA]" if info["no_safety_data"] else ""
        print(f"  {doc_id}: {len(info['techniques'])} active techniques{flag}")

    if no_safety_docs:
        print(f"\n  {len(no_safety_docs)} document(s) flagged as containing no safety data.")
        print("  These are excluded from aggregate precision/recall (FP-only distortion).")

    # Initialize analyzer
    print("\nLoading NLU models...")
    analyzer = NLUAnalyzer()

    # Run analysis on each reviewed document
    results = {}
    for doc_id in sorted(ground_truth.keys()):
        info = ground_truth[doc_id]
        gt = info["techniques"]
        is_no_safety = info["no_safety_data"]

        label = " [NO SAFETY DATA]" if is_no_safety else ""
        print(f"\nAnalyzing: {doc_id}{label}")
        detected = run_nlu_on_doc(analyzer, doc_id)

        tp = detected & gt
        fp = detected - gt
        fn = gt - detected

        precision = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) > 0 else float("nan")
        recall = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) > 0 else float("nan")
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        results[doc_id] = {
            "gt_count": len(gt),
            "detected": len(detected),
            "tp": len(tp),
            "fp": len(fp),
            "fn": len(fn),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "fp_list": sorted(fp),
            "fn_list": sorted(fn),
            "no_safety_data": is_no_safety,
        }

        print(f"  GT={len(gt)} Detected={len(detected)} TP={len(tp)} FP={len(fp)} FN={len(fn)}")
        print(f"  P={precision:.3f} R={recall:.3f} F1={f1:.3f}")
        if fp:
            print(f"  FP: {sorted(fp)}")
        if fn:
            print(f"  FN: {sorted(fn)}")

    # Aggregate — excluding no-safety-data documents
    print("\n" + "=" * 70)
    print("AGGREGATE RESULTS (excluding no-safety-data documents)")
    print("=" * 70)

    eval_results = {k: v for k, v in results.items() if not v["no_safety_data"]}

    total_tp = sum(r["tp"] for r in eval_results.values())
    total_fp = sum(r["fp"] for r in eval_results.values())
    total_fn = sum(r["fn"] for r in eval_results.values())

    agg_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    agg_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    agg_f1 = 2 * agg_precision * agg_recall / (agg_precision + agg_recall) if (agg_precision + agg_recall) > 0 else 0

    print(f"\nDocuments evaluated: {len(eval_results)} (excluded {len(no_safety_docs)} no-safety-data)")
    print(f"Total TP={total_tp}  FP={total_fp}  FN={total_fn}")
    print(f"Precision: {agg_precision:.3f}  ({total_tp}/{total_tp + total_fp})")
    print(f"Recall:    {agg_recall:.3f}  ({total_tp}/{total_tp + total_fn})")
    print(f"F1:        {agg_f1:.3f}")

    # Show no-safety-data documents separately
    if no_safety_docs:
        excluded_fp = sum(results[k]["fp"] for k in no_safety_docs)
        print(f"\nNo-safety-data documents ({len(no_safety_docs)}):")
        for doc_id in sorted(no_safety_docs):
            r = results[doc_id]
            print(f"  {doc_id}: {r['fp']} spurious detections")
            if r["fp_list"]:
                print(f"    {r['fp_list']}")
        print(f"  Total excluded FPs: {excluded_fp}")

    # FP/FN frequency (from evaluated documents only)
    from collections import Counter
    fp_counter = Counter()
    fn_counter = Counter()
    for r in eval_results.values():
        fp_counter.update(r["fp_list"])
        fn_counter.update(r["fn_list"])

    if fp_counter:
        print("\nTop FP techniques:")
        for tech, count in fp_counter.most_common(10):
            print(f"  {count}x {tech}")

    if fn_counter:
        print("\nTop FN techniques:")
        for tech, count in fn_counter.most_common(10):
            print(f"  {count}x {tech}")


if __name__ == "__main__":
    main()
