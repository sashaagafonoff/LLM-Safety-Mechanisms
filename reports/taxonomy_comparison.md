# Taxonomy Comparison Report

Comparison of automated extraction (new taxonomy) against manually-reviewed ground truth.

## Overall Metrics

| Metric | Value |
|--------|-------|
| True Positives | 339 |
| False Positives | 122 |
| False Negatives | 40 |
| **Precision** | **73.5%** |
| **Recall** | **89.4%** |
| **F1 Score** | **80.7%** |

## Recall by Evidence Source

How well the automated pipeline recovers techniques that were originally found by each source.

| Source | Recovered | Missed | Recall |
|--------|-----------|--------|--------|
| nlu | 67 | 6 | 91.8% |
| llm | 156 | 32 | 83.0% |
| manual | 116 | 2 | 98.3% |

## Per-Category Performance

| Category | TP | FP | FN | Precision | Recall | F1 |
|----------|----|----|----|-----------|---------|----|
| Evaluation & Red Teaming | 41 | 13 | 4 | 75.9% | 91.1% | 82.8% |
| Governance & Oversight | 65 | 11 | 13 | 85.5% | 83.3% | 84.4% |
| Harm & Content Classification | 65 | 36 | 6 | 64.4% | 91.5% | 75.6% |
| Model Development | 83 | 30 | 10 | 73.5% | 89.2% | 80.6% |
| Runtime Safety Systems | 85 | 26 | 7 | 76.6% | 92.4% | 83.7% |
| unknown | 0 | 6 | 0 | 0.0% | 0.0% | 0.0% |

## Technique-Level Analysis

### Techniques Needing Improvement (lowest F1)

| Technique | TP | FP | FN | Precision | Recall | F1 |
|-----------|----|----|----|-----------|---------|----|
| Cybersecurity Threat Detection | 0 | 3 | 0 | 0% | 0% | 0% |
| Autonomous Behaviour Classification | 0 | 3 | 0 | 0% | 0% | 0% |
| tech-safety-benchmarking | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-vulnerability-reporting | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-rlaif | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-safety-policies | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-transparency | 0 | 1 | 0 | 0% | 0% | 0% |
| tech-frontier-risk-evaluation | 0 | 1 | 0 | 0% | 0% | 0% |
| RAG Guardrails | 1 | 4 | 0 | 20% | 100% | 33% |
| Responsible Release Protocols | 2 | 0 | 4 | 100% | 33% | 50% |
| Data Retention Policies | 1 | 0 | 2 | 100% | 33% | 50% |
| Provenance & Watermarking | 3 | 3 | 1 | 50% | 75% | 60% |
| Bias Mitigation (Post-Training) | 9 | 10 | 0 | 47% | 100% | 64% |
| Data Sovereignty Controls | 2 | 2 | 0 | 50% | 100% | 67% |
| Code Execution Sandboxing | 1 | 0 | 1 | 100% | 50% | 67% |

### Well-Performing Techniques (highest F1)

| Technique | TP | FP | FN | Precision | Recall | F1 |
|-----------|----|----|----|-----------|---------|----|
| Jailbreak & Injection Defense | 15 | 0 | 0 | 100% | 100% | 100% |
| Direct Preference Optimization (DPO) | 6 | 0 | 0 | 100% | 100% | 100% |
| Copyright & IP Violation Detection | 3 | 0 | 0 | 100% | 100% | 100% |
| Access Control Documentation | 3 | 0 | 0 | 100% | 100% | 100% |
| Sycophancy Detection | 3 | 0 | 0 | 100% | 100% | 100% |
| Enterprise Integration Safety | 2 | 0 | 0 | 100% | 100% | 100% |
| Ethical Human Labour Sourcing | 1 | 0 | 0 | 100% | 100% | 100% |
| Multi-stage Safety Pipeline | 9 | 1 | 0 | 90% | 100% | 95% |
| Incident Reporting Systems | 22 | 4 | 0 | 85% | 100% | 92% |
| Regulatory Compliance | 5 | 0 | 1 | 100% | 83% | 91% |

### New Techniques (automated only, not in ground truth)

These are new taxonomy techniques — automated detections with no ground truth to validate against.

| Technique | Auto Detections |
|-----------|----------------|
| Cybersecurity Threat Detection | 0 |
| Autonomous Behaviour Classification | 0 |
| tech-safety-benchmarking | 0 |
| tech-vulnerability-reporting | 0 |
| tech-rlaif | 0 |
| tech-safety-policies | 0 |
| tech-transparency | 0 |
| tech-frontier-risk-evaluation | 0 |

## Per-Document Details

### aws-nova-service-card
Ground truth: 0 | Automated: 11 | TP: 0 | FP: 11 | FN: 0
- False positives: Bias Mitigation (Post-Training), Configurable Safety Policies, CSAM Detection & Prevention, Incident Reporting Systems, Input Guardrail Systems, Misinformation & False Claims Detection, Output Safety Systems, Red Teaming, Reinforcement Learning from Human Feedback (RLHF), Safety Benchmarking, Violence & Gore Detection

### claude-3-5-sonnet-card
Ground truth: 9 | Automated: 8 | TP: 7 | FP: 1 | FN: 2
- False positives: Independent Safety Advisory
- Missed: Constitutional AI / Self-Critique, Responsible Release Protocols

### claude-3-haiku-model-card
Ground truth: 15 | Automated: 16 | TP: 14 | FP: 2 | FN: 1
- False positives: tech-frontier-risk-evaluation, Incident Reporting Systems
- Missed: Capability Threshold Monitoring

### claude-opus-4-5-system-card
Ground truth: 27 | Automated: 31 | TP: 27 | FP: 4 | FN: 0
- False positives: Autonomous Behaviour Classification, Community-Based Evaluation, Incident Reporting Systems, PII Detection & Redaction

### cohere-safety-framework
Ground truth: 7 | Automated: 8 | TP: 7 | FP: 1 | FN: 0
- False positives: Cybersecurity Threat Detection

### command-a
Ground truth: 14 | Automated: 18 | TP: 14 | FP: 4 | FN: 0
- False positives: Input Guardrail Systems, RAG Guardrails, Real-time Fact Checking, Safety Benchmarking

### deepseek-privacy
Ground truth: 5 | Automated: 4 | TP: 4 | FP: 0 | FN: 1
- Missed: Data Retention Policies

### deepseek-r1-paper
Ground truth: 15 | Automated: 22 | TP: 15 | FP: 7 | FN: 0
- False positives: Adversarial Training, Community-Based Evaluation, Hate Speech & Harassment Detection, Misinformation & False Claims Detection, RAG Guardrails, Red Teaming, System Prompts / Metaprompts

### deepseek-v3-paper
Ground truth: 6 | Automated: 7 | TP: 5 | FP: 2 | FN: 1
- False positives: Constitutional AI / Self-Critique, tech-safety-benchmarking
- Missed: Dataset Auditing & Representation Analysis

### falcon-series-paper
Ground truth: 0 | Automated: 4 | TP: 0 | FP: 4 | FN: 0
- False positives: Misinformation & False Claims Detection, Refusal / Abstention Training, Training Data Quality Filtering, Provenance & Watermarking

### gemini-1-5-paper
Ground truth: 12 | Automated: 18 | TP: 9 | FP: 9 | FN: 3
- False positives: Community-Based Evaluation, Hate Speech & Harassment Detection, Input Guardrail Systems, Misinformation & False Claims Detection, Multimodal Safety Alignment, Output Safety Systems, Safety Benchmarking, Sexual Content Moderation, Violence & Gore Detection
- Missed: Dataset Auditing & Representation Analysis, Observability & Audit Logging, Training Data Quality Filtering

### gemini-25-flash-lite
Ground truth: 9 | Automated: 8 | TP: 5 | FP: 3 | FN: 4
- False positives: Bias Mitigation (Post-Training), Reinforcement Learning from Human Feedback (RLHF), Safety Benchmarking
- Missed: CSAM Detection & Prevention, Hate Speech & Harassment Detection, Safety Reward Modeling, Self-Harm & Suicide Prevention

### gemini-3-pro
Ground truth: 8 | Automated: 11 | TP: 7 | FP: 4 | FN: 1
- False positives: Bias Mitigation (Post-Training), Misinformation & False Claims Detection, tech-safety-policies, Sexual Content Moderation
- Missed: Dataset Auditing & Representation Analysis

### gemini-3-technical-report
Ground truth: 11 | Automated: 9 | TP: 9 | FP: 0 | FN: 2
- Missed: Hallucination Detection & Grounding, Misinformation & False Claims Detection

### google-ai-principles-2024
Ground truth: 9 | Automated: 10 | TP: 8 | FP: 2 | FN: 1
- False positives: PII Detection & Redaction, Reinforcement Learning from Human Feedback (RLHF)
- Missed: Capability Threshold Monitoring

### gpt-4o-system-card
Ground truth: 13 | Automated: 16 | TP: 13 | FP: 3 | FN: 0
- False positives: Cybersecurity Threat Detection, PII Detection & Redaction, Weapons & Illegal Activity Detection

### gpt-5-system-card
Ground truth: 28 | Automated: 29 | TP: 27 | FP: 2 | FN: 1
- False positives: Autonomous Behaviour Classification, Self-Harm & Suicide Prevention
- Missed: Red Teaming

### grok-4
Ground truth: 9 | Automated: 9 | TP: 8 | FP: 1 | FN: 1
- False positives: Weapons & Illegal Activity Detection
- Missed: Red Teaming

### hunyuan-technical-report
Ground truth: 5 | Automated: 7 | TP: 5 | FP: 2 | FN: 0
- False positives: Bias Mitigation (Post-Training), Refusal / Abstention Training

### llama-3-paper
Ground truth: 26 | Automated: 33 | TP: 25 | FP: 8 | FN: 1
- False positives: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Community-Based Evaluation, Data Sovereignty Controls, Incident Reporting Systems, Multimodal Safety Alignment, RAG Guardrails, Safety Reward Modeling
- Missed: Safety Benchmarking

### llama-4-maverick
Ground truth: 7 | Automated: 8 | TP: 6 | FP: 2 | FN: 1
- False positives: Cybersecurity Threat Detection, Multimodal Safety Alignment
- Missed: Safety Benchmarking

### llama-4-responsible-use-guide
Ground truth: 8 | Automated: 8 | TP: 4 | FP: 4 | FN: 4
- False positives: Bias Mitigation (Post-Training), Red Teaming, Safety Benchmarking, Provenance & Watermarking
- Missed: Regulatory Compliance, Responsible Release Protocols, Independent Safety Advisory, Stakeholder Engagement

### magistral-paper
Ground truth: 0 | Automated: 2 | TP: 0 | FP: 2 | FN: 0
- False positives: Bias Mitigation (Post-Training), Input Guardrail Systems

### meta-llama-responsible-use
Ground truth: 17 | Automated: 17 | TP: 14 | FP: 3 | FN: 3
- False positives: PII Detection & Redaction, tech-rlaif, tech-transparency
- Missed: Refusal / Abstention Training, Provenance & Watermarking, Weapons & Illegal Activity Detection

### microsoft-rai-standard
Ground truth: 5 | Automated: 9 | TP: 5 | FP: 4 | FN: 0
- False positives: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Dataset Auditing & Representation Analysis, PII Detection & Redaction

### mistral-large-2411-card
Ground truth: 0 | Automated: 2 | TP: 0 | FP: 2 | FN: 0
- False positives: Refusal / Abstention Training, System Prompts / Metaprompts

### mistral-large-3
Ground truth: 10 | Automated: 11 | TP: 9 | FP: 2 | FN: 1
- False positives: Misinformation & False Claims Detection, Refusal / Abstention Training
- Missed: Weapons & Illegal Activity Detection

### nemotron-4-tech-report
Ground truth: 13 | Automated: 16 | TP: 9 | FP: 7 | FN: 4
- False positives: Hate Speech & Harassment Detection, Input Guardrail Systems, Multi-stage Safety Pipeline, RAG Guardrails, Sexual Content Moderation, Violence & Gore Detection, Weapons & Illegal Activity Detection
- Missed: Capability Threshold Monitoring, Dataset Auditing & Representation Analysis, Observability & Audit Logging, Training Data Quality Filtering

### o3-pro
Ground truth: 13 | Automated: 19 | TP: 12 | FP: 7 | FN: 1
- False positives: Constitutional AI / Self-Critique, Hallucination Detection & Grounding, Input Guardrail Systems, Multimodal Safety Alignment, PII Detection & Redaction, Sexual Content Moderation, Training Data Quality Filtering
- Missed: Observability & Audit Logging

### openai-preparedness
Ground truth: 8 | Automated: 7 | TP: 7 | FP: 0 | FN: 1
- Missed: Responsible Release Protocols

### phi-4-tech-report
Ground truth: 8 | Automated: 11 | TP: 8 | FP: 3 | FN: 0
- False positives: Hallucination Detection & Grounding, Misinformation & False Claims Detection, Violence & Gore Detection

### qwen2-5-coder-tech-report
Ground truth: 5 | Automated: 4 | TP: 4 | FP: 0 | FN: 1
- Missed: Code Execution Sandboxing

### qwen2-5-tech-report
Ground truth: 4 | Automated: 7 | TP: 2 | FP: 5 | FN: 2
- False positives: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Input Guardrail Systems, Refusal / Abstention Training, Provenance & Watermarking
- Missed: Hallucination Detection & Grounding, Multimodal Safety Alignment

### qwen3-max
Ground truth: 22 | Automated: 24 | TP: 22 | FP: 2 | FN: 0
- False positives: Configurable Safety Policies, Reinforcement Learning from Human Feedback (RLHF)

### qwen3-tech-report
Ground truth: 0 | Automated: 6 | TP: 0 | FP: 6 | FN: 0
- False positives: Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Input Guardrail Systems, Misinformation & False Claims Detection, Red Teaming

### xai-security
Ground truth: 8 | Automated: 8 | TP: 5 | FP: 3 | FN: 3
- False positives: Data Sovereignty Controls, Input Guardrail Systems, tech-vulnerability-reporting
- Missed: Capability Threshold Monitoring, Data Retention Policies, Responsible Release Protocols
