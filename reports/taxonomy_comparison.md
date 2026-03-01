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
| Model Development | 61 | 93 | 32 | 39.6% | 65.6% | 49.4% |
| Runtime Safety Systems | 68 | 74 | 24 | 47.9% | 73.9% | 58.1% |
| unknown | 0 | 1 | 0 | 0.0% | 0.0% | 0.0% |

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
| Circuit Breakers / Kill Switches | 0 | 5 | 0 | 0% | 0% | 0% |
| RAG Guardrails | 0 | 4 | 1 | 0% | 0% | 0% |
| Machine Unlearning | 0 | 4 | 0 | 0% | 0% | 0% |
| Whistleblower & Internal Safety Reporting | 0 | 2 | 0 | 0% | 0% | 0% |
| tech-supervised-fine-tuning | 0 | 1 | 0 | 0% | 0% | 0% |
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
| tech-supervised-fine-tuning | 0 |

## Per-Document Details

### anthropic-rsp
Ground truth: 16 | Automated: 21 | TP: 14 | FP: 7 | FN: 2
- False positives: Access Control Documentation, Data Retention Policies, Model Weight Security, Jailbreak & Injection Defense, Refusal / Abstention Training, Voluntary Safety Commitments & Pledges, Whistleblower & Internal Safety Reporting
- Missed: Community-Based Evaluation, Safety Benchmarking

### aws-nova-service-card
Ground truth: 0 | Automated: 28 | TP: 0 | FP: 28 | FN: 0
- False positives: Access Control Documentation, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Configurable Safety Policies, Constitutional AI / Self-Critique, Copyright & IP Violation Detection, CSAM Detection & Prevention, Cybersecurity Threat Detection, Data Retention Policies, Hate Speech & Harassment Detection, Input Guardrail Systems, Model Weight Security, Multimodal Safety Alignment, Multi-stage Safety Pipeline, Observability & Audit Logging, Output Safety Systems, PII Detection & Redaction, Real-time Fact Checking, Red Teaming, Regulatory Compliance, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF), Safety Benchmarking, Self-Harm & Suicide Prevention, Sexual Content Moderation, Training Data Quality Filtering, Violence & Gore Detection, Weapons & Illegal Activity Detection

### claude-3-5-sonnet-card
Ground truth: 9 | Automated: 6 | TP: 4 | FP: 2 | FN: 5
- False positives: Independent Safety Advisory, Voluntary Safety Commitments & Pledges
- Missed: Community-Based Evaluation, Constitutional AI / Self-Critique, Incident Reporting Systems, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF)

### claude-3-haiku-model-card
Ground truth: 15 | Automated: 13 | TP: 10 | FP: 3 | FN: 5
- False positives: Adversarial Training, Responsible Release Protocols, System Prompts / Metaprompts
- Missed: Community-Based Evaluation, Constitutional AI / Self-Critique, Input Guardrail Systems, Independent Safety Advisory, Stakeholder Engagement

### claude-opus-4-5-system-card
Ground truth: 27 | Automated: 47 | TP: 26 | FP: 21 | FN: 1
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Circuit Breakers / Kill Switches, Community-Based Evaluation, Constitutional AI / Self-Critique, Data Retention Policies, Data Sovereignty Controls, Differential Privacy in Training, Direct Preference Optimization (DPO), Enterprise Integration Safety, Incident Reporting Systems, Machine Unlearning, Model Weight Security, Multimodal Safety Alignment, PII Detection & Redaction, Safety Reward Modeling, Scalable Oversight & Debate, Sexual Content Moderation, Stakeholder Engagement, Voluntary Safety Commitments & Pledges, Provenance & Watermarking
- Missed: Reinforcement Learning from Human Feedback (RLHF)

### claude-sonnet-4-6-system-card
Ground truth: 0 | Automated: 51 | TP: 0 | FP: 51 | FN: 0
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Circuit Breakers / Kill Switches, Code Execution Sandboxing, Community-Based Evaluation, Configurable Safety Policies, Constitutional AI / Self-Critique, Copyright & IP Violation Detection, CSAM Detection & Prevention, Cybersecurity Threat Detection, Data Retention Policies, Data Sovereignty Controls, Dataset Auditing & Representation Analysis, Differential Privacy in Training, Direct Preference Optimization (DPO), Enterprise Integration Safety, Ethical Human Labour Sourcing, Hallucination Detection & Grounding, Hate Speech & Harassment Detection, Incident Reporting Systems, Input Guardrail Systems, Misinformation & False Claims Detection, Model Weight Security, Multimodal Safety Alignment, Multi-stage Safety Pipeline, Observability & Audit Logging, Output Safety Systems, PII Detection & Redaction, Jailbreak & Injection Defense, RAG Guardrails, Real-time Fact Checking, Red Teaming, Refusal / Abstention Training, Regulatory Compliance, Responsible Release Protocols, Independent Safety Advisory, Safety Benchmarking, Safety Reward Modeling, Scalable Oversight & Debate, Self-Harm & Suicide Prevention, Sexual Content Moderation, Stakeholder Engagement, Sycophancy Detection, System Prompts / Metaprompts, Training Data Quality Filtering, Violence & Gore Detection, Voluntary Safety Commitments & Pledges, Provenance & Watermarking, Weapons & Illegal Activity Detection

### cohere-safety-framework
Ground truth: 7 | Automated: 3 | TP: 3 | FP: 0 | FN: 4
- Missed: Hallucination Detection & Grounding, Input Guardrail Systems, RAG Guardrails, Provenance & Watermarking

### command-a
Ground truth: 14 | Automated: 24 | TP: 10 | FP: 14 | FN: 4
- False positives: Access Control Documentation, Bias Mitigation (Post-Training), Dataset Auditing & Representation Analysis, Hallucination Detection & Grounding, Hate Speech & Harassment Detection, Misinformation & False Claims Detection, PII Detection & Redaction, Red Teaming, Responsible Release Protocols, Safety Benchmarking, Scalable Oversight & Debate, Self-Harm & Suicide Prevention, Violence & Gore Detection, Weapons & Illegal Activity Detection
- Missed: Capability Threshold Monitoring, Incident Reporting Systems, Multimodal Safety Alignment, Jailbreak & Injection Defense

### deepseek-privacy
Ground truth: 5 | Automated: 1 | TP: 1 | FP: 0 | FN: 4
- Missed: Data Sovereignty Controls, Incident Reporting Systems, PII Detection & Redaction, Regulatory Compliance

### deepseek-r1-paper
Ground truth: 15 | Automated: 17 | TP: 9 | FP: 8 | FN: 6
- False positives: Community-Based Evaluation, Hate Speech & Harassment Detection, Multi-stage Safety Pipeline, Output Safety Systems, Red Teaming, Scalable Oversight & Debate, Sexual Content Moderation, System Prompts / Metaprompts
- Missed: Bias Mitigation (Post-Training), Configurable Safety Policies, Dataset Auditing & Representation Analysis, Input Guardrail Systems, Multimodal Safety Alignment, Reinforcement Learning from Human Feedback (RLHF)

### deepseek-v3-paper
Ground truth: 6 | Automated: 6 | TP: 2 | FP: 4 | FN: 4
- False positives: Constitutional AI / Self-Critique, Safety Benchmarking, Safety Reward Modeling, Scalable Oversight & Debate
- Missed: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Dataset Auditing & Representation Analysis, Red Teaming

### falcon-series-paper
Ground truth: 0 | Automated: 2 | TP: 0 | FP: 2 | FN: 0
- False positives: Safety Benchmarking, Training Data Quality Filtering

### gemini-1-5-paper
Ground truth: 12 | Automated: 48 | TP: 10 | FP: 38 | FN: 2
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Circuit Breakers / Kill Switches, Code Execution Sandboxing, Community-Based Evaluation, Constitutional AI / Self-Critique, Copyright & IP Violation Detection, CSAM Detection & Prevention, Cybersecurity Threat Detection, Data Retention Policies, Data Sovereignty Controls, Differential Privacy in Training, Direct Preference Optimization (DPO), Enterprise Integration Safety, Ethical Human Labour Sourcing, Hallucination Detection & Grounding, Hate Speech & Harassment Detection, Input Guardrail Systems, Misinformation & False Claims Detection, Model Weight Security, Multimodal Safety Alignment, Multi-stage Safety Pipeline, Output Safety Systems, RAG Guardrails, Real-time Fact Checking, Responsible Release Protocols, Independent Safety Advisory, Safety Benchmarking, Scalable Oversight & Debate, Self-Harm & Suicide Prevention, Sexual Content Moderation, Stakeholder Engagement, Sycophancy Detection, System Prompts / Metaprompts, Violence & Gore Detection, Voluntary Safety Commitments & Pledges, Provenance & Watermarking, Weapons & Illegal Activity Detection
- Missed: Observability & Audit Logging, Refusal / Abstention Training

### gemini-25-flash-lite
Ground truth: 9 | Automated: 12 | TP: 6 | FP: 6 | FN: 3
- False positives: Multimodal Safety Alignment, Output Safety Systems, Responsible Release Protocols, Safety Benchmarking, Sexual Content Moderation, Violence & Gore Detection
- Missed: Incident Reporting Systems, Refusal / Abstention Training, Safety Reward Modeling

### gemini-3-pro
Ground truth: 8 | Automated: 13 | TP: 6 | FP: 7 | FN: 2
- False positives: Hate Speech & Harassment Detection, Multimodal Safety Alignment, Output Safety Systems, Self-Harm & Suicide Prevention, Sexual Content Moderation, tech-supervised-fine-tuning, Violence & Gore Detection
- Missed: Dataset Auditing & Representation Analysis, Incident Reporting Systems

### gemini-3-technical-report
Ground truth: 11 | Automated: 12 | TP: 7 | FP: 5 | FN: 4
- False positives: Autonomous Behaviour Classification, Model Weight Security, Responsible Release Protocols, Scalable Oversight & Debate, Stakeholder Engagement
- Missed: Hallucination Detection & Grounding, Incident Reporting Systems, Misinformation & False Claims Detection, Refusal / Abstention Training

### google-ai-principles-2024
Ground truth: 9 | Automated: 12 | TP: 4 | FP: 8 | FN: 5
- False positives: Community-Based Evaluation, Differential Privacy in Training, Observability & Audit Logging, Jailbreak & Injection Defense, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF), Stakeholder Engagement, Voluntary Safety Commitments & Pledges
- Missed: Capability Threshold Monitoring, Hallucination Detection & Grounding, Input Guardrail Systems, Misinformation & False Claims Detection, System Prompts / Metaprompts

### gpt-4o-system-card
Ground truth: 13 | Automated: 21 | TP: 11 | FP: 10 | FN: 2
- False positives: Dataset Auditing & Representation Analysis, Multi-stage Safety Pipeline, PII Detection & Redaction, Red Teaming, Responsible Release Protocols, Scalable Oversight & Debate, System Prompts / Metaprompts, Training Data Quality Filtering, Voluntary Safety Commitments & Pledges, Weapons & Illegal Activity Detection
- Missed: CSAM Detection & Prevention, Hate Speech & Harassment Detection

### gpt-5-system-card
Ground truth: 28 | Automated: 42 | TP: 26 | FP: 16 | FN: 2
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Code Execution Sandboxing, Copyright & IP Violation Detection, Dataset Auditing & Representation Analysis, Differential Privacy in Training, Direct Preference Optimization (DPO), Machine Unlearning, Model Weight Security, RAG Guardrails, Scalable Oversight & Debate, Self-Harm & Suicide Prevention, Stakeholder Engagement, Training Data Quality Filtering, Voluntary Safety Commitments & Pledges
- Missed: Misinformation & False Claims Detection, Reinforcement Learning from Human Feedback (RLHF)

### grok-4
Ground truth: 9 | Automated: 15 | TP: 7 | FP: 8 | FN: 2
- False positives: Bias Mitigation (Post-Training), CSAM Detection & Prevention, Cybersecurity Threat Detection, Output Safety Systems, Safety Benchmarking, Self-Harm & Suicide Prevention, Training Data Quality Filtering, Weapons & Illegal Activity Detection
- Missed: Incident Reporting Systems, Misinformation & False Claims Detection

### grok-security
Ground truth: 4 | Automated: 3 | TP: 2 | FP: 1 | FN: 2
- False positives: Regulatory Compliance
- Missed: Access Control Documentation, Incident Reporting Systems

### llama-3-paper
Ground truth: 26 | Automated: 47 | TP: 26 | FP: 21 | FN: 0
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Circuit Breakers / Kill Switches, Code Execution Sandboxing, Community-Based Evaluation, Cybersecurity Threat Detection, Data Retention Policies, Data Sovereignty Controls, Ethical Human Labour Sourcing, Incident Reporting Systems, Machine Unlearning, Model Weight Security, Multimodal Safety Alignment, Real-time Fact Checking, Safety Reward Modeling, Scalable Oversight & Debate, Stakeholder Engagement, Sycophancy Detection, Voluntary Safety Commitments & Pledges

### llama-4-maverick
Ground truth: 7 | Automated: 7 | TP: 5 | FP: 2 | FN: 2
- False positives: Cybersecurity Threat Detection, Multi-stage Safety Pipeline
- Missed: Red Teaming, System Prompts / Metaprompts

### llama-4-responsible-use-guide
Ground truth: 8 | Automated: 8 | TP: 2 | FP: 6 | FN: 6
- False positives: Dataset Auditing & Representation Analysis, Output Safety Systems, Red Teaming, Reinforcement Learning from Human Feedback (RLHF), Training Data Quality Filtering, Provenance & Watermarking
- Missed: Access Control Documentation, Capability Threshold Monitoring, Configurable Safety Policies, Incident Reporting Systems, Responsible Release Protocols, Independent Safety Advisory

### magistral-paper
Ground truth: 0 | Automated: 5 | TP: 0 | FP: 5 | FN: 0
- False positives: Dataset Auditing & Representation Analysis, Reinforcement Learning from Human Feedback (RLHF), Safety Reward Modeling, Scalable Oversight & Debate, Training Data Quality Filtering

### meta-llama-responsible-use
Ground truth: 17 | Automated: 15 | TP: 8 | FP: 7 | FN: 9
- False positives: Dataset Auditing & Representation Analysis, Ethical Human Labour Sourcing, Observability & Audit Logging, Responsible Release Protocols, Safety Benchmarking, System Prompts / Metaprompts, Training Data Quality Filtering
- Missed: Capability Threshold Monitoring, Community-Based Evaluation, Input Guardrail Systems, Misinformation & False Claims Detection, Refusal / Abstention Training, Safety Reward Modeling, Sexual Content Moderation, Provenance & Watermarking, Weapons & Illegal Activity Detection

### microsoft-rai-standard
Ground truth: 5 | Automated: 5 | TP: 2 | FP: 3 | FN: 3
- False positives: Dataset Auditing & Representation Analysis, Observability & Audit Logging, Responsible Release Protocols
- Missed: Misinformation & False Claims Detection, Red Teaming, Safety Benchmarking

### mistral-large-2411-card
Ground truth: 0 | Automated: 1 | TP: 0 | FP: 1 | FN: 0
- False positives: System Prompts / Metaprompts

### mistral-large-3
Ground truth: 10 | Automated: 11 | TP: 8 | FP: 3 | FN: 2
- False positives: Adversarial Training, Configurable Safety Policies, CSAM Detection & Prevention
- Missed: Incident Reporting Systems, Output Safety Systems

### nemotron-4-tech-report
Ground truth: 13 | Automated: 7 | TP: 5 | FP: 2 | FN: 8
- False positives: Reinforcement Learning from Human Feedback (RLHF), Scalable Oversight & Debate
- Missed: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Data Sovereignty Controls, Dataset Auditing & Representation Analysis, Incident Reporting Systems, Multimodal Safety Alignment, Observability & Audit Logging, Jailbreak & Injection Defense

### o3-pro
Ground truth: 13 | Automated: 15 | TP: 5 | FP: 10 | FN: 8
- False positives: Access Control Documentation, Autonomous Behaviour Classification, CSAM Detection & Prevention, Multimodal Safety Alignment, Output Safety Systems, PII Detection & Redaction, Independent Safety Advisory, Scalable Oversight & Debate, Sexual Content Moderation, Training Data Quality Filtering
- Missed: Bias Mitigation (Post-Training), Community-Based Evaluation, Incident Reporting Systems, Misinformation & False Claims Detection, Multi-stage Safety Pipeline, Observability & Audit Logging, Reinforcement Learning from Human Feedback (RLHF), Safety Reward Modeling

### openai-preparedness
Ground truth: 8 | Automated: 11 | TP: 7 | FP: 4 | FN: 1
- False positives: Access Control Documentation, Model Weight Security, Stakeholder Engagement, Voluntary Safety Commitments & Pledges
- Missed: Configurable Safety Policies

### phi-4-tech-report
Ground truth: 8 | Automated: 9 | TP: 5 | FP: 4 | FN: 3
- False positives: Dataset Auditing & Representation Analysis, Ethical Human Labour Sourcing, Independent Safety Advisory, Scalable Oversight & Debate
- Missed: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Incident Reporting Systems

### pixtral-12b-blog
Ground truth: 3 | Automated: 0 | TP: 0 | FP: 0 | FN: 3
- Missed: Multimodal Safety Alignment, Safety Benchmarking, Training Data Quality Filtering

### qwen2-5-coder-tech-report
Ground truth: 5 | Automated: 3 | TP: 3 | FP: 0 | FN: 2
- Missed: Capability Threshold Monitoring, Dataset Auditing & Representation Analysis

### qwen2-5-tech-report
Ground truth: 4 | Automated: 55 | TP: 4 | FP: 51 | FN: 0
- False positives: Access Control Documentation, Adversarial Training, Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Circuit Breakers / Kill Switches, Code Execution Sandboxing, Community-Based Evaluation, Configurable Safety Policies, Constitutional AI / Self-Critique, Copyright & IP Violation Detection, CSAM Detection & Prevention, Cybersecurity Threat Detection, Data Retention Policies, Data Sovereignty Controls, Differential Privacy in Training, Direct Preference Optimization (DPO), Enterprise Integration Safety, Ethical Human Labour Sourcing, Hate Speech & Harassment Detection, Incident Reporting Systems, Input Guardrail Systems, Machine Unlearning, Misinformation & False Claims Detection, Model Weight Security, Multi-stage Safety Pipeline, Observability & Audit Logging, Output Safety Systems, PII Detection & Redaction, Jailbreak & Injection Defense, RAG Guardrails, Real-time Fact Checking, Red Teaming, Refusal / Abstention Training, Regulatory Compliance, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF), Independent Safety Advisory, Safety Benchmarking, Safety Reward Modeling, Scalable Oversight & Debate, Self-Harm & Suicide Prevention, Sexual Content Moderation, Stakeholder Engagement, Sycophancy Detection, System Prompts / Metaprompts, Violence & Gore Detection, Voluntary Safety Commitments & Pledges, Provenance & Watermarking, Weapons & Illegal Activity Detection, Whistleblower & Internal Safety Reporting

### qwen3-max
Ground truth: 22 | Automated: 23 | TP: 18 | FP: 5 | FN: 4
- False positives: Configurable Safety Policies, Observability & Audit Logging, Red Teaming, Scalable Oversight & Debate, Training Data Quality Filtering
- Missed: Constitutional AI / Self-Critique, Dataset Auditing & Representation Analysis, Multimodal Safety Alignment, Real-time Fact Checking

### qwen3-tech-report
Ground truth: 0 | Automated: 6 | TP: 0 | FP: 6 | FN: 0
- False positives: Multi-stage Safety Pipeline, Reinforcement Learning from Human Feedback (RLHF), Safety Benchmarking, Scalable Oversight & Debate, System Prompts / Metaprompts, Training Data Quality Filtering

### xai-security
Ground truth: 8 | Automated: 7 | TP: 6 | FP: 1 | FN: 2
- False positives: Model Weight Security
- Missed: Capability Threshold Monitoring, Responsible Release Protocols
