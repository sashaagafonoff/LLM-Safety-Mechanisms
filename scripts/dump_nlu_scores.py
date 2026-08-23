#!/usr/bin/env python3
"""Dump per-candidate NLU scores for threshold calibration (B.1.3; T4.1/T4.2).

Runs the retrieval+verification scorers (no gating) over a set of documents and
writes the raw (retrieval_score, verification_score) for each technique candidate.
The blind TEST split is hard-excluded — calibration must never see it.

Two doc selections (`--docs`):
  - "dev" (default, back-compat): the frozen `data/eval/dev_split.json` list
    (24 docs as of the 2026-06 split freeze). Output: data/eval/nlu_scores_dev.json.
  - "reviewed" (T4.1 expanded pool): every document in
    `data/model_technique_map.json` that `eval_common.is_reviewed_document`
    considers reviewed, minus the holdout — a superset of "dev" once documents
    have been reviewed since the split was frozen (38 reviewed vs. 24 dev as of
    2026-08). Output: data/eval/nlu_scores_reviewed.json. Feeds
    `threshold_pool.build_labelled_pool` via
    `calibrate_thresholds.py --per-technique`.

Output shape (both modes):
    {
      "split": "dev" | "reviewed",
      "retrieval_floor": 0.30,
      "candidates": [{"doc_id", "techniqueId", "retrieval_score", "verification_score"}, ...]
    }

Requires the ML stack (sentence-transformers / torch). Consumed by
calibrate_thresholds.py, which loads gold labels itself.

Usage:
    python scripts/dump_nlu_scores.py
    python scripts/dump_nlu_scores.py --retrieval-floor 0.25
    python scripts/dump_nlu_scores.py --docs reviewed
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import DATA, load_split, load_holdout_ids, is_reviewed_document  # noqa: E402

INPUT_DIR = Path("data/flat_text")
OUT_PATH = Path("data/eval/nlu_scores_dev.json")
REVIEWED_OUT_PATH = Path("data/eval/nlu_scores_reviewed.json")
MODEL_MAP_PATH = DATA / "model_technique_map.json"


def _read_body(doc_id: str):
    p = INPUT_DIR / f"{doc_id}.txt"
    if not p.exists():
        return None
    content = p.read_text(encoding="utf-8")
    parts = content.split("-" * 20 + "\n", 1)
    return parts[1] if len(parts) > 1 else content


def _reviewed_doc_ids() -> set:
    """Every doc id in model_technique_map.json that is_reviewed_document
    considers reviewed (T4.1 expanded pool — superset of the frozen dev split)."""
    if not MODEL_MAP_PATH.exists():
        return set()
    with open(MODEL_MAP_PATH, encoding="utf-8") as f:
        map_data = json.load(f)
    return {doc_id for doc_id, entries in map_data.items() if is_reviewed_document(entries)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--retrieval-floor", type=float, default=0.30)
    ap.add_argument("--docs", choices=["dev", "reviewed"], default="dev",
                     help="'dev' (default): frozen dev split, back-compat. "
                          "'reviewed': every reviewed doc in model_technique_map.json "
                          "(T4.1's expanded pool), minus the blind-test holdout.")
    ap.add_argument("--out", default=None,
                     help="Output path; defaults to nlu_scores_dev.json for --docs dev, "
                          "nlu_scores_reviewed.json for --docs reviewed.")
    args = ap.parse_args()

    holdout = load_holdout_ids()
    if args.docs == "dev":
        doc_ids = set(load_split("dev"))
        if not doc_ids:
            print("No dev split frozen — run scripts/make_eval_split.py first.")
            return 1
        if holdout & set(load_split("dev")):
            print("WARNING: dev/holdout overlap detected; excluded.")
        default_out = OUT_PATH
        split_label = "dev"
    else:
        doc_ids = _reviewed_doc_ids()
        if not doc_ids:
            print(f"No reviewed docs found in {MODEL_MAP_PATH}.")
            return 1
        default_out = REVIEWED_OUT_PATH
        split_label = "reviewed"
    doc_ids -= holdout  # belt-and-braces: never score a blind doc

    from analyze_nlu import NLUAnalyzer  # heavy import; deferred until needed
    analyzer = NLUAnalyzer()

    records = []
    for doc_id in sorted(doc_ids):
        body = _read_body(doc_id)
        if body is None:
            print(f"  WARN: no flat text for {doc_id}")
            continue
        scored = analyzer.score_candidates(body, doc_id, retrieval_floor=args.retrieval_floor)
        for s in scored:
            records.append({
                "doc_id": doc_id,
                "techniqueId": s["techniqueId"],
                "retrieval_score": round(s["retrieval_score"], 5),
                "verification_score": round(s["verification_score"], 5),
            })
        print(f"  {doc_id}: {len(scored)} candidates")

    out = Path(args.out) if args.out else default_out
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"split": split_label, "retrieval_floor": args.retrieval_floor,
                   "candidates": records}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(records)} candidate scores for {len(doc_ids)} {split_label} docs -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
