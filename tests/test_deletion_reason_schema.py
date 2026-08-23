"""Tests for T3.4 — capturing `deletion_reason` on tagging-tool rejections.

The tagging tool (tools/tagging_tool.html) already soft-deletes a rejected
technique entry or evidence item (`active: false` + `deleted_by`); this
covers the schema side of also letting it carry an optional `deletion_reason`
string, which `llm_assisted_extraction._build_review_index` reads (via
`e.get("deletion_reason", "")`) to explain *why* a past detection was
rejected when building the review index's negatives.

No browser/JS harness exists for the HTML tool (by design — see CLAUDE.md),
so this validates the data shape the tool now produces: a synthetic
model_technique_map entry carrying `deletion_reason` at both the entry level
(whole technique rejected) and the evidence level (single snippet rejected),
against schema/llm-safety-v1.1.0.json, reusing validate.py's machinery — the
same approach as tests/test_validate.py and tests/test_raw_scores.py.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate  # noqa: E402

jsonschema = pytest.importorskip("jsonschema")  # skip cleanly if absent

BUNDLE = validate.load_bundle()


def test_entry_level_deletion_reason_validates():
    # Whole technique rejected (last active evidence snippet removed) —
    # tagging_tool.html's removeEvidence() sets this on the map_entry itself.
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": False,
            "confidence": "High",
            "deleted_by": "manual",
            "deletion_reason": "glossary / definition",
            "evidence": [{
                "text": "some passage",
                "created_by": "nlu",
                "active": False,
                "deleted_by": "manual",
            }],
        }]
    }
    assert validate.validate_file(BUNDLE, entry, "model_technique_map_file") == []


def test_evidence_level_deletion_reason_validates():
    # Single evidence snippet rejected while other active snippets remain —
    # removeEvidence() sets deletion_reason on that evidence item, not the entry.
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": True,
            "confidence": "High",
            "evidence": [
                {
                    "text": "kept passage",
                    "created_by": "nlu",
                    "active": True,
                },
                {
                    "text": "rejected passage",
                    "created_by": "llm",
                    "active": False,
                    "deleted_by": "manual",
                    "deletion_reason": "table-formatting artifact",
                },
            ],
        }]
    }
    assert validate.validate_file(BUNDLE, entry, "model_technique_map_file") == []


def test_deletion_reason_optional_absent_still_validates():
    # Skipping the reason prompt must not add the field at all (tool keeps
    # the JSON clean) — schema must accept its absence at both levels.
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": False,
            "deleted_by": "manual",
            "evidence": [{
                "text": "x",
                "created_by": "manual",
                "active": False,
                "deleted_by": "manual",
            }],
        }]
    }
    assert validate.validate_file(BUNDLE, entry, "model_technique_map_file") == []


def test_deletion_reason_must_be_string():
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": False,
            "deletion_reason": 12345,  # wrong type
            "evidence": [{"text": "x", "created_by": "manual"}],
        }]
    }
    assert validate.validate_file(BUNDLE, entry, "model_technique_map_file") != []
