#!/usr/bin/env python3
"""Dump per-candidate NLU scores on the DEV split for threshold calibration (B.1.3).

Runs the retrieval+verification scorers (no gating) over every dev document and
writes the raw (retrieval_score, verification_score) for each technique candidate.
The blind TEST split is hard-excluded — calibration must never see it.

Output: data/eval/nlu_scores_dev.json
    {
      "split": "dev",
      "retrieval_floor": 0.30,
      "candidates": [{"doc_id", "techniqueId", "retrieval_score", "verification_score"}, ...]
    }

Requires the ML stack (sentence-transformers / torch). Consumed by
calibrate_thresholds.py, which loads gold labels itself.

Usage:
    python scripts/dump_nlu_scores.py
    python scripts/dump_nlu_scores.py --retrieval-floor 0.25
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import load_split, load_holdout_ids  # noqa: E402

INPUT_DIR = Path("data/flat_text")
OUT_PATH = Path("data/eval/nlu_scores_dev.json")


def _read_body(doc_id: str):
    p = INPUT_DIR / f"{doc_id}.txt"
    if not p.exists():
        return None
    content = p.read_text(encoding="utf-8")
    parts = content.split("-" * 20 + "\n", 1)
    return parts[1] if len(parts) > 1 else content


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--retrieval-floor", type=float, default=0.30)
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    dev = set(load_split("dev"))
    holdout = load_holdout_ids()
    if not dev:
        print("No dev split frozen — run scripts/make_eval_split.py first.")
        return 1
    dev -= holdout  # belt-and-braces: never score a blind doc
    if holdout & set(load_split("dev")):
        print("WARNING: dev/holdout overlap detected; excluded.")

    from analyze_nlu import NLUAnalyzer  # heavy import; deferred until needed
    analyzer = NLUAnalyzer()

    records = []
    for doc_id in sorted(dev):
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

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"split": "dev", "retrieval_floor": args.retrieval_floor,
                   "candidates": records}, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(records)} candidate scores for {len(dev)} dev docs -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
