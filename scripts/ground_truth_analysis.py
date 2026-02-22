#!/usr/bin/env python3
"""
Ground Truth Analysis of NLU/LLM Technique Extraction Performance.

Analyzes model_technique_map.json to compute precision, recall, and F1
for documents that have been manually reviewed.
"""

import json
from collections import defaultdict, Counter
from pathlib import Path


def load_data():
    data_dir = Path(__file__).parent.parent / "data"
    with open(data_dir / "model_technique_map.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_techniques():
    data_dir = Path(__file__).parent.parent / "data"
    with open(data_dir / "techniques.json", "r", encoding="utf-8") as f:
        techniques = json.load(f)
    return {t["id"]: t.get("name", t["id"]) for t in techniques}


def is_reviewed_document(doc_id, techniques_list):
    """
    A document is considered 'reviewed' if:
    1. It has any evidence with created_by in ("manual", "sashaagafonoff"), OR
    2. It has any technique-level deletion by a human reviewer
       (deleted_by is not null and not "system")
    """
    for tech in techniques_list:
        # Check evidence level for manual additions
        for ev in tech.get("evidence", []):
            cb = ev.get("created_by", "")
            if cb in ("manual", "sashaagafonoff"):
                return True

        # Check technique-level deletions by human reviewers
        db = tech.get("deleted_by")
        if db and db not in ("system",):
            # Human-reviewed deletion (could be "manual", "sashaagafonoff", "llm" used during review)
            return True

    return False


def classify_techniques(doc_id, techniques_list):
    """
    For a reviewed document, classify each technique entry:

    - TP: created by nlu/llm, still active (reviewer kept it)
    - FP: created by nlu/llm, deleted (reviewer removed it)
    - FN: created by manual/sashaagafonoff, no nlu/llm evidence existed before

    We also need to handle mixed cases where both NLU and manual evidence exist.
    """
    tp = []
    fp = []
    fn = []

    for tech in techniques_list:
        tech_id = tech["techniqueId"]
        tech_active = tech.get("active", True)
        tech_deleted_by = tech.get("deleted_by")

        evidences = tech.get("evidence", [])

        # Determine the origin of this technique entry
        has_nlu_llm_evidence = False
        has_manual_evidence = False

        for ev in evidences:
            cb = ev.get("created_by", "")
            if cb in ("nlu", "llm", "legacy"):
                has_nlu_llm_evidence = True
            if cb in ("manual", "sashaagafonoff"):
                has_manual_evidence = True

        if has_nlu_llm_evidence:
            if tech_active:
                # NLU/LLM found it and reviewer kept it
                tp.append(tech_id)
            else:
                # NLU/LLM found it but reviewer deleted it
                fp.append(tech_id)
        elif has_manual_evidence:
            # Only manual evidence - NLU/LLM missed it
            fn.append(tech_id)

    return tp, fp, fn


def main():
    data = load_data()
    tech_names = load_techniques()

    # Find all reviewed documents
    reviewed_docs = {}
    all_docs_summary = []

    for doc_id, techniques_list in data.items():
        if is_reviewed_document(doc_id, techniques_list):
            reviewed_docs[doc_id] = techniques_list

    print("=" * 120)
    print("GROUND TRUTH ANALYSIS: NLU/LLM Technique Extraction Performance")
    print("=" * 120)
    print()
    print(f"Total documents in dataset: {len(data)}")
    print(f"Manually reviewed documents: {len(reviewed_docs)}")
    print()

    # Aggregate counters
    total_tp = 0
    total_fp = 0
    total_fn = 0
    all_fp_techniques = []
    all_fn_techniques = []
    all_tp_techniques = []

    # Per-document analysis
    print("-" * 120)
    print(f"{'Document ID':<45} {'Ground Truth':>12} {'TP':>5} {'FP':>5} {'FN':>5} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 120)

    doc_details = []

    for doc_id in sorted(reviewed_docs.keys()):
        techniques_list = reviewed_docs[doc_id]
        tp, fp, fn = classify_techniques(doc_id, techniques_list)

        gt = len(tp) + len(fn)  # ground truth = TP + FN

        precision = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) > 0 else 0.0
        recall = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        print(f"{doc_id:<45} {gt:>12} {len(tp):>5} {len(fp):>5} {len(fn):>5} {precision:>10.3f} {recall:>10.3f} {f1:>10.3f}")

        doc_details.append({
            "doc_id": doc_id,
            "gt": gt,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })

        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)
        all_fp_techniques.extend(fp)
        all_fn_techniques.extend(fn)
        all_tp_techniques.extend(tp)

    # Aggregate metrics
    agg_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    agg_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    agg_f1 = 2 * agg_precision * agg_recall / (agg_precision + agg_recall) if (agg_precision + agg_recall) > 0 else 0.0

    print("-" * 120)
    print(f"{'AGGREGATE':<45} {total_tp + total_fn:>12} {total_tp:>5} {total_fp:>5} {total_fn:>5} {agg_precision:>10.3f} {agg_recall:>10.3f} {agg_f1:>10.3f}")
    print("=" * 120)
    print()

    # Detailed per-document breakdown
    print()
    print("=" * 120)
    print("DETAILED PER-DOCUMENT BREAKDOWN")
    print("=" * 120)

    for d in doc_details:
        print()
        print(f"--- {d['doc_id']} ---")
        print(f"  Ground Truth: {d['gt']} | TP: {len(d['tp'])} | FP: {len(d['fp'])} | FN: {len(d['fn'])}")
        print(f"  Precision: {d['precision']:.3f} | Recall: {d['recall']:.3f} | F1: {d['f1']:.3f}")

        if d['fp']:
            fp_names = [f"{tid} ({tech_names.get(tid, '?')})" for tid in sorted(d['fp'])]
            print(f"  FALSE POSITIVES (NLU wrongly detected):")
            for name in fp_names:
                print(f"    - {name}")

        if d['fn']:
            fn_names = [f"{tid} ({tech_names.get(tid, '?')})" for tid in sorted(d['fn'])]
            print(f"  FALSE NEGATIVES (NLU missed):")
            for name in fn_names:
                print(f"    - {name}")

        if d['tp']:
            tp_names = [f"{tid} ({tech_names.get(tid, '?')})" for tid in sorted(d['tp'])]
            print(f"  TRUE POSITIVES (NLU correctly detected):")
            for name in tp_names:
                print(f"    - {name}")

    # Top FP and FN techniques
    print()
    print("=" * 120)
    print("TOP 10 MOST COMMON FALSE POSITIVE TECHNIQUES (NLU wrongly detected)")
    print("=" * 120)
    fp_counter = Counter(all_fp_techniques)
    for tech_id, count in fp_counter.most_common(10):
        name = tech_names.get(tech_id, "?")
        print(f"  {count:>3}x  {tech_id} ({name})")

    print()
    print("=" * 120)
    print("TOP 10 MOST COMMON FALSE NEGATIVE TECHNIQUES (NLU missed)")
    print("=" * 120)
    fn_counter = Counter(all_fn_techniques)
    for tech_id, count in fn_counter.most_common(10):
        name = tech_names.get(tech_id, "?")
        print(f"  {count:>3}x  {tech_id} ({name})")

    # Also show top TP for context
    print()
    print("=" * 120)
    print("TOP 10 MOST COMMON TRUE POSITIVE TECHNIQUES (NLU correctly detected)")
    print("=" * 120)
    tp_counter = Counter(all_tp_techniques)
    for tech_id, count in tp_counter.most_common(10):
        name = tech_names.get(tech_id, "?")
        print(f"  {count:>3}x  {tech_id} ({name})")

    # Summary statistics
    print()
    print("=" * 120)
    print("SUMMARY STATISTICS")
    print("=" * 120)
    print(f"  Total reviewed documents: {len(reviewed_docs)}")
    print(f"  Total technique entries across reviewed docs: {total_tp + total_fp + total_fn}")
    print(f"  Total True Positives:  {total_tp}")
    print(f"  Total False Positives: {total_fp}")
    print(f"  Total False Negatives: {total_fn}")
    print(f"  Aggregate Precision:   {agg_precision:.4f} ({agg_precision*100:.1f}%)")
    print(f"  Aggregate Recall:      {agg_recall:.4f} ({agg_recall*100:.1f}%)")
    print(f"  Aggregate F1:          {agg_f1:.4f} ({agg_f1*100:.1f}%)")
    print()

    # Check for unique FP/FN technique counts
    print(f"  Unique FP technique types: {len(fp_counter)}")
    print(f"  Unique FN technique types: {len(fn_counter)}")
    print(f"  Unique TP technique types: {len(tp_counter)}")

    # Break down by creator type
    print()
    print("=" * 120)
    print("BREAKDOWN BY EVIDENCE CREATOR TYPE")
    print("=" * 120)
    creator_counts = defaultdict(int)
    for doc_id, techniques_list in data.items():
        for tech in techniques_list:
            for ev in tech.get("evidence", []):
                creator_counts[ev.get("created_by", "unknown")] += 1
    for creator, count in sorted(creator_counts.items(), key=lambda x: -x[1]):
        print(f"  {creator}: {count} evidence entries")

    # Also show which documents were reviewed and why
    print()
    print("=" * 120)
    print("REVIEWED DOCUMENT IDENTIFICATION REASONS")
    print("=" * 120)
    for doc_id in sorted(reviewed_docs.keys()):
        reasons = set()
        techniques_list = reviewed_docs[doc_id]
        for tech in techniques_list:
            for ev in tech.get("evidence", []):
                cb = ev.get("created_by", "")
                if cb in ("manual", "sashaagafonoff"):
                    reasons.add(f"has {cb}-created evidence")
            db = tech.get("deleted_by")
            if db and db not in ("system",):
                reasons.add(f"has technique deleted_by={db}")
        print(f"  {doc_id}: {', '.join(sorted(reasons))}")


if __name__ == "__main__":
    main()
