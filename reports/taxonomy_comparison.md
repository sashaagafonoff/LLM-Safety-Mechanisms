# Taxonomy Comparison Report

Comparison of automated extraction (new taxonomy) against manually-reviewed ground truth.

## Overall Metrics

| Metric | Value |
|--------|-------|
| True Positives | 278 |
| False Positives | 335 |
| False Negatives | 101 |
| **Precision** | **45.4%** |
| **Recall** | **73.4%** |
| **F1 Score** | **56.0%** |

## Recall by Evidence Source

How well the automated pipeline recovers techniques that were originally found by each source.

| Source | Recovered | Missed | Recall |
|--------|-----------|--------|--------|
| nlu | 31 | 42 | 42.5% |
| llm | 142 | 46 | 75.5% |
| manual | 105 | 13 | 89.0% |

## Per-Category Performance

| Category | TP | FP | FN | Precision | Recall | F1 |
|----------|----|----|----|-----------|---------|----|
| Evaluation & Red Teaming | 36 | 23 | 9 | 61.0% | 80.0% | 69.2% |
| Governance & Oversight | 47 | 62 | 31 | 43.1% | 60.3% | 50.3% |
| Harm & Content Classification | 59 | 95 | 12 | 38.3% | 83.1% | 52.4% |
| Model Development | 64 | 69 | 29 | 48.1% | 68.8% | 56.6% |
| Runtime Safety Systems | 72 | 86 | 20 | 45.6% | 78.3% | 57.6% |

## Technique-Level Analysis

### Techniques Needing Improvement (lowest F1)

| Technique | TP | FP | FN | Precision | Recall | F1 |
|-----------|----|----|----|-----------|---------|----|
| Autonomous Behaviour Classification | 0 | 14 | 0 | 0% | 0% | 0% |
| Cybersecurity Threat Detection | 0 | 11 | 0 | 0% | 0% | 0% |
| Circuit Breakers / Kill Switches | 0 | 5 | 0 | 0% | 0% | 0% |
| Machine Unlearning | 0 | 4 | 0 | 0% | 0% | 0% |
| RAG Guardrails | 0 | 3 | 1 | 0% | 0% | 0% |
| Data Sovereignty Controls | 1 | 4 | 1 | 20% | 50% | 29% |
| Constitutional AI / Self-Critique | 2 | 6 | 3 | 25% | 40% | 31% |
| Responsible Release Protocols | 4 | 15 | 2 | 21% | 67% | 32% |
| Access Control Documentation | 2 | 7 | 1 | 22% | 67% | 33% |
| Enterprise Integration Safety | 1 | 3 | 1 | 25% | 50% | 33% |
| Ethical Human Labour Sourcing | 1 | 4 | 0 | 20% | 100% | 33% |
| Code Execution Sandboxing | 2 | 7 | 0 | 22% | 100% | 36% |
| Multimodal Safety Alignment | 4 | 9 | 5 | 31% | 44% | 36% |
| Community-Based Evaluation | 3 | 6 | 3 | 33% | 50% | 40% |
| Provenance & Watermarking | 2 | 4 | 2 | 33% | 50% | 40% |

### Well-Performing Techniques (highest F1)

| Technique | TP | FP | FN | Precision | Recall | F1 |
|-----------|----|----|----|-----------|---------|----|
| Jailbreak & Injection Defense | 13 | 4 | 2 | 76% | 87% | 81% |
| Regulatory Compliance | 6 | 3 | 0 | 67% | 100% | 80% |
| Direct Preference Optimization (DPO) | 6 | 4 | 0 | 60% | 100% | 75% |
| Safety Benchmarking | 16 | 9 | 2 | 64% | 89% | 74% |
| Red Teaming | 17 | 8 | 4 | 68% | 81% | 74% |
| Violence & Gore Detection | 8 | 6 | 0 | 57% | 100% | 73% |
| Refusal / Abstention Training | 12 | 6 | 3 | 67% | 80% | 73% |
| Training Data Quality Filtering | 13 | 10 | 1 | 57% | 93% | 70% |
| Input Guardrail Systems | 10 | 5 | 4 | 67% | 71% | 69% |
| Capability Threshold Monitoring | 13 | 4 | 9 | 76% | 59% | 67% |

### New Techniques (automated only, not in ground truth)

These are new taxonomy techniques — automated detections with no ground truth to validate against.

| Technique | Auto Detections |
|-----------|----------------|
| Autonomous Behaviour Classification | 0 |
| Cybersecurity Threat Detection | 0 |
| Circuit Breakers / Kill Switches | 0 |
| Machine Unlearning | 0 |

## Per-Document Details

### anthropic-rsp
Ground truth: 16 | Automated: 18 | TP: 15 | FP: 3 | FN: 1
- False positives: Access Control Documentation, Circuit Breakers / Kill Switches, Refusal / Abstention Training
- Missed: Community-Based Evaluation

### aws-nova-service-card
Ground truth: 0 | Automated: 27 | TP: 0 | FP: 27 | FN: 0
- False positives: Access Control Documentation, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Configurable Safety Policies, Constitutional AI / Self-Critique, CSAM Detection & Prevention, Cybersecurity Threat Detection, Data Retention Policies, Hate Speech & Harassment Detection, Input Guardrail Systems, Multimodal Safety Alignment, Multi-stage Safety Pipeline, Observability & Audit Logging, Output Safety Systems, PII Detection & Redaction, Real-time Fact Checking, Red Teaming, Refusal / Abstention Training, Regulatory Compliance, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF), Safety Benchmarking, Self-Harm & Suicide Prevention, Sexual Content Moderation, Training Data Quality Filtering, Violence & Gore Detection, Weapons & Illegal Activity Detection

### claude-3-5-sonnet-card
Ground truth: 9 | Automated: 11 | TP: 6 | FP: 5 | FN: 3
- False positives: Autonomous Behaviour Classification, Code Execution Sandboxing, Independent Safety Advisory, Stakeholder Engagement, Weapons & Illegal Activity Detection
- Missed: Constitutional AI / Self-Critique, Incident Reporting Systems, Reinforcement Learning from Human Feedback (RLHF)

### claude-3-haiku-model-card
Ground truth: 15 | Automated: 16 | TP: 11 | FP: 5 | FN: 4
- False positives: Adversarial Training, Autonomous Behaviour Classification, Cybersecurity Threat Detection, Output Safety Systems, Responsible Release Protocols
- Missed: Community-Based Evaluation, Constitutional AI / Self-Critique, Input Guardrail Systems, Independent Safety Advisory

### claude-opus-4-5-system-card
Ground truth: 27 | Automated: 43 | TP: 26 | FP: 17 | FN: 1
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Circuit Breakers / Kill Switches, Community-Based Evaluation, Constitutional AI / Self-Critique, Data Retention Policies, Data Sovereignty Controls, Direct Preference Optimization (DPO), Enterprise Integration Safety, Incident Reporting Systems, Machine Unlearning, Multimodal Safety Alignment, PII Detection & Redaction, Safety Reward Modeling, Sexual Content Moderation, Stakeholder Engagement, Provenance & Watermarking
- Missed: Reinforcement Learning from Human Feedback (RLHF)

### claude-sonnet-4-6-system-card
Ground truth: 0 | Automated: 21 | TP: 0 | FP: 21 | FN: 0
- False positives: Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Code Execution Sandboxing, Configurable Safety Policies, CSAM Detection & Prevention, Cybersecurity Threat Detection, Ethical Human Labour Sourcing, Multimodal Safety Alignment, Multi-stage Safety Pipeline, Observability & Audit Logging, Jailbreak & Injection Defense, Red Teaming, Refusal / Abstention Training, Responsible Release Protocols, Safety Benchmarking, Self-Harm & Suicide Prevention, Sycophancy Detection, System Prompts / Metaprompts, Training Data Quality Filtering, Weapons & Illegal Activity Detection

### cohere-safety-framework
Ground truth: 7 | Automated: 1 | TP: 0 | FP: 1 | FN: 7
- False positives: System Prompts / Metaprompts
- Missed: Hallucination Detection & Grounding, Input Guardrail Systems, PII Detection & Redaction, Jailbreak & Injection Defense, RAG Guardrails, Red Teaming, Provenance & Watermarking

### command-a
Ground truth: 14 | Automated: 19 | TP: 9 | FP: 10 | FN: 5
- False positives: Bias Mitigation (Post-Training), Code Execution Sandboxing, Hallucination Detection & Grounding, Misinformation & False Claims Detection, Red Teaming, Safety Benchmarking, Self-Harm & Suicide Prevention, System Prompts / Metaprompts, Violence & Gore Detection, Weapons & Illegal Activity Detection
- Missed: Capability Threshold Monitoring, Enterprise Integration Safety, Incident Reporting Systems, Multimodal Safety Alignment, Jailbreak & Injection Defense

### deepseek-privacy
Ground truth: 5 | Automated: 3 | TP: 3 | FP: 0 | FN: 2
- Missed: Incident Reporting Systems, PII Detection & Redaction

### deepseek-r1-paper
Ground truth: 15 | Automated: 20 | TP: 12 | FP: 8 | FN: 3
- False positives: CSAM Detection & Prevention, Cybersecurity Threat Detection, Hate Speech & Harassment Detection, Multi-stage Safety Pipeline, Output Safety Systems, Red Teaming, Sexual Content Moderation, System Prompts / Metaprompts
- Missed: Bias Mitigation (Post-Training), Dataset Auditing & Representation Analysis, Multimodal Safety Alignment

### deepseek-v3-paper
Ground truth: 6 | Automated: 3 | TP: 2 | FP: 1 | FN: 4
- False positives: Constitutional AI / Self-Critique
- Missed: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Dataset Auditing & Representation Analysis, Red Teaming

### falcon-series-paper
Ground truth: 0 | Automated: 3 | TP: 0 | FP: 3 | FN: 0
- False positives: Dataset Auditing & Representation Analysis, Responsible Release Protocols, Training Data Quality Filtering

### gemini-1-5-paper
Ground truth: 12 | Automated: 44 | TP: 10 | FP: 34 | FN: 2
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Circuit Breakers / Kill Switches, Code Execution Sandboxing, Community-Based Evaluation, Constitutional AI / Self-Critique, Copyright & IP Violation Detection, CSAM Detection & Prevention, Cybersecurity Threat Detection, Data Retention Policies, Data Sovereignty Controls, Direct Preference Optimization (DPO), Enterprise Integration Safety, Ethical Human Labour Sourcing, Hallucination Detection & Grounding, Hate Speech & Harassment Detection, Input Guardrail Systems, Misinformation & False Claims Detection, Multimodal Safety Alignment, Multi-stage Safety Pipeline, Output Safety Systems, RAG Guardrails, Real-time Fact Checking, Responsible Release Protocols, Independent Safety Advisory, Safety Benchmarking, Self-Harm & Suicide Prevention, Sexual Content Moderation, Stakeholder Engagement, Sycophancy Detection, System Prompts / Metaprompts, Violence & Gore Detection, Provenance & Watermarking, Weapons & Illegal Activity Detection
- Missed: Observability & Audit Logging, Refusal / Abstention Training

### gemini-25-flash-lite
Ground truth: 9 | Automated: 13 | TP: 7 | FP: 6 | FN: 2
- False positives: Multimodal Safety Alignment, Output Safety Systems, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF), Safety Benchmarking, Sexual Content Moderation
- Missed: Incident Reporting Systems, Safety Reward Modeling

### gemini-3-pro
Ground truth: 8 | Automated: 16 | TP: 6 | FP: 10 | FN: 2
- False positives: Autonomous Behaviour Classification, Cybersecurity Threat Detection, Hate Speech & Harassment Detection, Multimodal Safety Alignment, Refusal / Abstention Training, Responsible Release Protocols, Self-Harm & Suicide Prevention, Sexual Content Moderation, Violence & Gore Detection, Weapons & Illegal Activity Detection
- Missed: Dataset Auditing & Representation Analysis, Incident Reporting Systems

### gemini-3-technical-report
Ground truth: 11 | Automated: 11 | TP: 6 | FP: 5 | FN: 5
- False positives: Adversarial Training, Autonomous Behaviour Classification, Responsible Release Protocols, Independent Safety Advisory, Weapons & Illegal Activity Detection
- Missed: Hallucination Detection & Grounding, Incident Reporting Systems, Misinformation & False Claims Detection, Observability & Audit Logging, Refusal / Abstention Training

### google-ai-principles-2024
Ground truth: 9 | Automated: 11 | TP: 4 | FP: 7 | FN: 5
- False positives: Community-Based Evaluation, Multi-stage Safety Pipeline, Observability & Audit Logging, Jailbreak & Injection Defense, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF), Stakeholder Engagement
- Missed: Capability Threshold Monitoring, Incident Reporting Systems, Input Guardrail Systems, Misinformation & False Claims Detection, System Prompts / Metaprompts

### gpt-4o-system-card
Ground truth: 13 | Automated: 21 | TP: 11 | FP: 10 | FN: 2
- False positives: Adversarial Training, Autonomous Behaviour Classification, Multi-stage Safety Pipeline, PII Detection & Redaction, Red Teaming, Responsible Release Protocols, Safety Benchmarking, Stakeholder Engagement, Training Data Quality Filtering, Weapons & Illegal Activity Detection
- Missed: Hate Speech & Harassment Detection, Incident Reporting Systems

### gpt-5-system-card
Ground truth: 28 | Automated: 38 | TP: 26 | FP: 12 | FN: 2
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Code Execution Sandboxing, Copyright & IP Violation Detection, Dataset Auditing & Representation Analysis, Direct Preference Optimization (DPO), Machine Unlearning, RAG Guardrails, Self-Harm & Suicide Prevention, Stakeholder Engagement, Training Data Quality Filtering
- Missed: Misinformation & False Claims Detection, Reinforcement Learning from Human Feedback (RLHF)

### grok-4
Ground truth: 9 | Automated: 19 | TP: 6 | FP: 13 | FN: 3
- False positives: Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Configurable Safety Policies, CSAM Detection & Prevention, Cybersecurity Threat Detection, Multi-stage Safety Pipeline, Output Safety Systems, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF), Safety Benchmarking, Self-Harm & Suicide Prevention, Training Data Quality Filtering, Weapons & Illegal Activity Detection
- Missed: Incident Reporting Systems, Misinformation & False Claims Detection, Red Teaming

### grok-security
Ground truth: 4 | Automated: 4 | TP: 3 | FP: 1 | FN: 1
- False positives: Regulatory Compliance
- Missed: Incident Reporting Systems

### hunyuan-technical-report
Ground truth: 5 | Automated: 5 | TP: 4 | FP: 1 | FN: 1
- False positives: Safety Reward Modeling
- Missed: Dataset Auditing & Representation Analysis

### llama-3-paper
Ground truth: 26 | Automated: 44 | TP: 26 | FP: 18 | FN: 0
- False positives: Access Control Documentation, Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Circuit Breakers / Kill Switches, Code Execution Sandboxing, Community-Based Evaluation, Cybersecurity Threat Detection, Data Retention Policies, Data Sovereignty Controls, Ethical Human Labour Sourcing, Incident Reporting Systems, Machine Unlearning, Multimodal Safety Alignment, Real-time Fact Checking, Safety Reward Modeling, Stakeholder Engagement, Sycophancy Detection

### llama-4-maverick
Ground truth: 7 | Automated: 9 | TP: 5 | FP: 4 | FN: 2
- False positives: Configurable Safety Policies, Cybersecurity Threat Detection, Multimodal Safety Alignment, Multi-stage Safety Pipeline
- Missed: Red Teaming, System Prompts / Metaprompts

### llama-4-responsible-use-guide
Ground truth: 8 | Automated: 12 | TP: 3 | FP: 9 | FN: 5
- False positives: Dataset Auditing & Representation Analysis, Hate Speech & Harassment Detection, Input Guardrail Systems, Output Safety Systems, PII Detection & Redaction, Red Teaming, Reinforcement Learning from Human Feedback (RLHF), System Prompts / Metaprompts, Provenance & Watermarking
- Missed: Access Control Documentation, Capability Threshold Monitoring, Incident Reporting Systems, Responsible Release Protocols, Independent Safety Advisory

### magistral-paper
Ground truth: 0 | Automated: 2 | TP: 0 | FP: 2 | FN: 0
- False positives: System Prompts / Metaprompts, Training Data Quality Filtering

### meta-llama-responsible-use
Ground truth: 17 | Automated: 13 | TP: 8 | FP: 5 | FN: 9
- False positives: Constitutional AI / Self-Critique, Responsible Release Protocols, Safety Benchmarking, System Prompts / Metaprompts, Training Data Quality Filtering
- Missed: Capability Threshold Monitoring, Community-Based Evaluation, Input Guardrail Systems, Misinformation & False Claims Detection, Refusal / Abstention Training, Safety Reward Modeling, Sexual Content Moderation, Provenance & Watermarking, Weapons & Illegal Activity Detection

### microsoft-rai-standard
Ground truth: 5 | Automated: 7 | TP: 3 | FP: 4 | FN: 2
- False positives: Bias Mitigation (Post-Training), Dataset Auditing & Representation Analysis, Observability & Audit Logging, Responsible Release Protocols
- Missed: Misinformation & False Claims Detection, Safety Benchmarking

### mistral-large-2411-card
Ground truth: 0 | Automated: 1 | TP: 0 | FP: 1 | FN: 0
- False positives: System Prompts / Metaprompts

### mistral-large-3
Ground truth: 10 | Automated: 14 | TP: 9 | FP: 5 | FN: 1
- False positives: Adversarial Training, Configurable Safety Policies, CSAM Detection & Prevention, Multi-stage Safety Pipeline, Red Teaming
- Missed: Incident Reporting Systems

### nemotron-4-tech-report
Ground truth: 13 | Automated: 18 | TP: 6 | FP: 12 | FN: 7
- False positives: CSAM Detection & Prevention, Hallucination Detection & Grounding, Hate Speech & Harassment Detection, Input Guardrail Systems, Multi-stage Safety Pipeline, PII Detection & Redaction, Refusal / Abstention Training, Reinforcement Learning from Human Feedback (RLHF), Self-Harm & Suicide Prevention, Sexual Content Moderation, Violence & Gore Detection, Weapons & Illegal Activity Detection
- Missed: Bias Mitigation (Post-Training), Capability Threshold Monitoring, Data Sovereignty Controls, Dataset Auditing & Representation Analysis, Incident Reporting Systems, Multimodal Safety Alignment, Observability & Audit Logging

### o3-pro
Ground truth: 13 | Automated: 22 | TP: 8 | FP: 14 | FN: 5
- False positives: Autonomous Behaviour Classification, Configurable Safety Policies, CSAM Detection & Prevention, Hallucination Detection & Grounding, Multimodal Safety Alignment, Output Safety Systems, PII Detection & Redaction, Responsible Release Protocols, Independent Safety Advisory, Sexual Content Moderation, Stakeholder Engagement, System Prompts / Metaprompts, Training Data Quality Filtering, Weapons & Illegal Activity Detection
- Missed: Incident Reporting Systems, Misinformation & False Claims Detection, Observability & Audit Logging, Reinforcement Learning from Human Feedback (RLHF), Safety Reward Modeling

### openai-preparedness
Ground truth: 8 | Automated: 10 | TP: 6 | FP: 4 | FN: 2
- False positives: Autonomous Behaviour Classification, Community-Based Evaluation, Cybersecurity Threat Detection, Weapons & Illegal Activity Detection
- Missed: Configurable Safety Policies, Observability & Audit Logging

### phi-4-tech-report
Ground truth: 8 | Automated: 9 | TP: 6 | FP: 3 | FN: 2
- False positives: Adversarial Training, Hallucination Detection & Grounding, Jailbreak & Injection Defense
- Missed: Capability Threshold Monitoring, Incident Reporting Systems

### pixtral-12b-blog
Ground truth: 3 | Automated: 0 | TP: 0 | FP: 0 | FN: 3
- Missed: Multimodal Safety Alignment, Safety Benchmarking, Training Data Quality Filtering

### qwen2-5-coder-tech-report
Ground truth: 5 | Automated: 5 | TP: 3 | FP: 2 | FN: 2
- False positives: Hallucination Detection & Grounding, Multi-stage Safety Pipeline
- Missed: Capability Threshold Monitoring, Dataset Auditing & Representation Analysis

### qwen2-5-tech-report
Ground truth: 4 | Automated: 50 | TP: 4 | FP: 46 | FN: 0
- False positives: Access Control Documentation, Adversarial Training, Autonomous Behaviour Classification, Bias Mitigation (Post-Training), Capability Threshold Monitoring, Circuit Breakers / Kill Switches, Code Execution Sandboxing, Community-Based Evaluation, Configurable Safety Policies, Constitutional AI / Self-Critique, Copyright & IP Violation Detection, CSAM Detection & Prevention, Cybersecurity Threat Detection, Data Retention Policies, Data Sovereignty Controls, Direct Preference Optimization (DPO), Enterprise Integration Safety, Ethical Human Labour Sourcing, Hate Speech & Harassment Detection, Incident Reporting Systems, Input Guardrail Systems, Machine Unlearning, Misinformation & False Claims Detection, Multi-stage Safety Pipeline, Observability & Audit Logging, Output Safety Systems, PII Detection & Redaction, Jailbreak & Injection Defense, RAG Guardrails, Real-time Fact Checking, Red Teaming, Refusal / Abstention Training, Regulatory Compliance, Responsible Release Protocols, Reinforcement Learning from Human Feedback (RLHF), Independent Safety Advisory, Safety Benchmarking, Safety Reward Modeling, Self-Harm & Suicide Prevention, Sexual Content Moderation, Stakeholder Engagement, Sycophancy Detection, System Prompts / Metaprompts, Violence & Gore Detection, Provenance & Watermarking, Weapons & Illegal Activity Detection

### qwen3-max
Ground truth: 22 | Automated: 19 | TP: 18 | FP: 1 | FN: 4
- False positives: Configurable Safety Policies
- Missed: Constitutional AI / Self-Critique, Dataset Auditing & Representation Analysis, Multimodal Safety Alignment, Real-time Fact Checking

### qwen3-tech-report
Ground truth: 0 | Automated: 5 | TP: 0 | FP: 5 | FN: 0
- False positives: Configurable Safety Policies, Hallucination Detection & Grounding, Multi-stage Safety Pipeline, Safety Reward Modeling, Training Data Quality Filtering

### xai-security
Ground truth: 8 | Automated: 6 | TP: 6 | FP: 0 | FN: 2
- Missed: Capability Threshold Monitoring, Responsible Release Protocols
