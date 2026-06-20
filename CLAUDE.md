# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based dataset and analysis tool for tracking safety mechanisms implemented by LLM providers (OpenAI, Anthropic, Google, Meta, Amazon). The project maintains structured JSON data about providers, models, safety techniques, categories, risk areas, and evidence records, then generates visualizations and reports.

The dataset is published as an interactive dashboard at https://sashaagafonoff.github.io/LLM-Safety-Mechanisms/

## Core Architecture

### Data Model

The data model is centered around these key JSON files in [data/](data/):

- [evidence.json](data/evidence.json) - Core dataset containing evidence records that link providers to safety techniques they implement. Each record includes:
  - `providerId` and `techniqueId` references
  - `rating` (high/medium/low) indicating implementation maturity
  - `severityBand` (P/B/C/V/U) indicating evidence quality (Primary/Benchmarked/Claimed/Volunteered/Unverified)
  - `sources` array with URLs and metadata about where evidence was found
  - Optional `implementationDate` for timeline tracking

- [techniques.json](data/techniques.json) - Defines safety techniques (e.g., "RLHF", "Constitutional AI", "Input Filtering"). Each technique includes:
  - `categoryId` reference
  - `riskAreaIds` array
  - `nlu_profile` for semantic analysis (used by analyze_nlu.py)

- [providers.json](data/providers.json) - Provider metadata (name, type, website)
- [models.json](data/models.json) - Model metadata linked to providers
- [categories.json](data/categories.json) - Technique categories (e.g., "Alignment Methods", "Inference Safeguards")
- [risk_areas.json](data/risk_areas.json) - Risk area taxonomy
- [model_technique_map.json](data/model_technique_map.json) - **Generated** map of source documents → detected techniques, and the human-review surface. Each entry carries `created_by` provenance (`manual`/`nlu`/`llm`) and an `active` flag (reviewers set `active: false` / delete to record false positives). The merge step in `run_extraction_pipeline.py` preserves manual annotations across re-runs.
  - [map_nlu.json](data/map_nlu.json) / [map_llm.json](data/map_llm.json) - Per-stage outputs (NLU-only and LLM-only) that the orchestrator merges into the map above.
  - [model_technique_map_reviewed.json](data/model_technique_map_reviewed.json) - Frozen manually-reviewed ground truth used by the evaluation scripts.

- [model_lifecycle.json](data/model_lifecycle.json) - Lifecycle stage definitions (pre-training, training, evaluation, inference, governance) that techniques map to.
- [stats.json](data/stats.json) - **Generated** by `generate_report.py`; aggregate counts consumed by the dashboard.

- [standards.json](data/standards.json) - External framework definitions (NIST AI RMF, NIST AI 600-1, OWASP LLM Top 10, MITRE ATLAS, EU AI Act, ISO 42001, Weidinger taxonomy). Each framework has an id, version, URL, and hierarchical structure of codes.

- [standards_mapping.json](data/standards_mapping.json) - Many-to-many mapping of techniques to standard controls. Each entry links a `techniqueId` to a `frameworkId` with specific `codes[]`, a `relationship` type (mitigates/addresses/supports/defends), and optional notes.

- [commentary.json](data/commentary.json) - Third-party references (academic papers, audits, blog posts) discussing technique effectiveness. Links to techniques via `techniqueIds[]`.

- [incidents.json](data/incidents.json) - Safety incident register sourced from the [AI Incident Database (AIID)](https://incidentdatabase.ai/) (CC BY-SA 4.0). Ingested by `scripts/ingest_aiid.py`. Each incident links to `providerIds[]`, `modelIds[]`, optional `techniqueIds[]` (which techniques failed), `riskAreaIds[]`, and external `sources[]`.

### RAG Architecture

The extraction pipeline implements a **Retrieval-Augmented Generation (RAG)** pattern at two levels:

#### Macro RAG: NLU Retrieval → LLM Generation (document-level)

```
┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Flat Text   │───▶│  NLU Pipeline    │───▶│  LLM Pipeline    │
│  Documents   │    │  (Retrieval +    │    │  (Augmented      │
│              │    │   Verification)  │    │   Generation)    │
└─────────────┘    └──────────────────┘    └──────────────────┘
                    Stage 1: bge-large       Pass 1: Claude
                    bi-encoder retrieves     classifies document
                    candidate chunks         against taxonomy

                    Stage 2: nli-deberta     Pass 2: Review index
                    cross-encoder verifies   provides technique-
                    entailment               specific examples
```

- **R (Retrieval)**: `analyze_nlu.py` — Bi-encoder (BAAI/bge-large-en-v1.5) embeds document chunks and technique descriptions into a shared vector space. Cosine similarity retrieves candidate chunks above `RETRIEVAL_THRESHOLD`. Cross-encoder (nli-deberta-v3-large) verifies entailment above `VERIFICATION_THRESHOLD`.
- **A (Augmentation)**: `llm_assisted_extraction.py` — NLU results augment the LLM prompt as prior context. After initial extraction, the review index injects technique-specific confirmed/rejected examples from human reviews.
- **G (Generation)**: Claude produces structured technique classifications, then verifies each against review history.

#### Micro RAG: Review Index → Verification (technique-level)

After the LLM's initial classification (Pass 1), each proposed technique triggers a lookup into the **review index** — the cumulative history of human review decisions stored in `model_technique_map.json`:

- **Positives**: Entries that are `active: true` in manually reviewed documents (confirmed implementations)
- **Negatives**: Entries explicitly deleted by reviewers (confirmed false positives)

Only the relevant technique's examples are retrieved and fed to Claude for a focused verification pass (Pass 2). This avoids flooding the prompt with unrelated examples and ensures the verification signal is authoritative and current.

#### Pipeline Orchestration

`run_extraction_pipeline.py` orchestrates the full RAG pipeline: NLU pass → LLM pass → merge → optional report regeneration.

### Data Processing Pipeline

The typical workflow for updating the dataset:

1. **Ingest**: Download and convert source documents to flat text
   ```bash
   python scripts/ingest_universal.py
   # Or target a specific document:
   python scripts/ingest_universal.py --id <document-id>
   ```
   - Fetches PDFs, HTML pages, or other documents from URLs in evidence.json sources
   - Converts to clean text using MarkItDown and BeautifulSoup
   - Saves to [data/flat_text/](data/flat_text/)

2. **Analyze**: Drive the pipeline through the orchestrator (preferred — it merges stage outputs and preserves manual annotations)
   ```bash
   # Full collection, e.g. after changing the taxonomy or semantic anchors
   python scripts/run_extraction_pipeline.py --regenerate

   # Single document, after adding/updating one source
   python scripts/run_extraction_pipeline.py --id <document-id> --regenerate

   # Individual stages
   python scripts/run_extraction_pipeline.py --nlu-only   # no API key needed
   python scripts/run_extraction_pipeline.py --llm-only   # uses existing NLU results; needs ANTHROPIC_API_KEY
   ```
   - NLU stage: `BAAI/bge-large-en-v1.5` retrieval + `cross-encoder/nli-deberta-v3-large` verification (`analyze_nlu.py`)
   - LLM stage: Two-pass extraction with review-index-augmented verification (`llm_assisted_extraction.py`). Model is selectable via `--model haiku|sonnet|opus` (see `MODEL_MAP` in the script; default `sonnet` = `claude-sonnet-4-6`).
   - The stages can also be invoked directly (`python scripts/analyze_nlu.py`, `python scripts/llm_assisted_extraction.py`), but doing so writes `map_nlu.json`/`map_llm.json` without the merge step.
   - Final merged output: [data/model_technique_map.json](data/model_technique_map.json)

3. **Generate**: Create reports
   ```bash
   python scripts/generate_report.py    # Updates README "Dataset at a Glance", docs/SUMMARY.md, data/stats.json
   ```
   > **Do NOT script-generate the dashboard.** The interactive dashboard
   > (`docs/index.html` + `docs/components/*.js`) is a **hand-maintained** static
   > site that fetches `data/*.json` from GitHub `main` at runtime — it has no
   > build step and updates itself when data is pushed. There is no
   > `generate_dashboard.py`; an old Plotly-based script by that name was removed
   > because it overwrote the real Explorer dashboard with an inferior page.

### Key Scripts

- [scripts/ingest_universal.py](scripts/ingest_universal.py) - Universal document ingestion supporting PDFs, HTML, GitHub raw files. Handles various content types and converts to flat text.

- [scripts/analyze_nlu.py](scripts/analyze_nlu.py) - RAG retrieval + verification stage. Bi-encoder retrieval (bge-large-en-v1.5) finds candidate chunks, cross-encoder (nli-deberta-v3-large) verifies entailment. Includes quality filters and metadata-aware document skipping.

- [scripts/llm_assisted_extraction.py](scripts/llm_assisted_extraction.py) - RAG augmented generation stage. Two-pass architecture: Pass 1 extracts technique candidates using Claude; Pass 2 verifies each against the per-technique review index of confirmed/rejected human decisions.

- [scripts/run_extraction_pipeline.py](scripts/run_extraction_pipeline.py) - RAG pipeline orchestrator. Runs NLU → LLM → merge, preserving manual annotations. Supports single-document and full-collection modes.

- [scripts/evaluate_nlu.py](scripts/evaluate_nlu.py) - Evaluation harness. Runs NLU pipeline against ground truth from manually reviewed documents. Computes precision/recall/F1 per document and aggregate. Respects `no_safety_content` flags.

- **Dashboard** — there is no dashboard-generation script. The interactive
  dashboard lives in [docs/index.html](docs/index.html) + [docs/components/](docs/components/)
  (vanilla D3/htl ES modules) and is edited by hand. It fetches `data/*.json`
  from GitHub `main` at runtime, so updating data and pushing is all that's
  needed for the live site to reflect changes. (A legacy `generate_dashboard.py`
  was removed — it produced an inferior Plotly page that clobbered this one.)

- [scripts/generate_report.py](scripts/generate_report.py) - Generates markdown summary reports with tables and statistics.

- [scripts/semantic_retriever.py](scripts/semantic_retriever.py) - Utility for semantic search across flat text documents.

- [scripts/clean_flat_text.py](scripts/clean_flat_text.py) - Post-ingestion cleanup. Strips structural noise that causes NLU false positives (tables of contents, reference/bibliography sections, benchmark tables, arXiv metadata stamps, contributor lists), replacing each with a transparent `[PIPELINE INGESTION WORKFLOW - REMOVED ...]` placeholder. Run between ingest and analyze.

- [scripts/robust_tokenizer.py](scripts/robust_tokenizer.py) - Shared sentence-boundary tokenizer used by retrieval (handles abbreviations, decimals, URLs, initials). Imported by other scripts, not run directly.

- [scripts/check_sources.py](scripts/check_sources.py) - Detects upstream source changes via HTTP HEAD (Last-Modified/ETag/Content-Length); `--update --analyse` re-ingests and re-analyses changed docs. Designed as a scheduled task.

- [scripts/snapshot.py](scripts/snapshot.py) - Temporal versioning of `model_technique_map.json`. Archives dated copies and generates diffs (`--diff`, `--list`) to track coverage over time.

### Data-source ingestion (beyond the core RAG pipeline)

- [scripts/ingest_aiid.py](scripts/ingest_aiid.py) - Ingests safety incidents from the AI Incident Database into `incidents.json`.
- [scripts/ingest_fmti.py](scripts/ingest_fmti.py) - Ingests Stanford Foundation Model Transparency Index (FMTI) scores, mapping indicators to technique IDs and writing supplementary entries into `evidence.json`.
- [scripts/expand_collections.py](scripts/expand_collections.py) - Uses Claude's built-in `web_search` tool to discover new `commentary.json` / `incidents.json` entries (`--provider`, `--type`). Requires `ANTHROPIC_API_KEY`.

### Evaluation

Three overlapping evaluators measure extraction quality against the reviewed ground truth — know which one you want:

- [scripts/compare_taxonomy_runs.py](scripts/compare_taxonomy_runs.py) - Compares a fresh automated run against `model_technique_map_reviewed.json`; accounts for technique merges/renames/removals across taxonomy versions (`--detailed`). This is the evaluator the README documents.
- [scripts/evaluate_nlu.py](scripts/evaluate_nlu.py) - Runs the NLU pipeline against ground truth, computing per-document and aggregate P/R/F1; respects `no_safety_content` flags.
- [scripts/ground_truth_analysis.py](scripts/ground_truth_analysis.py) - Computes P/R/F1 directly from the `created_by`/`active` provenance already in `model_technique_map.json` (no re-run).

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# For NLU analysis, you'll need sentence-transformers (large download):
# pip install sentence-transformers
```

### Testing
There is currently **no automated test suite** — no `tests/` directory exists, and CI does not run tests. `pytest`/`pytest-cov` are listed in `requirements.txt` but unused. The de facto correctness checks are the evaluation scripts (see Evaluation above) run against the reviewed ground truth, plus the data-integrity check below. If you add tests, place them under `tests/` and run with `pytest`.

### Code Quality
```bash
# Format code
black scripts/

# Lint code
flake8 scripts/
```

### Common Tasks

**Regenerate reports after data changes:**
```bash
python scripts/generate_report.py
```
The dashboard needs no regeneration — it reads `data/*.json` from GitHub `main`
client-side, so pushing data changes updates the live site automatically.

**Add a new source document:**
1. Add source entry to `evidence.json` under the `sources` array
2. Run `python scripts/ingest_universal.py --id <new-id>`
3. Optionally run `python scripts/analyze_nlu.py` to auto-detect techniques

**Validate data integrity:**
```bash
# Umbrella gate: JSON Schema validation (schema/llm-safety-v1.1.0.json) + referential
# integrity for all datasets. Same checks the validate.yml CI gate runs. Needs jsonschema.
python scripts/validate.py
python scripts/validate.py --schema-only   # structure/type/enum only (incl. created_by)
python scripts/check_integrity.py          # referential integrity only (no jsonschema needed)
```
Schemas live in `schema/llm-safety-v1.1.0.json` (`$defs` per record type). After editing a
data file's shape, update the matching `$def` or `validate.py` will fail.

## Data Editing Guidelines

When manually editing JSON data files:

- **Always maintain referential integrity**: `providerId`, `techniqueId`, `categoryId`, etc. must reference existing entities
- **Use consistent IDs**: IDs should be lowercase, hyphen-separated (e.g., `constitutional-ai`, `rlhf`)
- **Evidence quality bands**: Use P (Primary) for official documentation, B (Benchmarked) for quantitative evidence, C (Claimed) for unverified claims
- **Ratings**: Use "high" for mature implementations, "medium" for partial/limited implementations, "low" for minimal implementations
- **Source URLs**: Always prefer stable, primary source URLs (official docs, research papers) over blog posts or news articles

## CI/CD Automation

Two GitHub Actions workflows exist in [.github/workflows/](.github/workflows/):

- **dashboard-deploy.yml** - Auto-deploys `docs/` to GitHub Pages when `docs/**` or `data/**.json` change on main (no build step)
- **process-review.yml** - Processes approved community tag submissions: parses structured JSON from GitHub issues, updates `model_technique_map.json`, and opens a PR

(Source-change detection and snapshotting — `check_sources.py`, `snapshot.py` — are written to run as scheduled tasks but are not currently wired into a workflow.)

## Notable Implementation Details

### NLU Analysis Quality Filters

The [scripts/analyze_nlu.py](scripts/analyze_nlu.py) includes specific heuristics to avoid false positives:
- Filters out glossary definitions (not actual implementations)
- Ignores "future work" or "planned" mentions
- Distinguishes "Access Control" from "Refusal" based on context
- Uses two-stage verification with configurable thresholds (RETRIEVAL_THRESHOLD=0.40, VERIFICATION_THRESHOLD=0.85)
- Skips documents flagged as `no_safety_content` in evidence.json content_metadata
- NLU profiles in techniques.json define per-technique: `primary_concept`, `semantic_anchors`, `entailment_hypothesis`, `excluded_terms`

### Document Ingestion Robustness

[scripts/ingest_universal.py](scripts/ingest_universal.py) handles various edge cases:
- Automatically converts GitHub blob URLs to raw content URLs
- Uses realistic browser headers to bypass bot detection
- Supports PDF, HTML, JSON, and plain text with automatic type detection
- Extracts clean text from HTML by removing scripts, navigation, footers

### Dashboard Visualization

The interactive dashboard at `docs/` is a plain static HTML site (no build step) deployed to GitHub Pages. It uses D3.js and htl loaded via ES module import maps from esm.sh CDN. All chart components are vanilla ES modules in `docs/components/`. The dashboard deploys automatically when `docs/**` or `data/**.json` files change on main.

## Generated vs. hand-edited files

The most important thing to know before editing: **which files are authored by hand and which are produced by the pipeline.** Overwriting a generated file by hand, or hand-editing one that a re-run will clobber, is the easy mistake here.

- **Hand-authored (edit these directly):** `evidence.json`, `techniques.json`, `providers.json`, `models.json`, `categories.json`, `risk_areas.json`, `model_lifecycle.json`, `standards.json`, `standards_mapping.json`. The `flat_text/` documents are downloaded, not hand-written.
- **Pipeline-generated (do not hand-edit; regenerate instead):** `map_nlu.json`, `map_llm.json`, `stats.json`, `docs/index.html`.
- **Hybrid — generated but human-curated:** `model_technique_map.json` is produced by the pipeline and then corrected through review (the tagging tool / `process-review.yml`); the merge step preserves those manual edits. `commentary.json` is seeded by `expand_collections.py` and curated thereafter.
- **Generated wholesale from an upstream snapshot (do not hand-edit):** `incidents.json` is produced entirely by `scripts/ingest_aiid.py` from a downloaded AI Incident Database (AIID) snapshot. There is **no human-curation layer** — every field (`providerIds`, `techniqueIds`, `riskAreaIds`, `severity`) is *derived* by the script (heuristic entity/text matching + CSETv1 classifications). The script rebuilds the whole file from the snapshot and does not read the existing `incidents.json`, so refreshing is just `python scripts/ingest_aiid.py --download` (network only, no API/credits) — there are no manual edits to preserve. Technique ids emitted by the keyword mapper are routed through `taxonomy_aliases.canonical_techniques`, so a project-wide technique rename is picked up automatically on the next re-ingest rather than reintroducing dangling references.
- **Ground truth (frozen):** `model_technique_map_reviewed.json` — don't regenerate; the evaluators compare against it.

Other top-level dirs: `schema/` (JSON Schema definitions), `reports/` (generated evaluation reports, e.g. `taxonomy_comparison.md`), `cache/` (source checksums + pipeline logs), `tools/tagging_tool.html` (standalone browser review/annotation tool, distinct from the deployed `docs/tag.html`).

### Reviewing / correcting automated tags (human-in-the-loop)

The automated map is high-recall and carries false positives. To correct them
locally with in-place persistence (no online tool, no manual file shuffling):

```bash
py scripts/review_server.py        # serves the repo on http://127.0.0.1:8000
# open http://127.0.0.1:8000/tools/tagging_tool.html
```

`tools/tagging_tool.html` loads `data/*.json`, shows each document with its
detections (provenance-marked N/L/M) against the source text, and lets you
confirm/reject techniques and evidence. Its **Save** button POSTs to the
server's `/api/save-map`, which writes `data/model_technique_map.json` **in
place** after backing up the prior version to `cache/tagging_backups/`. Rejected
items are soft-deleted (`active: false` with a `deleted_by` provenance), which
also feeds the LLM review index so the same false positives are suppressed on
future runs. After a review session, `python scripts/validate.py` then commit +
push — the dashboard reads `data/*.json` from `main`, so it updates on push.

(Served by a plain `python -m http.server` instead, the tool still works but
Save falls back to downloading a copy you must move into `data/` by hand.)
