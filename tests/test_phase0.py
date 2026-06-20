"""Phase 0 reliability-hardening tests (no heavy ML deps required).

Covers the dependency-free logic introduced by the Phase 0 quick wins:
  - nli_utils.resolve_entailment_index (B.0.1)
  - taxonomy_maps.CATEGORY_TO_TOPIC (B.0.5 / §1.9)
  - run_extraction_pipeline._has_manual_evidence (B.0.3)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from nli_utils import resolve_entailment_index
from taxonomy_maps import CATEGORY_TO_TOPIC, assert_categories_mapped
import run_extraction_pipeline as pipe


# --- B.0.1: entailment index resolution ---

def test_resolve_entailment_index_standard():
    assert resolve_entailment_index({0: "contradiction", 1: "entailment", 2: "neutral"}) == 1


def test_resolve_entailment_index_reordered():
    assert resolve_entailment_index({0: "entailment", 1: "neutral", 2: "contradiction"}) == 0


def test_resolve_entailment_index_case_and_whitespace():
    assert resolve_entailment_index({0: "Contradiction", 1: " ENTAILMENT "}) == 1


def test_resolve_entailment_index_missing_defaults():
    assert resolve_entailment_index({0: "a", 1: "b"}) == 1
    assert resolve_entailment_index(None) == 1
    assert resolve_entailment_index({}) == 1
    assert resolve_entailment_index(None, default=2) == 2


# --- B.0.5 / §1.9: single category->topic map ---

def test_category_topic_map_complete():
    expected = {"cat-model-development", "cat-evaluation", "cat-runtime-safety",
                "cat-harm-classification", "cat-governance"}
    assert set(CATEGORY_TO_TOPIC) == expected
    assert assert_categories_mapped(expected) == []
    assert assert_categories_mapped(["cat-unknown"]) == ["cat-unknown"]


# --- B.0.3: per-evidence manual detection ---

def test_has_manual_evidence_any_position():
    tech = {"evidence": [{"created_by": "nlu"}, {"created_by": "manual"}]}
    assert pipe._has_manual_evidence(tech) is True


def test_has_manual_evidence_sashaagafonoff():
    assert pipe._has_manual_evidence({"evidence": [{"created_by": "sashaagafonoff"}]}) is True


def test_has_manual_evidence_string_form():
    assert pipe._has_manual_evidence({"evidence": ["Manual annotation"]}) is True


def test_has_manual_evidence_negative():
    assert pipe._has_manual_evidence({"evidence": [{"created_by": "nlu"}, {"created_by": "llm"}]}) is False
    assert pipe._has_manual_evidence({"evidence": []}) is False
    assert pipe._has_manual_evidence({}) is False
