# Taxonomy Comparison Report

Comparison of automated extraction (new taxonomy) against manually-reviewed ground truth.

## Overall Metrics

| Metric | Value |
|--------|-------|
| True Positives | 267 |
| False Positives | 370 |
| False Negatives | 112 |
| **Precision** | **41.9%** |
| **Recall** | **70.4%** |
| **F1 Score** | **52.6%** |

## Recall by Evidence Source

How well the automated pipeline recovers techniques that were originally found by each source.

| Source | Recovered | Missed | Recall |
|--------|-----------|--------|--------|
| nlu | 25 | 48 | 34.2% |
| llm | 139 | 49 | 73.9% |
| manual | 103 | 15 | 87.3% |

## Per-Category Performance

| Category | TP | FP | FN | Precision | Recall | F1 |
|----------|----|----|----|-----------|---------|----|
| Evaluation & Red Teaming | 34 | 26 | 11 | 56.7% | 75.6% | 64.8% |
| Governance & Oversight | 45 | 96 | 33 | 31.9% | 57.7% | 41.1% |
| Harm & Content Classification | 59 | 80 | 12 | 42.4% | 83.1% | 56.2% |
| Model Development | 61 | 94 | 32 | 39.4% | 65.6% | 49.2% |
| Runtime Safety Systems | 68 | 74 | 24 | 47.9% | 73.9% | 58.1% |

## Technique-Level Analysis

### Techniques Needing Improvement (lowest F1)

| Technique | TP | FP | FN | Precision | Recall | F1 |
|-----------|----|----|----|-----------|---------|----|
| Scalable Oversight & Debate | 0 | 17 | 0 | 0% | 0% | 0% |
| Voluntary Safety Commitments & Pledges | 0 | 11 | 0 | 0% | 0% | 0% |
| Model Weight Security | 0 | 11 | 0 | 0% | 0% | 0% |
| Autonomous Behaviour Classification | 0 | 8 | 0 | 0% | 0% | 0% |
| Cybersecurity Threat Detection | 0 | 7 | 0 | 0% | 0% | 0% |
| Data Sovereignty Controls | 0 | 5 | 2 | 0% | 0% | 0% |
| Differential Privacy in Training | 0 | 6 | 0 | 0% | 0% | 0% |
| RAG Guardrails | 0 | 4 | 1 | 0% | 0% | 0% |
| Circuit Breakers / Kill Switches | 0 | 5 | 0 | 0% | 0% | 0% |
| Machine Unlearning | 0 | 4 | 0 | 0% | 0% | 0% |
| Whistleblower & Internal Safety Reporting | 0 | 2 | 0 | 0% | 0% | 0% |
| Supervised Fine-Tuning (SFT) | 0 | 1 | 0 | 0% | 0% | 0% |
| Access Control Documentation | 1 | 11 | 2 | 8% | 33% | 13% |
| Community-Based Evaluation | 1 | 7 | 5 | 12% | 17% | 14% |
| Ethical Human Labour Sourcing | 1 | 6 | 0 | 14% | 100% | 25% |

### Well-Performing Techniques (highest F1)

| Technique | TP | FP | FN | Precision | Recall | F1 |
|-----------|----|----|----|-----------|---------|----|
| Jailbreak & Injection Defense | 13 | 4 | 2 | 76% | 87% | 81% |
| Red Teaming | 18 | 8 | 3 | 69% | 86% | 77% |
| Refusal / Abstention Training | 11 | 3 | 4 | 79% | 73% | 76% |
| Direct Preference Optimization (DPO) | 6 | 5 | 0 | 55% | 100% | 71% |
| Violence & Gore Detection | 8 | 7 | 0 | 53% | 100% | 70% |
| Safety Benchmarking | 15 | 11 | 3 | 58% | 83% | 68% |
| Capability Threshold Monitoring | 13 | 4 | 9 | 76% | 59% | 67% |
| PII Detection & Redaction | 8 | 7 | 1 | 53% | 89% | 67% |
| Weapons & Illegal Activity Detection | 8 | 7 | 1 | 53% | 89% | 67% |
| Regulatory Compliance | 5 | 4 | 1 | 56% | 83% | 67% |

### New Techniques (automated only, not in ground truth)

These are new taxonomy techniques — automated detections with no ground truth to validate against.

| Technique | Auto Detections |
|-----------|----------------|
| Scalable Oversight & Debate | 0 |
| Voluntary Safety Commitments & Pledges | 0 |
| Model Weight Security | 0 |
| Autonomous Behaviour Classification | 0 |
| Cybersecurity Threat Detection | 0 |
| Differential Privacy in Training | 0 |
| Circuit Breakers / Kill Switches | 0 |
| Machine Unlearning | 0 |
| Whistleblower & Internal Safety Reporting | 0 |
| Supervised Fine-Tuning (SFT) | 0 |
