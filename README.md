# LLM Safety Mechanisms Dataset

[![GitHub issues](https://img.shields.io/github/issues/sashaagafonoff/LLM-Safety-Mechanisms)](https://github.com/sashaagafonoff/LLM-Safety-Mechanisms/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTORS.md)
[![Dashboard](https://img.shields.io/badge/dashboard-live-blue)](https://sashaagafonoff.github.io/LLM-Safety-Mechanisms/)

**A structured dataset and analysis tool for tracking safety mechanisms implemented by LLM providers.**

As AI systems become more powerful, understanding their safety mechanisms is critical for researchers, policymakers, and practitioners. This project maintains structured data about how providers implement safety techniques, extracted from official documentation, system cards, and technical reports.

**[View Interactive Dashboard](https://sashaagafonoff.github.io/LLM-Safety-Mechanisms/)** | **[View on Observable](https://observablehq.com/d/88c345368b7d0fa1)**

## Dataset at a Glance

- **48 active safety techniques** across **5 categories** (+2 aspirational)
- **14 providers** (OpenAI, Anthropic, Google, Meta, Cohere, Mistral, xAI, and more)
- **40 source documents** (system cards, technical reports, safety frameworks)
- **461+ technique-document links** with provenance tracking

## Safety Taxonomy

Techniques are organised into five categories that span the model lifecycle:

| Category | Description | Example Techniques |
|----------|-------------|-------------------|
| **Model Development** | Pre-training data safety and alignment methods | RLHF, DPO, Constitutional AI, Training Data Filtering |
| **Evaluation & Red Teaming** | Pre-deployment testing and capability assessment | Red Teaming, Safety Benchmarking, Frontier Risk Evaluation |
| **Runtime Safety Systems** | Input/output filtering, guardrails, and monitoring | Jailbreak Defense, System Prompts, Multi-stage Safety Pipeline |
| **Harm & Content Classification** | Cross-stage classifiers for specific harm types | CSAM Detection, Violence Detection, PII Redaction |
| **Governance & Oversight** | Organisational structures, compliance, and release protocols | Responsible Release, Regulatory Compliance, Incident Reporting |

Each technique also maps to **lifecycle stages** (pre-training, training, evaluation, inference, governance) and **risk areas** for cross-cutting analysis.

## Extraction Methodology

The dataset is built using a three-stage pipeline that combines automated extraction with human review:

### Stage 1: Document Ingestion
Source documents (PDFs, HTML pages, system cards) are downloaded and converted to clean text using `scripts/ingest_universal.py`.

### Stage 2: NLU Extraction
A two-stage semantic analysis pipeline identifies technique mentions:
1. **Retrieval**: `all-mpnet-base-v2` sentence embeddings find candidate text chunks matching each technique's semantic anchors
2. **Verification**: `cross-encoder/nli-deberta-v3-small` performs natural language inference to confirm entailment against each technique's hypothesis

Quality filters exclude glossary definitions, "future work" mentions, and metadata-excluded topics.

### Stage 3: LLM Verification
Claude reviews each document with NLU findings as context, confirming matches, suggesting additions the NLU missed, and flagging false positives for removal. Each detection includes a supporting quote from the source text.

### Stage 4: Human Review
All automated findings are reviewed and corrected using a tagging tool (`tools/tagging_tool.html`). Each evidence passage carries provenance metadata (`created_by`: manual, nlu, or llm) for auditability.

### Pipeline Performance

Measured against manually-reviewed ground truth (375 technique-document links):

| Metric | NLU Only | NLU + LLM |
|--------|----------|-----------|
| Precision | 75.4% | 73.6% |
| Recall | 76.0% | 89.3% |
| F1 Score | 75.7% | 80.7% |

The LLM stage recovers techniques that require contextual understanding beyond semantic similarity — particularly Red Teaming mentions (recall improved from 24% to 91%) and governance techniques.

## Project Structure

```
data/
├── evidence.json                    # Core evidence linking providers to techniques
├── techniques.json                  # 50 safety technique definitions with NLU profiles
├── categories.json                  # 5 technique categories
├── providers.json                   # Provider metadata
├── models.json                      # Model metadata
├── risk_areas.json                  # Risk area taxonomy
├── model_lifecycle.json             # Lifecycle stage definitions
├── model_technique_map.json         # Generated: document-to-technique mappings
├── model_technique_map_reviewed.json # Reviewed ground truth for evaluation
├── map_nlu.json                     # NLU stage output
├── map_llm.json                     # LLM stage output
└── flat_text/                       # Processed source documents

scripts/
├── ingest_universal.py              # Document ingestion (PDF, HTML, text)
├── clean_flat_text.py               # Post-ingestion cleanup (TOC, refs, tables)
├── analyze_nlu.py                   # NLU technique extraction
├── run_extraction_pipeline.py       # Full pipeline orchestration
├── llm_assisted_extraction.py       # LLM-based technique extraction (Claude API)
├── compare_taxonomy_runs.py         # Evaluation against ground truth
├── check_sources.py                 # Source change detection for automation
├── generate_dashboard.py            # Interactive dashboard generation
├── generate_report.py               # Summary report generation
└── semantic_retriever.py            # Semantic search utility

tools/
└── tagging_tool.html                # Browser-based review and annotation tool

reports/
└── taxonomy_comparison.md           # Latest pipeline evaluation results

cache/                               # Source checksums and pipeline logs
docs/                                # Generated dashboard (GitHub Pages)
```

## Getting Started

### Prerequisites

```bash
pip install -r requirements.txt

# For NLU analysis (large download):
pip install sentence-transformers
```

### Running the Pipeline

There are two workflow modes:

**Mode A: Full collection** (after changing taxonomy or semantic anchors):
```bash
python scripts/run_extraction_pipeline.py --regenerate
```

**Mode B: Single document** (after adding or updating a document):
```bash
python scripts/ingest_universal.py --id <document-id>
python scripts/run_extraction_pipeline.py --id <document-id> --regenerate
```

**Individual stages:**
```bash
# NLU only:
python scripts/run_extraction_pipeline.py --nlu-only

# LLM only (uses existing NLU results):
python scripts/run_extraction_pipeline.py --llm-only

# Re-download all sources (--force overwrites existing files):
python scripts/ingest_universal.py --force

# Clean flat text files (remove TOCs, references, tables):
python scripts/clean_flat_text.py

# Evaluate against ground truth:
python scripts/compare_taxonomy_runs.py --detailed

# Check sources for updates:
python scripts/check_sources.py                     # Report only
python scripts/check_sources.py --update --analyse   # Re-ingest and analyse changed docs
```

## Contributing

Contributions are welcome! See [CONTRIBUTORS.md](CONTRIBUTORS.md) for acknowledgments.

The most impactful contributions are:
- Adding new source documents and evidence records
- Reviewing and correcting automated technique detections
- Improving NLU semantic anchors for low-performing techniques
