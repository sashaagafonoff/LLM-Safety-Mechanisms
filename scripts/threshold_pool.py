"""Expanded labelled pool + per-technique threshold fitting (T4.1 / T4.2).

docs/workplan/2026-08-execution-plan.md Phase 4. The June calibration
(`calibrate_thresholds.py` in its original PR-curve form) ran on only 39
labelled points drawn from the 24-doc dev split and recommended overfit
thresholds that were rightly never applied. The reviewed map has since grown
to ~1,253 active + ~518 rejected entries across 38 reviewed documents — a real
pool. This module turns that pool into:

  1. `build_labelled_pool()` (T4.1) — every (reviewed-doc, technique) pair with
     an NLU candidate score gets a label: 1 if the technique is active in that
     doc, 0 ("rejected") if it was explicitly deactivated, 0 ("absent") if it
     never appears in the doc's entries at all. Blind-test docs
     (`eval_common.load_holdout_ids`) and unreviewed docs are excluded.

  2. `fit_verification_threshold()` / `compute_per_technique_thresholds()`
     (T4.2) — per-technique verification thresholds fit by F-beta-subject-to-
     precision-floor sweep, then shrunk toward the global threshold for
     techniques with too few points to fit reliably (`shrink_threshold`,
     `w = n/(n+K)`).

Pure stdlib; every function here takes already-loaded in-memory data
(candidate score dicts, the `model_technique_map.json` payload) rather than
reading files itself, so it is unit-testable on synthetic data without the ML
stack and without touching the real dataset. NEVER reads
`data/model_technique_map_reviewed.json` (frozen ground truth) — labels come
entirely from `data/model_technique_map.json`.

Consumed by `scripts/calibrate_thresholds.py --per-technique`, which owns the
file I/O and writes the GENERATED `data/eval/nlu_thresholds.json` (never
committed — see that script's docstring).
"""
import hashlib
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence

from eval_common import is_reviewed_document, active_technique_set, fbeta
from taxonomy_aliases import canonical_technique

# Shrinkage default: techniques need at least this many labelled points before
# a local threshold is fit at all (below this, use the global threshold
# outright — too little data to fit reliably).
MIN_POINTS = 15

# Shrinkage strength: w = n / (n + K). K=20 means a technique needs roughly
# 20 labelled points before its local fit carries as much weight as the
# global prior.
SHRINKAGE_K = 20


# --- T4.1: expanded labelled pool ---

def build_labelled_pool(candidates: Iterable[dict], map_data: dict,
                         holdout_ids: Optional[Iterable[str]] = None) -> List[dict]:
    """Turn NLU candidate scores into labelled (doc, technique) points.

    candidates: iterable of dicts in dump_nlu_scores.py's format — each has
      at least `doc_id`, `techniqueId`, `retrieval_score`, `verification_score`
      (scored via NLUAnalyzer.score_candidates with its 0.30 retrieval floor;
      this function does not itself apply any floor — it just labels whatever
      candidates it's given).
    map_data: the full parsed `model_technique_map.json` payload,
      `{doc_id: [entry, ...]}`. This is the ONLY source of labels — the frozen
      `model_technique_map_reviewed.json` ground truth is never read here.
    holdout_ids: blind-test doc ids to quarantine (pass
      `eval_common.load_holdout_ids()`); defaults to empty (no quarantine) so
      callers that have already filtered can pass nothing.

    A candidate is emitted as a labelled point iff its doc is a *reviewed*
    document (`eval_common.is_reviewed_document`) and not in `holdout_ids`.
    Candidates from unreviewed docs, docs absent from `map_data`, or
    holdout docs are silently dropped (not an error) — a scores file that
    happens to include such docs just contributes nothing from them.

    Label/kind for each emitted point:
      label=1, kind="active"   — technique is in the doc's active-technique set
      label=0, kind="rejected" — technique appears in the doc's entries but is
                                  not active (explicitly deactivated)
      label=0, kind="absent"   — technique never appears in the doc's entries

    Technique ids are canonicalized (`taxonomy_aliases.canonical_technique`) so
    renamed/merged techniques don't fragment across old/new ids.
    """
    holdout = set(holdout_ids or ())
    points: List[dict] = []
    # Cache per-doc derived state so repeated candidates for the same doc
    # (multiple techniques) don't recompute is_reviewed_document/active set.
    doc_cache: Dict[str, tuple] = {}

    for cand in candidates:
        doc_id = cand.get("doc_id")
        if not doc_id or doc_id in holdout:
            continue
        entries = map_data.get(doc_id)
        if not entries:
            continue

        if doc_id not in doc_cache:
            reviewed = is_reviewed_document(entries)
            if reviewed:
                active_set = active_technique_set(entries)
                present_ids = {
                    canonical_technique(e.get("techniqueId", ""))
                    for e in entries if e.get("techniqueId")
                }
            else:
                active_set, present_ids = set(), set()
            doc_cache[doc_id] = (reviewed, active_set, present_ids)

        reviewed, active_set, present_ids = doc_cache[doc_id]
        if not reviewed:
            continue

        raw_tech = cand.get("techniqueId")
        if not raw_tech:
            continue
        tech = canonical_technique(raw_tech)

        if tech in active_set:
            label, kind = 1, "active"
        elif tech in present_ids:
            label, kind = 0, "rejected"
        else:
            label, kind = 0, "absent"

        points.append({
            "doc_id": doc_id,
            "techniqueId": tech,
            "retrieval_score": cand.get("retrieval_score"),
            "verification_score": cand.get("verification_score"),
            "label": label,
            "kind": kind,
        })

    return points


# --- T4.2: per-technique threshold fitting + shrinkage ---

def fit_verification_threshold(points: Sequence[dict], vt_grid: Sequence[float],
                                beta: float, precision_floor: float) -> dict:
    """Sweep verification-score thresholds over labelled points; return the
    operating point maximising F-beta subject to a precision floor (falling
    back to the best unconstrained F-beta if no threshold clears the floor).

    Mirrors `calibrate_thresholds.sweep()`'s recommendation logic, but over a
    flat pool of labelled (verification_score, label) points rather than a 2D
    (retrieval, verification) grid keyed by (doc, technique) — this is what
    lets the same shape fit either one technique's points or the whole pool
    (the "global" threshold).

    Returns a dict with verification_threshold/tp/fp/fn/precision/recall/fbeta.
    Callers should not call this with an empty `points` (the fit is
    meaningless with no data); `compute_per_technique_thresholds` guards that
    via `MIN_POINTS`.
    """
    best = None
    best_floored = None
    for vt in vt_grid:
        tp = fp = fn = 0
        for p in points:
            detected = p["verification_score"] >= vt
            if detected:
                if p["label"] == 1:
                    tp += 1
                else:
                    fp += 1
            else:
                if p["label"] == 1:
                    fn += 1
                # detected=False, label=0 -> true negative, doesn't enter P/R
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        fb = fbeta(precision, recall, beta)
        point = {
            "verification_threshold": vt, "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall, "fbeta": fb,
        }
        if best is None or fb > best["fbeta"]:
            best = point
        if precision >= precision_floor and (best_floored is None or fb > best_floored["fbeta"]):
            best_floored = point
    return best_floored or best


def shrink_threshold(t_local: float, t_global: float, n: int, k: float = SHRINKAGE_K) -> float:
    """Shrink a per-technique threshold toward the global threshold.

    w = n / (n + k): n=0 -> w=0 (pure global); n>>k -> w->1 (pure local).
    Low-data techniques stay close to the well-supported global operating
    point instead of overfitting a threshold to a handful of points.
    """
    if n <= 0:
        return t_global
    w = n / (n + k)
    return w * t_local + (1 - w) * t_global


def compute_per_technique_thresholds(pool: Sequence[dict], global_threshold: float,
                                      vt_grid: Sequence[float], beta: float,
                                      precision_floor: float,
                                      min_points: int = MIN_POINTS,
                                      k: float = SHRINKAGE_K) -> Dict[str, dict]:
    """Per-technique verification thresholds with shrinkage (T4.2 step 1).

    Techniques with fewer than `min_points` labelled points in `pool` use the
    global threshold outright (no local fit attempted — too little data).
    Techniques at or above `min_points` get a local F-beta fit
    (`fit_verification_threshold`), then shrunk toward `global_threshold`
    (`shrink_threshold`) weighted by how much data they have.

    Returns `{techniqueId: {verification_threshold, n_points, local_threshold,
    shrinkage_weight, used_global_fallback, local_precision, local_recall}}`.
    """
    by_tech: Dict[str, List[dict]] = defaultdict(list)
    for p in pool:
        by_tech[p["techniqueId"]].append(p)

    out: Dict[str, dict] = {}
    for tech_id, pts in by_tech.items():
        n = len(pts)
        if n < min_points:
            out[tech_id] = {
                "verification_threshold": round(global_threshold, 4),
                "n_points": n,
                "local_threshold": None,
                "shrinkage_weight": 0.0,
                "used_global_fallback": True,
                "local_precision": None,
                "local_recall": None,
            }
            continue

        local_fit = fit_verification_threshold(pts, vt_grid, beta, precision_floor)
        t_local = local_fit["verification_threshold"]
        w = n / (n + k)
        t_shrunk = shrink_threshold(t_local, global_threshold, n, k)
        out[tech_id] = {
            "verification_threshold": round(t_shrunk, 4),
            "n_points": n,
            "local_threshold": t_local,
            "shrinkage_weight": round(w, 4),
            "used_global_fallback": False,
            "local_precision": local_fit["precision"],
            "local_recall": local_fit["recall"],
        }
    return out


# --- misc I/O helper ---

def sha256_file(path) -> str:
    """SHA-256 hex digest of a file's bytes, for the `generated` provenance
    block in nlu_thresholds.json (input-drift detection)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
