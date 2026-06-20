# Model Currency Audit — LLM Safety Mechanisms

**Audit date:** 2026-06-19
**Scope:** Generative foundation models (text-LLM-centric, with image-generation models flagged where in scope) across the providers tracked by this project, plus candidate new providers.

This document audits the model lists we currently track for currency: which current-generation models are **missing**, which tracked ids are **retired / deprecated / superseded** or **misnamed**, which **new providers/models** to add, and the **authoritative documentation pointers** for each. It is an input to editing the data files — not the data files themselves. Every claim that could be confirmed against a primary/secondary source this run carries that source; everything else is explicitly flagged for human confirmation in section 6.

### Legend — verification markers

| Marker | Meaning |
|---|---|
| **[web-verified]** | Confirmed this run against an official or reputable source (URL listed where available). |
| **[unverified]** | From training knowledge or a secondary/third-party source only; a human must confirm the exact id/date before editing data files. |

> **Rule applied:** Only source URLs and dates that appear in the audit input are reproduced here. Where a primary page could not be fetched (403 / JS-render / timeout), the claim is marked accordingly and surfaced again in section 6.

---

## 1. Models to ADD

Grouped by provider. Each entry lists proposed **id / family / version / modality** and a verification marker. "Optional" flags items that are GA/real but outside a strict text-LLM scope (embeddings, speech, image) — include per the tracker's chosen scope.

### Anthropic (highest priority — flagships first)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `claude-fable-5` | claude-fable-5 | text | Most-capable flagship (1M context), active as of June 2026. Cover the top flagship first. | [web-verified] |
| `claude-opus-4-8` | claude-opus-4-8 | text | Current Opus flagship, active. High-priority production-tier coverage. | [web-verified] |
| `claude-opus-4-7` | claude-opus-4-7 | text | Active Opus model. | [web-verified] |
| `claude-opus-4-6` | claude-opus-4-6 | text | Active Opus model. | [web-verified] |
| `claude-haiku-4-5` | claude-haiku-4-5 | text | Active Haiku tier. Canonical id uses **hyphens** (`claude-haiku-4-5`), not the dot form we currently track. | [web-verified] |

> **Do NOT add:** `claude-mythos-5` (Project-Glasswing-only) must not be added to a public dataset. Claude Opus 4.1 (retires 2026-08-05) and Claude 3 Haiku (retires 2026-04-19) are deprecated-but-served and not currently in our list — add only if historical/deprecated coverage is intended.

### Amazon (new generation — Nova 2 — entirely missing)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `amazon.nova-2-lite-v1:0` | Amazon Nova 2 | text+image+video in, text out | Current-gen flagship-tier, GA/Active since 2025-12-02, 1M context, extended thinking. **Highest-priority Amazon addition.** | [web-verified] |
| Nova 2 Pro (id TBD) | Amazon Nova 2 | text+image+video in, text out | Most capable Nova 2; in **Preview** (early access via Amazon Nova Forge) as of this run. Add on GA or track as preview. Exact model id not confirmed on an official page. | [web-verified] (id unverified) |
| `amazon.nova-2-sonic-v1:0` | Amazon Nova 2 | speech↔speech | GA/Active since 2025-12-02; supersedes first-gen Nova Sonic. *Optional* for a text-only scope. | [web-verified] |
| Nova Multimodal Embedding (id TBD) | Amazon Nova | multimodal in, embedding out | GA per official Nova models page. *Optional* (embedding model). Exact id not confirmed on an official page. | [web-verified] (id unverified) |

### OpenAI (tracked list substantially stale)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `gpt-5.5` | GPT-5.5 | text | Current flagship chat/reasoning model (released 2026-04-23; API 2026-04-24). Replacement target for gpt-4o, gpt-5.2, o3. | [web-verified] |
| `gpt-5.5-pro` | GPT-5.5 | text | Pro/high-reasoning tier (API since 2026-04-24); replacement for o3-pro. | [web-verified] |
| `gpt-5.4` | GPT-5.4 | text | Released 2026-03-05; affordable flagship-class for coding/professional work. | [web-verified] |
| `gpt-5.4-mini` | GPT-5.4 | text | Strongest current mini (coding, computer use, subagents); replaces gpt-5-mini and o4-mini. | [web-verified] |
| `gpt-5.4-nano` | GPT-5.4 | text | Lowest-cost current variant in the GPT-5.4 line. | [web-verified] |

> `gpt-oss-120b` (Apache-2.0 open-weight, released 2025-08-05) is already tracked and remains active — keep. GPT-5.5 mini/nano and a distinct "thinking" id were **not** added: no distinct canonical API ids confirmed this run. GPT-5.6 reported as expected late June 2026 but not yet confirmed released — omitted.

### Google (Pro and Flash lines advanced to point releases)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `gemini-3.5-flash` | Gemini 3 Flash | text | Current GA Flash (released 2026-05-19); replaces gemini-3-flash-preview and gemini-2.5-flash. | [web-verified] |
| `gemini-3.1-flash-lite` | Gemini 3 Flash-Lite | text | Current GA Flash-Lite (released 2026-05-07); replaces gemini-2.5-flash-lite. Canonical low-cost tier. | [web-verified] |
| `gemini-3.1-pro` | Gemini 3 Pro | text | Successor to gemini-3-pro; **in preview** (`gemini-3.1-pro-preview`, released 2026-02-19), GA pending. Current top reasoning model — confirm GA id before treating as stable. | [web-verified] (GA id unverified) |
| `gemini-2.5-pro` | Gemini 2.5 Pro | text | Still GA (released 2025-06-17), shutdown not before 2026-10-16. *Optional* given imminent retirement. | [web-verified] |
| `gemini-2.5-flash` | Gemini 2.5 Flash | text | Still GA (released 2025-06-17), shutdown not before 2026-10-16. *Optional* given imminent retirement. | [web-verified] |

### Meta (fix fabricated ids; advance the 70B; new flagship family)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `meta-llama/Llama-3.3-70B-Instruct` | Llama 3.3 | text | Current production 70B (released 2024-12-06); near-405B quality at 70B serving cost. Supersedes the plain Llama 3 70B we track. | [web-verified] |
| Muse Spark (id TBD) | Muse (Meta Superintelligence Labs) | multimodal | New flagship announced 2026-04-08 (update 2026-05-12); **proprietary, private-preview via API only**, not open weight. Add only if scope extends beyond open-weight Llama. | [web-verified] (availability ambiguous) |

> Also worth tracking even though not currently listed: Llama 4 Scout, Llama 4 Maverick (canonical names — see section 2), Llama 3.1 405B / 70B / 8B (widely deployed). Behemoth remains in training and is **not** a production model — exclude.

### Mistral (2026 trend = consolidation)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| Mistral Medium 3.5 (`mistral-medium-3.5` / `mistral-medium-2604`?) | mistral-medium | text+vision | New merged flagship (chat+reasoning+code), released ~2026-04-29; replaces Magistral Medium 1.2, Devstral 2, Mistral Large 2, Pixtral Large, Mistral Medium 3/3.1. **Exact date-stamped id unverified — confirm on model card before adding.** | [web-verified] (id unverified) |
| `mistral-small-4` | mistral-small | text+vision, reasoning, coding | Released 2026-03-16 (Apache 2.0, 119B MoE / ~6B active). Unifies Magistral+Pixtral+Devstral; replaces Magistral Small 1.2, Mistral Small 3.2, Devstral Small 1.1. | [web-verified] |
| `ministral-8b-2512` | ministral-3 | text+vision | Ministral 3 edge family (released 2025-12-02, Apache 2.0). | [web-verified] |
| `ministral-14b-2512` | ministral-3 | text+vision | Largest Ministral 3 edge model; also replaces deprecated Pixtral 12B. | [web-verified] |
| `ministral-3b-2512` | ministral-3 | text+vision | Smallest Ministral 3 edge model (split out from our bare `ministral-3`). | [web-verified] |
| `codestral` | codestral | code | Current low-latency coding specialist on the official models page. | [web-verified] |
| Devstral 2 | devstral | agentic coding | On the official models page. **Caution:** third-party retirement summary lists it for 2026-06-30 retirement — verify before adding. | [web-verified] (retirement unverified) |

### DeepSeek (V4 generation entirely missing)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `deepseek-v4-pro` | DeepSeek-V4 | text | Current flagship MoE (~1.6T total / ~49B active), 1M context, released 2026-04-24 (MIT). Top production model — absent from our list. | [web-verified] |
| `deepseek-v4-flash` | DeepSeek-V4 | text | Fast/cheaper V4 (~284B total / ~13B active), 1M context, released 2026-04-24 (MIT). The `deepseek-chat`/`deepseek-reasoner` aliases now point here. | [web-verified] |
| `deepseek-r1-0528` | DeepSeek-R1 | text | Updated R1 reasoning release (2025-05-28), substantially higher benchmarks than original R1; basis for current distill checkpoints. | [web-verified] |

### Alibaba (normalize naming; add current tiers; replace invalid ids)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `qwen3.5-plus` | qwen3.5 | text | Current flagship-tier commercial text model (latest snapshot `qwen3.5-plus-2026-02-15`), hybrid thinking. | [web-verified] |
| `qwen3.5-flash` | qwen3.5 | text | Current fast/low-cost production model (snapshot `qwen3.5-flash-2026-02-23`). | [web-verified] |
| `qwen-plus` | qwen | text | Core balanced production model (latest `qwen-plus-2025-12-01`), hybrid thinking. | [web-verified] |
| `qwen-flash` | qwen | text | Current speed tier; recommended replacement for discontinued `qwen-turbo`. | [web-verified] |
| `qwen3-coder-plus` | qwen3-coder | code | Flagship code-gen model; correct replacement for our `qwen-2-5-coder`. | [web-verified] |
| `qwen3-coder-next` | qwen3-coder | code | Primary recommended coder model (quality/speed/cost balance). | [web-verified] |
| `qwq-plus` | qwq | text-reasoning | Dedicated reasoning/thinking-only model (snapshot `qwq-plus-2025-03-05`) — the real "thinking" offering, replacing the non-existent `qwen3-thinking`. | [web-verified] |

### xAI (flagship + active 4.20 variants missing)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `grok-4.3` | Grok 4.3 | text (1M ctx, native video in) | Current flagship (released ~2026-04-30); redirect target for all retired slugs. | [web-verified] |
| `grok-4.20-0309-reasoning` | Grok 4.20 | text-reasoning | Active reasoning variant (1M ctx). | [web-verified] |
| `grok-4.20-0309-non-reasoning` | Grok 4.20 | text | Active non-reasoning variant (1M ctx). | [web-verified] |
| `grok-4.20-multi-agent-0309` | Grok 4.20 | text (multi-agent) | Active multi-agent variant; `reasoning.effort` controls agent count. | [web-verified] |
| `grok-build-0.1` | Grok Build | agentic coding (256k) | Replacement for retired `grok-code-fast-1`. *Optional* (outside core text-LLM scope). | [web-verified] |

> xAI recommends production aliases (`<modelname>` / `<modelname>-latest`), so the canonical set may alternatively be expressed as `grok-4.3` / `grok-4.20` / `grok-4.20-multi-agent` / `grok-build`.

### Microsoft (Phi-4 reasoning line + new in-house MAI family)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `Phi-4-mini-instruct` | Phi | text | Replacement for retired Phi-3-mini / Phi-3.5-mini. Active in Foundry. | [web-verified] |
| `Phi-4-reasoning` | Phi | text-reasoning | 14B open-weight reasoning model (SFT of Phi-4). | [web-verified] |
| `Phi-4-reasoning-plus` | Phi | text-reasoning | RL-enhanced variant (longer traces, higher performance). | [web-verified] |
| `Phi-4-mini-reasoning` | Phi | text-reasoning | Small reasoning-focused Phi-4 variant. | [web-verified] |
| `Phi-4-reasoning-vision-15B` | Phi | vision+text reasoning | Newest Phi (released 2026-03-04); vision-reasoning successor direction. | [web-verified] |
| `MAI-Thinking-1` | MAI | text-reasoning | First in-house flagship reasoning model (35B active MoE, 256K ctx), trained from scratch. **Private preview** in Foundry (Build 2026). High priority. | [web-verified] (preview) |
| `MAI-1-preview` | MAI | text | First end-to-end in-house foundation text model (MoE). **Public preview** on LMArena. | [web-verified] (preview) |
| `MAI-Voice-2` | MAI | speech-gen | In-house voice generation (15+ langs) via Azure Speech. *Optional* (speech). | [web-verified] |
| `MAI-Image-2.5` | MAI | image-gen | In-house text-to-image/editing, GA in Foundry. *Optional* (image). | [web-verified] |
| `MAI-Transcribe-1.5` | MAI | speech-to-text | In-house ASR (43 langs) via Azure Speech. *Optional* (speech). | [web-verified] |
| `MAI-Code-1` | MAI | code-gen | In-house code model in GitHub Copilot / VS Code. *Optional* (code). | [web-verified] |

### Cohere (dated canonical ids + current flagships)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `command-a-plus-05-2026` | Command A | text | Latest flagship MoE (released 2026-05-20). | [web-verified] |
| `command-a-reasoning-08-2025` | Command A | text-reasoning | Cohere's first reasoning model (extended thinking). | [web-verified] |
| `command-a-vision-07-2025` | Command A | image+text | Multimodal production model. | [web-verified] |
| `command-a-translate-08-2025` | Command A | text (translation) | Translation specialist (23 languages). | [web-verified] |
| `command-r-plus-08-2024` | Command R | text | Active successor to the retired `command-r-plus` (04-2024) alias. | [web-verified] |
| `command-r-08-2024` | Command R | text | Active instruction-following conversational model. | [web-verified] |
| `command-r7b-12-2024` | Command R | text | Small/fast RAG-agent model. | [web-verified] |

### NVIDIA (Nemotron 3 family — current generation, all missing)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `nemotron-3-nano-30b-a3b` | Nemotron 3 | text | Nemotron 3 Nano (30B total / ~3B active hybrid MoE), available since 2025-12-15 launch. | [web-verified] |
| `nemotron-3-super-120b-a12b` | Nemotron 3 | text | Nemotron 3 Super (~100–120B total / ~10–12B active), shipped H1 2026 (GTC ~Mar 2026). Exact id from search results, **not** page-verified (build.nvidia.com timeouts). | [web-verified] (id unverified) |
| `nemotron-3-ultra-550b-a55b` | Nemotron 3 | text | Nemotron 3 Ultra (550B total / 55B active), announced ~Jun 2026 (Computex). Exact id from search results, **not** page-verified. | [web-verified] (id unverified) |
| `nemotron-3-nano-omni-30b-a3b-reasoning` | Nemotron 3 | text/image/audio/video | Nemotron 3 Nano Omni multimodal (30B-A3B, 256K ctx), released 2026-04-28. | [web-verified] |
| `nemotron-3-content-safety` | Nemotron 3 | text (safety guard) | Content-safety guard model — directly relevant to a safety dataset. Listed on build.nvidia.com but **not** page-verified. | [unverified] |

### TII (Falcon-H1 flagship hybrid family + variants missing)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| Falcon-H1 (per-size SKUs, e.g. `Falcon-H1-34B-Instruct`) | Falcon-H1 | text | Flagship hybrid Transformer-SSM (Mamba2) family (released 2025-05-20/21): 0.5B–34B base+instruct. 34B rivals 70B-class. | [web-verified] |
| Falcon-H1R (e.g. `Falcon-H1R-7B`) | Falcon-H1R | text | Reasoning variant launched Jan 2026; frontier-class reasoning at compact scale. | [web-verified] |
| Falcon Arabic | Falcon Arabic | text | First Arabic model in the Falcon series (launched 2025-05-21), on Falcon3-7B. | [web-verified] |
| Falcon-H1 Arabic | Falcon-H1 Arabic | text | Arabic LLM on hybrid Mamba-Transformer (announced 2026-01-05), 3B/7B/34B. | [web-verified] |
| Falcon Perception | Falcon Perception | multimodal | ~0.6B early-fusion model for grounding/segmentation/doc-intelligence (released ~Apr/May 2026). | [web-verified] |
| Falcon Mamba 7B | FalconMamba | text | Pure SSM (Mamba) 7B; distinct architecture line. *Optional.* | [web-verified] |

### Tencent (Hunyuan line rebuilt around Hy3)

| Proposed id | Family | Modality | Notes | Verify |
|---|---|---|---|---|
| `hy3-preview` | Hunyuan Hy3 (Hunyuan 3.0) | text / agentic reasoning | Current flagship after platform rebuild: 295B MoE / 21B active / 256K ctx, released ~2026-04-22, open-sourced, served on the new TokenHub platform. **Single unambiguously-canonical active Tencent model.** | [web-verified] |
| `hunyuan-turbos-latest` | Hunyuan TurboS | text/chat | Fast-thinking flagship; live general-chat alias through early 2026. **Base `hunyuan-turbos` goes offline 2026-06-22.** Add only if covering the pre-migration API window; verify TokenHub availability first. | [web-verified] (availability ambiguous) |

### New image-generation models (add only if image scope is in play)

**Black Forest Labs / FLUX — new provider, see section 4.**

**OpenAI GPT Image family** (provider already tracked, `is_new_provider=false`):

| Proposed id | Family | Version | Modality | Status / date | Verify |
|---|---|---|---|---|---|
| `gpt-image-1` | GPT Image | 1 | image-generation | GA; API 2025-04-23 | [web-verified] |
| `gpt-image-1-mini` | GPT Image | 1-mini | image-generation | GA; released ~2025-10-06 (~80% cheaper) | [web-verified] (date secondary-source) |
| `gpt-image-1.5` | GPT Image | 1.5 | image-generation | GA; announced 2025-12-16 | [web-verified] |
| `gpt-image-2` | GPT Image | 2 | image-generation | GA; announced 2026-04-21; most capable, reasoning before generation | [web-verified] |

**GPT Image — confirmed real vs uncertain vs do-not-exist (explicit):**
- **GPT Image 1** → `gpt-image-1` — **confirmed real** [web-verified].
- **GPT Image 1.5** → `gpt-image-1.5` — **confirmed real** [web-verified] (announced 2025-12-16).
- **GPT Image 2** → `gpt-image-2` — **confirmed real** [web-verified] (announced 2026-04-21).
- `gpt-image-1-mini` — **confirmed real** [web-verified]; existence via docs model page + Wikipedia (date from secondary source).
- **None of the requested versions are uncertain or do-not-exist.** All four GPT Image ids are genuine, released OpenAI products — none are hallucinations.

> **OpenAI GPT Image safety mechanisms (relevant to a safety tracker)** [web-verified]: (1) C2PA / Content Credentials provenance metadata on every generated image, plus SynthID watermarking that persists when metadata is stripped (OpenAI cautions C2PA is removable, not a silver bullet); (2) input/output moderation pipeline with a tunable `moderation` parameter (`auto` default / `low`); (3) usage-policy enforcement incl. real-person-likeness restrictions and a strict CSAM prohibition; (4) access gating via API Organization Verification.

---

## 2. Models to RETIRE / re-status

Tracked ids that are retired, deprecated, superseded, fabricated, or misnamed. **Deprecated-but-not-yet-shut-down** ids remain technically callable until their shutdown date — a tracker may keep them flagged as "deprecated/sunsetting" rather than deleting immediately.

| Provider | Our id | New status | Date | Reason / action | Source | Verify |
|---|---|---|---|---|---|---|
| Anthropic | `claude-3-opus` | **retired** | 2026-01-05 | Claude 3 Opus (`claude-3-opus-20240229`) no longer served (returns 404). Remove or mark retired. | — | [web-verified] |
| Anthropic | `claude-3-5-sonnet` | **retired** | 2025-10-28 | Claude 3.5 Sonnet (`-20241022` / `-20240620`) no longer served (404). Remove or mark retired. | — | [web-verified] |
| Anthropic | `claude-opus-4.5` | **rename-needed** | — | Active/legacy but dot-form; canonical `claude-opus-4-5` (hyphens). | — | [web-verified] |
| Anthropic | `claude-sonnet-4.5` | **rename-needed** | — | Active; canonical `claude-sonnet-4-5`. | — | [web-verified] |
| Anthropic | `claude-sonnet-4.6` | **rename-needed** | — | Active; canonical `claude-sonnet-4-6`. | — | [web-verified] |
| Anthropic | `claude-haiku-4.5` | **rename-needed** | — | Active; canonical `claude-haiku-4-5`. | — | [web-verified] |
| OpenAI | `gpt-4o` | **deprecated** (API shutdown) | 2026-10-23 | Replacement `gpt-5.5`. Retired from ChatGPT 2026-02-13, fully after 2026-04-03. | developers.openai.com/api/docs/deprecations | [web-verified] |
| OpenAI | `gpt-5.2` | **retired** | 2026-06-12 | Removed from ChatGPT 2026-06-12; `gpt-5.2-chat-latest` alias shutdown 2026-08-10. Replacement `gpt-5.5`. | developers.openai.com/api/docs/deprecations | [web-verified] |
| OpenAI | `o3-pro` | **deprecated** | 2026-06-11 (shutdown 2026-12-11) | Replacement `gpt-5.5-pro`. | developers.openai.com/api/docs/deprecations | [web-verified] |
| OpenAI | `o3` | **deprecated** | 2026-06-11 (API shutdown 2026-12-11) | ChatGPT retirement 2026-08-26. Replacement `gpt-5.5`. | developers.openai.com/api/docs/deprecations | [web-verified] |
| OpenAI | `gpt-5-mini` | **deprecated** | 2026-06-11 (shutdown 2026-12-11) | Replacement `gpt-5.4-mini`. | developers.openai.com/api/docs/deprecations | [web-verified] |
| OpenAI | `gpt-5-thinking` | **rename-needed / remove** | — | ChatGPT product-mode label, not a canonical API id. Reasoning is now an effort level on unified GPT-5.4/5.5. Map to a current model. | developers.openai.com/api/docs/models | [web-verified] |
| OpenAI | `o4-mini` | **deprecated** (shutdown) | 2026-10-23 | Replacement `gpt-5.4-mini`. Also retired from ChatGPT in 2026. | developers.openai.com/api/docs/deprecations | [web-verified] |
| Google | `gemini-1-5-pro` | **retired + mis-formatted** | 2025-09-24 | Real id `gemini-1.5-pro` (dots). 1.5 family fully retired (`-002` shut down 2025-09-24). Remove. | ai.google.dev/gemini-api/docs/deprecations.md.txt | [web-verified] |
| Google | `gemini-3-pro` | **superseded** | 2026-03-09 | Preview `gemini-3-pro-preview` shut down 2026-03-09; active Pro line is now 3.1. Replace with `gemini-3.1-pro`. | ai.google.dev/gemini-api/docs/deprecations.md.txt | [web-verified] |
| Google | `gemini-3-flash` | **superseded** | 2026-05-19 | No standalone GA `gemini-3-flash`; canonical current Flash is `gemini-3.5-flash`. Replace. | ai.google.dev/gemini-api/docs/deprecations.md.txt | [web-verified] |
| Google | `gemini-2.5-flash-lite` | **deprecated** | 2026-10-16 (earliest shutdown) | Still GA (released 2025-07-22); migrate to `gemini-3.1-flash-lite`. | ai.google.dev/gemini-api/docs/deprecations.md.txt | [web-verified] |
| Google | `gemini-3-deep-think` | **keep — verify id** | — | Genuinely active (Gemini app AI Ultra + API early-access), but not in the public deprecations table; no official API id/lifecycle published. Verify precise id. | blog.google/.../gemini-3-deep-think/ | [web-verified] |
| Meta | `llama-4-8b` | **remove (fabricated)** | — | No Llama 4 8B exists. Llama 4 shipped only Scout and Maverick (+ in-training Behemoth). | ai.meta.com/blog/llama-4-multimodal-intelligence/ | [web-verified] |
| Meta | `llama-4-17b` | **remove/rename (fabricated)** | — | "17B" is the active-param count shared by **both** Scout and Maverick; never a model name. Replace with `llama-4-scout` / `llama-4-maverick`. | llama.com/docs/model-cards-and-prompt-formats/llama4/ | [web-verified] |
| Meta | `llama-3-70b` | **superseded** | 2024-12-06 | Superseded by Llama 3.1 70B then Llama 3.3 70B. Move to Llama 3.3 70B. | huggingface.co/meta-llama/Llama-3.3-70B-Instruct | [web-verified] |
| Meta | `llama-4-maverick` | **keep (awareness)** | 2026-02-20 (third-party only) | Valid current open-weight flagship; no official Meta retirement. A 2026-02-20 deprecation was a **Groq** hosting decision, not Meta. | console.groq.com/docs/deprecations | [web-verified] |
| Mistral | `magistral-medium-1.2` | **deprecated** | 2026-05-22 (retiring ~2026-06-30) | Canonical id `magistral-medium-2509`. Folded into Mistral Medium 3.5. Past its deprecation date. | docs.mistral.ai/models/magistral-medium-1-2-25-09 | [web-verified] |
| Mistral | `pixtral` | **deprecated** | 2025-12-02 | Pixtral 12B (`pixtral-12b-2409`) → Ministral 3 14B; Pixtral Large → Mistral Medium 3.5. Bare `pixtral` is non-canonical. | docs.mistral.ai/models/pixtral-12b-24-09 | [web-verified] |
| Mistral | `ministral-3` | **rename-needed (split)** | 2025-12-02 | Family of three; split into `ministral-3b-2512`, `ministral-8b-2512`, `ministral-14b-2512`. Bare id not usable. | mistral.ai/news/mistral-3/ | [web-verified] |
| Mistral | `mistral-large-3` | **rename-needed** | 2025-12-02 | Active flagship (675B total / 41B active, 256K ctx); canonical dated id `mistral-large-2512`. Keep, track dated id. | mistral.ai/news/mistral-3/ | [web-verified] |
| DeepSeek | `deepseek-v3.2` | **superseded** | 2026-04-24 | Last release before V4; aliases now map to V4-Flash. Weights may remain on HF; no longer canonical served flagship. | api-docs.deepseek.com/news/news260424 | [web-verified] |
| DeepSeek | `deepseek-v3` | **superseded** | 2026-04-24 | Old generation (V3 → V3.1 → V3.2 → V4). Not in current canonical lineup. | api-docs.deepseek.com/updates | [web-verified] |
| DeepSeek | `deepseek-v3-lite` | **remove/verify (likely invented)** | — | Could not match any official "deepseek-v3-lite" SKU. Remove or rename after verification. | — | [unverified] |
| DeepSeek | `deepseek-r1` | **superseded** | 2025-05-28 | Original R1 still open-weight but superseded by R1-0528, then V3.1/V3.2 hybrid-reasoning and V4. Stale as a "current" flagship. | huggingface.co/deepseek-ai/DeepSeek-R1-0528 | [web-verified] |
| DeepSeek | `deepseek-r1-distill` | **rename-needed (split)** | — | No single distill model; family of Qwen/Llama checkpoints (1.5B–70B) + R1-0528-Qwen3-8B. Split or label as a family. | huggingface.co/deepseek-ai/DeepSeek-R1 | [web-verified] |
| Alibaba | `qwen3-thinking` | **rename-needed (invalid id)** | — | No such id. "Thinking" is a mode on hybrid models; the dedicated reasoning product is `qwq-plus`. Replace. | alibabacloud.com/help/en/model-studio/deep-thinking | [web-verified] |
| Alibaba | `qwen3-turbo` | **rename-needed + superseded** | — | No `qwen3-turbo`; real id `qwen-turbo`, marked "no longer updated" — migrate to `qwen-flash`. | alibabacloud.com/help/en/model-studio/models | [web-verified] |
| Alibaba | `qwen-2-5-72b` | **rename-needed** | — | Canonical `qwen2.5-72b-instruct` (dots). Still available open-weight but prior-gen. | alibabacloud.com/help/en/model-studio/models | [web-verified] |
| Alibaba | `qwen-2-5-coder` | **superseded + rename** | — | Real ids `qwen2.5-coder-{7b,14b,32b}-instruct`; superseded by `qwen3-coder-plus` / `-next`. | alibabacloud.com/help/en/model-studio/qwen-coder | [web-verified] |
| xAI | `grok-1-5` | **retired** | — | Early-2024 model, long superseded; not on the current official models page. | docs.x.ai/developers/models | [web-verified] |
| xAI | `grok-4` | **retired** | 2026-05-15 | `grok-4-0709` retired 2026-05-15; requests redirect to `grok-4.3` (low reasoning) at grok-4.3 pricing. | docs.x.ai/developers/migration/may-15-retirement | [web-verified] |
| xAI | `grok-4-thinking` | **remove (invalid id)** | — | Not an official xAI id; Grok 4 reasoning is intrinsic, never a separate slug. Tracker artifact. | docs.x.ai/developers/models | [web-verified] |
| xAI | `grok-4-fast` | **deprecated** | 2026-05-15 (full retirement 2026-08-15) | Maps to `grok-4-fast-reasoning`/`-non-reasoning`; redirect to `grok-4.3`. | docs.x.ai/developers/migration/may-15-retirement | [web-verified] |
| Microsoft | `phi-3-mini` | **retired** | 2025-08-30 | Phi-3-mini-4k/128k-instruct retired in Foundry; entire Phi-3/3.5 families retired. Replacement `Phi-4-mini-instruct`. | learn.microsoft.com/.../foundry/openai/concepts/retired-models | [web-verified] |
| Microsoft | `phi-4` | **keep — disambiguate** | — | Not on the retired list; active base model. Coarse alias now mapping to Phi-4 / Phi-4-mini-instruct / reasoning variants. Consider splitting. | learn.microsoft.com/.../foundry/openai/concepts/retired-models | [web-verified] |
| Microsoft | `phi-4-multimodal` | **keep (active)** | — | 5.6B unified speech/vision/text; not on retired list. Complemented (not replaced) by Phi-4-reasoning-vision-15B. | learn.microsoft.com/.../foundry/openai/concepts/retired-models | [web-verified] |
| Cohere | `command-r-plus` | **retired** | 2025-09-15 | Bare alias = `command-r-plus-04-2024`, shut down 2025-09-15; requests fail. Replace with `command-r-plus-08-2024` / `command-a-03-2025`. | docs.cohere.com/docs/deprecations | [web-verified] |
| Cohere | `command-a` | **rename-needed** | 2025-03 | Active but unversioned; maps to `command-a-03-2025`. Track dated id (note `command-a-plus-05-2026` now also exists). | docs.cohere.com/v2/docs/models | [web-verified] |
| NVIDIA | `nemotron-4` | **superseded / legacy** | 2025-12-15 | June-2024 Nemotron-4 340B gen; two generations behind. Bare id imprecise (Base/Instruct/Reward). | nvidianews.nvidia.com/news/nvidia-debuts-nemotron-3-family-of-open-models | [web-verified] |
| NVIDIA | `llama-3.1-nemotron` | **superseded + rename/split** | 2025-12-15 | Llama-Nemotron family superseded by Nemotron 3. Non-canonical umbrella id mapping to multiple SKUs; the 70B-instruct NIM is explicitly Deprecated on build.nvidia.com. | build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct/modelcard | [web-verified] |
| TII | `falcon-180b` | **superseded / legacy** | 2023-09-06 | Original 2023 dense 180B; still on HF but superseded by Falcon 3 and Falcon-H1. Not part of current flagship lineup. | huggingface.co/tiiuae/falcon-180B | [web-verified] |
| Tencent | `hunyuan-large` | **superseded** | 2026-06-22 | Nov-2024 legacy-platform model. Legacy Hunyuan platform sunsetting (46 models offline 2026-06-22; full shutdown 2026-09-30); migrate to `hy3-preview`. Open weights remain on HF. | finance.sina.com.cn/.../2026-05-22/doc-inhyurwk6036551.shtml | [web-verified] |

### Amazon — tracked Nova ids: no removal needed, but label as prior-generation

The Amazon ids we track are **all still Active** per their official model cards — do **not** retire them — but they are prior-generation and should be labeled to avoid confusion with Nova 2:

| Our id | Status | Note | Source | Verify |
|---|---|---|---|---|
| `nova-pro` | **Active (prior-gen)** | `amazon.nova-pro-v1:0`, launched 2024-12-05. NOT retired (some third-party blogs wrongly claim Legacy). Superseded in practice by Nova 2. | docs.aws.amazon.com/.../model-card-amazon-nova-pro.html | [web-verified] |
| `nova-lite` | **Active (prior-gen)** | `amazon.nova-lite-v1:0`. **Disambiguate from `nova-2-lite`** — different models, ids must not be conflated. | docs.aws.amazon.com/.../model-lifecycle.html | [web-verified] |
| `nova-micro` | **Active (prior-gen)** | `amazon.nova-micro-v1:0`, launched 2024-12-05. No Nova 2 Micro exists yet. | docs.aws.amazon.com/.../model-card-amazon-nova-micro.html | [web-verified] |

> **Confirmed Amazon Legacy/EOL** (official lifecycle page; not in our tracked list, for context): Nova Premier (`amazon.nova-premier-v1:0`) Legacy 2026-03-13 / EOL 2026-09-14; Nova Sonic (`amazon.nova-sonic-v1:0`) Legacy 2026-03-13 / EOL 2026-09-14; Nova Canvas Legacy 2026-03-30 / EOL 2026-09-30; Nova Reel (`v1:0`/`v1:1`) Legacy 2026-03-30 / EOL 2026-09-30; Titan Image Generator G1 v2 Legacy 2025-12-30 / EOL 2026-06-30. [web-verified]

---

## 3. (reserved)

*(Section numbering follows the requested structure; ADD = §1, RETIRE = §2, new providers = §4.)*

---

## 4. New providers to add

### Black Forest Labs — `black-forest-labs` (new provider) [web-verified]

German generative-AI lab (founded 2024 by Robin Rombach, Andreas Blattmann, Patrick Esser — Stable Diffusion / latent-diffusion researchers). **HQ:** Freiburg im Breisgau, Germany, with a San Francisco lab. Reported as Germany's most valuable AI company (~$3.25–4B valuation). Suggested `provider_id`: `black-forest-labs`. **Modality for the entire lineup is image-generation** (text-to-image + image editing / in-context editing); no LLM/text modality.

| Proposed id | Family | Version | Status | Verify |
|---|---|---|---|---|
| `flux-2-pro` | FLUX.2 | FLUX.2 [pro] | Active (managed API). **Current flagship** (~Nov 2025); multi-reference editing up to 10 images, edits up to 4MP. | [web-verified] |
| `flux-2-flex` | FLUX.2 | FLUX.2 [flex] | Active (managed API); developer controls over steps/guidance. | [web-verified] |
| `flux-2-dev` | FLUX.2 | FLUX.2 [dev] | Open weights (FLUX Non-Commercial License); 32B flow-matching transformer; most powerful open-weight image gen+edit model. | [web-verified] |
| `flux-2-klein` | FLUX.2 | FLUX.2 [klein] | Open weights (Apache 2.0), size-distilled 9B/4B (+fp8). "Coming soon" at FLUX.2 launch; HF repos exist; secondary sources indicate ~Jan 2026 (date not on official page). | [web-verified] (date unverified) |
| `flux-1-1-pro-ultra` | FLUX1.1 | FLUX1.1 [pro] Ultra | Active (managed API); up to 4MP, Raw mode. | [web-verified] |
| `flux-1-1-pro` | FLUX1.1 | FLUX1.1 [pro] | Active (managed API); previous flagship before FLUX.2. | [web-verified] |
| `flux-1-kontext-pro` | FLUX.1 Kontext | Kontext [pro] | Active (managed API); in-context editing (cited powering teams at Adobe, Meta). | [web-verified] |
| `flux-1-kontext-dev` | FLUX.1 Kontext | Kontext [dev] | Active (open weights, self-hosting); single-image editing. | [web-verified] |
| `flux-1-krea-dev` | FLUX.1 Krea | Krea [dev] | Active (open weights); 12B rectified-flow, photorealism, with Krea AI, released ~2025-07-31. | [web-verified] |
| `flux-1-dev` | FLUX.1 | FLUX.1 [dev] | Active (open weights, non-commercial); "most popular open image model globally" (launched Aug 2024). | [web-verified] |
| `flux-1-schnell` | FLUX.1 | FLUX.1 [schnell] | Active (open weights, Apache 2.0); fast distilled. | [unverified] (secondary source: Wikipedia) |
| `flux-1-pro` | FLUX.1 | FLUX.1 [pro] | Active/legacy (closed API; superseded by FLUX1.1 [pro] and FLUX.2). | [unverified] (secondary source: Wikipedia) |
| `flux-1-tools-dev` | FLUX.1 Tools | Tools [dev] | Active (open weights + API); editing suite (outpaint/inpaint/remove/structural conditioning). | [web-verified] |

**FLUX safety notes:** FLUX.2 [dev] inference code includes example pixel-layer watermarking and C2PA links; the FLUX Non-Commercial License requires filters or manual review for klein-9B (mitigations encouraged for 4B); FLUX.1 Krea [dev] GitHub repo includes filters for illegal/infringing content. [web-verified]

> **OpenAI is NOT a new provider** — the GPT Image models in §1 attach to the existing `openai` provider (`is_new_provider=false`).

---

## 5. Latest documentation references

Authoritative doc / model-card / announcement URLs gathered this run (only sources that appear in the audit input). Where a primary page could not be fetched directly, it is noted in §6.

| Provider / model | Authoritative URL |
|---|---|
| Amazon — Nova 2 Lite model card | https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-lite.html |
| Amazon — Nova 2 announcement | https://aws.amazon.com/about-aws/whats-new/2025/12/nova-2-foundation-models-amazon-bedrock/ |
| Amazon — Nova 2 Sonic model card | https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-2-sonic.html |
| Amazon — Nova models page | https://aws.amazon.com/nova/models/ |
| Amazon — Nova Pro model card | https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-pro.html |
| Amazon — Nova Micro model card | https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-micro.html |
| Amazon — model lifecycle / Legacy table | https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html |
| OpenAI — models | https://developers.openai.com/api/docs/models |
| OpenAI — deprecations | https://developers.openai.com/api/docs/deprecations |
| OpenAI — Image Generation API (gpt-image-1) | https://openai.com/index/image-generation-api/ |
| OpenAI — gpt-image-1-mini model page | https://developers.openai.com/api/docs/models/gpt-image-1-mini |
| OpenAI — gpt-image-1.5 model page | https://developers.openai.com/api/docs/models/gpt-image-1.5 |
| OpenAI — "New ChatGPT Images is here" (gpt-image-1.5) | https://openai.com/index/new-chatgpt-images-is-here/ |
| OpenAI — gpt-image-2 model page | https://developers.openai.com/api/docs/models/gpt-image-2 |
| OpenAI — "Introducing ChatGPT Images 2.0" (gpt-image-2) | https://openai.com/index/introducing-chatgpt-images-2-0/ |
| OpenAI — GPT Image (Wikipedia) | https://en.wikipedia.org/wiki/GPT_Image |
| OpenAI — C2PA in ChatGPT Images | https://help.openai.com/en/articles/8912793-c2pa-in-chatgpt-images |
| OpenAI — Advancing content provenance | https://openai.com/index/advancing-content-provenance/ |
| Google — Gemini API deprecations | https://ai.google.dev/gemini-api/docs/deprecations.md.txt |
| Google — Gemini 3.1 Pro blog | https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/ |
| Google — Gemini 3 Deep Think blog | https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-deep-think/ |
| Meta — Llama 3.3 70B Instruct (HF) | https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct |
| Meta — Llama 4 blog | https://ai.meta.com/blog/llama-4-multimodal-intelligence/ |
| Meta — Llama 4 model cards | https://www.llama.com/docs/model-cards-and-prompt-formats/llama4/ |
| Meta — Muse Spark newsroom | https://about.fb.com/news/2026/04/introducing-muse-spark-meta-superintelligence-labs/ |
| Meta — Maverick (third-party Groq deprecation) | https://console.groq.com/docs/deprecations |
| Mistral — Medium 3.5 news | https://mistral.ai/news/vibe-remote-agents-mistral-medium-3-5/ |
| Mistral — Small 4 news | https://mistral.ai/news/mistral-small-4/ |
| Mistral — Mistral 3 / Ministral 3 news | https://mistral.ai/news/mistral-3/ |
| Mistral — Ministral 3 3B model card | https://docs.mistral.ai/models/ministral-3-3b-25-12 |
| Mistral — models page | https://mistral.ai/models/ |
| Mistral — Magistral Medium 1.2 model card | https://docs.mistral.ai/models/magistral-medium-1-2-25-09 |
| Mistral — Pixtral 12B model card | https://docs.mistral.ai/models/pixtral-12b-24-09 |
| DeepSeek — V4 news | https://api-docs.deepseek.com/news/news260424 |
| DeepSeek — updates | https://api-docs.deepseek.com/updates |
| DeepSeek — R1-0528 (HF) | https://huggingface.co/deepseek-ai/DeepSeek-R1-0528 |
| DeepSeek — R1 (HF) | https://huggingface.co/deepseek-ai/DeepSeek-R1 |
| Alibaba — Model Studio models | https://www.alibabacloud.com/help/en/model-studio/models |
| Alibaba — Qwen Coder | https://www.alibabacloud.com/help/en/model-studio/qwen-coder |
| Alibaba — Deep Thinking (qwq) | https://www.alibabacloud.com/help/en/model-studio/deep-thinking |
| xAI — models page | https://docs.x.ai/developers/models |
| xAI — Grok 4.3 model card | https://docs.x.ai/developers/models/grok-4.3 |
| xAI — May-15 retirement / migration | https://docs.x.ai/developers/migration/may-15-retirement |
| Microsoft — Foundry retired models | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/retired-models |
| Microsoft — Phi-4 reasoning technical report | https://www.microsoft.com/en-us/research/publication/phi-4-reasoning-technical-report/ |
| Microsoft — Phi family blog | https://azure.microsoft.com/en-us/blog/empowering-innovation-the-next-generation-of-the-phi-family/ |
| Microsoft — Phi-4-Reasoning-Vision-15B (Foundry catalog) | https://ai.azure.com/catalog/models/Phi-4-Reasoning-Vision-15B |
| Microsoft — MAI new in-house models | https://microsoft.ai/news/two-new-in-house-models/ |
| Microsoft — MAI Foundry models (techcommunity) | https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/new-mai-models-in-microsoft-foundry-across-text-image-voice-and-speech/4524632 |
| Microsoft — MAI seven models (winbuzzer, secondary) | https://winbuzzer.com/2026/06/02/microsoft-adds-seven-mai-models-to-foundry-for-developers-xcxwbn/ |
| Cohere — models | https://docs.cohere.com/v2/docs/models |
| Cohere — deprecations | https://docs.cohere.com/docs/deprecations |
| NVIDIA — Nemotron 3 family press release | https://nvidianews.nvidia.com/news/nvidia-debuts-nemotron-3-family-of-open-models |
| NVIDIA — Nemotron 3 Nano Omni blog | https://blogs.nvidia.com/blog/nemotron-3-nano-omni-multimodal-ai-agents/ |
| NVIDIA — Nemotron 3 Content Safety model card | https://build.nvidia.com/nvidia/nemotron-3-content-safety/modelcard |
| NVIDIA — Llama-3.1-Nemotron-70B-Instruct model card | https://build.nvidia.com/nvidia/llama-3_1-nemotron-70b-instruct/modelcard |
| TII — Falcon-H1 collection (HF) | https://huggingface.co/collections/tiiuae/falcon-h1 |
| TII — Falcon-H1R collection (HF) | https://huggingface.co/collections/tiiuae/falcon-h1r |
| TII — Falcon Arabic / Falcon-H1 launch (BusinessWire) | https://www.businesswire.com/news/home/20250521901857/en/ |
| TII — Falcon-H1 Arabic (HPCwire/AIwire) | https://www.hpcwire.com/aiwire/2026/01/05/uaes-tii-launches-falcon-h1-arabic-models-in-3b-7b-and-34b-configurations/ |
| TII — Falcon Perception (MarkTechPost) | https://www.marktechpost.com/2026/04/03/tii-releases-falcon-perception-a-0-6b-parameter-early-fusion-transformer-for-open-vocabulary-grounding-and-segmentation-from-natural-language-prompts/ |
| TII — Falcon 180B (HF) | https://huggingface.co/tiiuae/falcon-180B |
| TII — org page (HF) | https://huggingface.co/tiiuae |
| Tencent — Hy3 article | https://www.tencent.com/en-us/articles/2202320.html |
| Tencent — legacy platform offline notice (Sina Finance, secondary) | https://finance.sina.com.cn/stock/estate/integration/2026-05-22/doc-inhyurwk6036551.shtml |
| Tencent — TurboS / legacy model doc | https://cloud.tencent.com/document/product/1729/105701 |
| Black Forest Labs — FLUX.2 blog | https://bfl.ai/blog/flux-2 |
| Black Forest Labs — docs | https://docs.bfl.ai/ |
| Black Forest Labs — FLUX.2-dev (HF) | https://huggingface.co/black-forest-labs/FLUX.2-dev/blob/main/README.md |
| Black Forest Labs — FLUX.2-klein-9B (HF) | https://huggingface.co/black-forest-labs/FLUX.2-klein-9B |
| Black Forest Labs — FLUX.1 Krea [dev] blog | https://bfl.ai/blog/flux-1-krea-dev |
| Black Forest Labs — FLUX.1-Kontext-dev (HF) | https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev |
| Black Forest Labs — FLUX (Wikipedia, secondary) | https://en.wikipedia.org/wiki/Flux_(text-to-image_model) |

---

## 6. Verification caveats — confirm before editing data files

Items below were **not** fully confirmed against a primary source this run. A human must verify the exact id / date / availability before committing them to data files.

**Exact model ids not confirmed on an official page (omit or confirm before adding):**
- Amazon **Nova 2 Pro** Bedrock model id and GA date (Preview as of announcement).
- Amazon **Nova Multimodal Embedding** model id.
- Google **`gemini-3.1-pro`** final GA model id (was still preview `gemini-3.1-pro-preview` as of the Feb 2026 announcement).
- Google **`gemini-3-deep-think`** precise API model id and lifecycle dates (gated behind AI Ultra / early-access; not in the public deprecations table).
- Mistral **Mistral Medium 3.5** exact API/date-stamped id (`mistral-medium-3.5` / `mistral-medium-2604` unverified — do not invent).
- NVIDIA **Nemotron 3 Super** (`nemotron-3-super-120b-a12b`), **Ultra** (`nemotron-3-ultra-550b-a55b`), and **Content Safety** ids — rest on press-release/blog + search-result titles; build.nvidia.com model cards timed out and were not directly read.
- Meta **Muse Spark** model id (proprietary, private-preview via API only — availability ambiguous).
- xAI active **Grok 4.20** dated slug forms (`grok-4.20-0309-*`) come from the rendered models page; aliases may be preferable for production.

**Status/availability to re-confirm:**
- Mistral **Devstral 2** appears on the official models page but is on a third-party retirement list (2026-06-30) — verify before treating as long-term.
- Tencent **`hunyuan-turbos-latest`** TokenHub availability post-migration (base `hunyuan-turbos` offline 2026-06-22); the full itemized 46-model offline list was not found on a primary English source, so `hunyuan-large` is `superseded` (not a hard dated-retired claim).
- Mistral retirement timeline (May 31 / Jun 30 / Jul 31 2026 batches) comes from a **third-party blog** summarizing a customer email — treat as indicative, not official.
- DeepSeek **`deepseek-v3.2`** open-weight endpoint availability after V4 (treated as superseded, not retired). **`deepseek-v3-lite`** could not be matched to any official SKU — **likely invented**, verify or remove. A **DeepSeek R2** was referenced by secondary/marketing sources but **not** confirmed shipped on official docs — deliberately omitted.
- Alibaba **`qwen3.6-max` / `qwen3.7-max`** were claimed by multiple third-party blogs (and an OpenRouter page) as April/May 2026 flagships but **could not** be confirmed on official Model Studio pages — deliberately excluded; confirm on an official model page or qwen.ai blog before adding.

**Secondary-source-only (not re-confirmed on the official/primary page this run):**
- OpenAI **`gpt-image-1-mini`** release date (~2025-10-06) and ~80% cost claim — Wikipedia/secondary only (existence is web-verified via the docs model page).
- OpenAI GPT Image **wording-level** details — primary openai.com/index pages returned 403 / JS-render; existence and dates corroborated via developers.openai.com model pages, Wikipedia, and Azure/Foundry blogs.
- Black Forest Labs **`flux-1-schnell`** and **`flux-1-pro`** — confirmed-real but via Wikipedia/secondary this run, not re-confirmed on an official BFL page. **FLUX.2 [klein]** ~Jan 2026 launch date is secondary-source.
- Black Forest Labs day-level release dates were generally **not** confirmed on official BFL pages (FLUX.2 dev HF card did not state a date) — treat day-level dates as approximate/reported.
- NVIDIA **`nemotron-3-content-safety`** marked `[unverified]` (training-knowledge / unreached model card).

**Naming-normalization actions (mechanical, but verify each id string):**
- Anthropic: convert dot ids to hyphen ids (`claude-opus-4.5` → `claude-opus-4-5`, etc.). Do **not** add `claude-mythos-5`.
- Alibaba: convert hyphen ids to dotted canonical (`qwen-2-5-72b` → `qwen2.5-72b-instruct`).
- Mistral: split `ministral-3` into 3B/8B/14B dated ids; track `mistral-large-2512` not `mistral-large-3`.
- DeepSeek: split `deepseek-r1-distill` into specific checkpoints or label as a family.
- Cohere: track dated ids (`command-a-03-2025`) rather than bare aliases.
- Meta: remove fabricated `llama-4-8b` and `llama-4-17b`; replace with `llama-4-scout` / `llama-4-maverick`.
- xAI: remove fabricated `grok-4-thinking`.
