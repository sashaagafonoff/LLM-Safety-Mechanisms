# Evaluation Report

- **Split:** `dev` (22 docs scored, 2 no-safety excluded)
- **Automated:** `D:\LLM Safety Mechanisms\data\model_technique_map.json` (sha256 `0a909e9f9fd9`)
- **Ground truth:** `D:\LLM Safety Mechanisms\data\model_technique_map_reviewed.json` (sha256 `5512deecb87d`)
- **Split gold_sha256:** `aa076a242175`
- **Model:** `n/a`  ·  **Commit:** `b81552a`  ·  **Generated:** 2026-06-20T02:12:16+00:00

> Single-rater metrics — inter-annotator κ not yet computable (see data/eval/README.md).

## Overall

| Metric | Value |
|--------|-------|
| True Positives | 180 |
| False Positives | 152 |
| False Negatives | 78 |
| **Precision** | **54.2%** |
| **Recall** | **69.8%** |
| **F1** | **61.0%** |
| Grounded precision | 54.2% (180/332) |

## Per-stage (attribution)

| Stage | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| nlu | 160 | 116 | 98 | 58% | 62% | 60% |
| llm | 108 | 84 | 150 | 56% | 42% | 48% |

## Recall by evidence source (in ground truth)

| Source | Recovered | Missed | Recall |
|--------|-----------|--------|--------|
| nlu | 18 | 35 | 34.0% |
| llm | 93 | 30 | 75.6% |
| manual | 69 | 13 | 84.1% |

## Per-category

| Category | TP | FP | FN | Precision | Recall | F1 |
|----------|----|----|----|-----------|--------|----|
| Evaluation & Red Teaming | 29 | 9 | 5 | 76% | 85% | 81% |
| Governance & Oversight | 33 | 28 | 22 | 54% | 60% | 57% |
| Harm & Content Classification | 34 | 34 | 7 | 50% | 83% | 62% |
| Model Development | 43 | 50 | 24 | 46% | 64% | 54% |
| Runtime Safety Systems | 41 | 31 | 20 | 57% | 67% | 62% |
