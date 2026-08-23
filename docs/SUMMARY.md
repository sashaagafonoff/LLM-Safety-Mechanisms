# LLM Safety Mechanisms - Dataset Summary

*Generated: 2026-08-23 10:41*

## Overall Statistics

- **Providers**: 14
- **Models tracked**: 110
- **Technique categories**: 5
- **Active techniques in taxonomy**: 55
- **Aspirational techniques** (no provider evidence): 2
- **Source documents**: 80
- **Techniques with detections**: 55 / 55

## Coverage by Category

| Category | Techniques | System Detected | Manual Entry |
|----------|------------|-----------------|--------------|
| Evaluation & Red Teaming | 3 | 3 | 0 |
| Governance & Oversight | 14 | 14 | 0 |
| Harm & Content Classification | 12 | 12 | 0 |
| Model Development | 14 | 14 | 0 |
| Runtime Safety Systems | 14 | 14 | 0 |

## Provider Breakdown

| Provider | Type | Source Docs | Techniques | Detection Confidence |
|----------|------|-------------|------------|----------------------|
| Anthropic | commercial | 12 | 57 | H:57 / M:0 / L:0 |
| Google | commercial | 9 | 52 | H:49 / M:3 / L:0 |
| Microsoft | commercial | 8 | 48 | H:45 / M:3 / L:0 |
| OpenAI | commercial | 8 | 51 | H:51 / M:0 / L:0 |
| Mistral AI | commercial | 7 | 16 | H:15 / M:1 / L:0 |
| xAI | commercial | 7 | 37 | H:37 / M:0 / L:0 |
| Meta | commercial | 6 | 50 | H:50 / M:0 / L:0 |
| Alibaba | commercial | 5 | 48 | H:47 / M:1 / L:0 |
| Cohere | commercial | 4 | 26 | H:24 / M:2 / L:0 |
| DeepSeek | commercial | 4 | 40 | H:39 / M:1 / L:0 |
| Amazon | commercial | 3 | 38 | H:38 / M:0 / L:0 |
| Nvidia | commercial | 3 | 36 | H:34 / M:2 / L:0 |
| TII | academic | 3 | 3 | H:2 / M:0 / L:1 |
| Tencent | commercial | 1 | 5 | H:5 / M:0 / L:0 |

## Technique Coverage Matrix

| Technique | Anthropic | Google | Microsoft | OpenAI | Mistral AI | xAI | Meta | Alibaba | Cohere | DeepSeek | Amazon | Nvidia | TII | Tencent |
|-----------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Community-Based Evaluation | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — |
| Red Teaming | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | — | — |
| Safety Benchmarking | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Access Control Documentation | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — |
| Capability Threshold Monitoring | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Data Retention Policies | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — |
| Data Sovereignty Controls | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | ✅ | — | ✅ | — | — |
| Enterprise Integration Safety | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | ✅ | — | — | — |
| Ethical Human Labour Sourcing | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | — | — | — | ✅ | — | — |
| Incident Reporting Systems | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — |
| Independent Safety Advisory | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | ✅ | — | — | — |
| Model Weight Security | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — | ✅ | — | — | — |
| Regulatory Compliance | ✅ | 🟡 | ✅ | ✅ | — | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | — | — |
| Responsible Release Protocols | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | ✅ | — | ✅ | — | 🟠 | — |
| Stakeholder Engagement | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — |
| Voluntary Safety Commitments & Pledges | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | — | ✅ | — | — |
| Whistleblower & Internal Safety Reporting | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Autonomous Behaviour Classification | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | — | — |
| CSAM Detection & Prevention | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Copyright & IP Violation Detection | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | — | ✅ | ✅ | 🟡 | — | — |
| Cybersecurity Threat Detection | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — |
| Hate Speech & Harassment Detection | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Misinformation & False Claims Detection | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — |
| PII Detection & Redaction | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — | — | ✅ |
| Self-Harm & Suicide Prevention | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Sexual Content Moderation | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Sycophancy Detection | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Violence & Gore Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Weapons & Illegal Activity Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | 🟡 | — | — |
| Adversarial Training | ✅ | — | ✅ | — | ✅ | — | ✅ | ✅ | — | — | — | — | — | — |
| Bias Mitigation (Post-Training) | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — |
| Constitutional AI / Self-Critique | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — |
| Dataset Auditing & Representation Analysis | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | ✅ | ✅ | — | — |
| Differential Privacy in Training | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | — | — | — | — | — | — |
| Direct Preference Optimization (DPO) | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ |
| Machine Unlearning * | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Multimodal Safety Alignment | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Refusal / Abstention Training | ✅ | 🟡 | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Reinforcement Learning from Human Feedback (RLHF) | ✅ | ✅ | ✅ | — | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| Safety Reward Modeling | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Scalable Oversight & Debate | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | — | — |
| Supervised Fine-Tuning (SFT) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| Training Data Quality Filtering | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Age Verification & Minor Protection | ✅ | — | — | — | — | — | — | — | — | 🟡 | — | — | — | — |
| Circuit Breakers / Kill Switches * | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Code Execution Sandboxing | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| Configurable Safety Policies | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Hallucination Detection & Grounding | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | ✅ | — | — | — | — |
| Input Guardrail Systems | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | — | — |
| Jailbreak & Injection Defense | ✅ | ✅ | 🟡 | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — |
| Multi-stage Safety Pipeline | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Observability & Audit Logging | ✅ | 🟡 | — | ✅ | — | ✅ | — | 🟡 | — | — | ✅ | — | — | — |
| Output Safety Systems | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — |
| Provenance & Watermarking | ✅ | ✅ | 🟡 | — | — | — | ✅ | ✅ | — | ✅ | — | ✅ | — | — |
| RAG Guardrails | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | — | ✅ | — | — | — | — |
| Real-time Fact Checking | ✅ | ✅ | — | ✅ | — | — | ✅ | — | — | ✅ | ✅ | ✅ | — | — |
| System Prompts / Metaprompts | ✅ | ✅ | 🟡 | ✅ | ✅ | — | ✅ | — | 🟡 | ✅ | — | — | — | — |

**Key:** ✅ = High confidence | 🟡 = Medium | 🟠 = Low | — = Not detected

**\*** Aspirational technique — no tracked provider has documented production deployment.

## Recent Source Documents

| Provider | Document | Type | URI | Date Added |
|----------|----------|------|-----|------------|
| Anthropic | System Card: Claude Sonnet 5 | System Card | https://www-cdn.anthropic.com/480e0bb54327b9622282e9c39a8... | 2026-08-23 |
| Anthropic | System Card: Claude Opus 5 | System Card | https://www-cdn.anthropic.com/c5fbac3f0b1280a933ebd26d3cb... | 2026-08-23 |
| OpenAI | GPT-5.6 System Card | System Card | https://deploymentsafety.openai.com/gpt-5-6/gpt-5-6.pdf | 2026-08-23 |
| xAI | Grok 4.20 Model Card | Model Card | https://data.x.ai/2026-04-07-grok-4-20-model-card.pdf | 2026-08-23 |
| xAI | Grok 4.6 Model Card | Model Card | https://media.x.ai/v1/website/card-4p6-4cd2dc57.pdf | 2026-08-23 |
| xAI | xAI Frontier Artificial Intelligence Framework (June 2026) | Framework | https://media.x.ai/v1/website/xai-frontier-artificial-int... | 2026-08-23 |
| DeepSeek | DeepSeek Model & Algorithm Disclosure | Policy | https://cdn.deepseek.com/policies/en-US/model-algorithm-d... | 2026-08-23 |
| TII | Falcon-H1: A Family of Hybrid-Head Language Models | Technical Report | https://arxiv.org/pdf/2507.22448 | 2026-08-23 |
| TII | Falcon-H1R: Pushing the Reasoning Frontiers | Technical Report | https://arxiv.org/pdf/2601.02346 | 2026-08-23 |
| Mistral AI | Shieldstral 1.0 Model Card (Moderation Model) | Documentation | https://docs.mistral.ai/models/model-cards/shieldstral-1-0 | 2026-08-23 |