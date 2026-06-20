"""Phase 1 evaluation-integrity tests (no heavy ML deps).

Covers the dependency-free logic introduced by Phase 1 (WORKPLAN B.1.*):
  - taxonomy_aliases  (B.1.5) — canonicalization + resolution guards
  - eval_common       (B.1.4) — shared active/reviewed/grounded definitions + metrics
  - make_eval_split   (B.1.1) — deterministic stratified split + disjointness
  - calibrate_thresholds (B.1.3) — isotonic PAV + F-beta + sweep
  - annotator_agreement  (B.1.1) — Cohen/Fleiss kappa
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import taxonomy_aliases as ta
import eval_common as ec
import make_eval_split as mes
import calibrate_thresholds as cal
import annotator_agreement as agree


# --- B.1.5: taxonomy aliases ---

def test_canonical_technique_maps_and_passthrough():
    assert ta.canonical_technique("tech-content-watermarking") == "tech-watermarking"
    assert ta.canonical_technique("tech-rlhf") == "tech-rlhf"  # unknown -> unchanged


def test_canonical_techniques_dedupes_merges():
    s = ta.canonical_techniques({"tech-content-watermarking", "tech-watermarking"})
    assert s == {"tech-watermarking"}


def test_alias_targets_resolve_against_live_taxonomy():
    valid = ec.technique_ids()
    assert ta.assert_technique_aliases_resolve(valid) == []
    assert ta.assert_no_alias_cycles() == []


def test_model_alias_targets_resolve_against_live_models():
    models = json.load(open(ROOT / "data" / "models.json", encoding="utf-8"))
    model_list = models["models"] if isinstance(models, dict) else models
    ids = {m["id"] for m in model_list}
    assert ta.assert_model_aliases_resolve(ids) == []


# --- B.1.4: shared definitions ---

def test_active_technique_set_canonicalizes_and_filters():
    entries = [
        {"techniqueId": "tech-a", "active": True, "evidence": [{"text": "x", "active": True}]},
        {"techniqueId": "tech-b", "active": False, "evidence": [{"text": "y"}]},  # inactive
        {"techniqueId": "tech-content-watermarking", "active": True, "evidence": ["legacy"]},
    ]
    assert ec.active_technique_set(entries) == {"tech-a", "tech-watermarking"}


def test_active_technique_set_no_evidence_counts_active():
    assert ec.active_technique_set([{"techniqueId": "tech-a", "active": True}]) == {"tech-a"}


def test_active_set_and_by_source_agree():
    # Regression for the SoT divergence: a technique appears in techniques_by_source
    # iff it appears in active_technique_set (incl. the all-inactive-evidence edge).
    cases = [
        [{"techniqueId": "tech-a", "active": True, "evidence": [{"text": "x", "active": True}]}],
        [{"techniqueId": "tech-b", "active": True,
          "evidence": [{"text": "x", "active": False}]}],          # all-inactive evidence
        [{"techniqueId": "tech-c", "active": True, "evidence": []}],  # empty evidence
        [{"techniqueId": "tech-d", "active": False, "evidence": [{"text": "x"}]}],  # inactive entry
        [{"techniqueId": "tech-e", "active": True, "evidence": ["legacy-str"]}],
    ]
    for entries in cases:
        active = ec.active_technique_set(entries)
        by_src = set().union(*ec.techniques_by_source(entries).values())
        assert active == by_src, f"divergence on {entries}: {active} != {by_src}"


def test_grounded_active_set_excludes_grounding_failed():
    entries = [
        {"techniqueId": "tech-grounded", "active": True,
         "evidence": [{"text": "real quote", "active": True}]},
        {"techniqueId": "tech-ungrounded", "active": True,
         "evidence": [{"text": "q", "active": True, "grounding_failed": True}]},
        {"techniqueId": "tech-noevidence", "active": True, "evidence": []},
    ]
    assert ec.grounded_active_set(entries) == {"tech-grounded"}


def test_is_reviewed_document():
    assert ec.is_reviewed_document([{"evidence": [{"created_by": "manual"}]}]) is True
    assert ec.is_reviewed_document(
        [{"active": False, "deleted_by": "sashaagafonoff", "evidence": []}]) is True
    assert ec.is_reviewed_document([{"evidence": [{"created_by": "nlu"}]}]) is False
    assert ec.is_reviewed_document(
        [{"active": False, "deleted_by": "system", "evidence": []}]) is False


def test_confusion_and_prf():
    tp, fp, fn = ec.confusion({"a", "b", "c"}, {"b", "c", "d"})
    assert (tp, fp, fn) == ({"b", "c"}, {"a"}, {"d"})
    p, r, f = ec.prf(2, 1, 1)
    assert round(p, 3) == 0.667 and round(r, 3) == 0.667 and round(f, 3) == 0.667
    assert ec.prf(0, 0, 0) == (0.0, 0.0, 0.0)  # no NaN


# --- B.1.1: split determinism + disjointness + loaders ---

def test_stratified_split_deterministic_and_disjoint():
    ids = mes.gold_doc_ids()
    dev1, test1, _ = mes.stratified_split(ids, 0.3)
    dev2, test2, _ = mes.stratified_split(ids, 0.3)
    assert dev1 == dev2 and test1 == test2          # deterministic
    assert not (set(dev1) & set(test1))             # disjoint
    assert set(dev1) | set(test1) == set(ids)       # complete
    assert len(test1) > 0


def test_family_of_known_prefixes():
    assert mes.family_of("claude-opus-4-5-system-card") == "anthropic"
    assert mes.family_of("gpt-5-system-card") == "openai"
    assert mes.family_of("qwen3-max") == "alibaba"
    assert mes.family_of("totally-unknown-doc") == "other"


def test_frozen_split_loaders_consistent():
    test_ids, dev_ids = set(ec.load_split("test")), set(ec.load_split("dev"))
    holdout = ec.load_holdout_ids()
    assert holdout == test_ids                       # holdout file == test split
    assert not (test_ids & dev_ids)                  # disjoint on disk


def test_on_disk_split_is_current():
    # the committed split must match regeneration (CI guard against stale freeze)
    assert mes.check_split(0.30) == 0


# --- B.1.3: calibration math ---

def test_isotonic_pav_monotone_and_coalesced():
    steps = cal.isotonic_pav([(0.1, 0), (0.2, 0), (0.8, 1), (0.9, 1)])
    assert len(steps) == 2
    assert steps[0]["p"] == 0.0 and steps[1]["p"] == 1.0
    # output is monotone non-decreasing in p
    ps = [s["p"] for s in steps]
    assert ps == sorted(ps)


def test_isotonic_pav_pools_violation():
    # a high-x negative after low-x positives must be pooled toward the mean
    steps = cal.isotonic_pav([(0.1, 1), (0.2, 0), (0.3, 1), (0.4, 0)])
    ps = [s["p"] for s in steps]
    assert ps == sorted(ps)  # still monotone after pooling


def test_fbeta():
    assert cal.fbeta(1.0, 1.0, 1.0) == 1.0
    assert cal.fbeta(0.0, 1.0, 1.0) == 0.0
    # beta<1 weights precision more than recall
    assert cal.fbeta(0.9, 0.5, 0.5) > cal.fbeta(0.5, 0.9, 0.5)


def test_sweep_recommends_separating_point():
    candidates, gold = cal._synthetic()
    grp = cal.group_candidates(candidates)
    curve, rec = cal.sweep(grp, gold, cal._frange(0.30, 0.60, 0.05),
                           cal._frange(0.50, 0.95, 0.05), 1.0, 0.6)
    assert rec["floor_met"]
    assert rec["recommended"]["precision"] == 1.0
    assert rec["recommended"]["recall"] == 1.0


# --- B.1.1: kappa ---

def test_cohen_kappa_perfect_and_chance():
    items = [("d", "t1"), ("d", "t2"), ("d", "t3")]
    full = {("d", "t1"), ("d", "t2"), ("d", "t3")}
    k, po, pe, n = agree.cohen_kappa(items, full, full)
    assert round(k, 6) == 1.0 and po == 1.0 and n == 3


def test_fleiss_kappa_perfect_agreement():
    items = [("d", "t1"), ("d", "t2")]
    r = {("d", "t1"), ("d", "t2")}
    k, pbar, pe, n = agree.fleiss_kappa(items, [r, r, r])
    assert round(k, 6) == 1.0
