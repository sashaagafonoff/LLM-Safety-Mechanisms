# Execution Plan — August 2026

**Scope:** model-list currency · incident/model linkage · extraction-accuracy uplift
**Prepared:** 2026-08-23 · **Companion diagram:** [2026-08-execution-plan.svg](2026-08-execution-plan.svg)
**Relationship to [docs/WORKPLAN.md](../WORKPLAN.md):** WORKPLAN.md remains the master backlog. This document is the *executable* plan for the 2026-08-23 review findings — it operationalizes the remaining B.2 items, unblocks A.3, and sequences the C phases. Item ids reference WORKPLAN where they overlap.

---

## 0. Goals and exit criteria

| Metric | Now (June-20 sonnet pass) | Target |
|---|---|---|
| Blind **test** precision | **41.8%** | **≥ 70%** |
| Blind **test** recall | 78.6% | ≥ 65% (may trade a little recall for precision) |
| Whole-technique FP factories (0-TP techniques emitting FPs) | 12 techniques, ~100 FPs | 0 |
| Model list currency | June-19 audit + 2 months' drift | Current to Aug 2026, verified sources |
| Incidents with `modelIds` | **0 / 1630** | ≥ 25% of provider-matched LLM incidents |
| Zero-coverage active models | 17 (incl. grok-4.3, deepseek-v4, qwen3.5) | ≤ 5 (docs sourced & ingested) |

Publishing gate: nothing merges to `main` (which auto-deploys the dashboard) without `validate.py` green **and** the blind eval run.

## 1. Constraints (carried from CLAUDE.md / WORKPLAN)

1. **Hand-authored files** (`models.json`, `evidence.json`, `techniques.json`, schema) are edited by the orchestrator only, never by subagents writing directly — subagents *propose*, orchestrator applies + validates.
2. **`model_technique_map_reviewed.json` is frozen** ground truth; nothing in this plan touches it. Blind-split holdout docs stay quarantined from the review index.
3. **Reliability fixes land before reprocessing data** (WORKPLAN's agreed sequencing) — Phase 6's full rerun happens only after Phases 2–4.
4. **Web-sourced model facts are verification-gated**: official provider pages only; anything else is flagged, not applied.
5. **Human gates** (marked `HG`): pushing to `main`, model retirements/removals, the Mythos 5 policy call, and the post-rerun review session.

## 2. Track structure

Three tracks run in parallel after Phase 0; they converge at Phase 6:

- **Track A — Data currency & sources** (haiku-heavy): Phase 1 (model list) → Phase 5 (document sourcing/ingestion).
- **Track B — Extraction accuracy** (sonnet-heavy): Phase 2 (precision) → Phase 3 (recall) → Phase 4 (calibration).
- **Track C — Incident linkage** (independent): T5.3 AIID model matcher.

---

## Phase 0 — Ship pending work (Day 0)

| Id | Task | Executor | Detail |
|---|---|---|---|
| T0.1 | Commit + push the completed AIID refresh (snapshot 2026-08-17: +115 incidents, 50 updated; `validate.py` green; stats/SUMMARY regenerated) | **HG** → orchestrator | Files: `data/incidents.json`, `data/stats.json`, `data/third_party/aiid/aiid_meta.json`, `docs/SUMMARY.md`. Push deploys the live dashboard — needs explicit go-ahead. |
| T0.2 | WORKPLAN hygiene: C.4 still references the deleted `generate_dashboard.py` | Orchestrator | One-line edit; dashboard needs no regeneration step. |

## Phase 1 — Model-list currency (Track A, Days 0–1)

### T1.1–T1.3 Verification fan-out — **3 parallel Haiku subagents**

Each agent gets one provider, the official URL(s), and a strict output contract (id, family, release date, status, source URL; official pages only; "UNCONFIRMED" otherwise):

| Agent | Verify | Primary sources |
|---|---|---|
| T1.1 | `claude-sonnet-5` (GA 2026-06-30), `claude-opus-5` (GA 2026-07-24); Mythos 5 availability wording | platform.claude.com models overview; anthropic.com/news |
| T1.2 | GPT-5.6 canonical API ids for Sol / Terra / Luna (+ whether 5.6-Cyber has a public id) | developers.openai.com/api/docs/models + deprecations |
| T1.3 | Llama 5 — **conflicting web reports; official pages only** (llama.com, ai.meta.com). Default outcome: do **not** add | llama.com, ai.meta.com |

### T1.4 Apply additions — orchestrator (edits `models.json` directly)

Ready now (already web-verified 2026-08-23), pending only the id checks above:

- `claude-sonnet-5`, `claude-opus-5` — active, Anthropic, with source URLs.
- GPT-5.6 entries (family GPT; one entry per canonical id confirmed by T1.2).
- `mistral-medium-3.5` — id confirmed on the official model card (`mistral-medium-3-5-26-04`); unblocks WORKPLAN A.3.
- Notes-only updates: DeepSeek V4 GA snapshots (`V4-Flash-0731` open-weights 2026-07-31; `V4-Pro-0813` GA 2026-08-12); GPT-5.5/5.4 notes marked prior-gen.

Explicit **non-adds** this cycle: Gemini 3.5 Pro (preview only, GA slipped), Grok 5 (unreleased), Nova 2 Pro (Forge preview), Llama 5 (unless T1.3 finds an official page), Muse Spark (scope decision deferred, WORKPLAN A.3).

### T1.5 Retirement / removal batch — **HG confirm → 1 Sonnet subagent executes**

Rule: **never retire a predecessor whose successor has zero ingested doc coverage.**

- Remove (invalid ids, WORKPLAN A.3): `deepseek-v3-lite`, `qwen3-thinking`, `qwen3-turbo`, `grok-4-thinking`; remap `gpt-5-thinking` evidence refs to the GPT-5 family entries.
- Retire/remove (zero or duplicated signal): `command-r-plus` (0 techniques; alias of `command-r-plus-08-2024`), `pixtral` (0), `llama-3-70b` (→ `llama-3-3-70b`), `qwen-2-5-coder` (→ qwen3-coder line), `nemotron-4`, `llama-3.1-nemotron` (→ Nemotron 3).
- Keep: all historical models with real coverage (`gemini-1-5-pro`, `claude-3-opus`, `claude-3-5-sonnet`, deprecated OpenAI models until shutdown dates).
- Hold: `hunyuan-large`, `deepseek-v3/v3.2`, `falcon-180b` — successors have no docs yet (Phase 5 unblocks these).

Procedure per removal: delete model entry → repoint/remove `sources[].models[]` refs in `evidence.json` → `py scripts/validate.py` + `py scripts/check_integrity.py`.

### T1.6 Mythos 5 policy — **HG**
Now publicly announced (limited release, Project Glasswing) *and* named in a July-30 AIID incident. Decide: add with `status: "active"` + availability note (enables incident linkage), or keep excluded. Recommendation: add, noting limited availability — the incident register references it either way.

**Phase gate:** `validate.py` green; no dangling refs.

## Phase 2 — Precision quick wins (Track B, Days 1–2)

All four are bounded code tasks — **Sonnet subagents, one per task, parallel**, each delivering code + pytest tests on a feature branch. Orchestrator reviews and merges.

| Id | Task | Implementation detail |
|---|---|---|
| T2.1 | **NLU deny-list** for the 12 FP-factory techniques (0 TP each in `reports/taxonomy_comparison.md`): scalable-oversight (17 FP), voluntary-commitments (11), model-weight-security (11), autonomous-behaviour-classification (8), cybersecurity-threat-detection (7), differential-privacy (6), data-sovereignty (5), circuit-breakers (5), machine-unlearning (4), rag-guardrails (4), whistleblower-reporting (2), supervised-fine-tuning (1) | Add `"nlu_enabled": false` to each technique's `nlu_profile` in `techniques.json`; `analyze_nlu._load_and_index_techniques` skips them (they remain in the LLM taxonomy). Schema: extend the technique `$def`. Expected: ~−25% of all FPs at zero recall cost. |
| T2.2 | **Chunk-quality gate** before embedding | New `is_low_quality_chunk()` (in `robust_tokenizer.py` or a new `chunk_filters.py`): alphabetic ratio, digit/pipe/dash density, mean word length, sentence-punctuation presence. Fixture: the real GPT-5.5 table-soup string (`"BasicCommandand Discover…PASS PASS PASS"`) plus 5 clean-positive controls. Log dropped-chunk counts per doc. Complements WORKPLAN B.2.3 (doesn't replace it). |
| T2.3 | **Corroboration rule** at merge time (`run_extraction_pipeline.py`) | NLU-only entries with exactly 1 evidence chunk and no LLM/manual corroboration → `active: false`, `needs_review: true`, `review_reason: "single_chunk_uncorroborated"`. Manual evidence always wins (existing guard). |
| T2.4 | **Store raw scores** on evidence items | `retrieval_score`, `verification_score` floats on each NLU evidence dict (feeds Phase 4). Update the map `$def` in `schema/llm-safety-v1.1.0.json`. Keep the High/Medium/Low label for dashboard back-compat. |

**Phase gate:** `pytest` green; `validate.py` green; NLU-only mini-run on 3 docs (`--nlu-only`, no API cost) shows deny-listed techniques absent and table-soup chunks dropped.

## Phase 3 — LLM-pass recall (Track B, Days 2–4)

The June pass's LLM stage recalled only 38–42% because the model got 57 techniques × a 150K-token document in one 4096-token call — and never saw the NLU's retrieved chunks. Code tasks to **Sonnet subagents**; prompt-design review stays with the orchestrator.

| Id | Task | Implementation detail |
|---|---|---|
| T3.1 | **Inject NLU evidence into the extraction prompt** | `NLU_CONTEXT_TEMPLATE` currently lists technique ids only. Include each detection's top chunk text + retrieval/verification scores (cap ~200 tokens/technique). This is the "R" of the RAG design finally reaching the "G". |
| T3.2 | **Category-batched extraction** | One API call per category (5 calls/doc, ~11 techniques each) instead of one monolithic call; raise `max_tokens` to 8192; merge + dedupe candidates across batches. Keeps each call's decision space small. |
| T3.3 | **Structured outputs** | Replace regex JSON parsing with a strict tool schema (`strict: true` + `additionalProperties: false`) or `output_config.format`; verdict enums enforced at the API layer. Parse-failure abstention path stays as fallback. |
| T3.4 | **Pass-2 verification upgrades** | Snippet budget 200→500 chars; verdict keys `(techniqueId, index)` to survive duplicates; capture `deletion_reason` in the tagging tool's save path (`tools/tagging_tool.html` + `review_server.py`) so the negatives index carries *why*. |
| T3.5 | **Model A/B on the dev split** — orchestrator runs, script scores | Extraction with `claude-sonnet-4-6` (current default) vs `claude-opus-5` (add to `MODEL_MAP`); optionally `claude-sonnet-5` (intro pricing $2/$10 per MTok through 2026-08-31). Score with the blind-gold evaluator on **dev only** (test stays untouched until Phase 6). Winner = best F1 subject to precision ≥ 60%. Rough cost: ~$3–5 per 22-doc dev run on sonnet, ~$5–9 on opus-5. |

## Phase 4 — Calibration (Track B, Days 4–5)

The June calibration ran on 39 labelled points (perfect-separation overfit; rightly unapplied). The review index now holds **1,253 confirmed positives and 518 rejected negatives** — a real pool.

| Id | Task | Executor | Detail |
|---|---|---|---|
| T4.1 | Build the labelled pool: reviewed docs × (evidence text, technique, label from `active`/`deleted_by`), scored via `score_candidates()` (NLU-only, no API cost) | Sonnet subagent | Extends `calibrate_thresholds.py` (B.1.3). |
| T4.2 | Per-technique thresholds with shrinkage toward the global threshold for low-data techniques; isotonic confidence calibration; write `data/nlu_thresholds.json`, consumed by `analyze_nlu.py` | Sonnet subagent | Fixes the "95% of entries are High" problem — labels derive from calibrated probability, not the pass/fail gate. |
| T4.3 | CI guard: threshold-regression test (calibration metrics can't silently degrade); minimum-anchor check (B.2.4 overlap) | Sonnet subagent | |
| T4.4 | Review operating points, approve per-technique thresholds | Orchestrator | Judgment call — precision floor per category. |

## Phase 5 — Source docs for coverage-gap models (Track A, Days 1–4, parallel with 2–4)

17 active models have zero documents (incl. `grok-4.3`, `deepseek-v4-pro/flash`, `qwen3.5-plus/flash`, `mistral-small-4`, `hy3-preview`, `command-a-plus-05-2026`, `falcon-h1-*`, `mai-1-preview`, `gpt-5.4-nano`) plus the Phase-1 adds.

| Id | Task | Executor | Detail |
|---|---|---|---|
| T5.1 | **Per-provider URL discovery — 6 parallel Haiku subagents** (xAI, DeepSeek, Alibaba, Mistral+Cohere, Tencent+TII+Microsoft, Anthropic+OpenAI new adds) | Haiku ×6 | Contract per agent: for each model, find the official system/model card or safety-relevant technical report URL (provider domain or arXiv only), doc type, publication date. No JSON edits. |
| T5.2 | Approve sources; write `evidence.json` source entries with `content_metadata` | Orchestrator | Hand-authored file; needs the metadata fields NLU/LLM stages rely on (`document_purpose`, `signal_strength`, `primary_topics`, …). |
| T5.3 *(Track C, independent)* | **AIID model matcher**: alias table generated from `models.json` (version strings + family names + curated aliases), matched against incident title/description; rerun `ingest_aiid.py` (local, no API); report match rate | Sonnet subagent | Fixes `modelIds: 0/1630`. Ties into WORKPLAN B.2.6 (measured mappings). Depends on T1.6 for the Mythos 5 alias only. |
| T5.4 | Ingest + clean: `ingest_universal.py --id …` per new source → `clean_flat_text.py`; Haiku spot-check of flat-text quality (garbled tables, empty extractions) | Script + Haiku | |

## Phase 6 — Converge: rerun, evaluate, publish (Week 2)

Strictly after Phases 2–4 merge and Phase 5 ingestion completes.

| Id | Task | Executor | Detail |
|---|---|---|---|
| T6.1 | Full pipeline rerun: `run_extraction_pipeline.py --regenerate` with the T3.5 winner model | Script (pipeline API) | ~70+ docs; rough cost $15–35 depending on winner. Manual annotations preserved by the merge. |
| T6.2 | Blind eval on dev **and** test; compare to the §0 targets | Script | If test precision < 60%: iterate Phase 2/4 parameters; **do not publish**. |
| T6.3 | Human review session in the tagging tool (`review_server.py`) — priority on newly ingested docs and `needs_review` quarantine | **HG** | Rejections feed the review index for the next cycle. |
| T6.4 | `snapshot.py` + `generate_report.py` + `validate.py` → commit + push | **HG** → orchestrator | Push auto-deploys the dashboard. |

---

## 7. Orchestration model

Two separate model axes — don't conflate them:
**(a) subagent models** (who writes code / gathers facts under my orchestration) and **(b) the pipeline's own Claude API model** (`MODEL_MAP` in `llm_assisted_extraction.py`, chosen by the T3.5 A/B).

| Executor | Model (API id · $/MTok in/out) | Used for | Why this tier |
|---|---|---|---|
| **Orchestrator** (this session) | Fable 5 (`claude-fable-5` · $10/$50) | Design decisions, prompt engineering, edits to hand-authored JSON, code review/merge, eval interpretation, human-gate prep | Judgment-heavy, cross-cutting context; lowest volume |
| **Haiku subagents** | Claude Haiku 4.5 (`claude-haiku-4-5` · $1/$5) | T1.1–T1.3 id verification, T5.1 URL discovery ×6, T5.4 spot-checks | Mechanical, well-specified, low-context fetch-and-report; cheapest tier; parallel fan-out |
| **Sonnet subagents** | Claude Sonnet (`claude-sonnet-4-6`/`-5` · $3/$15) | T1.5 retirement execution, T2.1–T2.4, T3.1–T3.4, T4.1–T4.3, T5.3 — bounded code + tests on a branch | Real implementation work with clear specs and test-verifiable outcomes; doesn't need frontier reasoning |
| **Pipeline API** | A/B: `claude-sonnet-4-6` vs `claude-opus-5` (vs `claude-sonnet-5` intro) | T3.5 comparison, T6.1 full rerun | Chosen empirically on the dev split, not by assumption |
| **Human (Sasha)** | — | T0.1 push, T1.5 confirm, T1.6 Mythos call, T6.3 review, T6.4 publish | Irreversible/outward-facing actions and taxonomy judgment |

**Never delegated to subagents:** direct writes to hand-authored data files, anything touching `model_technique_map_reviewed.json`, publishing to `main`, prompt wording that shapes extraction behavior (subagents implement the plumbing; the orchestrator owns the words).

**Parallelism at peak (Days 1–2):** 3 Haiku verifiers + 4 Sonnet implementers + 6 Haiku discoverers can run concurrently; every subagent works on a branch or reports findings only, so merge order is controlled.

## 8. Risks & mitigations

- **Precision fix regresses recall** → every Track-B change measured on the dev split before merge; test split touched once, at Phase 6.
- **Subagent hallucination of model facts** → official-domain-only contract; "UNCONFIRMED" is an acceptable answer; orchestrator re-checks anything applied to `models.json` (Llama 5 is the cautionary example — content-mill claims contradict official pages).
- **Taxonomy drift breaking eval comparisons** → route renames through `taxonomy_aliases.py` (B.1.5).
- **API cost overrun** → A/B on dev only; Haiku for all bulk web work; full rerun once, after all fixes merge.
- **Merge conflicts across parallel Sonnet tasks** → T2.1–T2.4 touch mostly disjoint files; T2.3 (pipeline merge logic) rebases last.

## 9. Timeline

| Day | Track A | Track B | Track C |
|---|---|---|---|
| 0 | Phase 0 ship · T1.1–T1.3 verify | — | — |
| 1 | T1.4–T1.6 apply + gates | T2.1–T2.4 in parallel | T5.3 matcher |
| 2 | T5.1 discovery fan-out | Phase 2 gate · T3.1–T3.4 | T5.3 re-ingest + measure |
| 3–4 | T5.2/T5.4 sources + ingest | T3.5 A/B · T4.1–T4.3 | — |
| 5 | ingest complete | T4.4 approve thresholds | — |
| Week 2 | **Phase 6:** full rerun → blind eval → review session → publish | | |

## 10. Deferred follow-on (captured, not planned here)

- **GitHub automation** — automate the recurring workflow (scheduled AIID re-ingest, source-drift
  checks, snapshots, report regeneration, review-loop PRs) via GitHub Actions. Captured as
  [WORKPLAN.md §E](../WORKPLAN.md) on 2026-08-23; to be planned and built **after** this
  plan's phases complete.
