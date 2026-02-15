# Taxonomy Comparison Report

Comparison of automated extraction (new taxonomy) against manually-reviewed ground truth.

## Overall Metrics

| Metric | Value |
|--------|-------|
| True Positives | 335 |
| False Positives | 120 |
| False Negatives | 40 |
| **Precision** | **73.6%** |
| **Recall** | **89.3%** |
| **F1 Score** | **80.7%** |

## Recall by Evidence Source

How well the automated pipeline recovers techniques that were originally found by each source.

| Source | Recovered | Missed | Recall |
|--------|-----------|--------|--------|
| nlu | 67 | 6 | 91.8% |
| llm | 156 | 32 | 83.0% |
| manual | 112 | 2 | 98.2% |

## Per-Category Performance

| Category | TP | FP | FN | Precision | Recall | F1 |
|----------|----|----|----|-----------|---------|----|
| Evaluation & Red Teaming | 41 | 11 | 4 | 78.8% | 91.1% | 84.5% |
| Governance & Oversight | 64 | 16 | 13 | 80.0% | 83.1% | 81.5% |
| Harm & Content Classification | 62 | 37 | 6 | 62.6% | 91.2% | 74.3% |
| Model Development | 83 | 26 | 10 | 76.1% | 89.2% | 82.2% |
| Runtime Safety Systems | 85 | 24 | 7 | 78.0% | 92.4% | 84.6% |
| unknown | 0 | 6 | 0 | 0.0% | 0.0% | 0.0% |

## Technique-Level Analysis

### Techniques Needing Improvement (lowest F1)

| Technique | TP | FP | FN | Precision | Recall | F1 |
|-----------|----|----|----|-----------|---------|----|
| Cybersecurity Threat Detection | 0 | 8 | 0 | 0% | 0% | 0% |
| Autonomous Behaviour Classification | 0 | 3 | 0 | 0% | 0% | 0% |
| tech-safety-policies | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-frontier-risk-evaluation | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-safety-benchmarking | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-rlaif | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-vulnerability-reporting | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-transparency | 0 | 1 | 0 | 0% | 0% | 0% |
| RAG Guardrails | 1 | 6 | 0 | 14% | 100% | 25% |
| Responsible Release Protocols | 2 | 0 | 4 | 100% | 33% | 50% |
| Data Retention Policies | 1 | 0 | 2 | 100% | 33% | 50% |
| Provenance & Watermarking | 3 | 2 | 1 | 60% | 75% | 67% |
| Data Sovereignty Controls | 2 | 2 | 0 | 50% | 100% | 67% |
| Code Execution Sandboxing | 1 | 0 | 1 | 100% | 50% | 67% |
| Community-Based Evaluation | 6 | 5 | 0 | 55% | 100% | 71% |

### Well-Performing Techniques (highest F1)

| Technique | TP | FP | FN | Precision | Recall | F1 |
|-----------|----|----|----|-----------|---------|----|
| Jailbreak & Injection Defense | 15 | 0 | 0 | 100% | 100% | 100% |
| Direct Preference Optimization (DPO) | 6 | 0 | 0 | 100% | 100% | 100% |
| Copyright & IP Violation Detection | 3 | 0 | 0 | 100% | 100% | 100% |
| Access Control Documentation | 3 | 0 | 0 | 100% | 100% | 100% |
| Enterprise Integration Safety | 2 | 0 | 0 | 100% | 100% | 100% |
| Multi-stage Safety Pipeline | 9 | 1 | 0 | 90% | 100% | 95% |
| Configurable Safety Policies | 9 | 1 | 0 | 90% | 100% | 95% |
| System Prompts / Metaprompts | 9 | 1 | 0 | 90% | 100% | 95% |
| CSAM Detection & Prevention | 6 | 0 | 1 | 100% | 86% | 92% |
| Regulatory Compliance | 5 | 0 | 1 | 100% | 83% | 91% |

### New Techniques (automated only, not in ground truth)

These are new taxonomy techniques — automated detections with no ground truth to validate against.

| Technique | Auto Detections |
|-----------|----------------|
| Cybersecurity Threat Detection | 0 |
| Autonomous Behaviour Classification | 0 |
| tech-safety-policies | 0 |
| tech-frontier-risk-evaluation | 0 |
| tech-safety-benchmarking | 0 |
| tech-rlaif | 0 |
| tech-vulnerability-reporting | 0 |
| tech-transparency | 0 |

## Per-Document Details

### claude-3-5-sonnet-card
Ground truth: 9 | Automated: 8 | TP: 7 | FP: 1 | FN: 2
- False positives: Independent Safety Advisory
- Missed: Constitutional AI / Self-Critique, Responsible Release Protocols

### claude-3-haiku-model-card
Ground truth: 15 | Automated: 16 | TP: 14 | FP: 2 | FN: 1
- False positives: tech-frontier-risk-evaluation, Incident Reporting Systems
- Missed: Capability Threshold Monitoring

### claude-opus-4-5-system-card
Ground truth: 25 | Automated: 29 | TP: 25 | FP: 4 | FN: 0
- False positives: Autonomous Behaviour Classification, Community-Based Evaluation, Incident Reporting Systems, PII Detection & Redaction

### cohere-safety-framework
Ground truth: 7 | Automated: 9 | TP: 7 | FP: 2 | FN: 0
- False positives: Cybersecurity Threat Detection, Incident Reporting Systems

### command-a
Ground truth: 14 | Automated: 19 | TP: 14 | FP: 5 | FN: 0
- False positives: Community-Based Evaluation, Input Guardrail Systems, RAG Guardrails, Real-time Fact Checking, Safety Benchmarking

### deepseek-privacy
Ground truth: 5 | Automated: 4 | TP: 4 | FP: 0 | FN: 1
- Missed: Data Retention Policies

### deepseek-r1-paper
Ground truth: 15 | Automated: 24 | TP: 15 | FP: 9 | FN: 0
- False positives: Adversarial Training, Capability Threshold Monitoring, Community-Based Evaluation, Hate Speech & Harassment Detection, Incident Reporting Systems, Misinformation & False Claims Detection, RAG Guardrails, Red Teaming, System Prompts / Metaprompts

### deepseek-v3-paper
Ground truth: 6 | Automated: 8 | TP: 5 | FP: 3 | FN: 1
- False positives: Constitutional AI / Self-Critique, RAG Guardrails, tech-safety-benchmarking
- Missed: Dataset Auditing & Representation Analysis

### gemini-1-5-paper
Ground truth: 12 | Automated: 19 | TP: 9 | FP: 10 | FN: 3
- False positives: Community-Based Evaluation, Cybersecurity Threat Detection, Hate Speech & Harassment Detection, Input Guardrail Systems, Misinformation & False Claims Detection, Multimodal Safety Alignment, Output Safety Systems, Safety Benchmarking, Sexual Content Moderation, Violence & Gore Detection
- Missed: Dataset Auditing & Representation Analysis, Observability & Audit Logging, Training Data Quality Filtering

### gemini-25-flash-lite
Ground truth: 9 | Automated: 8 | TP: 5 | FP: 3 | FN: 4
- False positives: Bias Mitigation (Post-Training), Reinforcement Learning from Human Feedback (RLHF), Safety Benchmarking
- Missed: CSAM Detection & Prevention, Hate Speech & Harassment Detection, Safety Reward Modeling, Self-Harm & Suicide Prevention

### gemini-3-pro
Ground truth: 8 | Automated: 12 | TP: 7 | FP: 5 | FN: 1
- False positives: Bias Mitigation (Post-Training), Misinformation & False Claims Detection, Output Safety Systems, tech-safety-policies, Sexual Content Moderation
- Missed: Dataset Auditing & Representation Analysis

### gemini-3-technical-report
Ground truth: 11 | Automated: 9 | TP: 9 | FP: 0 | FN: 2
- Missed: Hallucination Detection & Grounding, Misinformation & False Claims Detection

### google-ai-principles-2024
Ground truth: 9 | Automated: 11 | TP: 8 | FP: 3 | FN: 1
- False positives: Cybersecurity Threat Detection, PII Detection & Redaction, Reinforcement Learning from Human Feedback (RLHF)
- Missed: Capability Threshold Monitoring

### gpt-4o-system-card
Ground truth: 13 | Automated: 16 | TP: 13 | FP: 3 | FN: 0
- False positives: Cybersecurity Threat Detection, PII Detection & Redaction, Weapons & Illegal Activity Detection

### gpt-5-system-card
Ground truth: 27 | Automated: 28 | TP: 26 | FP: 2 | FN: 1
- False positives: Autonomous Behaviour Classification, Self-Harm & Suicide Prevention
- Missed: Red Teaming

### grok-4
Ground truth: 8 | Automated: 8 | TP: 7 | FP: 1 | FN: 1
- False positives: Weapons & Illegal Activity Detection
- Missed: Red Teaming

### hunyuan-technical-report
Ground truth: 5 | Automated: 10 | TP: 5 | FP: 5 | FN: 0
- False positives: Bias Mitigation (Post-Training), Community-Based Evaluation, Input Guardrail Systems, RAG Guardrails, Refusal / Abstention Training

### llama-3-paper
Ground truth: 26 | Automated: 32 | TP: 25 | FP: 7 | FN: 1
- False positives: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Data Sovereignty Controls, Incident Reporting Systems, Multimodal Safety Alignment, RAG Guardrails, Safety Reward Modeling
- Missed: Safety Benchmarking

### llama-4-maverick
Ground truth: 7 | Automated: 10 | TP: 6 | FP: 4 | FN: 1
- False positives: Capability Threshold Monitoring, Cybersecurity Threat Detection, Incident Reporting Systems, Multimodal Safety Alignment
- Missed: Safety Benchmarking

### llama-4-responsible-use-guide
Ground truth: 8 | Automated: 8 | TP: 4 | FP: 4 | FN: 4
- False positives: Bias Mitigation (Post-Training), Red Teaming, Safety Benchmarking, Provenance & Watermarking
- Missed: Regulatory Compliance, Responsible Release Protocols, Independent Safety Advisory, Stakeholder Engagement

### meta-llama-responsible-use
Ground truth: 17 | Automated: 17 | TP: 14 | FP: 3 | FN: 3
- False positives: PII Detection & Redaction, tech-rlaif, tech-transparency
- Missed: Refusal / Abstention Training, Provenance & Watermarking, Weapons & Illegal Activity Detection

### microsoft-rai-standard
Ground truth: 5 | Automated: 9 | TP: 5 | FP: 4 | FN: 0
- False positives: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Dataset Auditing & Representation Analysis, PII Detection & Redaction

### mistral-large-3
Ground truth: 10 | Automated: 12 | TP: 9 | FP: 3 | FN: 1
- False positives: Misinformation & False Claims Detection, Multimodal Safety Alignment, Refusal / Abstention Training
- Missed: Weapons & Illegal Activity Detection

### nemotron-4-tech-report
Ground truth: 13 | Automated: 17 | TP: 9 | FP: 8 | FN: 4
- False positives: Hate Speech & Harassment Detection, Input Guardrail Systems, Misinformation & False Claims Detection, Multi-stage Safety Pipeline, RAG Guardrails, Sexual Content Moderation, Violence & Gore Detection, Weapons & Illegal Activity Detection
- Missed: Capability Threshold Monitoring, Dataset Auditing & Representation Analysis, Observability & Audit Logging, Training Data Quality Filtering

### o3-pro
Ground truth: 13 | Automated: 20 | TP: 12 | FP: 8 | FN: 1
- False positives: Constitutional AI / Self-Critique, Cybersecurity Threat Detection, Hallucination Detection & Grounding, Input Guardrail Systems, Multimodal Safety Alignment, PII Detection & Redaction, Sexual Content Moderation, Training Data Quality Filtering
- Missed: Observability & Audit Logging

### openai-preparedness
Ground truth: 8 | Automated: 9 | TP: 7 | FP: 2 | FN: 1
- False positives: Autonomous Behaviour Classification, Safety Reward Modeling
- Missed: Responsible Release Protocols

### phi-4-tech-report
Ground truth: 8 | Automated: 12 | TP: 8 | FP: 4 | FN: 0
- False positives: Hallucination Detection & Grounding, Input Guardrail Systems, Misinformation & False Claims Detection, Violence & Gore Detection

### qwen2-5-coder-tech-report
Ground truth: 5 | Automated: 4 | TP: 4 | FP: 0 | FN: 1
- Missed: Code Execution Sandboxing

### qwen2-5-tech-report
Ground truth: 4 | Automated: 7 | TP: 2 | FP: 5 | FN: 2
- False positives: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Input Guardrail Systems, Refusal / Abstention Training, Provenance & Watermarking
- Missed: Hallucination Detection & Grounding, Multimodal Safety Alignment

### qwen3-max
Ground truth: 22 | Automated: 27 | TP: 22 | FP: 5 | FN: 0
- False positives: Capability Threshold Monitoring, Configurable Safety Policies, Cybersecurity Threat Detection, Incident Reporting Systems, Reinforcement Learning from Human Feedback (RLHF)

### xai-security
Ground truth: 8 | Automated: 10 | TP: 5 | FP: 5 | FN: 3
- False positives: Cybersecurity Threat Detection, Data Sovereignty Controls, Input Guardrail Systems, Safety Reward Modeling, tech-vulnerability-reporting
- Missed: Capability Threshold Monitoring, Data Retention Policies, Responsible Release Protocols
