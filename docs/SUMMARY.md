# LLM Safety Mechanisms - Dataset Summary

*Generated: 2026-02-16 09:19*

## Overall Statistics

- **Providers**: 14
- **Models tracked**: 57
- **Technique categories**: 5
- **Active techniques in taxonomy**: 48
- **Aspirational techniques** (no provider evidence): 2
- **Source documents**: 40
- **Techniques with detections**: 48 / 48

## Coverage by Category

| Category | Techniques | System Detected | Manual Entry |
|----------|------------|-----------------|--------------|
| Evaluation & Red Teaming | 3 | 3 | 0 |
| Governance & Oversight | 11 | 11 | 0 |
| Harm & Content Classification | 12 | 12 | 0 |
| Model Development | 11 | 10 | 0 |
| Runtime Safety Systems | 13 | 12 | 0 |

## Provider Breakdown

| Provider | Type | Source Docs | Techniques | Detection Confidence |
|----------|------|-------------|------------|----------------------|
| Google | commercial | 5 | 27 | H:24 / M:3 / L:0 |
| Alibaba | commercial | 4 | 30 | H:26 / M:4 / L:0 |
| Anthropic | commercial | 4 | 38 | H:38 / M:0 / L:0 |
| Meta | commercial | 4 | 39 | H:36 / M:2 / L:1 |
| Mistral AI | commercial | 4 | 15 | H:12 / M:2 / L:1 |
| OpenAI | commercial | 4 | 35 | H:32 / M:3 / L:0 |
| xAI | commercial | 4 | 16 | H:15 / M:1 / L:0 |
| DeepSeek | commercial | 3 | 28 | H:22 / M:6 / L:0 |
| Cohere | commercial | 2 | 23 | H:20 / M:3 / L:0 |
| Microsoft | commercial | 2 | 14 | H:14 / M:0 / L:0 |
| Amazon | commercial | 1 | 11 | H:10 / M:1 / L:0 |
| Nvidia | commercial | 1 | 16 | H:14 / M:2 / L:0 |
| TII | academic | 1 | 4 | H:2 / M:2 / L:0 |
| Tencent | commercial | 1 | 7 | H:4 / M:1 / L:2 |

## Technique Coverage Matrix

| Technique | Google | Alibaba | Anthropic | Meta | Mistral AI | OpenAI | xAI | DeepSeek | Cohere | Microsoft | Amazon | Nvidia | TII | Tencent |
|-----------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Community-Based Evaluation | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ | — | — | — | — | — | — |
| Red Teaming | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | 🟡 | 🟡 | ✅ | ✅ | ✅ | — | — |
| Safety Benchmarking | ✅ | 🟡 | ✅ | 🟠 | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Access Control Documentation | — | — | — | 🟡 | — | — | ✅ | — | — | — | — | — | — | — |
| Capability Threshold Monitoring | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| Data Retention Policies | — | — | — | — | — | — | ✅ | — | — | — | — | — | — | — |
| Data Sovereignty Controls | — | — | — | ✅ | — | — | 🟡 | ✅ | — | — | — | 🟡 | — | — |
| Enterprise Integration Safety | — | — | — | — | — | — | ✅ | — | ✅ | — | — | — | — | — |
| Ethical Human Labour Sourcing | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — |
| Incident Reporting Systems | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Independent Safety Advisory | — | — | ✅ | ✅ | — | ✅ | — | — | — | — | — | — | — | — |
| Regulatory Compliance | — | — | ✅ | — | — | ✅ | ✅ | ✅ | — | — | — | — | — | — |
| Responsible Release Protocols | — | — | ✅ | — | — | — | — | — | — | — | — | — | — | — |
| Stakeholder Engagement | — | — | ✅ | — | — | — | — | — | — | ✅ | — | — | — | — |
| Autonomous Behaviour Classification | — | 🟡 | ✅ | — | — | 🟡 | — | — | — | — | — | — | — | — |
| CSAM Detection & Prevention | ✅ | — | ✅ | ✅ | — | ✅ | — | — | ✅ | — | ✅ | — | — | — |
| Copyright & IP Violation Detection | — | ✅ | — | — | — | ✅ | — | ✅ | — | — | — | — | — | — |
| Cybersecurity Threat Detection | — | — | — | ✅ | — | ✅ | — | — | 🟡 | — | — | — | — | — |
| Hate Speech & Harassment Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | 🟡 | — | — | — | ✅ | — | — |
| Misinformation & False Claims Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | 🟡 | — |
| PII Detection & Redaction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — | — | ✅ |
| Self-Harm & Suicide Prevention | — | 🟡 | ✅ | ✅ | ✅ | 🟡 | — | ✅ | — | — | — | — | — | — |
| Sexual Content Moderation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | — | ✅ | — | — |
| Sycophancy Detection | — | — | ✅ | — | — | ✅ | ✅ | — | — | — | — | — | — | — |
| Violence & Gore Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | 🟡 | ✅ | — | — |
| Weapons & Illegal Activity Detection | — | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — | — | ✅ | — | — |
| Adversarial Training | — | ✅ | ✅ | ✅ | — | — | — | 🟡 | — | — | — | — | — | — |
| Bias Mitigation (Post-Training) | 🟡 | ✅ | ✅ | ✅ | ✅ | 🟡 | — | ✅ | — | ✅ | ✅ | ✅ | — | 🟠 |
| Constitutional AI / Self-Critique | — | ✅ | ✅ | ✅ | — | ✅ | — | 🟡 | — | — | — | — | — | — |
| Dataset Auditing & Representation Analysis | — | ✅ | ✅ | ✅ | — | — | — | ✅ | — | ✅ | — | — | — | 🟡 |
| Direct Preference Optimization (DPO) | — | ✅ | — | ✅ | — | — | — | — | ✅ | ✅ | — | ✅ | — | ✅ |
| Machine Unlearning * | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Multimodal Safety Alignment | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | — | ✅ | ✅ | — | — | ✅ | — | — |
| Refusal / Abstention Training | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | 🟡 | 🟠 |
| Reinforcement Learning from Human Feedback (RLHF) | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | — | ✅ | — | — | ✅ |
| Safety Reward Modeling | 🟡 | ✅ | — | ✅ | — | ✅ | — | ✅ | ✅ | — | — | ✅ | — | — |
| Training Data Quality Filtering | ✅ | ✅ | ✅ | ✅ | 🟠 | ✅ | — | ✅ | ✅ | ✅ | — | — | ✅ | ✅ |
| Circuit Breakers / Kill Switches * | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Code Execution Sandboxing | — | — | — | ✅ | — | — | — | — | — | — | — | — | — | — |
| Configurable Safety Policies | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | 🟡 | ✅ | — | ✅ | — | — | — |
| Hallucination Detection & Grounding | ✅ | — | ✅ | ✅ | — | ✅ | — | — | ✅ | ✅ | — | — | — | — |
| Input Guardrail Systems | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | 🟡 | — | — |
| Jailbreak & Injection Defense | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | — |
| Multi-stage Safety Pipeline | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | ✅ | — | — | ✅ | — | — |
| Observability & Audit Logging | ✅ | — | ✅ | — | — | ✅ | ✅ | — | — | — | — | — | — | — |
| Output Safety Systems | ✅ | 🟡 | ✅ | ✅ | 🟡 | ✅ | — | — | — | — | ✅ | — | — | — |
| Provenance & Watermarking | 🟡 | ✅ | — | 🟡 | — | — | — | — | 🟡 | — | — | — | ✅ | — |
| RAG Guardrails | — | — | — | ✅ | — | — | — | ✅ | ✅ | — | — | ✅ | — | — |
| Real-time Fact Checking | — | ✅ | ✅ | — | — | ✅ | — | — | ✅ | — | — | — | — | — |
| System Prompts / Metaprompts | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | — | — | — | — | — | — |

**Key:** ✅ = High confidence | 🟡 = Medium | 🟠 = Low | — = Not detected

**\*** Aspirational technique — no tracked provider has documented production deployment.

## Recent Source Documents

| Provider | Document | Type | URI | Date Added |
|----------|----------|------|-----|------------|
| TII | The Falcon Series of Open Language Models | Technical Report | https://arxiv.org/pdf/2311.16867 | 2026-02-16 |
| Mistral AI | Magistral Technical Report | Technical Report | https://arxiv.org/pdf/2506.10910 | 2026-02-16 |
| Alibaba | Qwen3 Technical Report | Technical Report | https://arxiv.org/pdf/2505.09388 | 2026-02-16 |
| Cohere | Command A Technical Report | Technical Report | https://arxiv.org/pdf/2504.00698 | 2026-02-06 |
| Google | Gemini 3 Pro - Model Card | Model Card | https://storage.googleapis.com/deepmind-media/Model-Cards... | 2026-02-06 |
| Google | Gemini 2.5 Flash-Lite - Model Card | Model Card | https://storage.googleapis.com/deepmind-media/Model-Cards... | 2026-02-06 |
| xAI | Grok 4 Model Card | Model Card | https://data.x.ai/2025-08-20-grok-4-model-card.pdf | 2026-02-06 |
| Meta | Llama 3 & 4 Safety Protections | Website | https://www.llama.com/llama-protections/ | 2026-02-06 |
| Mistral AI | Mistral Guardrailing Capabilities | Documentation | https://docs.mistral.ai/capabilities/guardrailing | 2026-02-06 |
| Alibaba | Qwen3Guard Technical Report | Technical Report | https://arxiv.org/pdf/2510.14276v1 | 2026-02-06 |