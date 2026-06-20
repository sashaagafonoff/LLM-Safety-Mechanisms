# WORKPLAN — LLM Safety Mechanisms

Consolidated, explicit backlog derived from [REFACTOR.md](REFACTOR.md) (reliability review) and
[MODEL_AUDIT.md](MODEL_AUDIT.md) (model-currency audit), plus the agreed sequencing.

**Agreed order of execution:**
1. **Model-collection update** (Section A) — _done this pass; residual items listed._
2. **Reliability-review implementation** (Section B) — _do next, **before** reprocessing data._
3. **Reprocess the data** for the updated model collection (Section C).
4. **Generative-media extension** (Section D) — _deferred; image/video models intentionally dropped for now._

Status legend: `[x]` done · `[ ]` to do · `[~]` partially done / deferred.

---

## A. Model-collection update

### A.1 Done (2026-06-19)
- [x] Added current Anthropic flagships: `claude-fable-5`, `claude-opus-4.8`, `claude-opus-4.7`, `claude-opus-4.6`.
- [x] Re-statused retired Anthropic models: `claude-3-opus` (retired 2026-01-05), `claude-3-5-sonnet` (retired 2025-10-28) — `status` changed, not deleted.
- [x] Applied the web-verified per-provider refresh from MODEL_AUDIT.md §1–§2: **44 models added**, **31 re-statused** (deprecated/retired/superseded), each carrying source URLs in a `sources[]` field.
- [x] Removed fabricated Meta ids `llama-4-8b` / `llama-4-17b`; repointed their 6 evidence references to `llama-4-scout` / `llama-4-maverick` (de-duplicated; no dangling refs).
- [x] Reverted the image-gen detour: dropped FLUX + GPT Image models, the `black-forest-labs` provider, and the `modality` field.
- [x] Captured authoritative documentation URLs (MODEL_AUDIT.md §5) onto changed/added model records.

### A.2 Deferred — id renames (do WITH the referential-integrity work, B.6)
Renaming a model `id` changes a primary key referenced by `evidence.json` and `model_technique_map.json`, so these are **held until referential-integrity validation exists** (avoid adding to the existing dangling-ref problem). From MODEL_AUDIT.md §2:
- [ ] Anthropic: dot→hyphen canonical ids (`claude-opus-4.5`→`claude-opus-4-5`, `claude-sonnet-4.5/4.6`, `claude-haiku-4.5`). _Decide whether the dataset tracks API id strings or its own slugs first._
- [ ] Alibaba: `qwen-2-5-72b`→`qwen2.5-72b-instruct`; track dated qwen ids.
- [ ] Mistral: split `ministral-3` → `ministral-3b/8b/14b-2512`; track `mistral-large-2512` (currently `mistral-large-3`).
- [ ] DeepSeek: split `deepseek-r1-distill` into specific checkpoints (or label as a family).
- [ ] Cohere: track dated ids (`command-a-03-2025`) for the bare `command-a` alias.

### A.3 Deferred — needs human confirmation (MODEL_AUDIT.md §6)
- [ ] **Candidate removals** (flagged invalid/fabricated, currently kept with a note): `gpt-5-thinking`, `qwen3-thinking`, `qwen3-turbo`, `grok-4-thinking`, `deepseek-v3-lite` (`status:"unknown"`). Confirm, then remove + repoint any refs.
- [ ] **Models with unconfirmed ids** (not added): Amazon Nova 2 Pro / Nova Multimodal Embedding, Google `gemini-3.1-pro` GA id, Mistral Medium 3.5 id, NVIDIA Nemotron 3 Super/Ultra/Content-Safety, Meta Muse Spark. Add once the exact id is confirmed on an official page.
- [ ] **Deliberately excluded, unverified** (re-check before adding): DeepSeek R2, Qwen 3.6/3.7-Max.
- [ ] Re-verify GPT-5.x / Gemini 3.x / DeepSeek V4 / Qwen 3.5 / Grok 4.x / Falcon-H1 / Hunyuan Hy3 ids against the official pages in MODEL_AUDIT.md §5 (these came from web research past the assistant's training cutoff).

---

## B. Reliability-review implementation (do before reprocessing data)

Sequenced per REFACTOR.md §8. **Phases 0–1 restore trust in the numbers; Phase 2 makes the corpus reproducible.** Each item cites its REFACTOR section.

### B.0 Phase 0 — Quick wins (DONE 2026-06-19)
All six landed with compile checks, 9 passing unit tests (`tests/test_phase0.py`), and the new integrity check reporting 0 dangling refs.
- [x] **B.0.1** Dynamic entailment-label lookup + unit test — `analyze_nlu.py` reads `id2label` via `nli_utils.resolve_entailment_index` (REFACTOR §1.3).
- [x] **B.0.2** Hard grounding gate + taxonomy-membership validation + abstain — `llm_assisted_extraction.py` quarantines ungrounded quotes / out-of-taxonomy ids (`active=False`, `needs_review`); verification failures and a new ABSTAIN verdict abstain instead of confirm (§2.2, §2.3).
- [x] **B.0.3** Per-evidence provenance + manual-preservation guard — `run_extraction_pipeline._has_manual_evidence`; `apply_deletions` never deactivates a technique with manual evidence (§2.4).
- [x] **B.0.4** Pinned NLU deps in `requirements.txt`; RNG seeding + HF `revision=` plumbing (default None — **still TODO: set actual commit SHAs**); provenance block written to `cache/pipeline_log.json` with lib versions + resolved model id + thresholds (§1.5, §2.5).
- [x] **B.0.5** Resolved all **535 dangling `techniqueId` refs** (repointed 3 synonyms in `incidents.json`; added `tech-age-verification` + `tech-supervised-fine-tuning`); de-duplicated the category-topic map into `scripts/taxonomy_maps.py`; added **`scripts/check_integrity.py`** (CI-able, exits non-zero on any orphan) (§4.2, §1.9).
- [x] **B.0.6** `expand_collections.py` now dry-run by default (writes require `--write`); LLM-sourced ids use a distinct `webllm-incident-`/`webllm-commentary-` namespace with a prefix-scoped counter (§5.6).

> Residual from Phase 0: ✅ `check_integrity.py` + `pytest` are now wired into the
> `validate.yml` CI gate (2026-06-19). ⏳ Still TODO: set real HF commit SHAs for the
> model revisions (needs a pinned NLU run).

### B.1 Phase 1 — Evaluation integrity (the central fix) — DONE 2026-06-19
Landed with 19 new unit tests (`tests/test_phase1.py`, 28 total) + CI-enforced alias
and split-freshness guards in `check_integrity.py`. Foundation modules:
`scripts/taxonomy_aliases.py`, `scripts/eval_common.py`.
- [x] **B.1.1** Frozen deterministic stratified blind split — `scripts/make_eval_split.py`
  writes `data/eval/{dev,test}_split.json`, `data/eval/split_manifest.json`,
  `data/eval_holdout_ids.json` (24 dev / 11 test, stratified by provider family,
  `--check` reproduces byte-for-byte). κ capability built (`scripts/annotator_agreement.py`)
  but **κ is not yet computable — single annotator**; honestly flagged in
  `data/eval/README.md` (§6, §3.1).
- [x] **B.1.2** Blind-test docs quarantined from `_build_review_index`
  (`load_holdout_ids`) and hard-refused by the calibrator (§2.1, §6).
- [x] **B.1.3** PR-curve threshold sweep + isotonic (PAV) confidence calibration on
  dev only — `scripts/calibrate_thresholds.py` (+ `scripts/dump_nlu_scores.py`,
  `NLUAnalyzer.score_candidates`). ⏳ The actual calibration **run** needs the ML
  stack to produce `data/eval/nlu_scores_dev.json` first; k-fold/bootstrap CIs still
  to add (§1.2, §1.6, §3.5).
- [x] **B.1.4** Authoritative blind-gold evaluator `scripts/evaluate.py` (reports on
  the held-out test split, grounded-precision, per-stage nlu/llm, sha/commit/model
  stamping); the three legacy evaluators now delegate to `eval_common`'s single
  "active technique" / "reviewed document" definitions (§3.2, §3.3, §3.7, §3.8).
- [x] **B.1.5** Taxonomy drift/alias map `scripts/taxonomy_aliases.py`; ids
  canonicalized before all set ops; alias targets CI-checked against the live
  taxonomy (§3.4).

### B.2 Phase 2 — Structural reliability (~2–4 weeks)
- [x] **B.2.1** DONE 2026-06-19 — Full JSON Schema (draft-2020-12) for all 12 datasets
  in `schema/llm-safety-v1.1.0.json` (`$defs` per record type, derived from the real
  data: required fields, type/pattern checks, and controlled-vocab enums incl. the
  `created_by` provenance enum). `scripts/validate.py` is the umbrella gate — schema
  validation **plus** referential integrity (delegated to `check_integrity.check()`,
  now an importable function) — and is wired into `.github/workflows/validate.yml`
  (installs `jsonschema`, runs `validate.py` + `pytest`, still torch-free). 7 schema
  tests in `tests/test_validate.py`; all 12 datasets validate clean (§4.1, §3.8).
- [ ] **B.2.2** Content-addressable, timestamped ingestion + full-content drift hashing, with a retained raw artifact and a reproducibility-rate metric (§5.1, §5.2).
- [ ] **B.2.3** Non-destructive, gold-tuned flat-text cleanup (sidecar removals, precision-floored thresholds, CI gold-set regression) (§5.3).
- [ ] **B.2.4** Token-budgeted, full-coverage chunking + per-technique recall reporting + minimum-anchor CI check (§1.7, §1.8).
- [ ] **B.2.5** Verification-gated, abstaining LLM ETL for `expand_collections.py` (URL fetch+confirm, two-pass agreement, pending-review queue) (§5.6).
- [ ] **B.2.6** Calibrated, measured AIID/FMTI mappings (alias resolver, sampled κ-backed precision/recall, immutable FMTI ref + checksums, header-by-name validation) (§5.4, §5.5).
- [ ] **B.2.7** Snapshot all generated datasets, CI-triggered, sha256-keyed, with field-level drift reports + alert thresholds (§5.7).

---

## C. Reprocess data for the updated model collection (after B)

- [ ] **C.1** Ingest model/system cards for the newly-added models (use the `sources[]` URLs now on each model record + MODEL_AUDIT.md §5) via `ingest_universal.py`.
- [ ] **C.2** Run the (now reliability-hardened) extraction pipeline over the new + existing corpus (`run_extraction_pipeline.py --regenerate`).
- [ ] **C.3** Evaluate against the blind gold set (B.1) and snapshot (B.2.7); report metrics with the new honest methodology.
- [ ] **C.4** Regenerate report + dashboard (`generate_report.py` → `generate_dashboard.py`).

> ⚠️ Do **not** regenerate the dashboard for any media models until Section D's modality-aware work lands (REFACTOR §7.5) — they would render as "fails every text technique."

---

## D. Generative-media extension (deferred — image/video models dropped for now)

Captured from REFACTOR.md §7 for whenever media coverage is revisited. The recommended approach is **one dataset with modality as a first-class dimension** (reject "fold flat" and "separate dataset").
- [ ] **D.1** Add structured `modality` (`{inputs, outputs}`) + `modelClass` to `models.json`; add `modalityApplicability` to `techniques.json` (§7.3.1–7.3.2).
- [ ] **D.2** Add the ~8–12 media-specific techniques; split `tech-watermarking` → provenance-C2PA + invisible-watermarking; narrow `tech-multimodal-safety-alignment` (§7.2).
- [ ] **D.3** Add `impersonation_and_likeness` (and optionally `synthetic_media_provenance`) risk areas; extend `copyright_and_ip` (§7.3.5).
- [ ] **D.4** Build a parallel set of NLU anchors + entailment hypotheses for media techniques; re-validate the extractor against media model cards (§7.4).
- [ ] **D.5** Make the dashboard modality-aware (filter facet + applicability-aware cells + modality-weighted coverage) (§7.5).
- [ ] **D.6** Re-add the image/video models (FLUX, GPT Image, etc. — see MODEL_AUDIT.md §1/§4) under the new modality schema.
