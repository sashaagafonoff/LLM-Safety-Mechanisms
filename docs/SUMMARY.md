# LLM Safety Mechanisms - Dataset Summary

*Generated: 2026-06-20 12:12*

## Overall Statistics

- **Providers**: 14
- **Models tracked**: 102
- **Technique categories**: 5
- **Active techniques in taxonomy**: 55
- **Aspirational techniques** (no provider evidence): 2
- **Source documents**: 70
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
| Anthropic | commercial | 10 | 57 | H:57 / M:0 / L:0 |
| Google | commercial | 9 | 52 | H:49 / M:3 / L:0 |
| Microsoft | commercial | 8 | 48 | H:45 / M:3 / L:0 |
| OpenAI | commercial | 7 | 51 | H:51 / M:0 / L:0 |
| Meta | commercial | 6 | 50 | H:50 / M:0 / L:0 |
| Mistral AI | commercial | 6 | 16 | H:15 / M:1 / L:0 |
| Alibaba | commercial | 5 | 48 | H:47 / M:1 / L:0 |
| Cohere | commercial | 4 | 26 | H:24 / M:2 / L:0 |
| xAI | commercial | 4 | 37 | H:37 / M:0 / L:0 |
| Amazon | commercial | 3 | 38 | H:38 / M:0 / L:0 |
| DeepSeek | commercial | 3 | 40 | H:39 / M:1 / L:0 |
| Nvidia | commercial | 3 | 36 | H:34 / M:2 / L:0 |
| TII | academic | 1 | 3 | H:2 / M:0 / L:1 |
| Tencent | commercial | 1 | 5 | H:5 / M:0 / L:0 |

## Technique Coverage Matrix

| Technique | Anthropic | Google | Microsoft | OpenAI | Meta | Mistral AI | Alibaba | Cohere | xAI | Amazon | DeepSeek | Nvidia | TII | Tencent |
|-----------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Community-Based Evaluation | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | — |
| Red Teaming | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ | — | — |
| Safety Benchmarking | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — |
| Access Control Documentation | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Capability Threshold Monitoring | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Data Retention Policies | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | — |
| Data Sovereignty Controls | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | — | ✅ | ✅ | — | — |
| Enterprise Integration Safety | ✅ | ✅ | ✅ | ✅ | — | — | — | — | ✅ | ✅ | — | — | — | — |
| Ethical Human Labour Sourcing | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ | — | — | ✅ | — | — |
| Incident Reporting Systems | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Independent Safety Advisory | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | ✅ | — | — | — | — |
| Model Weight Security | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | — | — | — | — |
| Regulatory Compliance | ✅ | 🟡 | ✅ | ✅ | ✅ | — | — | — | ✅ | ✅ | ✅ | ✅ | — | — |
| Responsible Release Protocols | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | ✅ | — | — | 🟠 | — |
| Stakeholder Engagement | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Voluntary Safety Commitments & Pledges | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — | ✅ | — | — |
| Whistleblower & Internal Safety Reporting | ✅ | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Autonomous Behaviour Classification | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | — | ✅ | ✅ | — | — |
| CSAM Detection & Prevention | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Copyright & IP Violation Detection | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | — | ✅ | ✅ | 🟡 | — | — |
| Cybersecurity Threat Detection | ✅ | ✅ | — | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | — | — | — |
| Hate Speech & Harassment Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — |
| Misinformation & False Claims Detection | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| PII Detection & Redaction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | ✅ | — | — | ✅ |
| Self-Harm & Suicide Prevention | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Sexual Content Moderation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — |
| Sycophancy Detection | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Violence & Gore Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Weapons & Illegal Activity Detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | 🟡 | — | — |
| Adversarial Training | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | — | — | — | — | — | — | — |
| Bias Mitigation (Post-Training) | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — |
| Constitutional AI / Self-Critique | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | — | — | — |
| Dataset Auditing & Representation Analysis | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | ✅ | ✅ | — | ✅ | — | — |
| Differential Privacy in Training | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | ✅ | — | — | — | — | — |
| Direct Preference Optimization (DPO) | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | ✅ |
| Machine Unlearning * | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Multimodal Safety Alignment | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Refusal / Abstention Training | ✅ | 🟡 | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Reinforcement Learning from Human Feedback (RLHF) | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | ✅ |
| Safety Reward Modeling | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | ✅ | ✅ | — | — |
| Scalable Oversight & Debate | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ | — | ✅ | ✅ | — | — |
| Supervised Fine-Tuning (SFT) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| Training Data Quality Filtering | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Age Verification & Minor Protection | ✅ | — | — | — | — | — | — | — | — | — | 🟡 | — | — | — |
| Circuit Breakers / Kill Switches * | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Code Execution Sandboxing | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | — | ✅ | — | — | — |
| Configurable Safety Policies | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | — | — |
| Hallucination Detection & Grounding | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | — | — | ✅ | — | — | — |
| Input Guardrail Systems | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — |
| Jailbreak & Injection Defense | ✅ | ✅ | 🟡 | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | — | — | — |
| Multi-stage Safety Pipeline | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| Observability & Audit Logging | ✅ | 🟡 | — | ✅ | — | — | 🟡 | — | ✅ | ✅ | — | — | — | — |
| Output Safety Systems | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | — |
| Provenance & Watermarking | ✅ | ✅ | 🟡 | — | ✅ | — | ✅ | — | — | — | ✅ | ✅ | — | — |
| RAG Guardrails | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | — | — | ✅ | — | — | — |
| Real-time Fact Checking | ✅ | ✅ | — | ✅ | ✅ | — | — | — | — | ✅ | ✅ | ✅ | — | — |
| System Prompts / Metaprompts | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | — | 🟡 | — | — | ✅ | — | — | — |

**Key:** ✅ = High confidence | 🟡 = Medium | 🟠 = Low | — = Not detected

**\*** Aspirational technique — no tracked provider has documented production deployment.

## Recent Source Documents

| Provider | Document | Type | URI | Date Added |
|----------|----------|------|-----|------------|
| Anthropic | System Card: Claude Opus 4.8 | System Card | https://www-cdn.anthropic.com/0b4915911bb0d19eca5b5ee635c... | 2026-06-19 |
| Anthropic | System Card: Claude Opus 4.7 | System Card | https://cdn.sanity.io/files/4zrzovbb/website/037f06850df7... | 2026-06-19 |
| Anthropic | System Card: Claude Opus 4.6 | System Card | https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574... | 2026-06-19 |
| Anthropic | System Card: Claude Fable 5 & Mythos 5 | System Card | https://www-cdn.anthropic.com/d00db56fa754a1b115b6dd7cb2e... | 2026-06-19 |
| OpenAI | GPT-5.5 System Card | System Card | https://deploymentsafety.openai.com/gpt-5-5/gpt-5-5.pdf | 2026-06-19 |
| OpenAI | GPT-5.4 Thinking System Card | System Card | https://deploymentsafety.openai.com/gpt-5-4-thinking/gpt-... | 2026-06-19 |
| Google | Gemini 3.5 Flash Model Card | Model Card | https://deepmind.google/models/model-cards/gemini-3-5-flash/ | 2026-06-19 |
| Google | Gemini 3.1 Pro Model Card | Model Card | https://deepmind.google/models/model-cards/gemini-3-1-pro/ | 2026-06-19 |
| Google | Gemini 3.1 Flash-Lite Model Card | Model Card | https://deepmind.google/models/model-cards/gemini-3-1-fla... | 2026-06-19 |
| Microsoft | Phi-4-reasoning Model Card | Model Card | https://huggingface.co/microsoft/Phi-4-reasoning | 2026-06-19 |