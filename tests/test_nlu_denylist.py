"""Tests for the NLU deny-list mechanism (WORKPLAN T2.1).

Covers:
  - `analyze_nlu.is_nlu_enabled` — the pure predicate that gates a technique's
    participation in NLU retrieval indexing (`_load_and_index_techniques`).
  - That every technique currently deny-listed (`nlu_profile.nlu_enabled: false`)
    in data/techniques.json is justified by the review-grounded evidence rule:
    zero human-confirmed positives AND at least two negatives, among entries for
    that technique in documents `eval_common.is_reviewed_document` considers
    reviewed. This is a regression guard against deny-listing a technique that
    later gains real supporting evidence, or a hand-edit that skips the bar.

Deliberately does NOT instantiate NLUAnalyzer or load any HuggingFace models —
only the module-level pure function is exercised. Importing `analyze_nlu` does
pull in `sentence_transformers` at import time (slow but functional in this
environment); that cost is accepted per the task spec rather than worked around.

Does NOT read data/model_technique_map_reviewed.json (frozen ground truth) —
evidence is derived solely from data/model_technique_map.json + eval_common.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import eval_common as ec  # noqa: E402
import analyze_nlu  # noqa: E402


# --- is_nlu_enabled: pure predicate ---

def test_is_nlu_enabled_true_by_default():
    assert analyze_nlu.is_nlu_enabled({}) is True
    assert analyze_nlu.is_nlu_enabled({"nlu_profile": {}}) is True
    assert analyze_nlu.is_nlu_enabled({"nlu_profile": {"nlu_enabled": True}}) is True


def test_is_nlu_enabled_false_when_set():
    assert analyze_nlu.is_nlu_enabled({"nlu_profile": {"nlu_enabled": False}}) is False


def test_is_nlu_enabled_only_false_is_false():
    # Anything other than the literal `False` value should not disable NLU —
    # this is a strict deny-list flag, not a generic falsiness check.
    assert analyze_nlu.is_nlu_enabled({"nlu_profile": {"nlu_enabled": None}}) is True
    assert analyze_nlu.is_nlu_enabled({"nlu_profile": {"nlu_enabled": 0}}) is True


# --- deny-list evidence justification ---

MANUAL_CREATORS = ec.MANUAL_CREATORS


def _load_map():
    with open(ROOT / "data" / "model_technique_map.json", encoding="utf-8") as f:
        return json.load(f)


def _load_techniques():
    with open(ROOT / "data" / "techniques.json", encoding="utf-8") as f:
        return json.load(f)


def _review_stats_for_technique(technique_map: dict, technique_id: str):
    """(confirmed_positives, negatives) for one technique within reviewed docs.

    confirmed_positive: entry is active=True AND has at least one evidence item
    with created_by in MANUAL_CREATORS (a human actually created/confirmed the
    evidence) — an untouched automated detection sitting in a document that was
    "reviewed" only because some *other* technique's entry was auto-rejected
    does not count as confirmed.
    negative: entry is active=False (any provenance), counted regardless of
    whether that specific entry carries manual evidence, since a deactivation
    is itself the review signal.
    """
    confirmed_positives = 0
    negatives = 0
    for entries in technique_map.values():
        if not ec.is_reviewed_document(entries):
            continue
        for entry in entries:
            if entry.get("techniqueId") != technique_id:
                continue
            if entry.get("active", True):
                evidence = entry.get("evidence") or []
                has_manual_evidence = any(
                    isinstance(ev, dict) and ev.get("created_by") in MANUAL_CREATORS
                    for ev in evidence
                )
                if has_manual_evidence:
                    confirmed_positives += 1
            else:
                negatives += 1
    return confirmed_positives, negatives


def _deny_listed_ids(techniques):
    return {
        t["id"] for t in techniques
        if isinstance(t, dict) and t.get("nlu_profile", {}).get("nlu_enabled") is False
    }


def test_deny_listed_techniques_are_evidence_justified():
    """Live invariant: no deny-listed technique has a human-confirmed positive.

    The original decision evidence (0 confirmed positives AND >=2 review
    negatives per technique, computed against the 2026-08-23 map) is a
    point-in-time record kept in the T2.1 report — it is deliberately NOT
    re-asserted against the live map, because once the deny-list is active the
    NLU stage stops generating those techniques and their historical rejection
    entries age out of the regenerated map. The self-erasing negatives bar
    would then fail precisely because the deny-list works.

    What must stay continuously true is the re-enable signal: if a human ever
    confirms a positive for a deny-listed technique, this test fires and the
    deny-listing should be reconsidered.
    """
    techniques = _load_techniques()
    technique_map = _load_map()
    deny_listed = _deny_listed_ids(techniques)

    assert deny_listed, "expected at least one nlu_enabled=false technique"

    failures = []
    for tid in sorted(deny_listed):
        pos, _neg = _review_stats_for_technique(technique_map, tid)
        if pos != 0:
            failures.append(
                f"{tid}: has {pos} human-confirmed positive(s) — reconsider its deny-listing"
            )

    assert not failures, "deny-list re-enable signal fired:\n" + "\n".join(failures)


def test_expected_deny_list_members_present():
    # WORKPLAN T2.1 named these as expected members of the final deny-list
    # (0 TP / many FP in reports/taxonomy_comparison.md, confirmed by review data).
    techniques = _load_techniques()
    deny_listed = _deny_listed_ids(techniques)
    expected = {
        "tech-scalable-oversight",
        "tech-voluntary-commitments",
        "tech-model-weight-security",
    }
    assert expected <= deny_listed


def test_deny_listed_techniques_exist_and_have_valid_nlu_profile():
    # Sanity: deny-listing must not corrupt the required nlu_profile fields
    # (primary_concept / semantic_anchors / entailment_hypothesis stay required
    # by the schema regardless of nlu_enabled).
    techniques = _load_techniques()
    by_id = {t["id"]: t for t in techniques if isinstance(t, dict)}
    for tid in _deny_listed_ids(techniques):
        assert tid in by_id
        profile = by_id[tid]["nlu_profile"]
        assert profile.get("primary_concept")
        assert profile.get("semantic_anchors")
        assert profile.get("entailment_hypothesis")
