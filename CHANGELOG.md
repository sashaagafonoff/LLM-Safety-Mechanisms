# Changelog

All notable changes to the LLM Safety Mechanisms dataset and pipeline are documented here.
Dates are ISO 8601 (UTC).

## 2026-06-20

### Dataset
- Expanded the model collection: **70 source documents**, **102 models**, **14 providers**, **1,253 active technique-document links** across **55 active techniques** (+2 aspirational).
- Added 23 newly-verified safety sources (system cards, model cards, technical reports). Every non-Anthropic source URL was web-verified before inclusion; unverifiable models were deliberately excluded rather than guessed.
- Reprocessed the full collection through the extraction pipeline (NLU retrieval + Claude Opus 4.8 generation + merge), preserving all manual annotations.
- Ran an evidence-grounded false-positive sweep on `tech-age-verification`: deactivated 31 NLU-only detections with no substantiating age-gating/minor-protection content and pruned 6 spurious evidence passages, keeping the 3 genuinely-substantiated entries. Deactivations are recorded with `deleted_by: system` so the review index treats them as confirmed negatives.

### Evaluation & integrity
- Introduced a **blind, stratified dev/test split** (24 dev / 11 test) with a quarantined holdout to eliminate train/test leakage in evaluation (`scripts/make_eval_split.py`, `scripts/evaluate.py`, `data/eval/`).
- Held-out test metrics (reported once, final config): merged map **P 41.8% / R 78.6% / F1 54.6%**; per-stage NLU P42/R67, LLM P59/R38.
- Added a JSON Schema (`schema/llm-safety-v1.1.0.json`, draft 2020-12) and an umbrella validator (`scripts/validate.py`) covering structure, enums (incl. `created_by`/`deleted_by` provenance), and referential integrity. Wired into CI (`.github/workflows/validate.yml`).
- Added supporting tooling: shared evaluation helpers (`scripts/eval_common.py`), taxonomy alias resolution (`scripts/taxonomy_aliases.py`), threshold calibration (`scripts/calibrate_thresholds.py`), and annotator-agreement reporting (`scripts/annotator_agreement.py`).

### Pipeline
- LLM extraction now runs concurrently (`--llm-concurrency`) on Claude Opus 4.8, with the review index quarantining held-out documents to keep evaluation blind.
- Fixed a UTF-8 ingestion bug for `.md`/`.txt`/`.json` source documents.

### Documentation
- Corrected the README extraction methodology (actual NLU models `bge-large-en-v1.5` / `nli-deberta-v3-large` and thresholds) and replaced the outdated, non-blind performance table with held-out blind metrics.
- Updated `data/DATA_DICTIONARY.md` to match the enforced `model_technique_map.json` schema (`created_by`/`deleted_by`/`evidence[]` provenance).
- Regenerated `docs/SUMMARY.md`, `data/stats.json`, and the README "Dataset at a Glance".

### Fixed
- Restored the hand-maintained **Explorer dashboard** (`docs/index.html` + `docs/components/`) after a regeneration step had overwritten it with output from a legacy Plotly script. **Removed `scripts/generate_dashboard.py`** (the cause) and its call site in `scripts/check_sources.py`; documented that the dashboard is a no-build static site that fetches `data/*.json` from `main` at runtime.
