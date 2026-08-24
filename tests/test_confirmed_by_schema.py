"""Tests for the tagging-tool review queue's `confirmed_by` field.

tools/tagging_tool.html now surfaces `needs_review`/`review_reason` quarantine
entries (machine abstentions written by llm_assisted_extraction._mark_abstained
and run_extraction_pipeline.apply_corroboration_rule) as an Accept/Reject queue.
Accept publishes the entry active and stamps `confirmed_by: <reviewer>` on the
map_entry, clearing needs_review/review_reason. This covers two things, same
approach as tests/test_deletion_reason_schema.py:

  1. The schema side (schema/llm-safety-v1.1.0.json's map_entry $def) accepts
     `confirmed_by` as an optional string and rejects the wrong type.
  2. The shared review predicate (scripts/eval_common.is_reviewed_document)
     treats `confirmed_by` as a human-review signal — required so an all-Accept
     review session doesn't look un-reviewed to _build_review_index /
     apply_corroboration_rule and get silently re-quarantined on the next run.

No browser/JS harness exists for the HTML tool (by design — see CLAUDE.md), so
this validates the data shape the tool now produces and the shared predicate
that shape must satisfy.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate  # noqa: E402
import eval_common as ec  # noqa: E402

jsonschema = pytest.importorskip("jsonschema")  # skip cleanly if absent

BUNDLE = validate.load_bundle()


def test_confirmed_by_present_validates():
    # acceptEntry() in tools/tagging_tool.html: active:true, needs_review/
    # review_reason removed, confirmed_by stamped with the reviewer identity.
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": True,
            "confidence": "High",
            "confirmed_by": "sashaagafonoff",
            "evidence": [{
                "text": "some passage",
                "created_by": "nlu",
                "active": True,
            }],
        }]
    }
    assert validate.validate_file(BUNDLE, entry, "model_technique_map_file") == []


def test_confirmed_by_absent_still_validates():
    # A normal (non-quarantined) entry never carries confirmed_by — schema
    # must accept its absence.
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": True,
            "evidence": [{"text": "x", "created_by": "manual"}],
        }]
    }
    assert validate.validate_file(BUNDLE, entry, "model_technique_map_file") == []


def test_confirmed_by_must_be_string():
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": True,
            "confirmed_by": 12345,  # wrong type
            "evidence": [{"text": "x", "created_by": "manual"}],
        }]
    }
    assert validate.validate_file(BUNDLE, entry, "model_technique_map_file") != []


def test_confirmed_by_marks_document_reviewed():
    # An all-Accept review session (no rejections, no new manual evidence)
    # must still register as a reviewed document — otherwise the accepted
    # entry is invisible to _build_review_index and gets re-quarantined by
    # apply_corroboration_rule on the next --regenerate.
    entries = [{
        "techniqueId": "tech-rlhf",
        "active": True,
        "confirmed_by": "manual",
        "evidence": [{"text": "some passage", "created_by": "nlu", "active": True}],
    }]
    assert ec.is_reviewed_document(entries) is True


def test_needs_review_alone_does_not_mark_reviewed():
    # A still-quarantined entry (machine-set, not yet acted on) must NOT be
    # mistaken for a reviewed document — only Accept (confirmed_by) or Reject
    # (deleted_by) count as human review.
    entries = [{
        "techniqueId": "tech-rlhf",
        "active": False,
        "needs_review": True,
        "review_reason": "single_chunk_uncorroborated",
        "evidence": [{"text": "some passage", "created_by": "nlu", "active": False}],
    }]
    assert ec.is_reviewed_document(entries) is False
