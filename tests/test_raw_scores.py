"""Tests for T2.4 — persisting raw NLU retrieval/verification scores.

Covers:
  - nlu_evidence.build_nlu_evidence(): a pure helper (no sentence-transformers
    / torch import chain — same "no heavy dependencies" convention as
    nli_utils.py), so this stays fast and importable without triggering any
    model loads. analyze_nlu.analyze_document() calls the same function.
  - A synthetic model_technique_map entry carrying the new fields validates
    against schema/llm-safety-v1.1.0.json (reusing validate.py's machinery,
    the same approach as tests/test_validate.py).

No HuggingFace models are loaded and no NLUAnalyzer is instantiated.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nlu_evidence import build_nlu_evidence  # noqa: E402


# --- build_nlu_evidence: pure-function shape checks ---

def test_build_nlu_evidence_shape():
    ev = build_nlu_evidence("some chunk text", 0.6234567, 0.912345)
    assert ev == {
        "text": "some chunk text",
        "created_by": "nlu",
        "active": True,
        "deleted_by": None,
        "retrieval_score": 0.6235,
        "verification_score": 0.9123,
    }


def test_build_nlu_evidence_rounds_to_4dp():
    ev = build_nlu_evidence("x", 0.123456789, 0.987654321)
    assert ev["retrieval_score"] == 0.1235
    assert ev["verification_score"] == 0.9877


def test_build_nlu_evidence_accepts_numpy_like_floats():
    # Stage 1/2 scores come off tensors/numpy arrays in production
    # (`.item()` results); the helper must coerce via float() regardless
    # of the exact numeric type passed in.
    class FloatLike:
        def __init__(self, v):
            self._v = v

        def __float__(self):
            return self._v

    ev = build_nlu_evidence("x", FloatLike(0.5), FloatLike(0.9))
    assert ev["retrieval_score"] == 0.5
    assert ev["verification_score"] == 0.9


def test_build_nlu_evidence_back_compat_keys_untouched():
    # Confidence label logic lives elsewhere (analyze_document) and is
    # untouched by this helper; the helper only owns the evidence dict.
    ev = build_nlu_evidence("x", 0.5, 0.9)
    assert set(ev.keys()) == {
        "text", "created_by", "active", "deleted_by",
        "retrieval_score", "verification_score",
    }


# --- schema validation: reuse validate.py's real bundle + validator ---

import validate  # noqa: E402

jsonschema = pytest.importorskip("jsonschema")  # skip cleanly if absent

BUNDLE = validate.load_bundle()


def test_evidence_with_raw_scores_validates():
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": True,
            "confidence": "High",
            "deleted_by": None,
            "evidence": [build_nlu_evidence("chunk text", 0.6234, 0.9123)],
        }]
    }
    errs = validate.validate_file(BUNDLE, entry, "model_technique_map_file")
    assert errs == []


def test_evidence_scores_out_of_range_rejected():
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": True,
            "evidence": [{
                "text": "x",
                "created_by": "nlu",
                "retrieval_score": 1.5,  # out of [0, 1]
                "verification_score": 0.9,
            }],
        }]
    }
    errs = validate.validate_file(BUNDLE, entry, "model_technique_map_file")
    assert errs


def test_evidence_without_raw_scores_still_validates():
    # Manual/legacy evidence entries have no raw scores — must stay optional.
    entry = {
        "doc-1": [{
            "techniqueId": "tech-rlhf",
            "active": True,
            "evidence": [{"text": "x", "created_by": "manual"}],
        }]
    }
    assert validate.validate_file(BUNDLE, entry, "model_technique_map_file") == []
