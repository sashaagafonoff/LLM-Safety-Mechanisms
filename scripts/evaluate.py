#!/usr/bin/env python3
"""Authoritative blind-gold evaluator (WORKPLAN B.1.4, REFACTOR §3.2/§3.3/§3.7/§3.8).

Replaces the three divergent evaluators (compare_taxonomy_runs / evaluate_nlu /
ground_truth_analysis) with ONE definition of "active technique" and "reviewed
document", sourced from eval_common. Key differences from the legacy scripts:

  * Reports on the BLIND TEST split by default (the honest, report-once number).
    Use --split dev while iterating; reserve --split test for final reporting.
  * Canonicalizes technique ids through the alias map before set ops, so renamed/
    merged techniques don't double-count (B.1.5).
  * Adds grounded-precision (precision among detections backed by a real source
    quote) and per-stage (nlu vs llm) precision/recall.
  * Stamps the report with gold/automated sha256, git commit, model id, split,
    and the gold_sha256 from the frozen split manifest, so a result is traceable
    to exact inputs.

Compares an automated run (model_technique_map.json) against frozen ground truth
(model_technique_map_reviewed.json). Does not modify any data file.

Usage:
    python scripts/evaluate.py                       # blind test split
    python scripts/evaluate.py --split dev           # dev split (iteration)
    python scripts/evaluate.py --split all           # every gold doc (legacy-comparable)
    python scripts/evaluate.py --automated data/map_nlu.json   # score an NLU-only run
    python scripts/evaluate.py --json reports/evaluation_test.json
"""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import (  # noqa: E402
    DATA, active_technique_set, grounded_active_set, techniques_by_source,
    load_split, load_no_safety_flags, load_techniques, confusion, prf,
)

REPORTS = Path(__file__).resolve().parent.parent / "reports"
GOLD_PATH = DATA / "model_technique_map_reviewed.json"
AUTOMATED_PATH = DATA / "model_technique_map.json"


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             cwd=str(Path(__file__).resolve().parent.parent),
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _doc_scope(gold: dict, automated: dict, split: str) -> list:
    """Documents to score: gold docs in the chosen split (test/dev/all)."""
    gold_docs = set(gold.keys())
    if split == "all":
        return sorted(gold_docs)
    split_ids = set(load_split(split))
    return sorted(gold_docs & split_ids)


def evaluate(gold, automated, split, tech_lookup, model_id=None):
    docs = _doc_scope(gold, automated, split)
    no_safety = load_no_safety_flags()

    tot = {"tp": 0, "fp": 0, "fn": 0}
    g_tot = {"tp": 0, "detected": 0}              # grounded precision accumulators
    stage_tot = {"nlu": {"tp": 0, "fp": 0, "fn": 0},
                 "llm": {"tp": 0, "fp": 0, "fn": 0}}
    tech = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    cat = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    src_recall = {"nlu": [0, 0], "llm": [0, 0], "manual": [0, 0], "legacy": [0, 0]}
    doc_details = {}
    n_no_safety = 0

    for doc_id in docs:
        gold_entries = gold.get(doc_id, [])
        auto_entries = automated.get(doc_id, [])

        gold_active = active_technique_set(gold_entries)
        auto_active = active_technique_set(auto_entries)
        is_no_safety = (len(gold_active) == 0) or (doc_id in no_safety)
        if is_no_safety:
            n_no_safety += 1
            # Spurious detections against an empty GT distort precision; record but
            # exclude from aggregate (matches evaluate_nlu's policy).
            doc_details[doc_id] = {
                "no_safety_data": True,
                "auto_count": len(auto_active),
                "spurious": sorted(auto_active),
            }
            continue

        tp, fp, fn = confusion(auto_active, gold_active)
        tot["tp"] += len(tp); tot["fp"] += len(fp); tot["fn"] += len(fn)

        # grounded precision
        grounded_detected = grounded_active_set(auto_entries)
        g_tp = grounded_detected & gold_active
        g_tot["tp"] += len(g_tp); g_tot["detected"] += len(grounded_detected)

        # per-stage (nlu vs llm) — detections attributable to each stage
        auto_by_src = techniques_by_source(auto_entries)
        for stage in ("nlu", "llm"):
            det = auto_by_src.get(stage, set())
            s_tp, s_fp, s_fn = confusion(det, gold_active)
            stage_tot[stage]["tp"] += len(s_tp)
            stage_tot[stage]["fp"] += len(s_fp)
            stage_tot[stage]["fn"] += len(s_fn)

        # per-technique / per-category
        for tid in tp:
            tech[tid]["tp"] += 1; cat[tech_lookup.get(tid, {}).get("categoryId", "unknown")]["tp"] += 1
        for tid in fp:
            tech[tid]["fp"] += 1; cat[tech_lookup.get(tid, {}).get("categoryId", "unknown")]["fp"] += 1
        for tid in fn:
            tech[tid]["fn"] += 1; cat[tech_lookup.get(tid, {}).get("categoryId", "unknown")]["fn"] += 1

        # per-source recall (which source originally found a hit/miss in GT)
        gold_by_src = techniques_by_source(gold_entries)
        for tid in tp:
            for s in ("manual", "llm", "nlu", "legacy"):
                if tid in gold_by_src.get(s, set()):
                    src_recall[s][0] += 1
                    break
        for tid in fn:
            for s in ("manual", "llm", "nlu", "legacy"):
                if tid in gold_by_src.get(s, set()):
                    src_recall[s][1] += 1
                    break

        doc_details[doc_id] = {
            "no_safety_data": False,
            "gt_count": len(gold_active), "auto_count": len(auto_active),
            "tp": len(tp), "fp": len(fp), "fn": len(fn),
            "false_positives": sorted(fp), "false_negatives": sorted(fn),
        }

    p, r, f = prf(tot["tp"], tot["fp"], tot["fn"])
    g_precision = g_tot["tp"] / g_tot["detected"] if g_tot["detected"] else 0.0

    return {
        "split": split,
        "model_id": model_id,
        "documents_scored": len([d for d in doc_details.values() if not d["no_safety_data"]]),
        "no_safety_excluded": n_no_safety,
        "overall": {**tot, "precision": p, "recall": r, "f1": f},
        "grounded_precision": {
            "grounded_tp": g_tot["tp"], "grounded_detected": g_tot["detected"],
            "precision": g_precision,
        },
        "per_stage": {
            s: {**stage_tot[s], **dict(zip(("precision", "recall", "f1"),
                prf(stage_tot[s]["tp"], stage_tot[s]["fp"], stage_tot[s]["fn"])))}
            for s in ("nlu", "llm")
        },
        "source_recall": {
            s: {"hits": src_recall[s][0], "misses": src_recall[s][1],
                "recall": src_recall[s][0] / max(1, sum(src_recall[s]))}
            for s in ("nlu", "llm", "manual", "legacy")
        },
        "per_category": {cid: {**c, **dict(zip(("precision", "recall", "f1"),
                          prf(c["tp"], c["fp"], c["fn"])))} for cid, c in cat.items()},
        "per_technique": dict(tech),
        "doc_details": doc_details,
    }


def render_md(result, tech_lookup, cat_lookup, meta):
    o = result["overall"]; g = result["grounded_precision"]
    L = ["# Evaluation Report", "",
         f"- **Split:** `{result['split']}` "
         f"({result['documents_scored']} docs scored, {result['no_safety_excluded']} no-safety excluded)",
         f"- **Automated:** `{meta['automated_path']}` (sha256 `{meta['automated_sha256'][:12]}`)",
         f"- **Ground truth:** `{meta['gold_path']}` (sha256 `{meta['gold_sha256'][:12]}`)",
         f"- **Split gold_sha256:** `{meta.get('split_gold_sha256','n/a')[:12]}`"
         + ("  ⚠️ DRIFT vs gold file" if meta.get("split_drift") else ""),
         f"- **Model:** `{result.get('model_id') or 'n/a'}`  ·  **Commit:** `{meta['git_commit']}`  ·  **Generated:** {meta['generated']}",
         "",
         "> Single-rater metrics — inter-annotator κ not yet computable "
         "(see data/eval/README.md).", "",
         "## Overall", "",
         "| Metric | Value |", "|--------|-------|",
         f"| True Positives | {o['tp']} |",
         f"| False Positives | {o['fp']} |",
         f"| False Negatives | {o['fn']} |",
         f"| **Precision** | **{o['precision']:.1%}** |",
         f"| **Recall** | **{o['recall']:.1%}** |",
         f"| **F1** | **{o['f1']:.1%}** |",
         f"| Grounded precision | {g['precision']:.1%} ({g['grounded_tp']}/{g['grounded_detected']}) |",
         "",
         "## Per-stage (attribution)", "",
         "| Stage | TP | FP | FN | Precision | Recall | F1 |",
         "|-------|----|----|----|-----------|--------|----|"]
    for s in ("nlu", "llm"):
        st = result["per_stage"][s]
        L.append(f"| {s} | {st['tp']} | {st['fp']} | {st['fn']} | "
                 f"{st['precision']:.0%} | {st['recall']:.0%} | {st['f1']:.0%} |")
    L += ["", "## Recall by evidence source (in ground truth)", "",
          "| Source | Recovered | Missed | Recall |", "|--------|-----------|--------|--------|"]
    for s in ("nlu", "llm", "manual", "legacy"):
        sr = result["source_recall"][s]
        if sr["hits"] + sr["misses"]:
            L.append(f"| {s} | {sr['hits']} | {sr['misses']} | {sr['recall']:.1%} |")
    L += ["", "## Per-category", "",
          "| Category | TP | FP | FN | Precision | Recall | F1 |",
          "|----------|----|----|----|-----------|--------|----|"]
    for cid, c in sorted(result["per_category"].items()):
        L.append(f"| {cat_lookup.get(cid, cid)} | {c['tp']} | {c['fp']} | {c['fn']} | "
                 f"{c['precision']:.0%} | {c['recall']:.0%} | {c['f1']:.0%} |")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["test", "dev", "all"], default="test")
    ap.add_argument("--automated", default=str(AUTOMATED_PATH))
    ap.add_argument("--ground-truth", default=str(GOLD_PATH))
    ap.add_argument("--model-id", default=None, help="model id to stamp into the report")
    ap.add_argument("--json", dest="json_out", default=None, help="write JSON report here")
    ap.add_argument("--md", dest="md_out", default=None, help="write markdown report here")
    args = ap.parse_args()

    if args.split == "test":
        print("⚠️  Reporting on the BLIND TEST split — do this once, with the final "
              "configuration. Use --split dev while iterating.\n")

    with open(args.ground_truth, encoding="utf-8") as f:
        gold = json.load(f)
    with open(args.automated, encoding="utf-8") as f:
        automated = json.load(f)

    tech_lookup = {t["id"]: t for t in load_techniques()}
    cat_lookup = {}
    cat_path = DATA / "categories.json"
    if cat_path.exists():
        cat_lookup = {c["id"]: c["name"] for c in json.load(open(cat_path, encoding="utf-8"))}

    result = evaluate(gold, automated, args.split, tech_lookup, args.model_id)

    # provenance / drift detection
    split_manifest = DATA / "eval" / "split_manifest.json"
    split_gold_sha = None
    if split_manifest.exists():
        split_gold_sha = json.load(open(split_manifest, encoding="utf-8")).get("gold_sha256")
    gold_sha = _sha256_file(Path(args.ground_truth))
    # gold_sha256 in the manifest is over the *key set*, not the file bytes; recompute
    gold_keys_sha = hashlib.sha256("\n".join(sorted(gold.keys())).encode()).hexdigest()
    meta = {
        "automated_path": args.automated, "automated_sha256": _sha256_file(Path(args.automated)),
        "gold_path": args.ground_truth, "gold_sha256": gold_sha,
        "split_gold_sha256": split_gold_sha,
        "split_drift": bool(split_gold_sha and split_gold_sha != gold_keys_sha),
        "git_commit": _git_commit(),
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    o = result["overall"]
    print(f"Split={result['split']}  docs={result['documents_scored']}  "
          f"(excluded {result['no_safety_excluded']} no-safety)")
    print(f"TP={o['tp']} FP={o['fp']} FN={o['fn']}")
    print(f"Precision={o['precision']:.1%}  Recall={o['recall']:.1%}  F1={o['f1']:.1%}")
    print(f"Grounded precision={result['grounded_precision']['precision']:.1%} "
          f"({result['grounded_precision']['grounded_tp']}/{result['grounded_precision']['grounded_detected']})")
    if meta["split_drift"]:
        print("⚠️  Split manifest gold_sha256 != current gold key set — split is STALE; "
              "re-freeze with make_eval_split.py before trusting blind numbers.")

    REPORTS.mkdir(parents=True, exist_ok=True)
    json_out = Path(args.json_out) if args.json_out else REPORTS / f"evaluation_{args.split}.json"
    md_out = Path(args.md_out) if args.md_out else REPORTS / f"evaluation_{args.split}.md"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, **result}, f, indent=2, ensure_ascii=False)
    with open(md_out, "w", encoding="utf-8") as f:
        f.write(render_md(result, tech_lookup, cat_lookup, meta))
    print(f"\nReports: {json_out}  |  {md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
