#!/usr/bin/env python3
"""Threshold + confidence calibration on the DEV split (WORKPLAN B.1.3; T4.2).

Two calibration modes, both quarantining the blind test split (hard-refused):

  1. Default mode — operating-point sweep. A 2D grid of (retrieval_threshold,
     verification_threshold), tracing the precision/recall trade-off and
     recommending the point that maximises F-beta subject to a precision
     floor. This replaces the hand-set RETRIEVAL_THRESHOLD=0.40 /
     VERIFICATION_THRESHOLD=0.85 in analyze_nlu.py with a number derived from
     labelled data (REFACTOR §1.2/§1.6). Gold labels come from
     model_technique_map_reviewed.json (frozen, dev-only). Writes
     reports/threshold_calibration.json.

  2. `--per-technique` mode (T4.2, 2026-08 execution plan Phase 4) — the
     expanded-pool calibration. Builds a labelled pool from EVERY reviewed
     document in `data/model_technique_map.json` (T4.1's
     `threshold_pool.build_labelled_pool`, ~1,253 active + ~518 rejected
     entries as of 2026-08, vs. the original 39-point pool) rather than only
     the frozen 35-doc gold set, fits a global verification threshold, fits
     per-technique thresholds with shrinkage toward that global threshold for
     low-data techniques (`threshold_pool.compute_per_technique_thresholds`),
     and builds an isotonic (PAV) calibration curve mapping verification score
     -> P(correct) across the whole pool. Writes the **GENERATED** file
     `data/eval/nlu_thresholds.json` — a fresh instance is produced by running
     this script; the repo never commits an actual instance of it (see
     `.gitignore` / commit guidance). Consumed by `analyze_nlu.NLUAnalyzer` at
     init (`load_thresholds`) if present.

Both modes never read the blind test split: default mode restricts gold to
`load_split("dev")`; `--per-technique` mode excludes `load_holdout_ids()` doc
ids from the pool and hard-refuses a scores file that contains any of them.
`--per-technique` mode also never reads model_technique_map_reviewed.json —
its labels come entirely from model_technique_map.json (see
threshold_pool.py's docstring).

Detection model (mode 1): a (doc, technique) is detected at (rt, vt) iff ANY of
its candidate chunks clears both gates. A gold technique with no candidate at
all is an unconditional miss (retrieval floor too high), which the recall
figure reflects.

Pure stdlib; `--self-test` runs the full math on synthetic separable scores so
the calibrator is verifiable without the ML stack.

Usage:
    python scripts/dump_nlu_scores.py                    # produce dev scores (needs ML stack)
    python scripts/calibrate_thresholds.py               # PR-curve sweep from those scores
    python scripts/calibrate_thresholds.py --precision-floor 0.7 --beta 0.5
    python scripts/calibrate_thresholds.py --self-test

    # T4.2 expanded-pool calibration:
    python scripts/dump_nlu_scores.py --docs reviewed     # score every reviewed doc (needs ML stack)
    python scripts/calibrate_thresholds.py --per-technique \\
        --scores data/eval/nlu_scores_reviewed.json
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import (  # noqa: E402
    DATA, load_split, load_holdout_ids, active_technique_set, fbeta,
)
from taxonomy_aliases import canonical_technique  # noqa: E402
from threshold_pool import (  # noqa: E402
    MIN_POINTS, SHRINKAGE_K, build_labelled_pool, fit_verification_threshold,
    compute_per_technique_thresholds, sha256_file,
)

SCORES_PATH = DATA / "eval" / "nlu_scores_dev.json"
GOLD_PATH = DATA / "model_technique_map_reviewed.json"
MODEL_MAP_PATH = DATA / "model_technique_map.json"
THRESHOLDS_OUT_PATH = DATA / "eval" / "nlu_thresholds.json"  # GENERATED — never commit an instance
REPORTS = Path(__file__).resolve().parent.parent / "reports"


def _frange(lo, hi, step):
    out, x = [], lo
    while x <= hi + 1e-9:
        out.append(round(x, 4))
        x += step
    return out


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


def per_technique_calibration(scores_path, map_path, beta, precision_floor,
                               vt_grid, min_points=MIN_POINTS, k=SHRINKAGE_K,
                               holdout_ids=None):
    """T4.2 end-to-end: pool -> global fit -> per-technique fit+shrinkage ->
    isotonic calibration curve. Returns the dict written to
    data/eval/nlu_thresholds.json (schema below); callers own file I/O so this
    stays testable on synthetic in-memory data (see tests/test_calibration.py).

    scores_path / map_path: paths to a dump_nlu_scores.py-format scores file
    and to data/model_technique_map.json (or synthetic equivalents in tests).
    holdout_ids: blind-test doc ids to quarantine; defaults to
    `load_holdout_ids()`. Raises ValueError if the scores file contains any
    holdout doc (same hard refusal as the default PR-curve mode) or if the
    resulting pool is empty.

    Output schema:
        {"global": {verification_threshold, precision, recall, fbeta, beta,
                     precision_floor, n_points},
         "per_technique": {techId: {verification_threshold, n_points,
                     local_threshold, shrinkage_weight, used_global_fallback,
                     local_precision, local_recall}},
         "calibration": [{x_min, x_max, p, n}, ...],   # isotonic_pav steps
         "generated": {scores_sha256, map_sha256, min_points, shrinkage_k}}
    """
    holdout = load_holdout_ids() if holdout_ids is None else set(holdout_ids)

    with open(scores_path, encoding="utf-8") as f:
        payload = json.load(f)
    candidates = payload.get("candidates", [])
    leaked = sorted({c["doc_id"] for c in candidates} & holdout)
    if leaked:
        raise ValueError(f"scores file contains blind-test docs {leaked}; "
                          f"re-dump with dump_nlu_scores.py (reviewed/dev only)")

    with open(map_path, encoding="utf-8") as f:
        map_data = json.load(f)

    pool = build_labelled_pool(candidates, map_data, holdout)
    if not pool:
        raise ValueError("labelled pool is empty — the scores file must cover "
                          "reviewed, non-holdout documents (see threshold_pool.py)")

    global_fit = fit_verification_threshold(pool, vt_grid, beta, precision_floor)
    global_threshold = global_fit["verification_threshold"]

    per_technique = compute_per_technique_thresholds(
        pool, global_threshold, vt_grid, beta, precision_floor, min_points, k)

    calibration = isotonic_pav([(p["verification_score"], p["label"]) for p in pool])

    return {
        "global": {
            "verification_threshold": global_threshold,
            "precision": global_fit["precision"],
            "recall": global_fit["recall"],
            "fbeta": global_fit["fbeta"],
            "beta": beta,
            "precision_floor": precision_floor,
            "n_points": len(pool),
        },
        "per_technique": per_technique,
        "calibration": calibration,
        "generated": {
            "scores_sha256": sha256_file(scores_path),
            "map_sha256": sha256_file(map_path),
            "min_points": min_points,
            "shrinkage_k": k,
        },
    }


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
    ap.add_argument("--per-technique", action="store_true",
                     help="T4.2 mode: build the expanded labelled pool from every "
                          "reviewed doc in --map (threshold_pool.py), fit a global "
                          "+ per-technique (shrunk) verification threshold, and an "
                          "isotonic calibration curve. Writes --thresholds-out "
                          "instead of --json. Mutually exclusive with --self-test.")
    ap.add_argument("--map", default=str(MODEL_MAP_PATH),
                     help="--per-technique only: path to model_technique_map.json.")
    ap.add_argument("--min-points", type=int, default=MIN_POINTS,
                     help="--per-technique only: minimum labelled points before a "
                          "technique gets a local (shrunk) fit instead of the "
                          "global threshold outright.")
    ap.add_argument("--shrinkage-k", type=float, default=SHRINKAGE_K,
                     help="--per-technique only: shrinkage strength K in w=n/(n+K).")
    ap.add_argument("--thresholds-out", default=str(THRESHOLDS_OUT_PATH),
                     help="--per-technique only: output path for the GENERATED "
                          "thresholds file (never commit an instance of it).")
    args = ap.parse_args()

    rt_grid = _frange(*[float(x) for x in args.rt_grid.split(":")])
    vt_grid = _frange(*[float(x) for x in args.vt_grid.split(":")])

    if args.per_technique:
        try:
            result = per_technique_calibration(
                args.scores, args.map, args.beta, args.precision_floor, vt_grid,
                min_points=args.min_points, k=args.shrinkage_k)
        except (FileNotFoundError, ValueError) as e:
            print(f"ABORT: {e}")
            return 2

        out_path = Path(args.thresholds_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        g = result["global"]
        n_tech = len(result["per_technique"])
        n_local = sum(1 for v in result["per_technique"].values()
                      if not v["used_global_fallback"])
        print("=" * 60)
        print("PER-TECHNIQUE THRESHOLD CALIBRATION (T4.2)")
        print("=" * 60)
        print(f"pool points: {g['n_points']}  techniques observed: {n_tech}  "
              f"locally fit (>= {args.min_points} pts): {n_local}")
        print(f"global verification_threshold={g['verification_threshold']:.3f}  "
              f"precision={g['precision']:.3f} recall={g['recall']:.3f} "
              f"fbeta={g['fbeta']:.3f}")
        print(f"calibration curve: {len(result['calibration'])} monotone step(s)")
        print(f"\nWrote {out_path}")
        print("NOTE: this file is GENERATED and must not be committed. "
              "analyze_nlu.NLUAnalyzer picks it up automatically at init if present.")
        return 0

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
