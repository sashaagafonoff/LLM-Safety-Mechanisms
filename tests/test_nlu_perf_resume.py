"""Tests for the NLU perf + resilience upgrade (2026-08).

Covers the pure-function surface of the fp16/batch-size perf change and the
per-document checkpointing / --resume-nlu resilience change:

  - analyze_nlu.should_use_fp16          — CUDA/flag dtype decision
  - run_extraction_pipeline.docs_to_process   — resume skip/merge decision
  - run_extraction_pipeline.atomic_write_json — crash-safe JSON writes
  - run_extraction_pipeline.nlu_config_drift  — resume config-drift comparison

Deliberately does NOT import sentence_transformers/torch machinery, load any
HuggingFace model, or instantiate NLUAnalyzer — everything here is exercised
through pure functions and plain files, matching the convention already used
by tests/test_corroboration.py and tests/test_phase0.py (run_extraction_pipeline
only imports anthropic/sentence-transformers lazily inside run_nlu_pass /
run_llm_pass, so importing the module itself is cheap and needs no API key).

Note: analyze_nlu.py DOES import sentence_transformers at module level (see
tests/test_nlu_denylist.py's docstring for the same tradeoff) — that import
cost is accepted here too, since should_use_fp16 itself does no model work.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import analyze_nlu as nlu  # noqa: E402
import run_extraction_pipeline as pipe  # noqa: E402


# --- analyze_nlu.should_use_fp16: dtype decision ---

def test_fp16_used_on_cuda_when_flag_true():
    assert nlu.should_use_fp16(cuda_available=True, flag=True) is True


def test_fp16_not_used_on_cuda_when_flag_false():
    # The documented escape hatch: NLU_FP16 = False must leave fp32 even on
    # a CUDA machine.
    assert nlu.should_use_fp16(cuda_available=True, flag=False) is False


def test_fp16_never_used_on_cpu_regardless_of_flag():
    # CPU always stays fp32, even if the flag is left True.
    assert nlu.should_use_fp16(cuda_available=False, flag=True) is False
    assert nlu.should_use_fp16(cuda_available=False, flag=False) is False


def test_fp16_defaults_to_module_constant():
    # should_use_fp16(cuda_available) with no explicit flag uses NLU_FP16.
    assert nlu.should_use_fp16(True) == (True and nlu.NLU_FP16)


def test_module_constants_have_expected_values():
    # Regression guard for the task's specified defaults.
    assert nlu.NLU_FP16 is True
    assert nlu.CROSS_ENCODER_BATCH_SIZE == 64


# --- run_extraction_pipeline.docs_to_process: resume skip/merge decision ---

def _paths(*stems):
    return [Path(f"data/flat_text/{s}.txt") for s in stems]


def test_fresh_run_processes_all_files_regardless_of_existing():
    # resume=False: always the full file list, even if map_nlu.json already
    # has some (presumably stale) entries on disk.
    all_files = _paths("doc-a", "doc-b", "doc-c")
    existing = {"doc-a": [], "doc-b": []}
    result = pipe.docs_to_process(all_files, existing, resume=False)
    assert result == all_files


def test_resume_skips_already_completed_documents():
    all_files = _paths("doc-a", "doc-b", "doc-c")
    existing = {"doc-a": [{"techniqueId": "tech-x"}]}
    result = pipe.docs_to_process(all_files, existing, resume=True)
    assert result == _paths("doc-b", "doc-c")


def test_resume_with_empty_existing_processes_everything():
    # Nothing has completed yet, so resume=True with {} behaves like a fresh
    # run rather than skipping everything (which would be the opposite bug).
    all_files = _paths("doc-a", "doc-b")
    result = pipe.docs_to_process(all_files, {}, resume=True)
    assert result == all_files


def test_resume_all_done_returns_empty_list():
    all_files = _paths("doc-a", "doc-b")
    existing = {"doc-a": [], "doc-b": []}
    result = pipe.docs_to_process(all_files, existing, resume=True)
    assert result == []


def test_resume_does_not_mutate_inputs():
    all_files = _paths("doc-a", "doc-b")
    existing = {"doc-a": []}
    before = list(all_files)
    pipe.docs_to_process(all_files, existing, resume=True)
    assert all_files == before


# --- run_extraction_pipeline.atomic_write_json: crash-safe writes ---

def test_atomic_write_creates_valid_json(tmp_path):
    target = tmp_path / "map_nlu.json"
    data = {"doc-1": [{"techniqueId": "tech-a"}]}

    pipe.atomic_write_json(target, data)

    assert target.exists()
    with open(target, encoding="utf-8") as f:
        assert json.load(f) == data


def test_atomic_write_leaves_no_tmp_residue(tmp_path):
    target = tmp_path / "map_nlu.json"
    pipe.atomic_write_json(target, {"a": 1})

    tmp_file = tmp_path / "map_nlu.json.tmp"
    assert not tmp_file.exists()
    # Only the final file should be present in the directory.
    assert [p.name for p in tmp_path.iterdir()] == ["map_nlu.json"]


def test_atomic_write_replaces_existing_file(tmp_path):
    target = tmp_path / "map_nlu.json"
    pipe.atomic_write_json(target, {"doc-1": ["old"]})
    pipe.atomic_write_json(target, {"doc-1": ["new"], "doc-2": ["new2"]})

    with open(target, encoding="utf-8") as f:
        result = json.load(f)
    assert result == {"doc-1": ["new"], "doc-2": ["new2"]}


def test_atomic_write_creates_parent_directories(tmp_path):
    target = tmp_path / "nested" / "dir" / "map_nlu.json"
    pipe.atomic_write_json(target, {"x": 1})
    assert target.exists()
    with open(target, encoding="utf-8") as f:
        assert json.load(f) == {"x": 1}


# --- run_extraction_pipeline.nlu_config_drift: resume config-drift compare ---

def test_no_drift_when_no_previous_config():
    # No sidecar to compare against -> "unknown", not "drift".
    current = {"fp16": True, "cross_encoder_batch_size": 64}
    assert pipe.nlu_config_drift(current, None) == []


def test_no_drift_when_configs_match():
    current = {"fp16": True, "cross_encoder_batch_size": 64, "retrieval_threshold": 0.4}
    previous = dict(current)
    assert pipe.nlu_config_drift(current, previous) == []


def test_drift_detected_on_changed_value():
    current = {"fp16": True, "cross_encoder_batch_size": 64}
    previous = {"fp16": False, "cross_encoder_batch_size": 64}
    diffs = pipe.nlu_config_drift(current, previous)
    assert len(diffs) == 1
    assert "fp16" in diffs[0]


def test_drift_detected_on_multiple_changed_values():
    current = {"fp16": True, "cross_encoder_batch_size": 64, "verification_threshold": 0.85}
    previous = {"fp16": False, "cross_encoder_batch_size": 32, "verification_threshold": 0.85}
    diffs = pipe.nlu_config_drift(current, previous)
    assert len(diffs) == 2
    joined = " ".join(diffs)
    assert "fp16" in joined and "cross_encoder_batch_size" in joined
    assert "verification_threshold" not in joined


def test_drift_detected_on_missing_key():
    # A key present in one config but not the other (e.g. added by a code
    # change) must also be reported, not silently ignored.
    current = {"fp16": True, "cross_encoder_batch_size": 64}
    previous = {"fp16": True}
    diffs = pipe.nlu_config_drift(current, previous)
    assert len(diffs) == 1
    assert "cross_encoder_batch_size" in diffs[0]
    assert "<missing>" in diffs[0]
