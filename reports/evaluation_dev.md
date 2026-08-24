# Evaluation Report

- **Split:** `dev` (22 docs scored, 2 no-safety excluded)
- **Automated:** `D:\LLM Safety Mechanisms\data\model_technique_map.json` (sha256 `2e432bd1fd44`)
- **Ground truth:** `D:\LLM Safety Mechanisms\data\model_technique_map_reviewed.json` (sha256 `5512deecb87d`)
- **Split gold_sha256:** `aa076a242175`
- **Model:** `claude-opus-5`  ·  **Commit:** `5cbbfdd`  ·  **Generated:** 2026-08-24T11:54:49+00:00

> Single-rater metrics — inter-annotator κ not yet computable (see data/eval/README.md).

## Overall

| Metric | Value |
|--------|-------|
| True Positives | 184 |
| False Positives | 149 |
| False Negatives | 74 |
| **Precision** | **55.3%** |
| **Recall** | **71.3%** |
| **F1** | **62.3%** |
| Grounded precision | 55.3% (184/333) |

## Per-stage (attribution)

| Stage | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| nlu | 171 | 121 | 87 | 59% | 66% | 62% |
| llm | 61 | 40 | 197 | 60% | 24% | 34% |

## Recall by evidence source (in ground truth)

| Source | Recovered | Missed | Recall |
|--------|-----------|--------|--------|
| nlu | 34 | 19 | 64.2% |
| llm | 81 | 42 | 65.9% |
| manual | 69 | 13 | 84.1% |

## Per-category

| Category | TP | FP | FN | Precision | Recall | F1 |
|----------|----|----|----|-----------|--------|----|
| Evaluation & Red Teaming | 29 | 12 | 5 | 71% | 85% | 77% |
| Governance & Oversight | 38 | 38 | 17 | 50% | 69% | 58% |
| Harm & Content Classification | 36 | 29 | 5 | 55% | 88% | 68% |
| Model Development | 39 | 25 | 28 | 61% | 58% | 60% |
| Runtime Safety Systems | 42 | 45 | 19 | 48% | 69% | 57% |
