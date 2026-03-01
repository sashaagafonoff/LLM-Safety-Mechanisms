# LLM Safety Mechanisms - Dataset Summary

*Generated: 2026-03-01 22:37*

## Overall Statistics

- **Providers**: 14
- **Models tracked**: 56
- **Technique categories**: 5
- **Active techniques in taxonomy**: 53
- **Aspirational techniques** (no provider evidence): 2
- **Source documents**: 41
- **Techniques with detections**: 53 / 53

## Coverage by Category

| Category | Techniques | System Detected | Manual Entry |
|----------|------------|-----------------|--------------|
| Evaluation & Red Teaming | 3 | 3 | 0 |
| Governance & Oversight | 14 | 14 | 0 |
| Harm & Content Classification | 12 | 12 | 0 |
| Model Development | 13 | 13 | 0 |
| Runtime Safety Systems | 13 | 13 | 0 |

## Provider Breakdown

| Provider | Type | Source Docs | Techniques | Detection Confidence |
|----------|------|-------------|------------|----------------------|
| Anthropic | commercial | 5 | 54 | H:54 / M:0 / L:0 |
| Google | commercial | 5 | 50 | H:50 / M:0 / L:0 |
| Alibaba | commercial | 4 | 55 | H:55 / M:0 / L:0 |
| Meta | commercial | 4 | 50 | H:50 / M:0 / L:0 |
| Mistral AI | commercial | 4 | 16 | H:15 / M:1 / L:0 |
| OpenAI | commercial | 4 | 44 | H:44 / M:0 / L:0 |
| xAI | commercial | 4 | 22 | H:22 / M:0 / L:0 |
| DeepSeek | commercial | 3 | 20 | H:20 / M:0 / L:0 |
| Cohere | commercial | 2 | 25 | H:25 / M:0 / L:0 |
| Microsoft | commercial | 2 | 13 | H:13 / M:0 / L:0 |
| Amazon | commercial | 1 | 28 | H:28 / M:0 / L:0 |
| Nvidia | commercial | 1 | 7 | H:7 / M:0 / L:0 |
| TII | academic | 1 | 2 | H:2 / M:0 / L:0 |
| Tencent | commercial | 1 | 5 | H:4 / M:1 / L:0 |

## Technique Coverage Matrix

| Technique | Anthropic | Google | Alibaba | Meta | Mistral AI | OpenAI | xAI | DeepSeek | Cohere | Microsoft | Amazon | Nvidia | TII | Tencent |
|-----------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Community-Based Evaluation | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | — | — | — | — | — | — |
| Red Teaming | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Safety Benchmarking | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| Access Control Documentation | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ | — | — | — |
| Capability Threshold Monitoring | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | ✅ | — | — | — |
| Data Retention Policies | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | ✅ | — | — | — |
| Data Sovereignty Controls | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — |
| Enterprise Integration Safety | ✅ | ✅ | ✅ | — | — | — | ✅ | — | ✅ | — | — | — | — | — |
| Ethical Human Labour Sourcing | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — | ✅ | — | — | — | — |
| Incident Reporting Systems | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | ✅ | — | — | — | — |
| Independent Safety Advisory | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | ✅ | — | — | — | — |
| Model Weight Security | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | ✅ | — | — | — |
| Regulatory Compliance | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — | — | — | ✅ | — | — | — |
| Responsible Release Protocols | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | ✅ | ✅ | ✅ | — | — | — |
| Stakeholder Engagement | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | ✅ | — | — | — | — |
| Voluntary Safety Commitments & Pledges | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | — | — | — | — |
| Whistleblower & Internal Safety Reporting | ✅ | — | ✅ | — | — | — | — | — | — | — | — | — | — | — |
| Autonomous Behaviour Classification | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | — | — | — | — |
| CSAM Detection & Prevention | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | — | — | — |
| Copyright & IP Violation Detection | ✅ | ✅ | ✅ | — | — | ✅ | — | ✅ | — | — | ✅ | — | — | — |
| Cybersecurity Threat Detection | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | — | — | ✅ | — | — | — |
| Hate Speech & Harassment Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | — | — |
| Misinformation & False Claims Detection | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | ✅ | — | — | — | — | — |
| PII Detection & Redaction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | — | ✅ |
| Self-Harm & Suicide Prevention | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — |
| Sexual Content Moderation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | — | — |
| Sycophancy Detection | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | — | — | — |
| Violence & Gore Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | — | — |
| Weapons & Illegal Activity Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — |
| Adversarial Training | ✅ | — | ✅ | ✅ | ✅ | — | — | — | — | — | — | — | — | — |
| Bias Mitigation (Post-Training) | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ | — | — | — |
| Constitutional AI / Self-Critique | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | — | — | ✅ | — | — | — |
| Dataset Auditing & Representation Analysis | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | — | — | ✅ | ✅ | — | — | — | 🟡 |
| Differential Privacy in Training | ✅ | ✅ | ✅ | — | — | ✅ | — | — | — | — | — | — | — | — |
| Direct Preference Optimization (DPO) | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | ✅ | ✅ | — | ✅ | — | ✅ |
| Machine Unlearning * | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Multimodal Safety Alignment | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | ✅ | — | — | — |
| Refusal / Abstention Training | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — |
| Reinforcement Learning from Human Feedback (RLHF) | — | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | ✅ | ✅ | — | ✅ |
| Safety Reward Modeling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | ✅ | — | — |
| Scalable Oversight & Debate | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Training Data Quality Filtering | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Circuit Breakers / Kill Switches * | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Code Execution Sandboxing | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | — | — | — | — |
| Configurable Safety Policies | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | ✅ | — | — | — |
| Hallucination Detection & Grounding | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | ✅ | — | — | — | — | — |
| Input Guardrail Systems | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | — | — | — |
| Jailbreak & Injection Defense | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — |
| Multi-stage Safety Pipeline | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | — | ✅ | — | — | — |
| Observability & Audit Logging | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — |
| Output Safety Systems | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — | ✅ | — | — | — |
| Provenance & Watermarking | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — | — | — | — | — | — |
| RAG Guardrails | ✅ | ✅ | ✅ | — | — | ✅ | — | — | — | — | — | — | — | — |
| Real-time Fact Checking | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | ✅ | — | — | — |
| System Prompts / Metaprompts | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — | — | — |

**Key:** ✅ = High confidence | 🟡 = Medium | 🟠 = Low | — = Not detected

**\*** Aspirational technique — no tracked provider has documented production deployment.

## Recent Source Documents

| Provider | Document | Type | URI | Date Added |
|----------|----------|------|-----|------------|
| Anthropic | Claude Sonnet 4.6 System Card | System Card | https://www-cdn.anthropic.com/78073f739564e986ff3e2852276... | 2026-02-17 |
| TII | The Falcon Series of Open Language Models | Technical Report | https://arxiv.org/pdf/2311.16867 | 2026-02-16 |
| Mistral AI | Magistral Technical Report | Technical Report | https://arxiv.org/pdf/2506.10910 | 2026-02-16 |
| Alibaba | Qwen3 Technical Report | Technical Report | https://arxiv.org/pdf/2505.09388 | 2026-02-16 |
| Cohere | Command A Technical Report | Technical Report | https://arxiv.org/pdf/2504.00698 | 2026-02-06 |
| Google | Gemini 3 Pro - Model Card | Model Card | https://storage.googleapis.com/deepmind-media/Model-Cards... | 2026-02-06 |
| Google | Gemini 2.5 Flash-Lite - Model Card | Model Card | https://storage.googleapis.com/deepmind-media/Model-Cards... | 2026-02-06 |
| xAI | Grok 4 Model Card | Model Card | https://data.x.ai/2025-08-20-grok-4-model-card.pdf | 2026-02-06 |
| Meta | Llama 3 & 4 Safety Protections | Website | https://www.llama.com/llama-protections/ | 2026-02-06 |
| Mistral AI | Mistral Guardrailing Capabilities | Documentation | https://docs.mistral.ai/capabilities/guardrailing | 2026-02-06 |