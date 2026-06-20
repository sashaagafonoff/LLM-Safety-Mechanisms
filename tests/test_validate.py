"""Tests for the dataset schema validator (WORKPLAN B.2.1).

Exercise validate.validate_file against the REAL schema bundle with synthetic
good/bad records, so the schemas themselves are tested (not just the plumbing).
Skipped cleanly if jsonschema is not installed.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate  # noqa: E402

jsonschema = pytest.importorskip("jsonschema")  # skip whole module if absent

BUNDLE = validate.load_bundle()


def vf(data, defname):
    return validate.validate_file(BUNDLE, data, defname)


# --- the bundle covers every dataset, and the real files validate clean ---

def test_file_map_covers_defs():
    for defname in validate.FILE_MAP.values():
        assert defname in BUNDLE["$defs"], f"missing $def: {defname}"


def test_real_data_files_conform():
    import json
    for fname, defname in validate.FILE_MAP.items():
        path = validate.DATA / fname
        if not path.exists():
            continue
        data = json.load(open(path, encoding="utf-8"))
        assert vf(data, defname) == [], f"{fname} should validate clean"


# --- positive/negative record cases ---

def test_provider_good_and_bad():
    assert vf([{"id": "openai", "name": "OpenAI", "type": "commercial",
               "headquarters": "USA"}], "providers_file") == []
    # bad enum value for type
    errs = vf([{"id": "x", "name": "X", "type": "startup", "headquarters": "USA"}],
              "providers_file")
    assert errs and any("type" in e or "startup" in e for e in errs)
    # unknown property rejected (additionalProperties: false)
    errs = vf([{"id": "x", "name": "X", "type": "commercial",
               "headquarters": "USA", "bogus": 1}], "providers_file")
    assert errs


def test_model_status_enum():
    assert vf({"models": [{"id": "m1", "family": "f", "provider": "openai",
              "status": "active", "version": "1", "notes": ""}]}, "models_file") == []
    errs = vf({"models": [{"id": "m1", "family": "f", "provider": "openai",
              "status": "sunset", "version": "1", "notes": ""}]}, "models_file")
    assert errs


def test_created_by_enum_enforced():
    # the headline B.2.1 deliverable: provenance enum on technique-map evidence
    good = {"doc": [{"techniqueId": "tech-rlhf", "active": True,
            "evidence": [{"text": "x", "created_by": "nlu"}]}]}
    assert vf(good, "model_technique_map_file") == []
    bad = {"doc": [{"techniqueId": "tech-rlhf", "active": True,
           "evidence": [{"text": "x", "created_by": "robot"}]}]}
    errs = vf(bad, "model_technique_map_file")
    assert errs and any("created_by" in e or "robot" in e for e in errs)


def test_technique_id_pattern_and_required():
    good = {"id": "tech-rlhf", "name": "RLHF", "description": "d",
            "categoryId": "cat-model-development", "riskAreaIds": [],
            "lifecycleStages": ["training"],
            "nlu_profile": {"primary_concept": "c", "semantic_anchors": ["a"],
                            "entailment_hypothesis": "h"}}
    assert vf([good], "techniques_file") == []
    bad_id = {**good, "id": "rlhf"}  # missing tech- prefix
    assert vf([bad_id], "techniques_file")
    no_profile = {k: v for k, v in good.items() if k != "nlu_profile"}
    assert vf([no_profile], "techniques_file")


def test_incident_severity_enum_and_types():
    base = {"id": "i1", "aiidIncidentId": 1, "aiidUrl": "https://x", "date": "2026",
            "title": "t", "description": "d", "severity": "high", "status": "confirmed",
            "isLLMRelated": True, "providerIds": [], "modelIds": [], "riskAreaIds": [],
            "techniqueIds": [], "sources": []}
    assert vf([base], "incidents_file") == []
    assert vf([{**base, "severity": "critical"}], "incidents_file")
    assert vf([{**base, "aiidIncidentId": "1"}], "incidents_file")  # wrong type
