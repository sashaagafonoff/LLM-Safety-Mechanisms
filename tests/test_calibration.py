"""T4.1-T4.3 tests: expanded labelled pool, per-technique threshold shrinkage,
isotonic calibration, and analyze_nlu.py's threshold-loading pure functions
(docs/workplan/2026-08-execution-plan.md Phase 4).

Covers:
  - threshold_pool.build_labelled_pool (T4.1) — active/rejected/absent
    labelling, holdout quarantine, unreviewed-doc exclusion, alias
    canonicalization. Never reads model_technique_map_reviewed.json — all
    labels here come from synthetic map payloads shaped like
    model_technique_map.json.
  - threshold_pool.shrink_threshold / compute_per_technique_thresholds (T4.2
    step 1) — shrinkage math at the n=0 and n>>K extremes, and the
    MIN_POINTS local-fit-vs-global-fallback branch.
  - calibrate_thresholds.isotonic_pav — monotonicity on a larger synthetic
    curve (test_phase1.py already covers the two tiny hand-built cases; this
    adds a randomized/noisy one).
  - calibrate_thresholds.per_technique_calibration (T4.2 steps 2-3) — output
    schema + JSON round-trip on synthetic scores/map data, plus its
    holdout-leak and empty-pool guards.
  - A regression guard: IF the real data/eval/nlu_thresholds.json exists, every
    per_technique verification_threshold must lie in [0.5, 0.99] (skips
    cleanly when the file hasn't been generated, since it's a GENERATED file
    never committed to the repo).
  - analyze_nlu.load_thresholds / verification_threshold_for /
    calibrated_probability — pure functions, exercised WITHOUT instantiating
    NLUAnalyzer (that would load the sentence-transformers/cross-encoder
    models, which this task must not do).

`analyze_nlu` is imported at module level for those three pure functions.
That import pulls in the `sentence_transformers` package (slow but functional
in this environment) — the same accepted cost tests/test_nlu_denylist.py
already pays for `analyze_nlu.is_nlu_enabled`. No model weights are ever
loaded: that only happens inside `NLUAnalyzer.__init__`, which this file never
calls.
"""
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import taxonomy_aliases as ta  # noqa: E402
import threshold_pool as tp  # noqa: E402
import calibrate_thresholds as cal  # noqa: E402
import analyze_nlu as nlu  # noqa: E402 -- module-level import only; NLUAnalyzer() never called


# ---------------------------------------------------------------------------
# T4.1 — build_labelled_pool
# ---------------------------------------------------------------------------

def _entry(tech_id, active=True, created_by="manual", ev_active=None):
    if ev_active is None:
        ev_active = active
    return {
        "techniqueId": tech_id,
        "active": active,
        "deleted_by": None if active else "sasha",
        "evidence": [{"text": "quote", "created_by": created_by, "active": ev_active}],
    }


REVIEWED_MAP = {
    # Reviewed via manual evidence on tech-active; tech-rejected explicitly deactivated.
    "doc-reviewed": [
        _entry("tech-active", active=True, created_by="manual"),
        _entry("tech-rejected", active=False, created_by="nlu", ev_active=False),
    ],
    # Reviewed ONLY because tech-other-rejected was deactivated by a real person
    # (deleted_by != "system") -- tech-active here carries only nlu evidence.
    "doc-reviewed-2": [
        _entry("tech-active", active=True, created_by="nlu"),
        _entry("tech-other-rejected", active=False, created_by="nlu", ev_active=False),
    ],
    # NOT reviewed: nlu-only evidence, nothing deactivated by a real person.
    "doc-unreviewed": [
        _entry("tech-active", active=True, created_by="nlu"),
    ],
}

HOLDOUT = {"doc-holdout"}


def _cand(doc_id, tech_id, rs=0.5, vs=0.9):
    return {"doc_id": doc_id, "techniqueId": tech_id,
            "retrieval_score": rs, "verification_score": vs}


def test_pool_labels_active():
    pool = tp.build_labelled_pool([_cand("doc-reviewed", "tech-active", vs=0.91)],
                                   REVIEWED_MAP, HOLDOUT)
    assert len(pool) == 1
    assert pool[0]["label"] == 1
    assert pool[0]["kind"] == "active"
    assert pool[0]["verification_score"] == 0.91


def test_pool_labels_rejected():
    pool = tp.build_labelled_pool([_cand("doc-reviewed", "tech-rejected")],
                                   REVIEWED_MAP, HOLDOUT)
    assert len(pool) == 1
    assert pool[0]["label"] == 0
    assert pool[0]["kind"] == "rejected"


def test_pool_labels_absent():
    # tech-never-seen never appears anywhere in doc-reviewed's entries.
    pool = tp.build_labelled_pool([_cand("doc-reviewed", "tech-never-seen")],
                                   REVIEWED_MAP, HOLDOUT)
    assert len(pool) == 1
    assert pool[0]["label"] == 0
    assert pool[0]["kind"] == "absent"


def test_pool_excludes_holdout_docs():
    holdout_map = {"doc-holdout": REVIEWED_MAP["doc-reviewed"]}
    pool = tp.build_labelled_pool([_cand("doc-holdout", "tech-active")], holdout_map, HOLDOUT)
    assert pool == []


def test_pool_excludes_unreviewed_docs():
    pool = tp.build_labelled_pool([_cand("doc-unreviewed", "tech-active")], REVIEWED_MAP, HOLDOUT)
    assert pool == []


def test_pool_reviewed_via_deletion_not_just_manual_evidence():
    pool = tp.build_labelled_pool([_cand("doc-reviewed-2", "tech-active")], REVIEWED_MAP, HOLDOUT)
    assert len(pool) == 1
    assert pool[0]["kind"] == "active"


def test_pool_missing_doc_skipped():
    pool = tp.build_labelled_pool([_cand("doc-not-in-map", "tech-active")], REVIEWED_MAP, HOLDOUT)
    assert pool == []


def test_pool_no_holdout_ids_means_no_quarantine():
    pool = tp.build_labelled_pool([_cand("doc-reviewed", "tech-active")], REVIEWED_MAP)
    assert len(pool) == 1


def test_pool_canonicalizes_technique_ids():
    old_id, new_id = next(iter(ta.TECHNIQUE_ALIASES.items()))
    fake_map = {"doc-alias": [_entry(new_id, active=True, created_by="manual")]}
    # Scored under the OLD (pre-rename) id, as an unrenamed dump would emit.
    pool = tp.build_labelled_pool([_cand("doc-alias", old_id)], fake_map, set())
    assert len(pool) == 1
    assert pool[0]["techniqueId"] == new_id
    assert pool[0]["kind"] == "active"


# ---------------------------------------------------------------------------
# T4.2 — shrinkage math
# ---------------------------------------------------------------------------

def test_shrink_n_zero_returns_global_exactly():
    assert tp.shrink_threshold(0.95, 0.70, n=0) == 0.70


def test_shrink_negative_n_returns_global():
    assert tp.shrink_threshold(0.95, 0.70, n=-3) == 0.70


def test_shrink_large_n_approaches_local():
    shrunk = tp.shrink_threshold(0.95, 0.70, n=1_000_000, k=20)
    assert abs(shrunk - 0.95) < 1e-3


def test_shrink_n_equals_k_is_midpoint():
    assert tp.shrink_threshold(0.90, 0.70, n=20, k=20) == pytest.approx(0.80)


def test_shrink_defaults():
    assert tp.SHRINKAGE_K == 20
    assert tp.MIN_POINTS == 15


def _make_points(n_pos, n_neg, tech="tech-t", vs_pos=0.9, vs_neg=0.6):
    pts = [{"techniqueId": tech, "verification_score": vs_pos, "label": 1} for _ in range(n_pos)]
    pts += [{"techniqueId": tech, "verification_score": vs_neg, "label": 0} for _ in range(n_neg)]
    return pts


def test_per_technique_below_min_points_uses_global():
    pool = _make_points(5, 5)  # 10 < MIN_POINTS default (15)
    per_tech = tp.compute_per_technique_thresholds(
        pool, global_threshold=0.85, vt_grid=[0.5, 0.7, 0.9], beta=1.0, precision_floor=0.5)
    entry = per_tech["tech-t"]
    assert entry["used_global_fallback"] is True
    assert entry["verification_threshold"] == 0.85
    assert entry["n_points"] == 10
    assert entry["local_threshold"] is None


def test_per_technique_at_min_points_fits_locally_and_shrinks():
    pool = _make_points(10, 10)  # 20 >= MIN_POINTS default (15)
    per_tech = tp.compute_per_technique_thresholds(
        pool, global_threshold=0.85, vt_grid=[0.5, 0.7, 0.9], beta=1.0, precision_floor=0.5,
        min_points=15, k=20)
    entry = per_tech["tech-t"]
    assert entry["used_global_fallback"] is False
    assert entry["n_points"] == 20
    assert entry["local_threshold"] is not None
    assert entry["shrinkage_weight"] == pytest.approx(20 / (20 + 20))  # n/(n+K) = 0.5


def test_fit_verification_threshold_separates_clean_signal():
    # Positives all score 0.9, negatives all score 0.3 -- a threshold anywhere
    # in between should reach perfect precision/recall.
    pts = _make_points(8, 8, vs_pos=0.9, vs_neg=0.3)
    fit = tp.fit_verification_threshold(pts, vt_grid=[0.2, 0.4, 0.6, 0.8], beta=1.0,
                                         precision_floor=0.9)
    assert fit["precision"] == 1.0
    assert fit["recall"] == 1.0


# ---------------------------------------------------------------------------
# T4.2 — isotonic monotonicity on a synthetic curve
# ---------------------------------------------------------------------------

def test_isotonic_pav_monotonic_on_noisy_synthetic_curve():
    rng = random.Random(42)
    points = []
    for _ in range(300):
        x = rng.random()
        y = 1 if rng.random() < x else 0  # P(y=1) increases with x, but noisy
        points.append((x, y))
    steps = cal.isotonic_pav(points)
    assert len(steps) >= 1
    ps = [s["p"] for s in steps]
    assert ps == sorted(ps)  # non-decreasing calibrated probability
    for a, b in zip(steps, steps[1:]):
        assert a["x_max"] <= b["x_min"]  # contiguous, non-overlapping ranges
    assert sum(int(s["n"]) for s in steps) == len(points)


# ---------------------------------------------------------------------------
# T4.2 — per_technique_calibration: schema, round-trip, guards
# ---------------------------------------------------------------------------

def _write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_per_technique_calibration_schema_and_roundtrip(tmp_path):
    map_data = {
        "doc-1": [
            _entry("tech-a", active=True, created_by="manual"),
            _entry("tech-b", active=False, created_by="nlu", ev_active=False),
        ],
        "doc-2": [
            _entry("tech-a", active=True, created_by="manual"),
        ],
    }
    candidates = [
        {"doc_id": "doc-1" if i % 2 == 0 else "doc-2", "techniqueId": "tech-a",
         "retrieval_score": 0.5, "verification_score": 0.9}
        for i in range(20)  # >= MIN_POINTS so tech-a gets a local fit
    ]
    candidates.append({"doc_id": "doc-1", "techniqueId": "tech-b",
                        "retrieval_score": 0.5, "verification_score": 0.4})

    scores_path = tmp_path / "scores.json"
    map_path = tmp_path / "map.json"
    _write_json(scores_path, {"split": "reviewed", "retrieval_floor": 0.3, "candidates": candidates})
    _write_json(map_path, map_data)

    result = cal.per_technique_calibration(
        scores_path, map_path, beta=1.0, precision_floor=0.5,
        vt_grid=[0.3, 0.5, 0.7, 0.85], min_points=15, k=20, holdout_ids=set())

    assert set(result.keys()) == {"global", "per_technique", "calibration", "generated"}

    g = result["global"]
    assert {"verification_threshold", "precision", "recall", "fbeta",
            "beta", "precision_floor", "n_points"} <= set(g.keys())

    assert "tech-a" in result["per_technique"]
    pt = result["per_technique"]["tech-a"]
    assert {"verification_threshold", "n_points", "local_threshold",
            "shrinkage_weight", "used_global_fallback",
            "local_precision", "local_recall"} == set(pt.keys())
    assert pt["used_global_fallback"] is False  # 20 points >= min_points=15

    assert isinstance(result["calibration"], list)
    for step in result["calibration"]:
        assert {"x_min", "x_max", "p", "n"} == set(step.keys())

    assert set(result["generated"].keys()) == {
        "scores_sha256", "map_sha256", "min_points", "shrinkage_k"}
    assert result["generated"]["min_points"] == 15
    assert result["generated"]["shrinkage_k"] == 20

    # JSON round-trip: what gets written is exactly what gets read back.
    out_path = tmp_path / "nlu_thresholds.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(out_path, encoding="utf-8") as f:
        reloaded = json.load(f)
    assert reloaded == result


def test_per_technique_calibration_refuses_holdout_leak(tmp_path):
    scores_path = tmp_path / "scores.json"
    map_path = tmp_path / "map.json"
    _write_json(scores_path, {"candidates": [
        {"doc_id": "doc-holdout", "techniqueId": "tech-a",
         "retrieval_score": 0.5, "verification_score": 0.9}]})
    _write_json(map_path, {"doc-holdout": [_entry("tech-a", active=True, created_by="manual")]})

    with pytest.raises(ValueError, match="blind-test"):
        cal.per_technique_calibration(scores_path, map_path, beta=1.0, precision_floor=0.5,
                                       vt_grid=[0.5], holdout_ids={"doc-holdout"})


def test_per_technique_calibration_empty_pool_raises(tmp_path):
    scores_path = tmp_path / "scores.json"
    map_path = tmp_path / "map.json"
    _write_json(scores_path, {"candidates": []})
    _write_json(map_path, {})

    with pytest.raises(ValueError, match="empty"):
        cal.per_technique_calibration(scores_path, map_path, beta=1.0, precision_floor=0.5,
                                       vt_grid=[0.5], holdout_ids=set())


# ---------------------------------------------------------------------------
# T4.3 — regression guard on the REAL generated file (skips cleanly if absent)
# ---------------------------------------------------------------------------

def test_real_thresholds_file_per_technique_range_if_present():
    real_path = ROOT / "data" / "eval" / "nlu_thresholds.json"
    if not real_path.exists():
        pytest.skip("data/eval/nlu_thresholds.json not generated in this environment "
                     "(GENERATED file, never committed) -- nothing to regress against")
    with open(real_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "per_technique" in data
    out_of_range = []
    for tech_id, entry in data["per_technique"].items():
        vt = entry.get("verification_threshold")
        if vt is None or not (0.5 <= vt <= 0.99):
            out_of_range.append((tech_id, vt))
    assert not out_of_range, f"thresholds outside [0.5, 0.99]: {out_of_range}"


# ---------------------------------------------------------------------------
# T4.3 — analyze_nlu.load_thresholds: pure function, no NLUAnalyzer instantiation
# ---------------------------------------------------------------------------

def test_load_thresholds_missing_file_returns_empty(tmp_path):
    assert nlu.load_thresholds(tmp_path / "does_not_exist.json") == {}


def test_load_thresholds_malformed_json_returns_empty(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    assert nlu.load_thresholds(bad) == {}


def test_load_thresholds_missing_global_key_returns_empty(tmp_path):
    p = tmp_path / "no_global.json"
    p.write_text(json.dumps({"per_technique": {}}), encoding="utf-8")
    assert nlu.load_thresholds(p) == {}


def test_load_thresholds_non_dict_payload_returns_empty(tmp_path):
    p = tmp_path / "list.json"
    p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert nlu.load_thresholds(p) == {}


def test_load_thresholds_well_formed_returns_data(tmp_path):
    payload = {"global": {"verification_threshold": 0.8}, "per_technique": {}, "calibration": []}
    p = tmp_path / "good.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    assert nlu.load_thresholds(p) == payload


# --- verification_threshold_for / calibrated_probability: also pure ---

def test_verification_threshold_for_empty_thresholds_uses_module_constant():
    assert nlu.verification_threshold_for({}, "tech-x") == nlu.VERIFICATION_THRESHOLD


def test_verification_threshold_for_per_technique_override():
    thresholds = {"global": {"verification_threshold": 0.8},
                  "per_technique": {"tech-x": {"verification_threshold": 0.65}}}
    assert nlu.verification_threshold_for(thresholds, "tech-x") == 0.65


def test_verification_threshold_for_falls_back_to_file_global():
    thresholds = {"global": {"verification_threshold": 0.8}, "per_technique": {}}
    assert nlu.verification_threshold_for(thresholds, "tech-unknown") == 0.8


def test_calibrated_probability_none_without_curve():
    assert nlu.calibrated_probability({}, 0.9) is None
    assert nlu.calibrated_probability({"global": {}}, 0.9) is None


def test_calibrated_probability_steps_and_extrapolation():
    thresholds = {"calibration": [
        {"x_min": 0.3, "x_max": 0.5, "p": 0.1, "n": 10},
        {"x_min": 0.5, "x_max": 0.8, "p": 0.6, "n": 10},
        {"x_min": 0.8, "x_max": 1.0, "p": 0.95, "n": 10},
    ]}
    assert nlu.calibrated_probability(thresholds, 0.2) == 0.1  # below range -> lowest bucket
    assert nlu.calibrated_probability(thresholds, 0.4) == 0.1
    assert nlu.calibrated_probability(thresholds, 0.6) == 0.6
    assert nlu.calibrated_probability(thresholds, 0.99) == 0.95
    assert nlu.calibrated_probability(thresholds, 5.0) == 0.95  # above range -> highest bucket


def test_calibrated_confidence_module_constants():
    assert nlu.CALIBRATED_HIGH_THRESHOLD == 0.75
    assert nlu.CALIBRATED_MEDIUM_THRESHOLD == 0.5
