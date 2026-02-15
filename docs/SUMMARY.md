# LLM Safety Mechanisms - Dataset Summary

*Generated: 2026-02-15 16:56*

## 📊 Overall Statistics

- **Providers**: 15
- **Models**: 1
- **Categories**: 5
- **Techniques**: 50
- **Source Documents**: 37
- **Techniques Detected**: 52

## 🎯 Coverage by Category

| Category | Total Techniques | Detected in Sources |
|----------|------------------|---------------------|
| Evaluation & Red Teaming | 3 | 3 |
| Governance & Oversight | 11 | 10 |
| Harm & Content Classification | 12 | 11 |
| Model Development | 11 | 10 |
| Runtime Safety Systems | 13 | 12 |

## 🏢 Provider Breakdown

### OpenAI

- **Type**: commercial
- **Source Documents**: 4
- **Techniques Detected**: 34

**Detection Confidence**:
- High: 65
- Medium: 8

### Anthropic

- **Type**: commercial
- **Source Documents**: 4
- **Techniques Detected**: 36

**Detection Confidence**:
- High: 61
- Medium: 8

### Google

- **Type**: commercial
- **Source Documents**: 5
- **Techniques Detected**: 28

**Detection Confidence**:
- High: 48
- Medium: 11
- Low: 2

### Meta

- **Type**: commercial
- **Source Documents**: 4
- **Techniques Detected**: 39

**Detection Confidence**:
- High: 51
- Medium: 13
- Low: 3

### Amazon

- **Type**: commercial
- **Source Documents**: 1
- **Techniques Detected**: 0

### Microsoft

- **Type**: commercial
- **Source Documents**: 2
- **Techniques Detected**: 15

**Detection Confidence**:
- High: 19
- Medium: 2

### DeepSeek

- **Type**: commercial
- **Source Documents**: 3
- **Techniques Detected**: 28

**Detection Confidence**:
- High: 27
- Medium: 9

### xAI

- **Type**: commercial
- **Source Documents**: 4
- **Techniques Detected**: 17

**Detection Confidence**:
- High: 17
- Medium: 5

### Cohere

- **Type**: commercial
- **Source Documents**: 2
- **Techniques Detected**: 24

**Detection Confidence**:
- High: 25
- Medium: 3

### Mistral AI

- **Type**: commercial
- **Source Documents**: 3
- **Techniques Detected**: 14

**Detection Confidence**:
- High: 11
- Medium: 3
- Low: 1

### Alibaba

- **Type**: commercial
- **Source Documents**: 3
- **Techniques Detected**: 31

**Detection Confidence**:
- High: 31
- Medium: 7
- Low: 2

### Nvidia

- **Type**: commercial
- **Source Documents**: 1
- **Techniques Detected**: 17

**Detection Confidence**:
- High: 15
- Medium: 2

### TII

- **Type**: academic
- **Source Documents**: 0
- **Techniques Detected**: 0

## 📋 Technique Coverage Matrix

| Technique | OpenAI | Anthropic | Google | Meta | Amazon |
|-----------|--------|-----------|---------|------|---------|
| Access Control Documentation | — | — | — | 🟡 Med | — |
| Adversarial Training | — | ✅ High | — | ✅ High | — |
| Autonomous Behaviour Classific | ✅ High | ✅ High | — | — | — |
| Bias Mitigation (Post-Training | 🟡 Med | ✅ High | 🟡 Med | ✅ High | — |
| Capability Threshold Monitorin | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Code Execution Sandboxing | — | — | — | ✅ High | — |
| Community-Based Evaluation | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Configurable Safety Policies | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Constitutional AI / Self-Criti | ✅ High | ✅ High | — | ✅ High | — |
| Copyright & IP Violation Detec | ✅ High | — | — | — | — |
| CSAM Detection & Prevention | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Cybersecurity Threat Detection | ✅ High | — | 🟡 Med | ✅ High | — |
| Data Retention Policies | — | — | — | — | — |
| Data Sovereignty Controls | — | — | — | ✅ High | — |
| Dataset Auditing & Representat | — | ✅ High | — | ✅ High | — |
| Direct Preference Optimization | — | — | — | ✅ High | — |
| Enterprise Integration Safety | — | — | — | — | — |
| Hallucination Detection & Grou | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Hate Speech & Harassment Detec | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Incident Reporting Systems | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Input Guardrail Systems | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Misinformation & False Claims  | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Multimodal Safety Alignment | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Multi-stage Safety Pipeline | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Observability & Audit Logging | ✅ High | ✅ High | ✅ High | — | — |
| Output Safety Systems | ✅ High | ✅ High | ✅ High | ✅ High | — |
| PII Detection & Redaction | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Jailbreak & Injection Defense | ✅ High | ✅ High | ✅ High | ✅ High | — |
| RAG Guardrails | — | — | — | ✅ High | — |
| Real-time Fact Checking | ✅ High | ✅ High | — | — | — |
| Red Teaming | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Refusal / Abstention Training | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Regulatory Compliance | ✅ High | ✅ High | — | — | — |
| Responsible Release Protocols | — | ✅ High | — | — | — |
| Reinforcement Learning from Hu | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Independent Safety Advisory | ✅ High | ✅ High | — | ✅ High | — |
| Safety Benchmarking | ✅ High | ✅ High | ✅ High | 🟠 Low | — |
| Safety Reward Modeling | ✅ High | — | 🟡 Med | ✅ High | — |
| Self-Harm & Suicide Prevention | 🟡 Med | ✅ High | — | ✅ High | — |
| Sexual Content Moderation | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Stakeholder Engagement | — | ✅ High | — | — | — |
| System Prompts / Metaprompts | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Training Data Quality Filterin | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Violence & Gore Detection | ✅ High | ✅ High | ✅ High | ✅ High | — |
| Provenance & Watermarking | — | — | 🟡 Med | 🟡 Med | — |
| Weapons & Illegal Activity Det | ✅ High | ✅ High | — | ✅ High | — |

## 📚 Recent Source Documents

| Provider | Document | Type | Date Added |
|----------|----------|------|------------|
| Cohere | Command A Technical Report | Technical Report | 2026-02-06 |
| Google | Gemini 3 Pro - Model Card | Model Card | 2026-02-06 |
| Google | Gemini 2.5 Flash-Lite - Model Card | Model Card | 2026-02-06 |
| xAI | Grok 4 Model Card | Model Card | 2026-02-06 |
| Meta | Llama 3 & 4 Safety Protections | Website | 2026-02-06 |
| Mistral AI | Mistral Guardrailing Capabilities | Documentation | 2026-02-06 |
| Alibaba | Qwen3Guard Technical Report | Technical Report | 2026-02-06 |
| Google | Gemini 3 Technical Report | Technical Report | 2026-01-22 |
| Anthropic | Claude Opus 4.5 System Card | System Card | 2026-01-20 |
| OpenAI | GPT-5 System Card | System Card | 2026-01-15 |