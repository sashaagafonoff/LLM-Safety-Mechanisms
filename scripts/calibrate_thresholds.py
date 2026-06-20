#!/usr/bin/env python3
"""Threshold + confidence calibration on the DEV split (WORKPLAN B.1.3).

Two calibrations, both DEV-only (the blind test split is hard-refused):

  1. Operating point — sweep a 2D grid of (retrieval_threshold,
     verification_threshold), trace the precision/recall trade-off, and recommend
     the point that maximises F-beta subject to a precision floor. This replaces
     the hand-set RETRIEVAL_THRESHOLD=0.40 / VERIFICATION_THRESHOLD=0.85 in
     analyze_nlu.py with a number derived from labelled data (REFACTOR §1.2/§1.6).

  2. Confidence calibration — isotonic regression (pool-adjacent-violators) maps a
     candidate's verification score to its empirical probability of being correct,
     so "confidence" means something measurable rather than a raw softmax value
     (REFACTOR §3.5).

Detection model: a (doc, technique) is detected at (rt, vt) iff ANY of its
candidate chunks clears both gates. Gold labels come from
model_technique_map_reviewed.json (active set, alias-canonicalized) restricted to
dev — a gold technique with no candidate at all is an unconditional miss (retrieval
floor too high), which the recall figure reflects.

Pure stdlib; `--self-test` runs the full math on synthetic separable scores so the
calibrator is verifiable without the ML stack.

Usage:
    python scripts/dump_nlu_scores.py            # produce dev scores (needs ML stack)
    python scripts/calibrate_thresholds.py       # calibrate from those scores
    python scripts/calibrate_thresholds.py --precision-floor 0.7 --beta 0.5
    python scripts/calibrate_thresholds.py --self-test
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import (  # noqa: E402
    DATA, load_split, load_holdout_ids, active_technique_set,
)
from taxonomy_aliases import canonical_technique  # noqa: E402

SCORES_PATH = DATA / "eval" / "nlu_scores_dev.json"
GOLD_PATH = DATA / "model_technique_map_reviewed.json"
REPORTS = Path(__file__).resolve().parent.parent / "reports"


def _frange(lo, hi, step):
    out, x = [], lo
    while x <= hi + 1e-9:
        out.append(round(x, 4))
        x += step
    return out


def fbeta(p, r, beta):
    b2 = beta * beta
    denom = b2 * p + r
    return (1 + b2) * p * r / denom if denom else 0.0


def load_gold_dev():
    """{doc_id: set(canonical technique ids)} for dev docs present in gold."""
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold = json.load(f)
    dev = set(load_split("dev"))
    return {d: active_technique_set(gold[d]) for d in sorted(dev) if d in gold}


def group_candidates(candidates):
    """{(doc, canonical_tech): [(retrieval, verification), ...]}."""
    grp = defaultdict(list)
    for c in candidates:
        key = (c["doc_id"], canonical_technique(c["techniqueId"]))
        grp[key].append((c["retrieval_score"], c["verification_score"]))
    return grp


def sweep(grp, gold_by_doc, rt_grid, vt_grid, beta, precision_floor):
    """Return (pr_curve, recommendation). pr_curve is a list of grid points."""
    docs = list(gold_by_doc)
    # pre-index candidate (doc,tech) keys per doc
    cand_techs_by_doc = defaultdict(set)
    for (doc, tech) in grp:
        cand_techs_by_doc[doc].add(tech)

    curve = []
    best = None
    best_floored = None
    for rt in rt_grid:
        for vt in vt_grid:
            tp = fp = fn = 0
            for doc in docs:
                gold = gold_by_doc[doc]
                detected = set()
                for tech in cand_techs_by_doc.get(doc, ()):
                    if any(r >= rt and v >= vt for (r, v) in grp[(doc, tech)]):
                        detected.add(tech)
                tp += len(detected & gold)
                fp += len(detected - gold)
                fn += len(gold - detected)
            p = tp / (tp + fp) if (tp + fp) else 0.0
            r = tp / (tp + fn) if (tp + fn) else 0.0
            fb = fbeta(p, r, beta)
            point = {"rt": rt, "vt": vt, "tp": tp, "fp": fp, "fn": fn,
                     "precision": p, "recall": r, "fbeta": fb}
            curve.append(point)
            if best is None or fb > best["fbeta"]:
                best = point
            if p >= precision_floor:
                if best_floored is None or fb > best_floored["fbeta"]:
                    best_floored = point
    rec = {
        "precision_floor": precision_floor, "beta": beta,
        "recommended": best_floored or best,
        "floor_met": best_floored is not None,
        "best_unconstrained": best,
    }
    return curve, rec


# --- isotonic regression via pool-adjacent-violators ---

def isotonic_pav(points):
    """points: list of (x, y in {0,1}) -> list of (x_threshold, calibrated_p) steps."""
    pts = sorted(points, key=lambda t: t[0])
    if not pts:
        return []
    # blocks: [x_min, x_max, sum_y, n]
    blocks = [[x, x, float(y), 1] for x, y in pts]
    merged = True
    while merged:
        merged = False
        i = 0
        while i < len(blocks) - 1:
            mean_i = blocks[i][2] / blocks[i][3]
            mean_j = blocks[i + 1][2] / blocks[i + 1][3]
            if mean_i > mean_j:  # violation of monotonicity -> pool
                blocks[i][1] = blocks[i + 1][1]
                blocks[i][2] += blocks[i + 1][2]
                blocks[i][3] += blocks[i + 1][3]
                del blocks[i + 1]
                merged = True
                if i > 0:
                    i -= 1
            else:
                i += 1
    # Coalesce adjacent blocks at the same calibrated level into one range, so the
    # reliability table is the minimal monotone step function (not one row/point).
    coalesced = []
    for b in blocks:
        p = b[2] / b[3]
        if coalesced and abs(coalesced[-1]["p"] - p) < 1e-9:
            coalesced[-1]["x_max"] = b[1]
            coalesced[-1]["n"] += b[3]
        else:
            coalesced.append({"x_min": b[0], "x_max": b[1], "p": p, "n": b[3]})
    return coalesced


def confidence_table(grp, gold_by_doc):
    """Isotonic map from max verification score per (doc,tech) -> P(correct)."""
    pts = []
    for (doc, tech), scores in grp.items():
        if doc not in gold_by_doc:
            continue
        x = max(v for (_, v) in scores)
        y = 1 if tech in gold_by_doc[doc] else 0
        pts.append((x, y))
    return isotonic_pav(pts), len(pts)


def _synthetic():
    """Separable synthetic scores for --self-test (no ML stack needed)."""
    cands, gold = [], defaultdict(set)
    # 3 docs, positives score high, negatives score low
    for d in range(3):
        doc = f"dev-doc-{d}"
        for t in range(5):  # positives
            tech = f"tech-pos-{d}-{t}"
            gold[doc].add(tech)
            cands.append({"doc_id": doc, "techniqueId": tech,
                          "retrieval_score": 0.55 + 0.01 * t,
                          "verification_score": 0.90 + 0.005 * t})
        for t in range(8):  # negatives
            cands.append({"doc_id": doc, "techniqueId": f"tech-neg-{d}-{t}",
                          "retrieval_score": 0.34 + 0.005 * t,
                          "verification_score": 0.55 + 0.02 * t})
    return cands, {d: set(v) for d, v in gold.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scores", default=str(SCORES_PATH))
    ap.add_argument("--beta", type=float, default=1.0, help="F-beta (recall weight)")
    ap.add_argument("--precision-floor", type=float, default=0.6)
    ap.add_argument("--rt-grid", default="0.30:0.60:0.02")
    ap.add_argument("--vt-grid", default="0.50:0.95:0.05")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", dest="json_out", default=str(REPORTS / "threshold_calibration.json"))
    args = ap.parse_args()

    rt_grid = _frange(*[float(x) for x in args.rt_grid.split(":")])
    vt_grid = _frange(*[float(x) for x in args.vt_grid.split(":")])

    if args.self_test:
        candidates, gold_by_doc = _synthetic()
        print("SELF-TEST: synthetic separable scores")
    else:
        sp = Path(args.scores)
        if not sp.exists():
            print(f"Scores file not found: {sp}\nRun scripts/dump_nlu_scores.py first.")
            return 1
        payload = json.load(open(sp, encoding="utf-8"))
        candidates = payload.get("candidates", [])
        # hard refuse blind-test contamination
        holdout = load_holdout_ids()
        leaked = sorted({c["doc_id"] for c in candidates} & holdout)
        if leaked:
            print(f"ABORT: scores file contains blind-test docs {leaked}. "
                  f"Re-dump with dump_nlu_scores.py (dev only).")
            return 2
        gold_by_doc = load_gold_dev()

    grp = group_candidates(candidates)
    curve, rec = sweep(grp, gold_by_doc, rt_grid, vt_grid, args.beta, args.precision_floor)
    conf_steps, n_conf = confidence_table(grp, gold_by_doc)

    r = rec["recommended"]
    print("=" * 60)
    print("THRESHOLD CALIBRATION (dev)")
    print("=" * 60)
    print(f"grid points evaluated: {len(curve)} | candidate groups: {len(grp)} | "
          f"dev docs: {len(gold_by_doc)}")
    print(f"precision floor: {args.precision_floor}  beta: {args.beta}  "
          f"floor_met: {rec['floor_met']}")
    print(f"\nRECOMMENDED  retrieval_threshold={r['rt']}  verification_threshold={r['vt']}")
    print(f"  precision={r['precision']:.3f}  recall={r['recall']:.3f}  "
          f"F{args.beta:g}={r['fbeta']:.3f}  (tp={r['tp']} fp={r['fp']} fn={r['fn']})")
    cur = {"rt": 0.40, "vt": 0.85}
    cur_pt = next((p for p in curve if p["rt"] == cur["rt"] and p["vt"] == cur["vt"]), None)
    if cur_pt:
        print(f"  current (0.40/0.85): precision={cur_pt['precision']:.3f} "
              f"recall={cur_pt['recall']:.3f} F{args.beta:g}={cur_pt['fbeta']:.3f}")
    print(f"\nConfidence calibration (isotonic, {n_conf} points): "
          f"{len(conf_steps)} monotone step(s)")
    for s in conf_steps:
        print(f"  verification in [{s['x_min']:.3f}, {s['x_max']:.3f}] -> "
              f"P(correct)={s['p']:.3f}  (n={int(s['n'])})")

    REPORTS.mkdir(parents=True, exist_ok=True)
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump({"recommendation": rec, "confidence_steps": conf_steps,
                   "n_confidence_points": n_conf, "pr_curve": curve},
                  f, indent=2, ensure_ascii=False)
    print(f"\nWrote {args.json_out}")
    print("NOTE: applying these thresholds means editing analyze_nlu.py constants, "
          "then reporting ONCE on the blind test split via evaluate.py --split test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
