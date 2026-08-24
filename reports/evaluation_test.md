# Evaluation Report

- **Split:** `test` (11 docs scored, 0 no-safety excluded)
- **Automated:** `D:\LLM Safety Mechanisms\data\model_technique_map.json` (sha256 `2e432bd1fd44`)
- **Ground truth:** `D:\LLM Safety Mechanisms\data\model_technique_map_reviewed.json` (sha256 `5512deecb87d`)
- **Split gold_sha256:** `aa076a242175`
- **Model:** `claude-opus-5`  ·  **Commit:** `5cbbfdd`  ·  **Generated:** 2026-08-24T11:54:49+00:00

> Single-rater metrics — inter-annotator κ not yet computable (see data/eval/README.md).

## Overall

| Metric | Value |
|--------|-------|
| True Positives | 87 |
| False Positives | 88 |
| False Negatives | 30 |
| **Precision** | **49.7%** |
| **Recall** | **74.4%** |
| **F1** | **59.6%** |
| Grounded precision | 49.7% (87/175) |

## Per-stage (attribution)

| Stage | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| nlu | 79 | 80 | 38 | 50% | 68% | 57% |
| llm | 21 | 10 | 96 | 68% | 18% | 28% |

## Recall by evidence source (in ground truth)

| Source | Recovered | Missed | Recall |
|--------|-----------|--------|--------|
| nlu | 9 | 11 | 45.0% |
| llm | 44 | 17 | 72.1% |
| manual | 34 | 2 | 94.4% |

## Per-category

| Category | TP | FP | FN | Precision | Recall | F1 |
|----------|----|----|----|-----------|--------|----|
| Evaluation & Red Teaming | 7 | 4 | 4 | 64% | 64% | 64% |
| Governance & Oversight | 19 | 26 | 4 | 42% | 83% | 56% |
| Harm & Content Classification | 23 | 24 | 7 | 49% | 77% | 60% |
| Model Development | 18 | 18 | 5 | 50% | 78% | 61% |
| Runtime Safety Systems | 20 | 16 | 10 | 56% | 67% | 61% |
