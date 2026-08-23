"""T2.3 corroboration-rule tests (2026-08 execution plan, Phase 2).

Covers `run_extraction_pipeline.apply_corroboration_rule`: an NLU-only technique
entry backed by exactly one evidence chunk is too weak to auto-publish, so it
must be quarantined (`active: False`, `needs_review: True`,
`review_reason: "single_chunk_uncorroborated"`) rather than left active — unless
it has corroborating evidence, is already inactive/quarantined, or lives in a
document a human has already reviewed.

No heavy deps required: run_extraction_pipeline only imports anthropic /
sentence-transformers lazily inside run_nlu_pass/run_llm_pass, so importing the
module here (like tests/test_phase0.py already does) needs no ANTHROPIC_API_KEY.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_extraction_pipeline as pipe  # noqa: E402


def _nlu_entry(active=True, needs_review=False):
    entry = {
        "techniqueId": "tech-example",
        "active": active,
        "evidence": [
            {"text": "a single retrieved chunk", "created_by": "nlu", "active": True}
        ],
    }
    if needs_review:
        entry["needs_review"] = True
        entry["review_reason"] = "some_prior_reason"
    return entry


def test_single_chunk_nlu_only_entry_is_quarantined():
    entry = _nlu_entry()
    entries = [entry]

    count = pipe.apply_corroboration_rule("doc-1", entries, reviewed=False)

    assert count == 1
    assert entry["active"] is False
    assert entry["needs_review"] is True
    assert entry["review_reason"] == "single_chunk_uncorroborated"
    assert entry["evidence"][0]["active"] is False
    assert "deleted_by" not in entry  # nothing rejected it — it awaits review


def test_two_chunk_nlu_entry_untouched():
    entry = {
        "techniqueId": "tech-example",
        "active": True,
        "evidence": [
            {"text": "chunk one", "created_by": "nlu", "active": True},
            {"text": "chunk two", "created_by": "nlu", "active": True},
        ],
    }
    entries = [entry]

    count = pipe.apply_corroboration_rule("doc-1", entries, reviewed=False)

    assert count == 0
    assert entry["active"] is True
    assert "needs_review" not in entry


def test_single_chunk_entry_with_llm_evidence_untouched():
    entry = {
        "techniqueId": "tech-example",
        "active": True,
        "evidence": [
            {"text": "llm-found chunk", "created_by": "llm", "active": True}
        ],
    }
    entries = [entry]

    count = pipe.apply_corroboration_rule("doc-1", entries, reviewed=False)

    assert count == 0
    assert entry["active"] is True
    assert "needs_review" not in entry


def test_single_chunk_entry_with_manual_evidence_untouched():
    entry = {
        "techniqueId": "tech-example",
        "active": True,
        "evidence": [
            {"text": "human-confirmed chunk", "created_by": "manual", "active": True}
        ],
    }
    entries = [entry]

    count = pipe.apply_corroboration_rule("doc-1", entries, reviewed=False)

    assert count == 0
    assert entry["active"] is True
    assert "needs_review" not in entry


def test_reviewed_document_untouched():
    # Otherwise-qualifying entry, but the document is human-reviewed — must
    # never be touched (this is what keeps model_technique_map_reviewed.json
    # ground truth, and any other reviewed doc, safe from re-quarantine).
    entry = _nlu_entry()
    entries = [entry]

    count = pipe.apply_corroboration_rule("doc-1", entries, reviewed=True)

    assert count == 0
    assert entry["active"] is True
    assert "needs_review" not in entry


def test_already_inactive_entry_untouched():
    entry = _nlu_entry(active=False)
    entries = [entry]

    count = pipe.apply_corroboration_rule("doc-1", entries, reviewed=False)

    assert count == 0
    assert entry["active"] is False
    assert "needs_review" not in entry


def test_already_needs_review_entry_untouched():
    entry = _nlu_entry(needs_review=True)
    entries = [entry]

    count = pipe.apply_corroboration_rule("doc-1", entries, reviewed=False)

    assert count == 0
    # Untouched means untouched — the prior reason must survive, not be
    # overwritten with "single_chunk_uncorroborated".
    assert entry["active"] is True
    assert entry["review_reason"] == "some_prior_reason"


def test_mixed_batch_only_qualifying_entry_quarantined():
    qualifying = _nlu_entry()
    corroborated = {
        "techniqueId": "tech-other",
        "active": True,
        "evidence": [
            {"text": "nlu chunk", "created_by": "nlu", "active": True},
            {"text": "llm chunk", "created_by": "llm", "active": True},
        ],
    }
    entries = [qualifying, corroborated]

    count = pipe.apply_corroboration_rule("doc-1", entries, reviewed=False)

    assert count == 1
    assert qualifying["active"] is False and qualifying["needs_review"] is True
    assert corroborated["active"] is True and "needs_review" not in corroborated
