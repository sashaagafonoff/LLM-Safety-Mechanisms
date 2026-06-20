# REFACTOR.md — Reliability Assessment of the Dataset-Extraction Approach

## Scope and what was reviewed

This document assesses the **methodological reliability** of the automated extraction pipeline that builds the LLM-Safety-Mechanisms dataset, and proposes concrete, codebase-specific methodologies to make its quality claims defensible. It then analyses the impact of extending the dataset beyond text LLMs to **image/video (generative-media) models**.

The assessment is grounded in subsystem reviews of five areas, all under `d:\LLM Safety Mechanisms`:

1. **NLU retrieval + verification** — `scripts/analyze_nlu.py`, `scripts/robust_tokenizer.py`, `scripts/semantic_retriever.py`, `scripts/clean_flat_text.py`, driven by `nlu_profile` fields in `data/techniques.json`.
2. **Two-pass LLM RAG extraction** — `scripts/llm_assisted_extraction.py`, `scripts/run_extraction_pipeline.py`.
3. **Evaluation integrity** — `scripts/evaluate_nlu.py`, `scripts/compare_taxonomy_runs.py`, `scripts/ground_truth_analysis.py`.
4. **Data model & validation** — `schema/llm-safety-v1.1.0.json`, `data/*.json`, `.github/workflows/process-review.yml`, `.github/scripts/update_technique_map.py`.
5. **Ingestion & reproducibility** — `scripts/ingest_universal.py`, `scripts/check_sources.py`, `scripts/clean_flat_text.py`, `scripts/ingest_aiid.py`, `scripts/ingest_fmti.py`, `scripts/expand_collections.py`, `scripts/snapshot.py`.

The single most consequential finding, recurring across **four** of the five subsystems, is **train/test leakage**: the manually-reviewed corpus is simultaneously used to (a) hand-tune thresholds, (b) seed the LLM verification pass's few-shot examples, and (c) define the ground truth the system is scored against. As a result the reported precision/recall/F1 measure in-sample fit, not generalization, and the per-record High/Medium/Low confidence labels are not calibrated. Secondary findings concern uncalibrated thresholds, brittle heuristics, missing reproducibility controls, silent failure-to-confirm defaults, an empty schema stub with no CI validation, and non-reproducible ingestion.

The dataset is not worthless — the pipeline is a competent two-stage bi-encoder/cross-encoder RAG retriever plus a two-pass LLM verifier — but its **trust labels and quoted metrics are not defensible as calibrated measures** until the items below are addressed.

---

## Executive summary — prioritized methodologies

| # | Methodology | Problem it fixes | Subsystem | Effort | Reliability impact |
|---|-------------|------------------|-----------|--------|--------------------|
| 1 | **Frozen, blind held-out gold split** (`data/eval/test_split.json` / `data/gold/`, never read by the review-index or threshold tuner) | CRITICAL train/test leakage across NLU, LLM, and evaluation; circular ground truth | NLU, LLM, Eval, Data model | M | Highest — converts in-sample fit into a real generalization estimate |
| 2 | **Independent blind annotation + inter-annotator kappa** for the gold set | Ground truth is the extractor's own kept output (261/379 active reviewed entries are nlu/llm-only); recall is bounded by unaided human recall | Eval | M | High — makes recall meaningful, not a "review-retention rate" |
| 3 | **Hard grounding gate on quotes** (drop/quarantine when `find_exact_passage` returns None; calibrated fuzzy threshold) | Fuzzy matcher silently substitutes unrelated sentences and keeps unverified LLM quotes | LLM | S | High — eliminates hallucinated/misattributed evidence text |
| 4 | **Abstention instead of confirm-on-failure** + taxonomy-membership validation of `techniqueId` | Verification pass and parse failures default to CONFIRM; hallucinated IDs survive and re-seed the review index | LLM | S | High — stops FP/hallucination accumulation |
| 5 | **Per-evidence provenance + manual-preservation guard** in the merge step | `partition_by_source` uses `evidence[0]` only; LLM deletions can deactivate human-confirmed techniques | LLM (pipeline) | S | High — protects the ground truth itself |
| 6 | **Schema (draft-2020-12) + referential-integrity CI gate** | Empty schema stub; 535 dangling techniqueId refs; no validation before commit | Data model | M | High — malformed/orphan records can't reach published analysis |
| 7 | **PR-curve threshold calibration + probability calibration** (isotonic/Platt) on the dev split | 0.40 / 0.85 are hand-tuned magic numbers; confidence is a stack of additive constants; confidence is "High" on 1056/1063 entries | NLU, Eval, Data model | M | High — operating point and confidence bands become evidence-based |
| 8 | **Dynamic entailment-label lookup + CI unit test** | `entailment_idx=1` hard-coded without reading `id2label` | NLU | S | High — guards against silently thresholding the wrong NLI class |
| 9 | **Content-addressable, timestamped ingestion** (sha256 of raw + cleaned text, `retrieved_at`, retained raw artifact) | No content hash/timestamp/raw artifact; corpus can't be regenerated or verified | Ingestion | M | High — makes the evidentiary corpus auditable |
| 10 | **Verification-gated, abstaining LLM ETL** for `expand_collections.py` (fetch+confirm URLs, distinct ID namespace, dry-run default) | Auto-ingests unverified web-search output marked `confirmed`; ID collision with 1365 `aiid-*` records | Ingestion | M | High — stops hallucinated incidents corrupting canonical datasets |
| 11 | **Non-destructive, gold-tuned flat-text cleanup** (sidecar removals, precision-floored thresholds) | Irreversible regex cleanup with eyeballed thresholds can delete safety-relevant prose undetectably | Ingestion / NLU | M | Medium — recovers hidden recall loss |
| 12 | **Token-budgeted chunking** with full-coverage windows | Fixed 3-sentence/stride-2 windows have no token cap; long sentences truncated, trailing sentences dropped | NLU | S | Medium — removes position-dependent recall gaps |
| 13 | **Version/seed pinning + provenance block** (torch/sentence-transformers/transformers pins, HF `revision=`, model SHA recorded per row) | Unpinned, commented-out heavy deps; floating `sonnet`/`opus` aliases; no recorded model id | NLU, LLM, Ingestion | S | Medium — bit-level reproducibility and drift attribution |
| 14 | **Per-technique recall reporting + minimum-anchor CI check** | `nlu_profile` anchor count varies ~6x (4→25); aggregate metric hides per-technique gaps | NLU, Data model | S | Medium — exposes uneven taxonomy coverage |
| 15 | **Single authoritative evaluator + drift/alias map + bootstrap CIs** | Three mutually-inconsistent evaluators; no taxonomy-drift handling despite docstring claim; point estimates on n=8–37 docs | Eval | M | Medium — comparable, honest metrics over time |
| 16 | **Snapshot all generated datasets, CI-triggered, sha256-keyed** | `snapshot.py` versions only `model_technique_map.json`, manually, one data point | Ingestion | S | Medium — longitudinal drift becomes diffable |

Effort: S = days, M = a week-plus. Severities below are the reviewers' own labels.

---

## 1. NLU retrieval + verification (`analyze_nlu.py`, `robust_tokenizer.py`, `semantic_retriever.py`)

The NLU stage is a two-stage bi-encoder retriever (bge-large-en-v1.5) over `semantic_anchors` followed by cross-encoder entailment verification (nli-deberta-v3-large) of each technique's `entailment_hypothesis`. It is competent, but its reliability claims rest on uncalibrated, hand-tuned thresholds evaluated on the same documents used to tune them.

### 1.1 No train/test isolation — thresholds tuned on the evaluation set (CRITICAL)

`RETRIEVAL_THRESHOLD = 0.40` (`analyze_nlu.py:41`, comment *"Raised from 0.35 to reduce FPs with bge-large"*) and `VERIFICATION_THRESHOLD = 0.85` (`analyze_nlu.py:45`, comment *"Raised from 0.65; large cross-encoder needs higher bar"*) were hand-adjusted in response to observed false positives. `evaluate_nlu.py:37-79` (`load_ground_truth`) and `ground_truth_analysis.py:26-46` (`is_reviewed_document`) define ground truth as the manually-reviewed documents — and 37 of 41 documents in `data/model_technique_map.json` carry manual evidence or human deletions. The thresholds were thus fitted on essentially the whole evaluation corpus; reported P/R/F1 measure in-sample fit.

**Methodology.** Split the reviewed corpus into a calibration (dev) set and a held-out test set at document level (e.g. 60/40, stratified by category and by the `no_safety_content` flag). Tune both thresholds **and** the confidence constants only on dev; report P/R/F1 once on the untouched test split. Because n≈37 is small, use leave-one-document-out or k-fold CV and report mean ± std. Freeze the test split in a committed `data/eval/test_split.json` so it cannot leak into future tuning. (See §3 and the dedicated leakage subsection for the cross-subsystem version of this.)

### 1.2 Thresholds are scalar magic numbers, never PR-calibrated (high)

Both thresholds are single global constants applied uniformly across all techniques and documents (used at `analyze_nlu.py:291` for retrieval, `:319` for verification). No script sweeps thresholds, plots a precision-recall curve, or selects an operating point by a stated objective. A global 0.85 verification cutoff is especially questionable because cross-encoder entailment scores are not calibrated probabilities and their distribution shifts with hypothesis phrasing.

**Methodology.** Add a calibration script that records, on the dev split, every `(retrieval_score, entailment_score, is_true_positive)` triple, sweeps thresholds to produce PR curves, and selects operating points by an explicit objective (max F1, or precision ≥ X). Consider per-category or per-technique thresholds since anchor richness and base rates vary. Report the selected thresholds with the dev F1/precision they achieve and confirm on test.

### 1.3 Entailment label index hard-coded without verifying label order (high)

At `analyze_nlu.py:312-313` the code calls `self.verifier.predict(pairs, apply_softmax=True)`, sets `entailment_idx = 1`, and reads `score_dist[1]` as the entailment probability (`:320`). The label order of `cross-encoder/nli-deberta-v3-large` is a property of the checkpoint's `id2label` config, not a guaranteed convention. If index 1 is not the entailment class, the entire `VERIFICATION_THRESHOLD=0.85` gate is thresholding the wrong class, and the "tuning" silently compensated for a mislabel.

**Methodology.** Read the entailment index dynamically: locate the key whose `label.lower() == 'entailment'` in `self.verifier.model.config.id2label` and assert it equals the index used. Add a CI unit test with a known-entailing and a known-contradicting pair asserting the entailing pair scores higher.

### 1.4 False-positive heuristics are brittle substring filters with self-canceling logic (high)

`_is_low_quality_match` (`analyze_nlu.py:142-206`) relies on raw lowercase substring membership:
- The glossary check inspects only `text_lower[:100]` (`:154`), so a trigger word after char 100 is missed.
- The future-work list (`:158-163`) is negation-blind: *"we do not plan to abandon RLHF"* is wrongly filtered.
- The comparative filter (`:167-185`) is gated by `has_implementation` built from generic verbs like `achieves`/`performs` (`:180`), so any chunk containing "achieves" — near-ubiquitous in benchmark prose — defeats the `unlike`/`compared to` filter, making it rarely fire.
- The Access Control special-case (`:198-201`) hard-filters any chunk containing the stems `refus`/`declin`/`answer`/`abstain` for that one technique, suppressing legitimate access-control evidence about refusal behavior.

**Methodology.** Replace substring heuristics with a small supervised classifier, or run an "implemented vs. mention/future/contrast" hypothesis through the same cross-encoder, calibrated on labeled dev chunks. At minimum: scope the glossary check to the chunk's section header rather than the first 100 chars; add negation handling (a negation-cue list or dependency parse); remove generic verbs from `implementation_keywords`. Measure each filter's precision/recall contribution by ablation on the dev split before keeping it.

### 1.5 No determinism controls or version/revision pinning (medium)

A grep across `scripts/` for `seed|torch.manual|random_state|deterministic|revision=` returns no matches. Models are loaded by name only (`analyze_nlu.py:40,44`; `semantic_retriever.py:15`) with no HuggingFace `revision`/commit pin, so an upstream re-upload silently changes scores. `requirements.txt` leaves `sentence-transformers>=2.2.0` and `torch>=2.0.0` commented out and unpinned — the heavy deps that determine every score are not part of the reproducible environment.

**Methodology.** Pin exact versions of `sentence-transformers`, `torch`, and `transformers` and move them out of the commented block; pass `revision='<commit-sha>'` to both `SentenceTransformer` and `CrossEncoder` loads; call `torch.manual_seed(...)` and `torch.use_deterministic_algorithms(True)`; write a provenance block (model SHAs, library versions, thresholds) alongside `data/model_technique_map.json`. Add a CI check that re-running on a fixed sample reproduces stored scores within tolerance.

### 1.6 Confidence scoring is a stack of unvalidated additive constants (medium)

Per-detection confidence (`analyze_nlu.py:331-371`) starts from the entailment score, then adds hand-picked constants: +0.05 implementation language (`:345`), ±0.03 `signal_strength` (`:348-351`), ±0.02 `technical_depth` (`:354-357`), +0.02/−0.03 `temporal_focus` (`:360-363`), bucketed into High/Medium/Low at 0.85/0.70 (`:366-371`). Several inputs are themselves human-assigned `content_metadata` in `evidence.json`, so the label partly reflects an annotator's prior. The bucket cutoffs are unrelated to the verification threshold's calibration.

**Methodology.** Calibrate confidence to empirical correctness: on the dev split, bin detections by raw entailment score and measure observed precision per bin (reliability diagram); fit isotonic or Platt scaling so "High" means a measured precision target (e.g. ≥0.90). Treat the metadata bonuses as features in a small logistic model fit to TP/FP labels rather than fixed constants, and report each feature's measured contribution.

### 1.7 Fixed-window chunking has no token cap and drops trailing sentences (medium)

Chunks are 3 sentences with stride 2 (`analyze_nlu.py:48-49`), built by `create_chunks` (`robust_tokenizer.py:229-265`) with no character/token budget. Three long sentences can exceed bge-large's 512-token limit and the NLI input window, silently truncating the tail. The loop at `robust_tokenizer.py:254` breaks when `i+window_size>=len` (`:262`), so the final 1–2 sentences can fall outside any full window; very short documents may yield zero chunks (handled as no detections at `analyze_nlu.py:250`).

**Methodology.** Add an explicit token budget to `create_chunks`: tokenize with the retriever's own tokenizer and split/limit so no chunk exceeds (model `max_seq_length` minus special tokens); log a warning on truncation. Use overlapping windows that guarantee every sentence appears in ≥1 full window (pad the final window). Add a unit test feeding 3 long sentences asserting no chunk exceeds the model token limit.

### 1.8 `nlu_profile` quality varies ~6x, hiding per-technique recall gaps (medium)

Retrieval recall depends entirely on a technique's `nlu_profile.semantic_anchors` and `primary_concept` (`analyze_nlu.py:221`, `semantic_retriever.py:80`). Across 55 techniques the anchor count ranges from 4 (Machine Unlearning, Data Sovereignty Controls, Circuit Breakers/Kill Switches, Enterprise Integration Safety) to 25 (Weapons & Illegal Activity Detection), median 8. Thinly-anchored techniques present a smaller embedding target, so their recall at a fixed 0.40 cutoff is structurally lower — yet only a single corpus-wide recall is reported. Two hypotheses still use the generic `The model uses {name}` template (fallback at `analyze_nlu.py:217`).

**Methodology.** Report recall **per technique** on the dev split and flag techniques below a recall floor for anchor enrichment. Standardize a minimum anchor count and a non-template `entailment_hypothesis` per technique; measure the marginal recall gain of each added anchor so enrichment is evidence-driven. Add a schema-validated CI check rejecting techniques with fewer than the minimum anchors or a default-template hypothesis.

### 1.9 Category-to-topic exclusion map is fragile string coupling (low)

Metadata-aware filtering depends on a hard-coded `category_to_topic_map` (`analyze_nlu.py:273-279`, duplicated in `semantic_retriever.py:154-160`) mapping `cat-evaluation` → `cat_evaluation` to match `excluded_topics` in `evidence.json`. The comment at `analyze_nlu.py:272` reveals a taxonomy migration; a new category id or renamed topic makes `.get()` return None and the technique is never excluded (`:284-287`), silently reverting to no filtering. The dict is duplicated across two files that can drift.

**Methodology.** Derive the category↔topic mapping from a single committed source of truth (e.g. a field on `categories.json`); add a startup/CI assertion that every `categoryId` has a mapping and every `excluded_topics` value is a known topic, failing loudly on mismatch. De-duplicate the dict into one shared module imported by both files.

---

## 2. Two-pass LLM RAG extraction (`llm_assisted_extraction.py`, `run_extraction_pipeline.py`)

A Pass-1 extraction call proposes techniques with verbatim quotes; a Pass-2 verification call confirms/rejects them, conditioned on few-shot examples drawn from the reviewed corpus. The pipeline merges results while "always preserving" manual annotations. It has one critical and several high-severity defects.

### 2.1 CRITICAL leakage — Pass-2 review index and the eval ground truth are the same entries (CRITICAL)

`_build_review_index` (`llm_assisted_extraction.py:377-448`) reads `data/model_technique_map.json` and treats a document as a source of confirmed positives / rejected negatives when it has evidence `created_by ∈ {manual, sashaagafonoff}` or a human deletion (`deleted_by ∉ {None, system}`) — `:404-409`. `evaluate_nlu.py:load_ground_truth` (`:54-77`) and `ground_truth_analysis.py:is_reviewed_document` (`:26-46`) use the **identical predicate on the same file**. The only isolation is per-document: `_build_verification_sections` excludes the current `doc_id` (`:565-567`) and `_verify_candidates` requires `has_external` from a different doc (`:607-609`). That prevents a document from grading itself but **not cross-document leakage**: when scoring reviewed doc A, the verifier for A was conditioned on reviewed docs B, C, D… which are themselves gold-labelled. Reported metrics are an upward-biased resubstitution estimate, and the bias **grows** as the review index accumulates.

**Methodology.** Add an exclusion-set parameter to `_build_review_index` so it skips any `doc_id` in a frozen `data/eval_holdout_ids.json`. Evaluators score only holdout docs; the review index is built only from the train split. For headroom, k-fold over the reviewed pool (build the index from the other folds, evaluate on the held fold). Persist the split so re-runs are comparable.

### 2.2 Verbatim-quote grounding silently defeated by the fuzzy matcher (high)

The prompt demands a verbatim quote and "be conservative" (`:184,256`), but `extract_techniques` (`:766-787`) passes the LLM quote through `find_exact_passage` (`:81-144`). With no exact substring match it falls back to keyword/`SequenceMatcher` scoring and **accepts any source sentence scoring > 0.4 with ≥2 keyword overlaps** (`:127-142`) — low enough to attach an unrelated sentence. Critically, when `find_exact_passage` returns None, `final_evidence = exact_quote if exact_quote else llm_evidence` (`:771`) keeps the **unverified** LLM quote and still records the addition. Grounding never gates inclusion; it only optionally rewrites. The `llm_original` field (`:784`) records the swap but nothing acts on it.

**Methodology.** Make grounding a **hard gate**: if `find_exact_passage` returns None, drop the candidate or mark `grounding_failed=True` / `active=False` until a human confirms. Replace the 0.4 score with a threshold chosen from a PR curve on labelled `(llm_quote, true_in_source)` pairs, targeting a fixed max false-attach rate. Store a normalized character offset of the matched span for downstream re-verification.

### 2.3 Verification and parse failures both default to CONFIRM / pass-through (high)

`VERIFICATION_PROMPT` instructs "When uncertain, CONFIRM" (`:305`). In code every failure also keeps the candidate: `verdict_map.get(tid, 'confirm')` defaults missing verdicts to confirm (`:651`); a None from `_parse_json_response` passes the whole batch through (`:636-638`); API/generic exceptions pass all candidates through (`:669-675`). Nothing validates that `match.get('techniqueId')` (`:754`) is a real taxonomy ID — a hallucinated `tech-self-reflection` is added as a real link, and `tech_names.get(tech_id, tech_id)` (`:546`) silently falls back to the raw id. Because the same file seeds the review index, a hallucinated technique can become a "confirmed positive" feeding future passes.

**Methodology.** Validate `techniqueId` against the loaded taxonomy at the addition site (`:754`) and quarantine unknowns. Replace blanket confirm-on-failure with explicit abstention: on parse/API failure, mark candidates `needs_review` (`active=False`). Add agreement-based confidence (require Pass-1 confidence and Pass-2 verdict to agree; route disagreements to a human queue), optionally a two-prompt/two-call ensemble.

### 2.4 Merge step can misroute manual annotations via `evidence[0]`-only detection (high)

`partition_by_source` (`run_extraction_pipeline.py:82-120`) decides provenance from `evidence[0].created_by` only (`:101-114`). An entry with manual evidence at index 1 but NLU/LLM evidence at index 0 is classified `nlu`/`llm` and loses its "always preserved" protection (`merge_all_results` step 1, `:337-340`). `merge_technique_lists` (`:123-159`) dedups by `techniqueId` and appends evidence (`:148-154`), so manual provenance can be buried behind an NLU `evidence[0]`, flipping its partition on the next run. `apply_deletions` (`:162-183`) deactivates by `techniqueId` for any LLM deletion — including a merged entry that now carries manual evidence, so **an LLM deletion can deactivate a human-confirmed technique**. The docstring's central guarantee ("Manual annotations are always preserved", `:21`) is not robust.

**Methodology.** Classify provenance per-evidence: an entry is `manual` if **any** evidence has `created_by ∈ {manual, sashaagafonoff}`. In `apply_deletions`, never deactivate a technique whose entry contains manual evidence. Keep manual and machine evidence in separate sub-lists (or tag each evidence with an immutable source) so merges cannot bury provenance. Add a CI regression guard asserting every manual entry present before a run is still active and still classified manual after it.

### 2.5 Inconsistent model pinning; resolved model id never recorded (medium)

`MODEL_MAP` (`:74-79`) date-pins only `haiku` (`claude-haiku-4-5-20251001`) and `sonnet-legacy`; `sonnet`→`claude-sonnet-4-6` and `opus`→`claude-opus-4-6` are floating aliases that resolve server-side at call time. The two scripts disagree on the default (`llm_assisted_extraction.py:313,1005` default `sonnet`; `run_extraction_pipeline.py:250` defaults `haiku`, CLI overrides to `sonnet` at `:439`). The resolved model string is never written to `model_technique_map.json` or `save_pipeline_log` (`:402-412` logs only stats).

**Methodology.** Pin every `MODEL_MAP` entry to a dated snapshot and reconcile the two defaults. Record the resolved model id (and prompt hash) into each evidence entry and `pipeline_log.json`. Add a drift check that re-runs a fixed sample on the pinned model and alerts on output change; re-evaluate metrics whenever a pinned id is bumped.

### 2.6 JSON parsing relies on greedy regex; truncation undetected (medium)

`_parse_json_response` (`:495-532`) falls back to `re.search(r'\[[\s\S]*\]', content)` (`:519`), a greedy first-`[`-to-last-`]` match that can capture prose brackets or nested/broken spans; on `JSONDecodeError` it returns None and the document yields zero techniques (`:744-747`) with no retry. `max_tokens=4096` (extraction, `:732`) and `2048` (verification, `:628`) can truncate a long array; there is no `stop_reason=='max_tokens'` check, no schema validation, no repair.

**Methodology.** Inspect `response.stop_reason` and retry with higher `max_tokens` (or "continue") on truncation. Validate each parsed object against a schema (`techniqueId` in taxonomy, `confidence ∈ {High,Medium,Low}`, `evidence` is str), dropping/flagging non-conforming items rather than the whole array. On parse failure retry once with a strict "JSON only" reminder, and record `parse_failed` per doc so evaluators exclude rather than count zero. Prefer the SDK's structured/tool-output mode over regex extraction.

---

## 3. Evaluation integrity (`evaluate_nlu.py`, `compare_taxonomy_runs.py`, `ground_truth_analysis.py`)

There are **three overlapping, mutually inconsistent evaluators** computing P/R/F1 three different ways against three different "ground truths", with no statement of which is authoritative.

### 3.1 Circular ground truth — labels are the extractor's own kept output (CRITICAL)

`classify_techniques` (`ground_truth_analysis.py:49-92`) defines TP as "created by nlu/llm AND still active" and FP as "created by nlu/llm AND deleted". The ground truth is therefore derived **from** the extractor's output: a technique is "correct" precisely when the extractor emitted it and a reviewer did not delete it. FN is only counted when a human added a technique with no prior nlu/llm/legacy evidence (`:88-90`). Empirically, in `model_technique_map_reviewed.json`, **261 of 379 active entries are nlu/llm-only** (no manual confirmation), 83 manual-only, 35 both — so the dominant positive label *is* the extractor signal. Recall is structurally inflated because the FN universe is bounded by unaided human recall.

**Methodology.** Build an **independent gold set** by **blind annotation**: annotators label a held-out sample for technique presence using only `techniques.json` definitions, without seeing pipeline output. Freeze it. Measure inter-annotator agreement (Cohen's/Fleiss' κ) on a double-annotated subset to bound label noise. Exclude any document whose extractor output was shown to reviewers from the evaluation split. Report recall against this blind gold set, and rename the current metric "review-retention rate" — it is not recall.

### 3.2 Three evaluators disagree; none declared authoritative (high)

(1) `evaluate_nlu.py` **re-runs** a live `NLUAnalyzer` and uniquely excludes `no_safety_data` docs (`:106-117,162-181`); (2) `ground_truth_analysis.py` never runs a model, infers TP/FP/FN from `active`/`deleted_by` flags (`:49-92`), and does not exclude no-safety docs; (3) `compare_taxonomy_runs.py` diffs two static files with yet another active-detection rule (`extract_active_techniques:44-68`, with an `or not evidence` fallback at `:66` that counts all-deleted-evidence entries as active). Doc-set sizes differ (35 reviewed / 41 auto / 37 "reviewed"). Three different numbers, none canonical.

**Methodology.** Designate one evaluator (the blind-gold evaluator from §3.1) authoritative; demote the others to clearly-labelled diagnostics. Unify the "active technique" definition into one shared imported function so TP/FP/FN are identical everywhere. Emit metrics to a versioned JSON artifact stamped with input file hashes and git commit, not console-only.

### 3.3 NLU and LLM stages are conflated; neither measured in isolation (high)

Despite the filename, `evaluate_nlu.py` mixes stages: `ground_truth_analysis.py:76` buckets `nlu`/`llm`/`legacy` together; `compare_taxonomy_runs.py`'s per-source table (`:71-90`) measures self-recovery/stability, not standalone LLM precision; `evaluate_nlu.py` runs only the NLU analyzer (`:120,94-96`) but compares against a map whose active set was shaped by LLM and manual additions. No script evaluates the LLM stage alone or isolates pure NLU precision against independent labels.

**Methodology.** Evaluate each stage against the blind gold set independently: (a) NLU-only vs gold, (b) LLM-only vs gold (feed the raw document, not NLU candidates), (c) combined pipeline. Report a contribution breakdown (found only by NLU, only by LLM, by both). If pipelined, report conditional metrics (LLM precision given NLU recall) so error propagation is visible.

### 3.4 Claimed taxonomy-drift handling is not implemented (high)

`compare_taxonomy_runs.py:8` claims it "Accounts for technique merges, renames, and removals", but `compare()` (`:93-189`) does plain set ops on raw `techniqueId` strings (`tp/fp/fn` at `:127-129`) with no alias map. `techniques.json` has **no** `replaced_by`/`alias`/`deprecated`/`merged_into` fields. A renamed ID is double-counted as one FP + one FN; removed techniques inflate FN; the "lowest-F1" table (`:277`) is dominated by renamed/merged IDs.

**Methodology.** Add an explicit migration map (`old_id → new_id`, plus a "removed" set) sourced from `techniques.json` status fields and a maintained crosswalk; canonicalize both GT and automated IDs through it **before** the set ops at `:127-129`. Add a drift report listing GT IDs absent from current `techniques.json` (removed) and orphans, excluding removed techniques from FN. Validate every `techniqueId` in CI so an unmapped ID fails fast instead of becoming an FP+FN pair.

### 3.5 No confidence intervals; tiny samples reported as point estimates (medium)

All three scripts micro-average (sum TP/FP/FN, divide once: `ground_truth_analysis.py:161-163`; `evaluate_nlu.py:169-175`; `compare_taxonomy_runs.py:213-216`). No CIs, no macro-average, no per-document variance, no sample-size caveat. The evaluable set is tiny (35–37 docs, single-digit per-doc counts); the "15 lowest-F1 techniques" ranking (`:281`) often runs on 1–2 observations. `f1()` uses `max(0.001, p+r)` as a denominator guard (`:201`), silently producing a tiny non-zero F1 for degenerate cells.

**Methodology.** Report both micro and macro averages with 95% bootstrap CIs over documents (resample docs with replacement, recompute, take 2.5/97.5 percentiles). For per-technique tables, suppress techniques below a minimum support (e.g. total < 5) and show Wilson intervals. Print the evaluable-doc count and a small-sample banner below a threshold. Replace the `max(0.001, …)` guard with explicit NaN/None when `p+r==0` so degenerate cells are visible.

### 3.6 Pipeline confidence is effectively constant — no thresholding possible (medium)

The `confidence` field is "High" on **1056 of 1063** entries (7 Medium, 0 Low, 0 numeric). None of the three evaluators reads it — TP/FP/FN are hard booleans. There is no PR curve, no threshold selection, no abstention, no way to trade precision against recall; `analyzer._aggregate_results` (`evaluate_nlu.py:95`) returns a flat set with no per-detection score.

**Methodology.** Have the NLU and LLM stages emit a real numeric score per detection; plot PR curves on the held-out split and pick the threshold maximizing F-β for the chosen trade-off, reporting the curve (AUC-PR) not one point. Add an abstention band (route low-confidence to human review) and report coverage vs accuracy; add a reliability diagram / Brier score for calibration. Minimum first step: bucket metrics by the existing confidence string so the 7 Medium entries are visible.

### 3.7 Whole correctness dimensions unmeasured — evidence grounding, source verification (high)

Evaluation is scoped to set-membership of technique IDs per document. No evaluator checks whether the `evidence.text` (a) supports the technique, (b) actually appears in the source, (c) matches reviewer confidence, or (d) points to the correct span. A detection counts as TP for having the right `techniqueId` even if its quote is fabricated. The `no_safety_content` exclusion (`evaluate_nlu.py:22-34,106-116`) is itself an unaudited human flag that changes the denominator.

**Methodology.** Add an **evidence-grounding** evaluation: verify each `evidence.text` is a substring (or high-similarity fuzzy match) of the source `flat_text` and report a hallucinated-quote rate. Add an **evidence-relevance** evaluation where blind annotators rate whether each quote supports its technique (report support-precision and κ). Audit `no_safety_content` flags against the blind gold set. Treat a detection as fully correct only if both the `techniqueId` and its grounding pass, and report this stricter "grounded precision" alongside ID-only precision.

### 3.8 Reproducibility gaps — live re-extraction inside the evaluator (medium)

`evaluate_nlu.py:120` instantiates a live `NLUAnalyzer` and re-runs analysis at eval time, so its numbers depend on current model/profile state. No script records input hashes, git commit, model version, or timestamp; only `compare_taxonomy_runs.py` writes a file. There is no schema validation; `by_source.get(source, by_source['legacy'])` (`compare_taxonomy_runs.py:89`) silently absorbs unknown `created_by` into `legacy`.

**Methodology.** Separate extraction from evaluation: snapshot the analyzer output to a versioned file and evaluate against the frozen snapshot, never re-running the model inside the evaluator. Stamp every metrics artifact with input SHA-256, git commit, model/profile version, and timestamp; write all three evaluators' outputs to versioned JSON. Add a jsonschema CI gate asserting required keys, a known `created_by` enum, and `techniqueId` membership in `techniques.json`. Replace the silent `legacy` fallback at `:89` with an explicit error or a logged unknown-source counter.

---

## 4. Data model & validation (`schema/llm-safety-v1.1.0.json`, `data/*.json`, CI)

### 4.1 Schema is an empty stub; `jsonschema` dependency unused (high)

`schema/llm-safety-v1.1.0.json` has only `$schema`/`$id`/`title` (confirmed: lines 1–5 in the repo) — no `type`/`properties`/`required` — so it validates any JSON. `requirements.txt:2` declares `jsonschema 4.20` but nothing imports it; only `validate_references()` in `.github/scripts/update_technique_map.py:31-38` checks `source_id`/`technique_id` for one submission.

**Methodology.** Write a real draft-2020-12 schema with `type`/`required`/`enum` domains for all `DATA_DICTIONARY.md` fields plus `additionalProperties: false`, and a `scripts/validate.py` running `Draft202012Validator` per file. Coverage target: 100% of documented fields constrained.

### 4.2 No CI validation; referential integrity broken — 535 dangling refs (CRITICAL)

`DATA_DICTIONARY.md:233-252` lists 13 integrity rules; `process-review.yml` commits (`:36-44`) with **no validation**. 534 `incidents` `techniqueIds` reference four IDs absent from `techniques.json` (`tech-content-watermarking`, `tech-hallucination-detection`, `tech-age-verification`, `tech-copyright-compliance`), and 1 map entry under `gemini-3-pro` references absent `tech-supervised-fine-tuning`. Dangling refs silently drop from joins, undercounting incident-by-technique coverage, and every commit can add more.

**Methodology.** Add a `validate.yml` on PR/push running the schema plus a `referential_integrity.py` enforcing all 13 rules (non-zero exit on any orphan); wire it into `process-review.yml` **before** the commit step. Fix the 535 existing refs. Per-file id-sets; foreign keys must be subsets; violations target 0.

### 4.3 NLU evaluation has no train/test isolation (high)

`evaluate_nlu.py:37-79` derives ground truth from `model_technique_map.json` (`created_by` manual/sashaagafonoff at `:61-62`; active techniqueIds at `:67-69`) — the same file the pipeline writes (`analyze_nlu.py:373-384` writes `created_by: nlu` entries into the same arrays). Manual GT and machine predictions co-mingle, so metrics are optimistically biased and unreproducible since each run mutates the label file. (Same root cause as §1.1/§2.1/§3.1.)

**Methodology.** Keep a separate append-only `data/gold/` file the pipeline cannot write; load GT only from it; freeze a held-out doc set.

### 4.4 Confidence rubric is hardcoded uncalibrated heuristics (medium)

`analyze_nlu.py:41,45` fix thresholds 0.40/0.85; confidence is additive (`:341-363`) bucketed at 0.85/0.70 (`:366-371`); `evidenceQuality`/`confidence_weight` in `evidence.json` are hand-assigned with no rubric. Identical evidence gets different bands from incidental phrasing.

**Methodology.** Calibrate thresholds via PR curves; replace the additive stack with a logistic/isotonic calibrator; document the rubric. (Consolidates with §1.2/§1.6.)

---

## 5. Ingestion & reproducibility (`ingest_*.py`, `check_sources.py`, `clean_flat_text.py`, `expand_collections.py`, `snapshot.py`)

The ingestion stack is functional but **not reproducible or auditable** in the senses that matter for a research corpus.

### 5.1 Document ingestion is not reproducible — no hash, timestamp, or raw artifact (high)

`ingest_all()` (`ingest_universal.py:87-208`) fetches each live URL (`requests.get` at `:153`), writes `data/flat_text/{id}.txt` with only `SOURCE_ID`/`SOURCE_TITLE`/`SOURCE_URI` (`:185-190`), then **deletes the raw file** (`:200`). No checksum of raw bytes or extracted text, no `retrieved_at`, no retained raw artifact; none of the 47 `evidence.json` entries carry a hash/timestamp. The skip-if-exists guard (`:144-146`) means files are never refreshed without `--force`, and MarkItDown/BeautifulSoup are unpinned, so the same URL can later yield different text with no record of which version produced the committed flat text.

**Methodology.** Make ingestion content-addressable and timestamped: on fetch, compute sha256 of raw bytes and of cleaned text; persist both plus `retrieved_at` (UTC), final URL after redirects, HTTP status, Content-Type, and markitdown/bs4 versions into the header and into `evidence.json` (or a sibling `data/provenance.json`). Retain the raw artifact (compressed) under `data/raw/{id}.{ext}` or store an archive snapshot URL. Gate re-ingestion on raw-hash change, not file existence. Track a "reproducibility rate" = fraction of sources whose re-fetched raw sha256 matches the recorded hash.

### 5.2 `check_sources.py` detects drift on HEAD metadata only, never hashes the text (high)

`get_source_fingerprint()` (`:69-97`) records only `Last-Modified`, `ETag`, `Content-Length`; only if all three are absent does it sha256 the **first 8 KB** of a GET (`:87-91`). `has_changed()` (`:100-124`) compares one field, preferring `ETag`. Header-poor or ETag-rotating hosts defeat this; the 8 KB fallback misses any change past the first 8 KB; the function never hashes the actual `flat_text/{id}.txt`. A "changed" verdict triggers `reingest_document()` (`:145-174`) with no diff against the prior text.

**Methodology.** Change the comparison unit from HEAD metadata to a normalized full-content hash: always GET the full body, run it through the same extraction+clean pipeline, and compare sha256 of the result against the stored value; use HEAD only as a cheap pre-filter. Record per-source extraction hash, raw hash, and `last_verified`. On change, store a unified diff in `cache/update_log.json` for human audit. Measure detection quality on an injected-change fixture set (recall of real changes, false-positive rate).

### 5.3 Flat-text cleanup is unvalidated, threshold-brittle, and irreversible (high)

`clean_file()` (`clean_flat_text.py:523-570`) runs five regex passes with eyeballed magic thresholds: `single_char_count >= 15` (`:102`), `dot_lines_in_block >= 3` (`:160`), `citation_signals < 2` (`:260`), `numeric_tokens/len >= 0.4` with `table_lines >= 5` (`:326,431`), `name_count >= 20` (`:507`). `remove_references()` deletes from a "References" heading to EOF or the next appendix-like heading (`:263-280`) with a fragile `^[A-Z]\s+[A-Z]` terminator (`:274`) that can swallow real content; `remove_tables()` removes any block where ≥40% of tokens parse as float (`:304-329`), catching benchmark-dense safety prose. Cleaning is **in-place** (`:566-568`), originals discarded, and runs inline during ingestion (`ingest_universal.py:195`) before any human sees the raw extraction — so over-deletion of safety content is permanent and undetectable.

**Methodology.** Hand-annotate a held-out gold set of ~30–50 documents marking which line spans are genuinely TOC/refs/tables/contributors vs content. Treat each remover as a binary classifier over line spans; tune thresholds via PR curves optimizing for high content-preservation precision (e.g. ≥0.98) before a threshold ships. Make cleanup **non-destructive**: keep raw flat text and store removals as a sidecar (span list + reason) so deletions are reversible; emit a per-document "content bytes removed" metric and flag outliers (>25% removed). Re-run the gold-set evaluation in CI on any edit to `clean_flat_text.py`.

### 5.4 AIID mapping relies on tiny hard-coded lookups and unmeasured substring matching (high)

`ENTITY_TO_PROVIDER` (`ingest_aiid.py:55-81`) is a ~30-entry hand list matched by exact lowercase-strip equality (`:491-499`), so legal-suffix/alias variants yield no provider. `classify_llm_related` (`:151-164`) flags LLM-relevance on any of ~80 substrings — bare company names `openai`/`anthropic` (`:135-136`) tag any mention as LLM-related, and `palm` (`:121`) matches unrelated text. `map_techniques_from_text` (`:255-269`) attributes a **failed** technique from description keywords (e.g. any `bias` substring → `tech-bias-mitigation`) with no notion of actual implication, and returns an always-empty `matched_risks` (`:269`) despite the docstring. `derive_severity` silently defaults unrecognized harm strings to `medium` (`:502-510`), and all 1365 incidents are stamped `status:'confirmed'` (`:601`) regardless of mapping confidence.

**Methodology.** Replace exact-match with a normalized alias resolver (lowercase, strip legal suffixes, fuzzy match against an approved alias table), logging unmatched entities and tracking match coverage. For LLM-relevance and technique attribution, draw a stratified sample (~200), have 2 annotators label relevance and implicated techniques, compute κ, then report classifier precision/recall against adjudicated labels; drop bare-company-name keywords. Emit per-field confidence and demote low-confidence attributions to a `candidate` status. Distinguish `unknown` from `medium` severity. Remove/implement the dead `matched_risks` return.

### 5.5 FMTI mapping is exact-string keyed and breaks silently on upstream change (medium)

`INDICATOR_TO_TECHNIQUE` (`ingest_fmti.py:45-85`) keys on exact indicator strings, looked up via `.get()` after `.strip()` (`:138`); any rename/whitespace/casing change falls through to `unmapped_indicators` (`:143`) and is dropped with only an aggregate count (`:157`). Company columns are detected **positionally** (`all_columns[0]`/`[1:]`, `:126-127`), so a column reorder mismaps scores. Score `1` is treated as technique-present (`:150`) despite the code's own notes that FMTI measures disclosure, not implementation. The Dec2025 URLs are hard-coded to `main` (`:25-26`) with no checksum or commit pin.

**Methodology.** Pin the FMTI source to an immutable ref (commit SHA / release tag, not `main`) and record sha256 of each CSV in `fmti_meta.json`. Validate company column **headers by name** (fail loudly), not by position. Emit an error / fail CI listing any indicator string not present in `INDICATOR_TO_TECHNIQUE` so renames are caught instead of silently dropped. Keep the disclosure/implementation distinction explicit in emitted evidence (the `confidence_weight 0.6` at `:221` is a good start) and document that `1` means disclosure-present.

### 5.6 `expand_collections.py` auto-ingests LLM web-search output with no verification and a colliding ID scheme (CRITICAL)

`expand_incidents`/`expand_commentary` (`:217-458`) parse a JSON array from the model's free text (`_parse_json_response:184-206`) and write accepted entries straight into `commentary.json`/`incidents.json` (`run():519-534`). Validation is purely structural — **no URL is ever fetched** to confirm it exists. The prompts ask for real, accessible URLs (`:261,376-379`) but nothing enforces it, so a fabricated URL/title/date passes every check and lands as `status:'confirmed'` (`:451`). Dedup is exact-URL + `SequenceMatcher` title ratio > 0.80 (`:208-215`), which cannot catch a hallucinated-but-novel record. The ID scheme collides: `_max_id` (`:123-129`) takes the max trailing number across **all** ids, but `incidents.json` already holds 1365 `aiid-<n>` records, so `_next_incident_num` produces `incident-1366…`, mixing two namespaces on one counter. A `max_uses:10` web_search tool and retry logic (`:150-182`) make output nondeterministic.

**Methodology.** Gate every auto-added record behind verification + human review. (1) Fetch each candidate URL server-side; require HTTP 200 and that the page text contains corroborating terms (title tokens / provider / incident keywords) — drop or quarantine failures. (2) Add a second-pass verification call (different model/temperature or a structured grounding check) and route disagreements to a `pending_review` queue, not the live JSON. (3) Require ≥2 independent domains for `confirmed` status; otherwise `unverified`. (4) Fix the ID namespace: give LLM-sourced records a distinct prefix (e.g. `webllm-incident-NNN`) and compute the counter only over that namespace, never over `aiid-*`. (5) Record the model id, prompt, tool-call transcript, and raw JSON alongside each record. (6) Default to `--dry-run`; write only after a human approves the diff. Measure auto-add precision by manual audit, targeting a near-zero hallucination rate before any unattended write.

### 5.7 `snapshot.py` tracks drift for only one dataset, manually, with one data point (medium)

`snapshot.py` versions exclusively `data/model_technique_map.json` (`MAP_PATH:23`) with a narrow stat set (`compute_stats:34-58`); the diff (`compute_diff:61-122`) only reports active-technique set changes and cannot detect an active→inactive flip without a set change. Snapshots are created only on manual invocation (`:338`), keyed by `date.today()` with same-day overwrite (`:173,178-179`), and `snapshot_index.json` contains exactly **one** snapshot (`model_technique_map_2026-03-01.json`). `evidence.json` (47), `incidents.json` (1365), `commentary.json`, and FMTI/AIID meta are never snapshotted, so the higher-churn corpora the LLM ETL mutates are untracked.

**Methodology.** Extend snapshotting to all generated datasets (`model_technique_map`, `evidence`, `incidents`, `commentary`, fmti/aiid meta), each with a content sha256 and richer stats (counts by provider, risk area, origin, status, active/inactive). Trigger snapshots automatically in CI on any commit touching `data/`, keyed by commit SHA + timestamp (not date-only). Add jsonschema validation as a CI gate so a malformed ingest fails before commit, and emit a field-level drift report as a PR artifact. Define alert thresholds (e.g. >X% records changed, or any detection silently flipped inactive) that fail the build.

---

## 6. Evaluation integrity / train-test leakage (cross-cutting)

This is the project's single most damaging reliability defect and it recurs in **four subsystems**, all reading `data/model_technique_map.json` with the **same** "manually reviewed" predicate (`created_by ∈ {manual, sashaagafonoff}` or human deletion):

- **NLU** — `RETRIEVAL_THRESHOLD=0.40` and `VERIFICATION_THRESHOLD=0.85` were hand-tuned on the reviewed corpus (`analyze_nlu.py:41,45`), which is 37/41 documents.
- **LLM** — `_build_review_index` (`llm_assisted_extraction.py:404-409`) seeds the Pass-2 few-shot positives/negatives from the same reviewed entries that become gold labels; only per-document isolation exists.
- **Evaluation** — `evaluate_nlu.py:54-77` and `ground_truth_analysis.py:35-44` select GT with the identical predicate, and 261/379 active reviewed entries are nlu/llm-only, so the "positive" label *is* the extractor signal.
- **Data model** — `analyze_nlu.py` writes `created_by: nlu` entries into the very arrays `evaluate_nlu.py` reads as GT (`:373-384` vs `:67-69`), so each run mutates the label file.

**Consequences.** Reported precision/recall/F1 are upward-biased resubstitution estimates, not generalization estimates; recall is additionally meaningless because the false-negative universe is bounded by unaided human recall; and the bias **grows over time** as the review index accumulates, so it is invisible and increasing.

**Unified methodology (do this once; all four subsystems consume it).**
1. **Freeze a blind gold set.** Blind-annotate a held-out sample of documents for technique presence using only `techniques.json` definitions; store in an append-only `data/gold/` the pipeline cannot write. Record `data/eval/test_split.json` and `data/eval_holdout_ids.json`.
2. **Quarantine the gold IDs from the review index.** Add an exclusion-set parameter to `_build_review_index` and to the threshold/confidence tuners so no gold/holdout `doc_id` ever conditions inference or calibration.
3. **Tune only on dev, report only on test.** Calibrate thresholds (PR curves) and confidence (isotonic/Platt) on the dev split; report metrics once on the untouched test split, with k-fold/LODO mean ± std and bootstrap CIs because n is small.
4. **Separate extraction from evaluation.** Evaluate against a frozen analyzer snapshot — never re-run the live model inside `evaluate_nlu.py`.
5. **Report grounded precision and per-stage metrics**, plus inter-annotator κ on the double-annotated subset to bound label noise.

Until this exists, label all quoted P/R/F1 as **in-sample / review-retention** figures, not accuracy.

---

## 7. Impact of adding image/video (generative-media) models

The dataset is built end to end on the assumption that a "model" is a text-producing LLM and "safety" is the techniques used to align/filter that text. Adding image/video models breaks that assumption in structural, not cosmetic, ways. (Counts here reflect the media-impact review and may differ from the 55-technique count used in §1–§4, which counts the current text taxonomy; both are reported as-found.)

### 7.0 Current shape relevant to media

- `data/techniques.json` — every technique is in text-LLM vocabulary (RLHF/DPO/Constitutional-AI/refusal on the training side; input/output guardrails, system prompts, prompt-injection defense, RAG/hallucination grounding at runtime). Each carries an `nlu_profile` (`primary_concept`, `semantic_anchors`, `entailment_hypothesis`) — the spine of the pipeline (§7.4).
- `data/categories.json` — 5 text-framed categories.
- `data/risk_areas.json` — 10 risk areas, none media-specific; `transparency` is the closest hook for provenance, `copyright_and_ip` for licensing.
- `data/models.json` — **flat schema** (`id/family/provider/status/version/notes`) with **no modality field** and no pure generative-media models.
- `schema/llm-safety-v1.1.0.json` — a stub, so no structural constraint is enforced.
- Pipeline/dashboard — `docs/components/data-pipeline.js` joins evidence sources → technique detections keyed by document, models attached via `source.models[].modelId`; `scripts/generate_dashboard.py` builds a **provider × technique** heatmap and risk/category rollups.

### 7.1 Where the text-LLM assumptions break

- **(a) The unit of safety is text-output moderation.** Output-filtering, hallucination-grounding, RAG-guardrails, realtime-fact-checking, and prompt-injection-defense only make sense for a token stream. An image generator has no completion to filter token-by-token, no hallucination-vs-grounding axis, no RAG, and only a degenerate notion of prompt injection. Video adds temporal and audio surfaces these techniques don't model.
- **(b) Refusal/abstention is a text behavior.** `tech-refusal-training` describes a conversational decline; the image equivalent is prompt-level blocking + output-image classification + returning a blank/safe image — a different mechanism with different evidence, with no slot in the taxonomy.
- **(c) Core alignment doesn't transfer cleanly.** RLHF/DPO have diffusion analogues (RLHF/DPO on diffusion, reward-guided sampling, safety LoRAs, concept-erasure, negative-prompt steering), but the anchors ("PPO", "InstructGPT", "preference pair") won't match an image card, so genuine alignment reads as *absent*.
- **(d) The harm taxonomy is text-shaped.** `cat-harm-classification` assumes text classifiers; it has no slot for media-dominant harms: NCII, likeness/deepfake impersonation, election deepfakes, and visual **CSAM generation** (vs. the current `tech-csam-detection`, framed around PhotoDNA hash-matching of *known* material).
- **(e) `tech-multimodal-safety-alignment` is a single catch-all** ("visual safety", "NSFW detection", "video safety") collapsing input filtering, output classification, watermarking, likeness protection, and training-data curation into one boolean — every media provider lights up exactly one heatmap cell, destroying discriminating power.
- **(f) The flat model schema cannot express "what does this model do."** With no modality, the dashboard cannot show only image models, cannot avoid penalizing an image model for lacking RAG guardrails, and cannot prevent a text model from being scored against watermarking.
- **(g) Provider ≠ model granularity becomes lossy.** OpenAI ships GPT-5 (text) and GPT Image; Google ships Gemini (text) and Imagen/Veo. The provider × technique rollup (`build_technique_matrix`) blurs media and text stacks unless modality is a first-class filter.

### 7.2 Taxonomy gaps — media-specific techniques absent today

Real, deployed mechanisms (FLUX / GPT Image / Imagen / Veo / Sora) with **no technique entry** (only the overloaded `tech-multimodal-safety-alignment` and a partial `tech-watermarking`):

| Gap | What it is | Closest existing entry (why insufficient) |
|---|---|---|
| **Content provenance / C2PA Content Credentials** | Signed manifest asserting AI origin + edit history | `tech-watermarking` lists C2PA as one anchor — conflates strippable metadata provenance with robust signal watermarking; **split needed** |
| **Invisible / robust watermarking (SynthID)** | Pixel/frequency signal surviving crops/compression, paired detector | Folded into `tech-watermarking`; needs its own technique with image/video applicability and a detector sub-aspect |
| **NCII detection** | Classifiers + hash banks (StopNCII) blocking nudification/deepfake porn | **No entry**; `tech-sexual-content-moderation` is generic NSFW, not consent-specific |
| **Generated-CSAM prevention** | Preventing *novel* synthesized CSAM (prompt blocking, concept erasure, output classifiers, IWF/NCMEC/Thorn) | `tech-csam-detection` is hash-matching of *known* material — different control surface |
| **Deepfake / likeness & consent safeguards** | Real-person/public-figure likeness blocks, face-similarity filters, opt-out registries, election blocks | **No entry**; maps to a missing risk area |
| **Prompt-level content filtering for image gen** | Pre-generation visual-harm prompt classification | `tech-input-guardrail-systems` anchors are text products (Llama Guard, NeMo, ShieldGemma) |
| **Output-image safety classification** | Post-generation visual classifier gating the returned asset | `tech-output-filtering-systems` is token/text-framed |
| **Training-data provenance / opt-out / licensing** | Corpus licensing, artist opt-out ("Do Not Train"/Spawning), CSAM scrubbing (post-LAION) | `tech-dataset-auditing` + `tech-copyright-ip-violation` are text-corpus oriented; no creator opt-out concept |
| **Recitation / memorization controls for images** | Suppressing near-duplicate regurgitation of training images / trademarked characters | `tech-copyright-ip-violation` "memorization prevention" is text-verbatim oriented |
| **Style / artist-mimicry safeguards** | Blocking "in the style of [living artist]"; anti-mimicry | **No entry** |
| **Diffusion-specific alignment** | Safety LoRAs, concept erasure/unlearning, negative-prompt steering, reward-guided sampling | RLHF/DPO/Constitutional entries don't cover diffusion; `tech-machine-unlearning` is text-weight oriented |

≈ **8–12 net-new techniques** plus the split of `tech-watermarking` into provenance-metadata vs. signal-watermarking.

### 7.3 Schema / data-model changes

- **7.3.1 Add `modality` + `modelClass` to `data/models.json`** (highest leverage). Structured, not `notes` free-text:
  ```jsonc
  { "id": "flux-1-1-pro", "family": "FLUX", "provider": "bfl", "status": "active",
    "version": "FLUX 1.1 Pro",
    "modality": { "inputs": ["text","image"], "outputs": ["image"] },
    "modelClass": "image-generation" }   // text-llm | image-generation | video-generation | multimodal-understanding | audio
  ```
  Outputs drive safety applicability (a vision-*understanding* model that emits text stays under the text taxonomy). Backfill-friendly: existing entries default to `outputs:["text"]`, `modelClass:"text-llm"`.
- **7.3.2 Add `modalityApplicability` to `data/techniques.json`** so the dashboard stops penalizing image models for lacking RAG: `["text"]` for RAG guardrails, `["image","video","audio"]` for watermarking, `["text","image","video"]` for shared governance/red-team/compliance. Preferable to duplicating the catalog per modality.
- **7.3.3 New techniques** (§7.2) with media `nlu_profile`s; split `tech-watermarking` → `tech-provenance-c2pa` + `tech-invisible-watermarking`.
- **7.3.4 Categories** (`categories.json`): minimal (slot media techniques into existing `cat-runtime-safety`/`cat-harm-classification`/`cat-model-development`, keeping the dashboard's category axis intact) or explicit (add `cat-content-provenance` / `cat-media-integrity`).
- **7.3.5 Risk areas** (`risk_areas.json`): add `impersonation_and_likeness` (deepfakes, NCII, voice/face cloning, election) — currently uncovered; add `synthetic_media_provenance` (or fold into `transparency`); extend `copyright_and_ip` for style mimicry / training-image opt-out.
- **7.3.6 Schema enforcement.** Flesh out `schema/llm-safety-v1.1.0.json` (or bump to v1.2.0) to **require** `modality`/`modelClass` on models and `modalityApplicability` on techniques, so a media model can't be ingested without declaring its modality. This dovetails with §4.1 (the schema is currently a stub anyway).

### 7.4 Impact on the NLU + LLM pipeline (highest, least obvious cost)

The pipeline assumes text-LLM source documents and text-LLM vocabulary:
- **(a) Semantic anchors don't transfer.** Anchors tuned to text cards ("PPO", "Llama Guard", "verbatim reproduction") yield near-zero recall on an image card that says "negative prompts", "C2PA manifest", "SynthID", "concept filtering", "face-similarity threshold", "nudity classifier", "opt-out / Do Not Train" — **falsely reporting media models as having no safety**. Each new media technique needs its own hand-curated anchors.
- **(b) Entailment hypotheses must be rewritten.** "The model was trained using RLHF during fine-tuning" is contradicted/neutral against a diffusion card; new hypotheses must be phrased for media (e.g. "The system embeds C2PA Content Credentials in generated images").
- **(c) Evidence sources differ.** Media disclosures live in C2PA/CAI specs, model-card "intended use / limitations", image-model usage policies, transparency/impact assessments, sometimes only API docs or blogs. `evidence.json` needs new `content_metadata.primary_topics` values (`provenance`, `likeness_protection`, `training_data_opt_out`, `visual_content_filtering`) and likely new source `type`s.
- **(d) Re-validate the NLI path.** No image understanding is needed for *extraction* (inputs are still text documents about media models), but the domain shift is large enough to require re-validating confidence calibration and re-checking the LLM-review prompt and the quality filter's glossary/future-work heuristics against media cards.
- **(e) `tech-multimodal-safety-alignment` becomes an FP magnet.** Once granular media techniques exist, deprecate or narrow it (to cross-modal/jailbreak-via-image alignment) or the extractor keeps collapsing distinct mechanisms into it.

This is a **parallel set of anchor lists, hypotheses, source types, and a re-validation pass** — not "add some rows." The detection record structure (`techniqueId / confidence / evidence[].text / created_by`) is reusable as-is.

### 7.5 Dashboard / lifecycle implications

- **Heatmap comparability breaks** (`generate_dashboard.py`, `data-pipeline.js`): image models show empty cells for text techniques (RAG, hallucination, fact-checking) and text models for media techniques (watermarking, NCII, likeness) — reading as "everyone fails half the techniques." **Fix:** add a `modality` facet to `applyFilters` in `data-pipeline.js` (it already filters providers/categories/techniques) reading `source.models[].modelId → models.json.modelClass`, and have `generate_dashboard.py` render separate text/image/video heatmaps or gray out non-applicable cells via `modalityApplicability` (distinct from "not detected").
- **Coverage math is modality-blind.** `create_category_chart`/`create_risk_coverage_chart` count detections without modality weighting; the "detected / total" denominators must become modality-aware or headline stats mislead.
- **Join key is fine.** The evidence→technique join (keyed on `source.id`/`url`/`title`, models via `source.models[].modelId`) needs no structural change — only `models.json` carrying modality.
- **Lifecycle (`model_lifecycle.json`) mostly holds.** Pre-training data work is heavier/legally central for media (licensing, opt-out, CSAM scrubbing) but the existing stage suffices; provenance/watermarking are inference-stage and slot into the existing `inference` stage. **No new lifecycle stage required.**

### 7.6 Recommendation — hybrid (one dataset, modality as a first-class dimension)

Keep one dataset and one pipeline; introduce modality as a first-class dimension and a media-safety sub-branch of techniques. Do **not** spin up a separate dataset.

1. Add `modality` + `modelClass` to `models.json` and `modalityApplicability` to `techniques.json` — the keystone everything else depends on.
2. Add the 8–12 media techniques, split `tech-watermarking`, deprecate/narrow `tech-multimodal-safety-alignment`; tag every technique (old and new) with applicable modalities so shared governance/eval/red-team techniques are reused, not duplicated.
3. Add `impersonation_and_likeness` (and optionally `synthetic_media_provenance`) risk areas; extend `copyright_and_ip`.
4. Build a parallel set of NLU anchors + entailment hypotheses for media techniques and re-validate the extractor against media cards.
5. Make the dashboard modality-aware (filter facet + applicability-aware cells).

**Tradeoffs:**
- **Fold flat (no modality):** zero schema churn, dashboard unchanged — but text and media techniques become mutually non-applicable noise, every model looks half-empty, and the catch-all stays one misleading boolean. **Reject.**
- **Hybrid (recommended):** preserves the shared backbone (governance, red-teaming, regulatory compliance, weight security, capability monitoring, incident reporting, ethical-labour sourcing apply identically), keeps cross-modal provider comparisons, and reuses the evidence/join/detection plumbing unchanged. Costs: schema work, a real schema instead of the stub, dashboard filtering, and a second anchor/hypothesis corpus — real but bounded and additive.
- **Separate parallel dataset:** cleanest isolation but duplicates ~15 genuinely shared techniques, the providers list, and all plumbing; forces a second dashboard; and **loses** the most valuable view — a provider's text vs. media safety posture side by side. **Reject unless** media coverage is expected to dwarf text and be maintained by a different team.

**Key files to change:** `data/models.json` (modality), `data/techniques.json` (`modalityApplicability` + new media techniques + split watermarking + narrow `tech-multimodal-safety-alignment`), `data/risk_areas.json` (likeness/provenance), optionally `data/categories.json` (media-integrity category), `schema/llm-safety-v1.1.0.json` (flesh out + version bump), `docs/components/data-pipeline.js` (modality filter facet), `scripts/generate_dashboard.py` (modality-aware heatmap + coverage denominators), plus new NLU anchor/hypothesis content feeding `data/map_nlu.json` / `data/map_llm.json` / `data/model_technique_map.json`.

---

## 8. Sequenced roadmap

### Phase 0 — Quick wins (days, low risk, no schema change)
1. **Dynamic entailment label lookup + CI unit test** (§1.3) — read `id2label`, assert the entailment index; guards every verification score.
2. **Hard grounding gate + taxonomy-membership validation** (§2.2, §2.3) — drop/quarantine ungrounded quotes and out-of-taxonomy `techniqueId`s; flip confirm-on-failure to abstain.
3. **Per-evidence provenance + manual-preservation guard** (§2.4) — classify provenance by any manual evidence; never let an LLM deletion deactivate a manual entry.
4. **Pin versions + seeds + record resolved model id** (§1.5, §2.5) — uncomment/pin `torch`, `sentence-transformers`, `transformers`; pass HF `revision=`; date-pin `MODEL_MAP`; write a provenance block.
5. **Fix the 535 dangling refs and the duplicated category-topic map** (§4.2, §1.9) — and add the basic referential-integrity script (wire into CI in Phase 1).
6. **Default `expand_collections.py` to `--dry-run`; switch LLM-sourced IDs to a `webllm-` namespace** (§5.6) — stops the worst corruption immediately, ahead of the full verification gate.

### Phase 1 — Evaluation integrity (the central fix; ~1–2 weeks)
7. **Freeze a blind gold set** (`data/gold/`, `data/eval/test_split.json`, `data/eval_holdout_ids.json`) with inter-annotator κ (§6, §3.1).
8. **Quarantine gold IDs from `_build_review_index` and the tuners** (§2.1, §6).
9. **PR-curve threshold calibration + isotonic/Platt confidence** on dev; report once on test with k-fold + bootstrap CIs (§1.2, §1.6, §3.5).
10. **Unify the three evaluators** into one authoritative blind-gold evaluator with a shared "active technique" function; add grounded-precision and per-stage metrics; stamp artifacts with hashes/commit/model id (§3.2, §3.3, §3.7, §3.8).
11. **Add the taxonomy drift/alias map** and canonicalize IDs before set ops (§3.4).

### Phase 2 — Structural reliability (~2–4 weeks)
12. **Flesh out the JSON Schema (draft-2020-12) + `scripts/validate.py` + `validate.yml` CI gate** for all datasets, including the referential-integrity rules and `created_by` enum (§4.1, §3.8, §5.7).
13. **Content-addressable, timestamped ingestion + full-content drift hashing** (§5.1, §5.2) with a retained raw artifact and a reproducibility-rate metric.
14. **Non-destructive, gold-tuned flat-text cleanup** (sidecar removals, precision-floored thresholds, CI gold-set regression) (§5.3).
15. **Token-budgeted, full-coverage chunking** + per-technique recall reporting and a minimum-anchor CI check (§1.7, §1.8).
16. **Verification-gated, abstaining LLM ETL** for `expand_collections.py` (URL fetch+confirm, two-pass agreement, pending-review queue) (§5.6).
17. **Calibrated, measured AIID/FMTI mappings** (alias resolver, sampled κ-backed precision/recall, immutable FMTI ref + checksums, header-by-name validation) (§5.4, §5.5).
18. **Snapshot all generated datasets, CI-triggered, sha256-keyed** with field-level drift reports and alert thresholds (§5.7).

### Phase 3 — Generative-media extension (after Phases 0–2; §7)
19. **Add `modality`/`modelClass` and `modalityApplicability`** and enforce them in the schema (§7.3).
20. **Add the 8–12 media techniques, split watermarking, narrow `tech-multimodal-safety-alignment`, add the likeness/provenance risk areas** (§7.2, §7.3).
21. **Build and re-validate the media NLU anchor/hypothesis corpus and media source types**, reusing Phase 1's blind-gold + calibration machinery (§7.4).
22. **Make the dashboard modality-aware** (filter facet + applicability-aware cells + modality-weighted coverage denominators) (§7.5).

Phases 0–1 restore trust in the numbers; Phase 2 makes the corpus reproducible and auditable; Phase 3 extends scope without re-introducing the comparability and leakage problems the earlier phases fix.
