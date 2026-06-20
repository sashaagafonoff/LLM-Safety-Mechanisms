# Evaluation Report

- **Split:** `test` (11 docs scored, 0 no-safety excluded)
- **Automated:** `D:\LLM Safety Mechanisms\data\model_technique_map.json` (sha256 `0a909e9f9fd9`)
- **Ground truth:** `D:\LLM Safety Mechanisms\data\model_technique_map_reviewed.json` (sha256 `5512deecb87d`)
- **Split gold_sha256:** `aa076a242175`
- **Model:** `n/a`  ·  **Commit:** `b81552a`  ·  **Generated:** 2026-06-20T02:12:16+00:00

> Single-rater metrics — inter-annotator κ not yet computable (see data/eval/README.md).

## Overall

| Metric | Value |
|--------|-------|
| True Positives | 92 |
| False Positives | 128 |
| False Negatives | 25 |
| **Precision** | **41.8%** |
| **Recall** | **78.6%** |
| **F1** | **54.6%** |
| Grounded precision | 41.8% (92/220) |

## Per-stage (attribution)

| Stage | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| nlu | 78 | 109 | 39 | 42% | 67% | 51% |
| llm | 45 | 31 | 72 | 59% | 38% | 47% |

## Recall by evidence source (in ground truth)

| Source | Recovered | Missed | Recall |
|--------|-----------|--------|--------|
| nlu | 11 | 9 | 55.0% |
| llm | 46 | 15 | 75.4% |
| manual | 35 | 1 | 97.2% |

## Per-category

| Category | TP | FP | FN | Precision | Recall | F1 |
|----------|----|----|----|-----------|--------|----|
| Evaluation & Red Teaming | 7 | 9 | 4 | 44% | 64% | 52% |
| Governance & Oversight | 18 | 36 | 5 | 33% | 78% | 47% |
| Harm & Content Classification | 25 | 27 | 5 | 48% | 83% | 61% |
| Model Development | 19 | 31 | 4 | 38% | 83% | 52% |
| Runtime Safety Systems | 23 | 25 | 7 | 48% | 77% | 59% |
