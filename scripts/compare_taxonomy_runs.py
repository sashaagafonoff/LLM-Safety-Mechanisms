#!/usr/bin/env python3
"""
Compare automated extraction results against reviewed ground truth.

Takes the manually-reviewed model_technique_map (ground truth) and compares
it against a fresh automated run to measure precision, recall, and F1.

Accounts for technique merges, renames, and removals between taxonomy versions.

Usage:
    python scripts/compare_taxonomy_runs.py
    python scripts/compare_taxonomy_runs.py --detailed
    python scripts/compare_taxonomy_runs.py --output reports/taxonomy_comparison.md
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

GROUND_TRUTH_PATH = DATA_DIR / "model_technique_map_reviewed.json"
AUTOMATED_PATH = DATA_DIR / "model_technique_map.json"
TECHNIQUES_PATH = DATA_DIR / "techniques.json"
CATEGORIES_PATH = DATA_DIR / "categories.json"


def load_technique_lookup():
    """Load technique name lookup."""
    with open(TECHNIQUES_PATH, "r", encoding="utf-8") as f:
        techniques = json.load(f)
    return {t["id"]: t for t in techniques}


def load_category_lookup():
    """Load category name lookup."""
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        categories = json.load(f)
    return {c["id"]: c["name"] for c in categories}


def extract_active_techniques(doc_techniques):
    """
    Extract the set of active technique IDs from a document's technique list.
    Only includes technique-level active entries (not deleted).
    """
    active = set()
    for tech in doc_techniques:
        # Check technique-level active flag
        if not tech.get("active", True):
            continue
        # Check if any evidence is active
        evidence = tech.get("evidence", [])
        has_active_evidence = False
        for ev in evidence:
            if isinstance(ev, dict):
                if ev.get("active", True):
                    has_active_evidence = True
                    break
            else:
                # Legacy string format - assume active
                has_active_evidence = True
                break
        if has_active_evidence or not evidence:
            active.add(tech["techniqueId"])
    return active


def extract_techniques_by_source(doc_techniques):
    """
    Extract technique IDs grouped by source (nlu, llm, manual).
    Only active entries.
    """
    by_source = {"nlu": set(), "llm": set(), "manual": set(), "legacy": set()}
    for tech in doc_techniques:
        if not tech.get("active", True):
            continue
        evidence = tech.get("evidence", [])
        sources = set()
        for ev in evidence:
            if isinstance(ev, dict):
                if ev.get("active", True):
                    sources.add(ev.get("created_by", "legacy"))
            else:
                sources.add("legacy")
        for source in sources:
            by_source.get(source, by_source["legacy"]).add(tech["techniqueId"])
    return by_source


def compare(ground_truth, automated, tech_lookup, cat_lookup, detailed=False):
    """Compare automated results against ground truth."""
    all_docs = sorted(set(ground_truth.keys()) | set(automated.keys()))

    # Overall counters
    total_tp = 0
    total_fp = 0
    total_fn = 0

    # Per-technique counters
    tech_tp = defaultdict(int)
    tech_fp = defaultdict(int)
    tech_fn = defaultdict(int)

    # Per-category counters
    cat_tp = defaultdict(int)
    cat_fp = defaultdict(int)
    cat_fn = defaultdict(int)

    # Per-source recall tracking (what source was the ground truth from)
    source_fn = defaultdict(int)  # source -> count of misses
    source_tp = defaultdict(int)  # source -> count of hits

    # Detailed per-document results
    doc_details = {}

    for doc_id in all_docs:
        gt_techs = ground_truth.get(doc_id, [])
        auto_techs = automated.get(doc_id, [])

        gt_active = extract_active_techniques(gt_techs)
        auto_active = extract_active_techniques(auto_techs)
        gt_by_source = extract_techniques_by_source(gt_techs)

        tp = gt_active & auto_active
        fp = auto_active - gt_active
        fn = gt_active - auto_active

        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)

        for tid in tp:
            tech_tp[tid] += 1
            cat_id = tech_lookup.get(tid, {}).get("categoryId", "unknown")
            cat_tp[cat_id] += 1
        for tid in fp:
            tech_fp[tid] += 1
            cat_id = tech_lookup.get(tid, {}).get("categoryId", "unknown")
            cat_fp[cat_id] += 1
        for tid in fn:
            tech_fn[tid] += 1
            cat_id = tech_lookup.get(tid, {}).get("categoryId", "unknown")
            cat_fn[cat_id] += 1

        # Track which source the missed techniques came from
        for tid in fn:
            for source in ["manual", "llm", "nlu", "legacy"]:
                if tid in gt_by_source[source]:
                    source_fn[source] += 1
                    break
        for tid in tp:
            for source in ["manual", "llm", "nlu", "legacy"]:
                if tid in gt_by_source[source]:
                    source_tp[source] += 1
                    break

        doc_details[doc_id] = {
            "gt_count": len(gt_active),
            "auto_count": len(auto_active),
            "tp": len(tp),
            "fp": len(fp),
            "fn": len(fn),
            "false_positives": sorted(fp),
            "false_negatives": sorted(fn),
        }

    return {
        "total": {"tp": total_tp, "fp": total_fp, "fn": total_fn},
        "per_technique": {
            tid: {"tp": tech_tp[tid], "fp": tech_fp[tid], "fn": tech_fn[tid]}
            for tid in set(tech_tp) | set(tech_fp) | set(tech_fn)
        },
        "per_category": {
            cid: {"tp": cat_tp[cid], "fp": cat_fp[cid], "fn": cat_fn[cid]}
            for cid in set(cat_tp) | set(cat_fp) | set(cat_fn)
        },
        "source_recall": {
            source: {
                "hits": source_tp[source],
                "misses": source_fn[source],
                "recall": source_tp[source] / max(1, source_tp[source] + source_fn[source])
            }
            for source in ["manual", "llm", "nlu", "legacy"]
        },
        "doc_details": doc_details,
    }


def precision(tp, fp):
    return tp / max(1, tp + fp)


def recall(tp, fn):
    return tp / max(1, tp + fn)


def f1(p, r):
    return 2 * p * r / max(0.001, p + r)


def format_report(results, tech_lookup, cat_lookup, detailed=False):
    """Format comparison results as markdown."""
    lines = []
    lines.append("# Taxonomy Comparison Report")
    lines.append("")
    lines.append("Comparison of automated extraction (new taxonomy) against manually-reviewed ground truth.")
    lines.append("")

    # Overall metrics
    t = results["total"]
    p = precision(t["tp"], t["fp"])
    r = recall(t["tp"], t["fn"])
    f = f1(p, r)

    lines.append("## Overall Metrics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| True Positives | {t['tp']} |")
    lines.append(f"| False Positives | {t['fp']} |")
    lines.append(f"| False Negatives | {t['fn']} |")
    lines.append(f"| **Precision** | **{p:.1%}** |")
    lines.append(f"| **Recall** | **{r:.1%}** |")
    lines.append(f"| **F1 Score** | **{f:.1%}** |")
    lines.append("")

    # Source-level recall
    lines.append("## Recall by Evidence Source")
    lines.append("")
    lines.append("How well the automated pipeline recovers techniques that were originally found by each source.")
    lines.append("")
    lines.append("| Source | Recovered | Missed | Recall |")
    lines.append("|--------|-----------|--------|--------|")
    for source in ["nlu", "llm", "manual", "legacy"]:
        sr = results["source_recall"].get(source, {"hits": 0, "misses": 0, "recall": 0})
        total = sr["hits"] + sr["misses"]
        if total > 0:
            lines.append(f"| {source} | {sr['hits']} | {sr['misses']} | {sr['recall']:.1%} |")
    lines.append("")

    # Per-category metrics
    lines.append("## Per-Category Performance")
    lines.append("")
    lines.append("| Category | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|----------|----|----|----|-----------|---------|----|")
    for cid, counts in sorted(results["per_category"].items(), key=lambda x: x[0]):
        cat_name = cat_lookup.get(cid, cid)
        cp = precision(counts["tp"], counts["fp"])
        cr = recall(counts["tp"], counts["fn"])
        cf = f1(cp, cr)
        lines.append(f"| {cat_name} | {counts['tp']} | {counts['fp']} | {counts['fn']} | {cp:.1%} | {cr:.1%} | {cf:.1%} |")
    lines.append("")

    # Worst-performing techniques (by F1)
    lines.append("## Technique-Level Analysis")
    lines.append("")

    tech_metrics = []
    for tid, counts in results["per_technique"].items():
        tp_ = counts["tp"]
        fp_ = counts["fp"]
        fn_ = counts["fn"]
        p_ = precision(tp_, fp_)
        r_ = recall(tp_, fn_)
        f_ = f1(p_, r_)
        total = tp_ + fp_ + fn_
        name = tech_lookup.get(tid, {}).get("name", tid)
        cat_id = tech_lookup.get(tid, {}).get("categoryId", "unknown")
        tech_metrics.append((tid, name, cat_id, tp_, fp_, fn_, p_, r_, f_, total))

    # Sort by F1 ascending (worst first), then by total volume descending
    tech_metrics.sort(key=lambda x: (x[8], -x[9]))

    lines.append("### Techniques Needing Improvement (lowest F1)")
    lines.append("")
    lines.append("| Technique | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|-----------|----|----|----|-----------|---------|----|")
    for tid, name, cat_id, tp_, fp_, fn_, p_, r_, f_, total in tech_metrics[:15]:
        lines.append(f"| {name} | {tp_} | {fp_} | {fn_} | {p_:.0%} | {r_:.0%} | {f_:.0%} |")
    lines.append("")

    # Best-performing techniques
    tech_metrics.sort(key=lambda x: (-x[8], -x[9]))
    lines.append("### Well-Performing Techniques (highest F1)")
    lines.append("")
    lines.append("| Technique | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|-----------|----|----|----|-----------|---------|----|")
    for tid, name, cat_id, tp_, fp_, fn_, p_, r_, f_, total in tech_metrics[:10]:
        if total > 0:
            lines.append(f"| {name} | {tp_} | {fp_} | {fn_} | {p_:.0%} | {r_:.0%} | {f_:.0%} |")
    lines.append("")

    # New techniques never in ground truth
    new_only = [t for t in tech_metrics if t[3] == 0 and t[5] == 0 and t[4] > 0]
    if new_only:
        lines.append("### New Techniques (automated only, not in ground truth)")
        lines.append("")
        lines.append("These are new taxonomy techniques — automated detections with no ground truth to validate against.")
        lines.append("")
        lines.append("| Technique | Auto Detections |")
        lines.append("|-----------|----------------|")
        for tid, name, *_, fp_, _, _, _, _ in new_only:
            lines.append(f"| {name} | {fp_} |")
        lines.append("")

    if detailed:
        lines.append("## Per-Document Details")
        lines.append("")
        for doc_id, details in sorted(results["doc_details"].items()):
            if details["fp"] == 0 and details["fn"] == 0:
                continue  # Skip perfect matches
            lines.append(f"### {doc_id}")
            lines.append(f"Ground truth: {details['gt_count']} | Automated: {details['auto_count']} | TP: {details['tp']} | FP: {details['fp']} | FN: {details['fn']}")
            if details["false_positives"]:
                fp_names = [tech_lookup.get(t, {}).get("name", t) for t in details["false_positives"]]
                lines.append(f"- False positives: {', '.join(fp_names)}")
            if details["false_negatives"]:
                fn_names = [tech_lookup.get(t, {}).get("name", t) for t in details["false_negatives"]]
                lines.append(f"- Missed: {', '.join(fn_names)}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare automated extraction against reviewed ground truth"
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        default=str(GROUND_TRUTH_PATH),
        help="Path to ground truth (reviewed) map"
    )
    parser.add_argument(
        "--automated",
        type=str,
        default=str(AUTOMATED_PATH),
        help="Path to automated extraction map"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(REPORTS_DIR / "taxonomy_comparison.md"),
        help="Output report path"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include per-document details"
    )

    args = parser.parse_args()

    # Load data
    with open(args.ground_truth, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
    with open(args.automated, "r", encoding="utf-8") as f:
        automated = json.load(f)

    tech_lookup = load_technique_lookup()
    cat_lookup = load_category_lookup()

    # Compare
    results = compare(ground_truth, automated, tech_lookup, cat_lookup, args.detailed)

    # Format and save report
    report = format_report(results, tech_lookup, cat_lookup, args.detailed)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Print summary to console
    t = results["total"]
    p = precision(t["tp"], t["fp"])
    r = recall(t["tp"], t["fn"])
    f_ = f1(p, r)

    print(f"\nComparison Results:")
    print(f"  Ground truth: {args.ground_truth}")
    print(f"  Automated:    {args.automated}")
    print(f"")
    print(f"  TP: {t['tp']}  FP: {t['fp']}  FN: {t['fn']}")
    print(f"  Precision: {p:.1%}  Recall: {r:.1%}  F1: {f_:.1%}")
    print(f"")
    print(f"  Report saved to: {output_path}")


if __name__ == "__main__":
    main()
