#!/usr/bin/env python3
"""
LLM-Assisted Technique Extraction (Two-Pass RAG Architecture)

Uses Claude API to analyze source documents and identify safety techniques.
Implements a Retrieval-Augmented Generation (RAG) pattern in two passes:

  Pass 1 — EXTRACTION: Claude classifies the document against the technique
           taxonomy, one API call per technique category (5 calls/doc), with
           the NLU pipeline's retrieved evidence (text + retrieval/verification
           scores) injected as prior context for that category's techniques.
           The document itself is sent once per document as a separate,
           byte-identical prompt-cache-eligible content block reused across
           all category calls (docs/workplan/2026-08-execution-plan.md T3.1/T3.2).

  Pass 2 — VERIFICATION: For each candidate technique from Pass 1, the
           review index is queried for that technique's confirmed positives
           and rejected negatives from prior human reviews. These are fed
           to Claude as technique-specific context, and it confirms, rejects,
           or abstains on each candidate, keyed by an explicit index so
           duplicate techniqueIds across candidates can't collide (T3.4).

Both passes ask Claude to report structured output via forced tool use
(`record_techniques` / `record_verdicts`, T3.3) instead of regex-parsed JSON
in free text; unparseable/missing tool output falls back to the legacy
free-text JSON parser, and only then to abstention.

The review index is authoritative and cumulative — it reflects all manual
additions, confirmed automated tags, and explicit deletions across the
full review history in model_technique_map.json.

Usage:
    python scripts/llm_assisted_extraction.py                    # Process all documents
    python scripts/llm_assisted_extraction.py --id doc-id        # Process specific document
    python scripts/llm_assisted_extraction.py --model haiku      # Use Haiku (cheaper)
    python scripts/llm_assisted_extraction.py --resume           # Resume from last checkpoint
    python scripts/llm_assisted_extraction.py --single-call      # Legacy one-call-per-doc mode (A/B fallback)

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - anthropic package installed: pip install anthropic
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import argparse
import time
import threading
from datetime import datetime
from difflib import SequenceMatcher

# Local scripts dir on path (works when run directly or imported as a module).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import load_holdout_ids, is_reviewed_document  # blind-split quarantine + shared review predicate (B.1.2/B.1.4)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try API_key.env first, then fall back to .env
    env_file = Path(__file__).parent.parent / "API_key.env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()  # Default .env in current directory
except ImportError:
    pass  # dotenv not installed, rely on environment variables

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed")
    print("Install with: pip install anthropic")
    sys.exit(1)

# Configuration
EVIDENCE_PATH = Path("data/evidence.json")
TECHNIQUES_PATH = Path("data/techniques.json")
CATEGORIES_PATH = Path("data/categories.json")
FLAT_TEXT_DIR = Path("data/flat_text")
OUTPUT_PATH = Path("data/model_technique_map.json")
CHECKPOINT_PATH = Path("cache/llm_extraction_checkpoint.json")

# Model configuration
MODEL_MAP = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "sonnet-legacy": "claude-3-5-sonnet-20241022",
    "opus": "claude-opus-4-8",  # current flagship for the reasoning/extraction task (was 4-6)
    "opus-5": "claude-opus-5",
    "sonnet-5": "claude-sonnet-5",
}

# Minimum fuzzy-match score to accept an LLM quote as grounded in the source text.
# Interim conservative value (raised from 0.4); calibrate via a PR curve on labelled
# (quote, true_in_source) pairs in phase B.1.3 (REFACTOR §2.2).
FUZZY_MATCH_MIN_SCORE = 0.6


def find_exact_passage(llm_quote: str, source_text: str, context_chars: int = 200) -> Optional[str]:
    """
    Find the exact passage in source text that best matches the LLM's quote.
    Uses fuzzy matching to handle paraphrasing/truncation by the LLM.

    Returns the exact text from the source, or None if no good match found.
    """
    if not llm_quote or not source_text:
        return None

    # Normalize for matching
    llm_lower = llm_quote.lower().strip()
    source_lower = source_text.lower()

    # Try exact match first
    idx = source_lower.find(llm_lower)
    if idx >= 0:
        # Found exact match - extract with context
        start = max(0, idx)
        end = min(len(source_text), idx + len(llm_quote))
        return source_text[start:end].strip()

    # Try finding significant keywords from the quote
    # Extract words that are likely distinctive (longer words, not common)
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                   'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                   'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                   'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
                   'that', 'these', 'those', 'it', 'its', 'we', 'our', 'they', 'their'}

    words = re.findall(r'\b\w{4,}\b', llm_lower)
    keywords = [w for w in words if w not in common_words][:5]  # Top 5 distinctive words

    if not keywords:
        return None

    # Find sentences in source that contain the most keywords
    sentences = re.split(r'(?<=[.!?])\s+', source_text)

    best_match = None
    best_score = 0

    for i, sent in enumerate(sentences):
        sent_lower = sent.lower()
        keyword_count = sum(1 for kw in keywords if kw in sent_lower)

        if keyword_count >= 2:  # At least 2 keyword matches
            # Calculate similarity with the LLM quote
            ratio = SequenceMatcher(None, llm_lower, sent_lower).ratio()
            score = keyword_count * 0.3 + ratio * 0.7

            if score > best_score:
                best_score = score
                # Get this sentence plus maybe the next one for context
                if i + 1 < len(sentences) and len(sent) < 100:
                    best_match = sent + ' ' + sentences[i + 1]
                else:
                    best_match = sent

    # Only return if we have a reasonable match
    if best_score > FUZZY_MATCH_MIN_SCORE and best_match:
        return best_match.strip()

    return None


def _mark_abstained(candidate: Dict, reason: str) -> None:
    """Quarantine a candidate for human review instead of auto-confirming.

    Implements explicit abstention (REFACTOR §2.3): on a parse/API failure or an
    explicit ABSTAIN verdict, the candidate is kept but marked inactive + needs_review
    rather than silently confirmed.
    """
    candidate["active"] = False
    candidate["needs_review"] = True
    candidate["review_reason"] = reason
    for ev in candidate.get("evidence", []):
        if isinstance(ev, dict):
            ev["active"] = False


# ---------------------------------------------------------------------------
# Pure helper functions (T3.1/T3.2/T3.3/T3.4) — no `self`, no API/network,
# no heavy deps, so these are directly unit-testable without an LLMExtractor
# instance or ANTHROPIC_API_KEY. Mirrors the convention already established
# by run_extraction_pipeline.apply_corroboration_rule / apply_deletions.
# ---------------------------------------------------------------------------

def _truncate_document(text: str, max_tokens: int = 150000) -> str:
    """Truncate document if too long (rough estimate: 1 token ≈ 4 chars)."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    truncated += f"\n\n[DOCUMENT TRUNCATED - Original length: {len(text)} chars, showing first {max_chars} chars]"
    return truncated


def _format_nlu_findings(nlu_results: Optional[List[Dict]], technique_ids: Optional[Set[str]] = None) -> str:
    """Format active NLU detections as the {nlu_findings} block for T3.1.

    One line per active entry:
        - {techniqueId} (retrieval {r:.2f}, verification {v:.2f}): "{evidence text}"
    Scores and evidence text come from the entry's first evidence dict via
    `.get()` with fallbacks — older entries may lack `retrieval_score` /
    `verification_score` (pre-T2.4), in which case the parenthetical is
    omitted entirely rather than printed with placeholder values. Evidence
    text is truncated to 300 chars.

    When `technique_ids` is given, only entries whose techniqueId is a member
    are included — used to scope the NLU section to one category's techniques
    in the category-batched extraction path (T3.2).
    """
    lines = []
    for r in nlu_results or []:
        if not isinstance(r, dict) or not r.get('active', True):
            continue
        tech_id = r.get('techniqueId')
        if not tech_id:
            continue
        if technique_ids is not None and tech_id not in technique_ids:
            continue

        evidence_list = r.get('evidence') or []
        first_ev = evidence_list[0] if evidence_list else {}
        if not isinstance(first_ev, dict):
            first_ev = {"text": str(first_ev)}

        text = (first_ev.get('text') or '')[:300]
        retrieval_score = first_ev.get('retrieval_score')
        verification_score = first_ev.get('verification_score')

        score_part = ""
        if retrieval_score is not None and verification_score is not None:
            try:
                score_part = (f" (retrieval {float(retrieval_score):.2f}, "
                              f"verification {float(verification_score):.2f})")
            except (TypeError, ValueError):
                score_part = ""

        lines.append(f'- {tech_id}{score_part}: "{text}"')

    return "\n".join(lines)


def _group_techniques_by_category(techniques: List[Dict], categories: Dict[str, Dict]) -> Dict[str, List[Dict]]:
    """Group techniques by categoryId, preserving categories' declared order.

    `categories` is expected to be the id-keyed dict built from categories.json
    (dict insertion order == file order in Python 3.7+), so iterating the
    result yields categories in their canonical order. Categories with zero
    techniques are omitted — one API call per *non-empty* category (T3.2). A
    technique whose categoryId isn't a known category is grouped under that
    id anyway (appended after the known categories) so nothing silently drops.
    """
    grouped: Dict[str, List[Dict]] = {cid: [] for cid in categories}
    for tech in techniques:
        cat_id = tech.get('categoryId')
        grouped.setdefault(cat_id, []).append(tech)

    return {cid: techs for cid, techs in grouped.items() if techs}


_CONFIDENCE_RANK = {"High": 3, "Medium": 2, "Low": 1}


def _dedupe_candidates(additions: List[Dict]) -> List[Dict]:
    """Merge addition candidates across category calls, deduped by techniqueId.

    Keeps the higher-confidence candidate on a collision; ties keep the
    first-seen candidate (stable — categories are disjoint by construction,
    so a collision only happens if the model proposes the same techniqueId
    from more than one category call).
    """
    best: Dict[str, Dict] = {}
    for a in additions:
        tid = a.get('techniqueId')
        if not tid:
            continue
        existing = best.get(tid)
        if existing is None:
            best[tid] = a
            continue
        existing_rank = _CONFIDENCE_RANK.get(existing.get('confidence', 'Medium'), 2)
        new_rank = _CONFIDENCE_RANK.get(a.get('confidence', 'Medium'), 2)
        if new_rank > existing_rank:
            best[tid] = a
    return list(best.values())


def _dedupe_deletions(deletions: List[Dict]) -> List[Dict]:
    """Union deletions across category calls, deduped by techniqueId (first wins)."""
    seen: Dict[str, Dict] = {}
    for d in deletions:
        tid = d.get('techniqueId')
        if not tid:
            continue
        if tid not in seen:
            seen[tid] = d
    return list(seen.values())


_VALID_CONFIDENCE = {"High", "Medium", "Low"}
_VALID_VERDICTS = {"confirm", "reject", "abstain"}


def _validate_matches_payload(raw: Dict) -> Optional[List[Dict]]:
    """Validate/normalize a `record_techniques` tool input into a flat match list.

    Local validation (T3.3) applied regardless of whether the tool call used
    `strict: true` — a schema is a contract, not a proof, and this is the
    *only* validation when the API/SDK rejected `strict` and the non-strict
    tool was used instead. Returns None if the payload's shape is
    fundamentally unusable (caller then falls back to legacy text parsing);
    malformed individual items are dropped rather than failing the batch.
    """
    if not isinstance(raw, dict):
        return None
    matches = raw.get('matches')
    if not isinstance(matches, list):
        return None

    cleaned = []
    for m in matches:
        if not isinstance(m, dict):
            continue
        tech_id = m.get('techniqueId')
        if not isinstance(tech_id, str) or not tech_id:
            continue
        confidence = m.get('confidence')
        if confidence not in _VALID_CONFIDENCE:
            confidence = 'Medium'
        cleaned.append({
            'techniqueId': tech_id,
            'confidence': confidence,
            'evidence': m.get('evidence') if isinstance(m.get('evidence'), str) else '',
            'reasoning': m.get('reasoning') if isinstance(m.get('reasoning'), str) else '',
            'delete': bool(m.get('delete', False)),
        })
    return cleaned


def _validate_verdicts_payload(raw: Dict) -> Optional[List[Dict]]:
    """Validate/normalize a `record_verdicts` tool input into a flat verdict list.

    Mirrors `_validate_matches_payload`. Entries without a valid integer
    `index` are dropped; `_apply_verdicts` then treats the corresponding
    candidate as unmatched and abstains (T3.4's documented semantics).
    """
    if not isinstance(raw, dict):
        return None
    verdicts = raw.get('verdicts')
    if not isinstance(verdicts, list):
        return None

    cleaned = []
    for v in verdicts:
        if not isinstance(v, dict):
            continue
        idx = v.get('index')
        if not isinstance(idx, int) or isinstance(idx, bool):
            continue
        verdict = v.get('verdict')
        if isinstance(verdict, str) and verdict.lower() in _VALID_VERDICTS:
            verdict = verdict.lower()
        else:
            verdict = 'abstain'
        cleaned.append({
            'index': idx,
            'techniqueId': v.get('techniqueId') if isinstance(v.get('techniqueId'), str) else '',
            'verdict': verdict,
            'reason': v.get('reason') if isinstance(v.get('reason'), str) else '',
        })
    return cleaned


def _apply_verdicts(indexed: List[Tuple[int, Dict]], verdicts: List[Dict],
                     used_legacy: bool) -> Tuple[List[Dict], List[Tuple[str, str]], List[Dict]]:
    """Partition verified candidates into confirmed/rejected/abstained (T3.4).

    `indexed` is `[(index, candidate), ...]`, the 1-based position of each
    candidate within the batch sent for verification (built by
    `_verify_candidates` via `enumerate(to_verify, 1)`). `verdicts` is the
    validated tool payload (every entry carries an `index`) when
    `used_legacy` is False, or the legacy `_parse_json_response` list (keyed
    by `techniqueId` only — no `index`) when True.

    Rejected/abstained candidates are mutated via `_mark_abstained`, matching
    this module's existing in-place-mutation convention (`apply_deletions`,
    `apply_corroboration_rule`). A missing/unmatched index (indexed mode) or
    missing techniqueId (legacy mode) means abstain, not confirm — quarantine
    for human review rather than guess. Indexed mode is what correctly
    disambiguates duplicate techniqueIds across candidates; legacy mode keeps
    the pre-T3.4 (degraded, collision-prone) techniqueId-keyed behavior since
    it's only reached when the structured tool call itself failed.

    Returns `(confirmed, rejected, abstained)` where `rejected` is a list of
    `(techniqueId, reason)` tuples for logging (mirrors the pre-T3.4 shape).
    """
    confirmed: List[Dict] = []
    rejected: List[Tuple[str, str]] = []
    abstained: List[Dict] = []

    if used_legacy:
        verdict_map: Dict[str, str] = {}
        reason_map: Dict[str, str] = {}
        for v in verdicts:
            tid = v.get("techniqueId", "")
            verdict_map[tid] = str(v.get("verdict", "abstain")).lower()
            reason_map[tid] = v.get("reason", "")
        for _idx, c in indexed:
            tid = c.get("techniqueId", "")
            verdict = verdict_map.get(tid, "abstain")
            if verdict == "confirm":
                confirmed.append(c)
            elif verdict == "reject":
                rejected.append((tid, reason_map.get(tid, "")))
            else:
                _mark_abstained(c, reason_map.get(tid, "") or "verifier_abstained")
                abstained.append(c)
        return confirmed, rejected, abstained

    verdict_by_index = {v["index"]: v for v in verdicts if isinstance(v.get("index"), int)}
    for idx, c in indexed:
        v = verdict_by_index.get(idx)
        tid = c.get("techniqueId", "")
        if v is None:
            _mark_abstained(c, "verifier_abstained")
            abstained.append(c)
            continue
        verdict = v.get("verdict", "abstain")
        if verdict == "confirm":
            confirmed.append(c)
        elif verdict == "reject":
            rejected.append((tid, v.get("reason", "")))
        else:
            _mark_abstained(c, v.get("reason", "") or "verifier_abstained")
            abstained.append(c)
    return confirmed, rejected, abstained


def _get_tool_input(response, tool_name: str) -> Optional[Dict]:
    """Return the parsed `input` dict of the first matching tool_use block, or None."""
    for block in getattr(response, 'content', None) or []:
        if getattr(block, 'type', None) == 'tool_use' and getattr(block, 'name', None) == tool_name:
            return block.input
    return None


def _get_text(response) -> str:
    """Concatenate all text blocks in a response's content (legacy-parse fallback input)."""
    parts = []
    for block in getattr(response, 'content', None) or []:
        if getattr(block, 'type', None) == 'text':
            parts.append(getattr(block, 'text', '') or '')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Structured-output tool schemas (T3.3)
# ---------------------------------------------------------------------------

RECORD_TECHNIQUES_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["matches"],
    "properties": {
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["techniqueId", "confidence", "evidence", "reasoning"],
                "properties": {
                    "techniqueId": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["High", "Medium", "Low"]},
                    "evidence": {"type": "string"},
                    "reasoning": {"type": "string"},
                    "delete": {"type": "boolean"},
                },
            },
        },
    },
}

RECORD_VERDICTS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdicts"],
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["index", "techniqueId", "verdict", "reason"],
                "properties": {
                    "index": {"type": "integer"},
                    "techniqueId": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["confirm", "reject", "abstain"]},
                    "reason": {"type": "string"},
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

# Block 1 (T3.2) — document metadata + full document text. Built once per
# document and reused byte-for-byte across every category call so it's
# eligible for prompt-cache hits on calls 2-5 (cache_control is attached to
# this block only, by the caller).
DOCUMENT_CONTEXT_TEMPLATE = """## Document Context

**Document ID**: {doc_id}
**Document Purpose**: {doc_purpose}
**Signal Strength**: {signal_strength}
**Temporal Focus**: {temporal_focus}
**Primary Topics**: {primary_topics}
**Excluded Topics**: {excluded_topics}

## Document Content

{document_text}
"""

# Shared few-shot examples, reused verbatim by both the single-call prompt
# and every category-batched call (it isn't category-specific).
FEW_SHOT_EXAMPLES_BLOCK = """Below are examples of CORRECT matches and CORRECT rejections from manually reviewed documents.

### TRUE POSITIVES (should be matched):

```json
[
  {
    "techniqueId": "tech-rlhf",
    "confidence": "High",
    "evidence": "The model underwent reinforcement learning from human feedback, with human raters scoring outputs for helpfulness and harmlessness.",
    "reasoning": "Explicit description of RLHF implementation with human raters and dual objectives."
  },
  {
    "techniqueId": "tech-red-teaming",
    "confidence": "High",
    "evidence": "We conducted extensive red teaming with over 100 external experts across domains including cybersecurity, biosecurity, and persuasion.",
    "reasoning": "Direct description of red teaming activity with specific details about team size and domains."
  },
  {
    "techniqueId": "tech-output-filtering-systems",
    "confidence": "Medium",
    "evidence": "A separate classifier is applied to model outputs to detect and filter harmful content before it reaches the user.",
    "reasoning": "Describes a post-generation output filtering system with a classifier."
  },
  {
    "techniqueId": "tech-safety-benchmarks",
    "confidence": "High",
    "evidence": "We evaluate on ToxiGen, BBQ, and BOLD benchmarks to measure the model's propensity for generating biased or toxic content.",
    "reasoning": "Specific named safety benchmarks used for evaluation."
  }
]
```

### FALSE POSITIVES (should NOT be matched):

These are examples of text that looks safety-related but should be REJECTED:

1. **Citation/related work (not their implementation)**:
   "Constitutional AI (Bai et al., 2022) has shown promise in aligning language models."
   → REJECT tech-constitutional-ai: Only citing another paper, not describing own implementation.

2. **Future work / aspirational**:
   "We plan to incorporate adversarial training in future model iterations."
   → REJECT tech-adversarial-training: Described as planned, not implemented.

3. **Glossary / definition**:
   "Red teaming: A practice where testers attempt to find vulnerabilities in AI systems."
   → REJECT tech-red-teaming: Just a definition, no evidence of actually performing it.

4. **Keyword match without implementation**:
   "Unlike real-time fact checking systems, our model relies on parametric knowledge."
   → REJECT tech-realtime-fact-checking: Explicitly states they do NOT use this technique.

5. **Attack description (not defense)**:
   "Adversarial prompts such as jailbreaks can bypass safety measures."
   → REJECT tech-adversarial-training: Discussing the threat, not implementing the defense.

6. **General mention without substance**:
   "Safety is a priority and we comply with applicable regulations."
   → REJECT tech-regulatory-compliance: Vague statement with no specific compliance details."""

# Single-call (legacy, --single-call) extraction prompt — one call for the
# whole taxonomy against the whole document. Kept for A/B fallback (T3.2).
EXTRACTION_PROMPT = """You are an expert at analyzing AI safety documentation. Your task is to identify which safety techniques are actually implemented or described in this document.

## Document Context

**Document ID**: {doc_id}
**Document Purpose**: {doc_purpose}
**Signal Strength**: {signal_strength}
**Temporal Focus**: {temporal_focus}
**Primary Topics**: {primary_topics}
**Excluded Topics**: {excluded_topics}

## Available Safety Techniques

{techniques_list}

## Document Content

{document_text}

## Your Task

Analyze the document and identify which techniques are:
1. **Actually implemented** in the system being described
2. **Explicitly discussed** as safety measures (not just mentioned in passing)
3. **Substantively described** with implementation details or evidence

**DO NOT match** techniques that are:
- Only mentioned in related work or citations
- Described as future work or aspirational
- Used as examples in a different context (e.g., "attacks we defend against")
- Part of glossaries or definitions without implementation evidence
- Tangentially related keyword matches without actual implementation

For each technique you identify, record via the `record_techniques` tool:
- `techniqueId`: The technique ID
- `confidence`: High/Medium/Low based on evidence strength
- `evidence`: A VERBATIM quote (1-2 sentences) copied EXACTLY from the document - do not paraphrase or summarize
- `reasoning`: Why you believe this is a true match (1 sentence)

{nlu_context}

## Few-Shot Examples

{few_shot_examples}

Call `record_techniques` exactly once with your complete findings (an empty `matches` array if none apply).
Be conservative: it's better to miss a technique than to include a false positive.
"""

# Category-batched (default, T3.2) task block — block 2 of the two-block
# message. The document itself (block 1, DOCUMENT_CONTEXT_TEMPLATE) precedes
# this in the same user turn.
CATEGORY_TASK_TEMPLATE = """You are an expert at analyzing AI safety documentation. The full document appears above as prior context in this message. Your task is to identify which safety techniques from the category below are actually implemented or described in that document.

## Safety Techniques — Category: {category_name}

{techniques_list}

## Your Task

Analyze the document (above) and identify which of the techniques in THIS category are:
1. **Actually implemented** in the system being described
2. **Explicitly discussed** as safety measures (not just mentioned in passing)
3. **Substantively described** with implementation details or evidence

**DO NOT match** techniques that are:
- Only mentioned in related work or citations
- Described as future work or aspirational
- Used as examples in a different context (e.g., "attacks we defend against")
- Part of glossaries or definitions without implementation evidence
- Tangentially related keyword matches without actual implementation

For each technique you identify, record via the `record_techniques` tool:
- `techniqueId`: The technique ID
- `confidence`: High/Medium/Low based on evidence strength
- `evidence`: A VERBATIM quote (1-2 sentences) copied EXACTLY from the document - do not paraphrase or summarize
- `reasoning`: Why you believe this is a true match (1 sentence)

{nlu_context}

## Few-Shot Examples

{few_shot_examples}

Only consider techniques from the "{category_name}" category listed above — techniques from other categories are handled in separate calls, so do not report on them here. Be conservative: it's better to miss a technique than to include a false positive. Call `record_techniques` exactly once with your complete findings for this category (an empty `matches` array if none apply).
"""

# Context injected when NLU results are available (T3.1). Rendered via
# str.replace() on the single `{nlu_findings}` placeholder — never passed
# through .format() itself — so the literal JSON example in point 2 below
# survives verbatim into the prompt.
NLU_CONTEXT_TEMPLATE = """
## Prior Analysis (NLU Pipeline)

A semantic retrieval pipeline scanned this document and proposes the techniques below. For each, it shows the strongest matching passage it found and two scores (retrieval = semantic similarity, verification = entailment; both 0-1). The pipeline's precision is limited (~50-60%): treat each proposal as a lead to check against the document, not a fact.

{nlu_findings}

Your task with these proposals:
1. CONFIRM a proposal only if the document genuinely describes an implemented technique — the quoted passage may itself be a false lead even when scores are high; find better evidence in the document if the quoted passage is weak.
2. REJECT proposals whose evidence is citation-only, future work, glossary text, negation, or an artifact of tables/formatting — add {"techniqueId": "...", "delete": true, "reasoning": "..."}.
3. ADD any techniques the NLU missed — its recall is also imperfect.
"""

_NO_NLU_FINDINGS_NOTE = ("(No NLU proposals for techniques in this category — "
                          "rely on your own reading of the document.)")


# RAG verification prompt (T3.4) — fed technique-specific review history
# after initial extraction, plus an explicit per-candidate index so
# duplicate techniqueIds among candidates can't collide in the verdict map.
VERIFICATION_PROMPT = """You are verifying technique classifications against prior human review decisions.

For each candidate below, I show:
- An explicit index (use this exact index in your verdict — techniqueIds may repeat across candidates)
- The proposed technique match and evidence quote
- Previously CONFIRMED matches for this technique (true positives from human review)
- Previously REJECTED matches for this technique (false positives caught by human review)

Use the confirmed/rejected patterns to judge whether each candidate is a genuine implementation match.

## Candidates to Verify

{candidates_section}

## Instructions

For each candidate, record a verdict via the `record_verdicts` tool: CONFIRM, REJECT, or ABSTAIN:
- CONFIRM: Evidence clearly describes implementation of the technique, consistent with confirmed examples
- REJECT: Evidence matches a false-positive pattern seen in rejected examples (citation-only, future work, glossary, negation, vague mention)
- ABSTAIN: Genuinely uncertain — a human reviewer should decide. The candidate is quarantined for review, not dropped, so abstain instead of guessing.

Call `record_verdicts` exactly once, with one entry per candidate index above — include both the `index` and `techniqueId` on every entry.
"""


class LLMExtractor:
    def __init__(self, model_name: str = "sonnet", resume: bool = False, single_call: bool = False):
        """Initialize the LLM-based extractor."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        # Higher max_retries (default 2) gives the SDK more exponential-backoff
        # attempts on 429/overloaded before the rate-limit path drops a doc —
        # important under the parallel LLM pass.
        self.client = anthropic.Anthropic(api_key=api_key, max_retries=5)
        self.model = MODEL_MAP.get(model_name, MODEL_MAP["sonnet"])
        self.resume = resume
        # T3.2: default is per-category batched extraction (5 calls/doc);
        # --single-call restores the legacy one-monolithic-call-per-doc path
        # for A/B comparison.
        self.single_call = single_call
        # Guards self.results + checkpoint file when documents are processed
        # concurrently (the Anthropic client itself is thread-safe).
        self._results_lock = threading.Lock()

        # Load data
        print("Loading taxonomy and metadata...")
        self.techniques = self._load_techniques()
        self.categories = self._load_categories()
        self.evidence_metadata = self._load_evidence_metadata()
        self.review_index = self._build_review_index()
        self.tech_names = {t['id']: t['name'] for t in self.techniques}

        # Load or initialize results
        self.results = self._load_checkpoint() if resume else {}

        # Review index stats
        techs_with_data = sum(1 for v in self.review_index.values()
                              if v["positives"] or v["negatives"])
        total_pos = sum(len(v["positives"]) for v in self.review_index.values())
        total_neg = sum(len(v["negatives"]) for v in self.review_index.values())

        print(f"✓ Loaded {len(self.techniques)} techniques")
        print(f"✓ Loaded {len(self.categories)} categories")
        print(f"✓ Loaded metadata for {len(self.evidence_metadata)} documents")
        print(f"✓ Review index: {techs_with_data} techniques with review data "
              f"({total_pos} positives, {total_neg} negatives)")
        if getattr(self, "_review_quarantined", 0):
            print(f"✓ Quarantined {self._review_quarantined} blind-test document(s) "
                  f"from the review index (WORKPLAN B.1.2)")
        print(f"✓ Using model: {self.model}")
        print(f"✓ Extraction mode: {'single-call (legacy A/B)' if single_call else 'category-batched'}")

        if resume and self.results:
            print(f"✓ Resuming from checkpoint with {len(self.results)} processed documents")

    def _load_techniques(self) -> List[Dict]:
        """Load techniques with category context."""
        with open(TECHNIQUES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_categories(self) -> Dict[str, Dict]:
        """Load categories."""
        with open(CATEGORIES_PATH, 'r', encoding='utf-8') as f:
            cats = json.load(f)
        return {cat['id']: cat for cat in cats}

    def _load_evidence_metadata(self) -> Dict[str, Dict]:
        """Load document metadata from evidence.json."""
        if not EVIDENCE_PATH.exists():
            return {}

        with open(EVIDENCE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        metadata_map = {}
        for source in data.get('sources', []):
            doc_id = source.get('id')
            if doc_id and 'content_metadata' in source:
                metadata_map[doc_id] = source['content_metadata']

        return metadata_map

    def _build_review_index(self) -> Dict[str, Dict[str, List]]:
        """Build per-technique index of confirmed and rejected matches from reviewed documents.

        This is the authoritative review history used in the RAG verification pass.
        Instead of injecting a static sample into every prompt, this index is queried
        per-technique AFTER the LLM makes its initial classification, providing
        targeted positive/negative examples only for techniques the LLM proposed.

        Returns:
            Dict mapping technique_id -> {
                "positives": [{"doc_id", "text", "created_by"}, ...],
                "negatives": [{"doc_id", "text", "deleted_by", "reason"}, ...]
            }
        """
        map_path = Path("data/model_technique_map.json")
        if not map_path.exists():
            return {}

        with open(map_path, 'r', encoding='utf-8') as f:
            technique_map = json.load(f)

        # Quarantine blind-test documents (WORKPLAN B.1.2): a test doc must never
        # seed a few-shot positive/negative, or the LLM verification pass would be
        # tuned on the very set it is later graded against. Empty until the split
        # is frozen (make_eval_split.py), so this is a safe no-op by default.
        holdout_ids = load_holdout_ids()
        quarantined = 0

        index = {}

        for doc_id, entries in technique_map.items():
            if doc_id in holdout_ids:
                quarantined += 1
                continue

            # Only include documents that have been manually reviewed — shared
            # definition (WORKPLAN B.1.4) so this index and the evaluators agree.
            if not is_reviewed_document(entries):
                continue

            for e in entries:
                tech_id = e.get("techniqueId", "")
                if not tech_id:
                    continue

                if tech_id not in index:
                    index[tech_id] = {"positives": [], "negatives": []}

                if e.get("active", True):
                    # Active in reviewed doc = confirmed positive
                    for ev in e.get("evidence", []):
                        if isinstance(ev, dict) and ev.get("text"):
                            # T3.4: 300 -> 500 char snippet budget (more context for the verifier).
                            text = ev["text"][:500].strip()
                            if len(text) > 30:
                                index[tech_id]["positives"].append({
                                    "doc_id": doc_id,
                                    "text": text,
                                    "created_by": ev.get("created_by", "unknown"),
                                })
                            break  # One snippet per entry
                else:
                    # Deleted in reviewed doc = confirmed false positive
                    evidence_text = ""
                    for ev in e.get("evidence", []):
                        if isinstance(ev, dict) and ev.get("text"):
                            evidence_text = ev["text"][:500].strip()
                            break

                    index[tech_id]["negatives"].append({
                        "doc_id": doc_id,
                        "text": evidence_text,
                        "deleted_by": e.get("deleted_by", "unknown"),
                        "reason": e.get("deletion_reason", ""),
                    })

        self._review_quarantined = quarantined
        return index

    def _load_checkpoint(self) -> Dict:
        """Load checkpoint if it exists."""
        if CHECKPOINT_PATH.exists():
            with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_checkpoint(self):
        """Save current progress to checkpoint."""
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)

    def _format_techniques_list(self, techs: Optional[List[Dict]] = None) -> str:
        """Format techniques for the prompt. Defaults to the full taxonomy;
        pass a subset (e.g. one category's techniques) for the category-batched path."""
        techs = self.techniques if techs is None else techs
        lines = []
        for tech in techs:
            cat = self.categories.get(tech.get('categoryId'), {})
            cat_name = cat.get('name', 'Unknown')

            lines.append(f"### {tech['id']}")
            lines.append(f"**Name**: {tech['name']}")
            lines.append(f"**Category**: {cat_name}")
            lines.append(f"**Description**: {tech['description']}")

            # Add NLU profile hints if available
            nlu = tech.get('nlu_profile', {})
            if nlu.get('primary_concept'):
                lines.append(f"**Key Concept**: {nlu['primary_concept']}")

            lines.append("")

        return "\n".join(lines)

    def _truncate_document(self, text: str, max_tokens: int = 150000) -> str:
        """Truncate document if too long (rough estimate: 1 token ≈ 4 chars)."""
        return _truncate_document(text, max_tokens)

    def _parse_json_response(self, content: str) -> Optional[list]:
        """Extract and parse a JSON array from an LLM response.

        Legacy free-text fallback (T3.3): used only when a forced tool call
        comes back without a usable tool_use block. Handles markdown code
        blocks, bare JSON, and embedded arrays. Returns parsed list or None
        on failure.
        """
        json_str = None

        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            if json_end > json_start:
                json_str = content[json_start:json_end].strip()

        if not json_str and "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            if json_end > json_start:
                json_str = content[json_start:json_end].strip()

        if not json_str:
            if content.strip().startswith('['):
                json_str = content.strip()
            else:
                match = re.search(r'\[[\s\S]*\]', content)
                if match:
                    json_str = match.group(0)

        if not json_str:
            return None

        try:
            result = json.loads(json_str)
            if not isinstance(result, list):
                result = [result] if result else []
            return result
        except json.JSONDecodeError:
            return None

    def _call_structured(self, *, content_blocks: List[Dict], tool_name: str,
                          tool_schema: Dict, tool_description: str, max_tokens: int,
                          validator) -> Tuple[Optional[List[Dict]], bool, object]:
        """Call Claude with a forced tool_choice (T3.3); return a validated payload.

        Tries `strict: true` on the tool definition first. If the pinned
        SDK/API rejects `strict` (anthropic.BadRequestError), retries the
        same tool call without it. Regardless of which attempt succeeds, the
        parsed `tool_use.input` is locally validated via `validator` — strict
        mode is trusted but verified, and it's the *only* validation on the
        non-strict retry path.

        If no usable tool_use block comes back (missing, or fails local
        validation), falls back to legacy free-text JSON parsing on the
        response's text content. Only if that also fails does this return
        None for the payload — the caller then abstains, as before T3.3.

        Returns `(payload, used_legacy_fallback, response)`. `response` is
        always returned (even when `payload` is None) so callers can log/
        debug-dump raw response text on total failure.
        """
        tool_def = {
            "name": tool_name,
            "description": tool_description,
            "input_schema": tool_schema,
            "strict": True,
        }
        messages = [{"role": "user", "content": content_blocks}]

        def _create(tool: Dict):
            return self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
                messages=messages,
            )

        try:
            response = _create(tool_def)
        except anthropic.BadRequestError:
            # The pinned SDK/API may reject `strict` — retry the same tool without it.
            tool_def_nostrict = {k: v for k, v in tool_def.items() if k != "strict"}
            response = _create(tool_def_nostrict)

        raw = _get_tool_input(response, tool_name)
        if raw is not None:
            validated = validator(raw)
            if validated is not None:
                return validated, False, response

        # Missing/unparseable tool_use -> legacy free-text JSON parsing.
        text = _get_text(response)
        legacy = self._parse_json_response(text) if text else None
        return legacy, True, response

    def _build_document_block(self, doc_id: str, text: str) -> str:
        """Build block 1 of the category-batched message (T3.2): document
        metadata + full document text. Deterministic given (doc_id, text) and
        the loaded evidence metadata, so calling this once per document and
        reusing the returned string across every category call keeps that
        block byte-identical — required for the calls to share a prompt cache."""
        metadata = self.evidence_metadata.get(doc_id, {})
        document_text = self._truncate_document(text)
        return DOCUMENT_CONTEXT_TEMPLATE.format(
            doc_id=doc_id,
            doc_purpose=metadata.get('document_purpose', 'unknown'),
            signal_strength=metadata.get('signal_strength', 'medium'),
            temporal_focus=metadata.get('temporal_focus', 'unknown'),
            primary_topics=', '.join(metadata.get('primary_topics', [])) or 'none specified',
            excluded_topics=', '.join(metadata.get('excluded_topics', [])) or 'none specified',
            document_text=document_text,
        )

    def _build_category_block(self, category_id: str, techs: List[Dict],
                               nlu_results: List[Dict], tech_ids_in_cat: Set[str]) -> str:
        """Build block 2 of the category-batched message: this category's
        techniques, task instructions, few-shot examples, and NLU findings
        filtered to this category's techniqueIds (T3.1 x T3.2)."""
        cat = self.categories.get(category_id, {})
        category_name = cat.get('name', category_id)
        techniques_list = self._format_techniques_list(techs)

        nlu_findings = _format_nlu_findings(nlu_results, technique_ids=tech_ids_in_cat)
        nlu_context = NLU_CONTEXT_TEMPLATE.replace(
            "{nlu_findings}", nlu_findings or _NO_NLU_FINDINGS_NOTE
        )

        return CATEGORY_TASK_TEMPLATE.format(
            category_name=category_name,
            techniques_list=techniques_list,
            nlu_context=nlu_context,
            few_shot_examples=FEW_SHOT_EXAMPLES_BLOCK,
        )

    def _build_verification_sections(self, indexed: List[Tuple[int, Dict]],
                                      exclude_doc_id: str = "") -> str:
        """Build the candidates section for the verification prompt (T3.4).

        `indexed` is `[(index, candidate), ...]`. Each candidate section's
        header carries its explicit index (so the model's verdict can key
        off it instead of techniqueId, which may repeat). For each candidate,
        confirmed/rejected examples are retrieved from the review index
        (excluding the current document to avoid circular reference).
        """
        sections = []

        for idx, c in indexed:
            tech_id = c.get("techniqueId", "")
            tech_name = self.tech_names.get(tech_id, tech_id)

            # Extract evidence text from the candidate
            evidence_text = ""
            if isinstance(c.get("evidence"), list) and c["evidence"]:
                ev = c["evidence"][0]
                evidence_text = ev.get("text", "") if isinstance(ev, dict) else str(ev)
            evidence_text = evidence_text[:500]  # T3.4: 300 -> 500

            reasoning = c.get("reasoning", "")

            section = f"### Candidate index={idx}: {tech_id} ({tech_name})\n"
            section += f'Evidence: "{evidence_text}"\n'
            if reasoning:
                section += f"Reasoning: {reasoning}\n"

            # Retrieve technique-specific review data (excluding current document)
            review = self.review_index.get(tech_id, {})
            positives = [p for p in review.get("positives", [])
                         if p["doc_id"] != exclude_doc_id][:3]
            negatives = [n for n in review.get("negatives", [])
                         if n["doc_id"] != exclude_doc_id][:3]

            if positives:
                section += "\nConfirmed matches from other documents:\n"
                for p in positives:
                    section += f'- {p["doc_id"]}: "{p["text"][:500]}"\n'  # T3.4: 200 -> 500

            if negatives:
                section += "\nRejected matches from other documents:\n"
                for n in negatives:
                    text_part = f': "{n["text"][:500]}"' if n.get("text") else ""  # T3.4: 200 -> 500
                    reason_part = f' ({n["reason"]})' if n.get("reason") else ""
                    section += f"- {n['doc_id']}{text_part}{reason_part}\n"

            if not positives and not negatives:
                section += "\n(No prior review data for this technique)\n"

            sections.append(section)

        return "\n".join(sections)

    def _verify_candidates(self, candidates: List[Dict], doc_id: str) -> List[Dict]:
        """RAG verification pass: verify extraction candidates against review history.

        For techniques that have prior review data (confirmed positives or rejected
        negatives), asks Claude to verify each candidate against technique-specific
        examples, keyed by an explicit index (T3.4) so duplicate techniqueIds can't
        collide. Techniques without review data pass through unmodified.

        This implements the "augmented generation" step of the RAG pattern:
        the review index is the retrieval source, technique-specific examples are
        the augmentation, and Claude's verdict is the generation.
        """
        to_verify: List[Dict] = []
        pass_through: List[Dict] = []

        for c in candidates:
            tech_id = c.get("techniqueId", "")
            review = self.review_index.get(tech_id, {})
            # Only verify if there are examples from OTHER documents
            has_external = any(p["doc_id"] != doc_id for p in review.get("positives", []))
            has_external = has_external or any(
                n["doc_id"] != doc_id for n in review.get("negatives", []))
            (to_verify if has_external else pass_through).append(c)

        if not to_verify:
            return candidates  # Nothing to verify

        indexed = list(enumerate(to_verify, 1))

        print(f"  Verifying {len(to_verify)} candidates against review index "
              f"({len(pass_through)} pass-through)...")

        candidates_section = self._build_verification_sections(indexed, exclude_doc_id=doc_id)
        prompt_text = VERIFICATION_PROMPT.format(candidates_section=candidates_section)

        try:
            verdicts, used_legacy, _response = self._call_structured(
                content_blocks=[{"type": "text", "text": prompt_text}],
                tool_name="record_verdicts",
                tool_schema=RECORD_VERDICTS_SCHEMA,
                tool_description="Record a confirm/reject/abstain verdict for each candidate technique match, by index.",
                max_tokens=2048,
                validator=_validate_verdicts_payload,
            )
        except anthropic.APIError as e:
            print(f"  ⚠️ Verification API error: {e}; abstaining on {len(to_verify)} candidate(s)")
            for c in to_verify:
                _mark_abstained(c, "verification_api_error")
            return to_verify + pass_through
        except Exception as e:
            print(f"  ⚠️ Verification failed: {e}; abstaining on {len(to_verify)} candidate(s)")
            for c in to_verify:
                _mark_abstained(c, "verification_error")
            return to_verify + pass_through

        if verdicts is None:
            # Abstain rather than confirm-on-failure (REFACTOR §2.3)
            print(f"  ⚠️ Could not parse verification response; abstaining on {len(to_verify)} candidate(s)")
            for c in to_verify:
                _mark_abstained(c, "verification_unparseable")
            return to_verify + pass_through

        confirmed, rejected, abstained = _apply_verdicts(indexed, verdicts, used_legacy)

        if rejected:
            print(f"  Verification rejected {len(rejected)} candidate(s):")
            for tid, reason in rejected:
                print(f"    [-] {tid}: {reason[:80]}")
        if abstained:
            print(f"  Verification abstained on {len(abstained)} candidate(s) (quarantined for review)")
        if confirmed:
            print(f"  Verification confirmed {len(confirmed)} candidate(s)")

        # Abstained candidates are returned but inactive, so a human can review them.
        return confirmed + abstained + pass_through

    def _matches_to_additions_deletions(self, matches: List[Dict], doc_id: str,
                                         text: str) -> Tuple[List[Dict], List[Dict]]:
        """Turn a validated `matches` list (from either extraction path) into
        (additions, deletions), applying taxonomy validation and fuzzy-quote
        grounding. Shared by the single-call and category-batched paths."""
        additions = []
        deletions = []

        for match in matches:
            tech_id = match.get('techniqueId')
            if not tech_id:
                continue

            # Validate against the loaded taxonomy; quarantine hallucinated ids
            # rather than recording them as real links (REFACTOR §2.3).
            if tech_id not in self.tech_names:
                print(f"    ⚠️ Skipping out-of-taxonomy techniqueId: {tech_id}")
                continue

            if match.get('delete'):
                deletions.append({
                    "techniqueId": tech_id,
                    "deleted_by": "llm",
                    "reasoning": match.get('reasoning', '')
                })
            else:
                # This is an addition - apply fuzzy matching to ground the quote
                llm_evidence = match.get('evidence', '')
                exact_quote = find_exact_passage(llm_evidence, text) if llm_evidence else None

                # Hard grounding gate (REFACTOR §2.2): if the quote can't be grounded
                # in the source, keep the candidate but quarantine it (active=False,
                # needs_review) instead of publishing an unverified quote.
                grounded = exact_quote is not None
                final_evidence = exact_quote if grounded else llm_evidence

                if final_evidence:
                    addition = {
                        "techniqueId": tech_id,
                        "confidence": match.get('confidence', 'Medium'),
                        "active": grounded,
                        "deleted_by": None,
                        "evidence": [{
                            "text": final_evidence,
                            "created_by": "llm",
                            "active": grounded,
                            "deleted_by": None,
                            "llm_original": llm_evidence if grounded else None,
                        }],
                        "reasoning": match.get('reasoning', '')
                    }
                    if not grounded:
                        addition["needs_review"] = True
                        addition["review_reason"] = "grounding_failed"
                        addition["evidence"][0]["grounding_failed"] = True
                        print(f"    ⚠️ Grounding failed for {tech_id} — quarantined for review")
                    elif exact_quote != llm_evidence:
                        print(f"    ↳ Fuzzy matched quote for {tech_id}")
                    additions.append(addition)

        return additions, deletions

    def extract_techniques(self, doc_id: str, text: str,
                            nlu_results: Optional[List[Dict]] = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract techniques from a document using Claude API.

        Dispatches to the category-batched path (default, T3.2) or the
        legacy single-call path (`--single-call` / `single_call=True`).

        Args:
            doc_id: Document identifier
            text: Full document text
            nlu_results: Optional list of NLU-detected techniques to review

        Returns:
            Tuple of (additions, deletions) where each is a list of technique dicts
        """
        if self.single_call:
            return self._extract_techniques_single_call(doc_id, text, nlu_results)
        return self._extract_techniques_by_category(doc_id, text, nlu_results)

    def _extract_techniques_single_call(self, doc_id: str, text: str,
                                         nlu_results: Optional[List[Dict]] = None
                                         ) -> Tuple[List[Dict], List[Dict]]:
        """Legacy one-monolithic-call-per-document extraction (A/B fallback, T3.2)."""
        metadata = self.evidence_metadata.get(doc_id, {})
        doc_purpose = metadata.get('document_purpose', 'unknown')
        signal_strength = metadata.get('signal_strength', 'medium')
        temporal_focus = metadata.get('temporal_focus', 'unknown')
        primary_topics = ', '.join(metadata.get('primary_topics', [])) or 'none specified'
        excluded_topics = ', '.join(metadata.get('excluded_topics', [])) or 'none specified'

        techniques_list = self._format_techniques_list()
        document_text = self._truncate_document(text)

        nlu_findings = _format_nlu_findings(nlu_results)
        nlu_context = NLU_CONTEXT_TEMPLATE.replace("{nlu_findings}", nlu_findings) if nlu_findings else ""

        prompt = EXTRACTION_PROMPT.format(
            doc_id=doc_id,
            doc_purpose=doc_purpose,
            signal_strength=signal_strength,
            temporal_focus=temporal_focus,
            primary_topics=primary_topics,
            excluded_topics=excluded_topics,
            techniques_list=techniques_list,
            document_text=document_text,
            nlu_context=nlu_context,
            few_shot_examples=FEW_SHOT_EXAMPLES_BLOCK,
        )

        response = None
        try:
            print(f"  Calling Claude API ({self.model})...")
            matches, _used_legacy, response = self._call_structured(
                content_blocks=[{"type": "text", "text": prompt}],
                tool_name="record_techniques",
                tool_schema=RECORD_TECHNIQUES_SCHEMA,
                tool_description="Record the safety techniques identified in the document.",
                max_tokens=4096,
                validator=_validate_matches_payload,
            )

            if matches is None:
                preview = _get_text(response)
                print("  ⚠️ Could not parse structured or free-text response")
                print(f"  Response preview: {preview[:500]}")
                return [], []

            return self._matches_to_additions_deletions(matches, doc_id, text)

        except anthropic.APIError as e:
            print(f"  ⚠️ API Error: {e}")
            if "rate_limit" in str(e).lower():
                print("  Sleeping 60s due to rate limit...")
                time.sleep(60)
            return [], []

        except Exception as e:
            print(f"  ⚠️ Unexpected error: {e}")
            print(f"  Error type: {type(e).__name__}")

            # Save raw response for debugging if available
            debug_text = _get_text(response) if response is not None else ""
            if debug_text:
                debug_file = Path(f"cache/debug_response_{doc_id}.txt")
                debug_file.parent.mkdir(parents=True, exist_ok=True)
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"Error: {e}\n")
                    f.write(f"Error type: {type(e).__name__}\n")
                    f.write("="*80 + "\n")
                    f.write("Raw Response:\n")
                    f.write("="*80 + "\n")
                    f.write(debug_text)
                print(f"  Debug info saved to: {debug_file}")

            import traceback
            print(f"  Traceback:\n{traceback.format_exc()}")
            return [], []

    def _extract_techniques_by_category(self, doc_id: str, text: str,
                                         nlu_results: Optional[List[Dict]] = None
                                         ) -> Tuple[List[Dict], List[Dict]]:
        """Default extraction path (T3.2): one API call per non-empty technique
        category, sharing a byte-identical, prompt-cache-eligible document block
        across all calls for this document."""
        nlu_results = nlu_results or []
        doc_block_text = self._build_document_block(doc_id, text)  # built ONCE, reused below
        grouped = _group_techniques_by_category(self.techniques, self.categories)

        all_additions: List[Dict] = []
        all_deletions: List[Dict] = []

        for category_id, techs in grouped.items():
            cat_name = self.categories.get(category_id, {}).get('name', category_id)
            tech_ids_in_cat = {t['id'] for t in techs}
            category_block_text = self._build_category_block(category_id, techs, nlu_results, tech_ids_in_cat)

            # Block 1 (doc context) is the SAME string object on every iteration —
            # required for the 4 later calls to hit the prompt cache written by the first.
            content_blocks = [
                {"type": "text", "text": doc_block_text, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": category_block_text},
            ]

            print(f"  Calling Claude API for category '{cat_name}' ({self.model})...")
            try:
                matches, _used_legacy, response = self._call_structured(
                    content_blocks=content_blocks,
                    tool_name="record_techniques",
                    tool_schema=RECORD_TECHNIQUES_SCHEMA,
                    tool_description="Record the safety techniques from this category identified in the document.",
                    max_tokens=8192,
                    validator=_validate_matches_payload,
                )
            except anthropic.APIError as e:
                print(f"  ⚠️ API Error in category '{cat_name}': {e}")
                if "rate_limit" in str(e).lower():
                    print("  Sleeping 60s due to rate limit...")
                    time.sleep(60)
                continue
            except Exception as e:
                print(f"  ⚠️ Unexpected error in category '{cat_name}': {e}")
                continue

            if matches is None:
                print(f"  ⚠️ Could not parse response for category '{cat_name}'")
                continue

            additions, deletions = self._matches_to_additions_deletions(matches, doc_id, text)
            all_additions.extend(additions)
            all_deletions.extend(deletions)

        return _dedupe_candidates(all_additions), _dedupe_deletions(all_deletions)

    def process_document(self, doc_id: str, file_path: Path, nlu_results: Optional[List[Dict]] = None) -> bool:
        """Process a single document."""
        print(f"\n{'='*80}")
        print(f"Processing: {doc_id}")
        print(f"{'='*80}")

        # Skip if already processed (when resuming)
        if self.resume and doc_id in self.results:
            print(f"  ✓ Already processed (resuming), skipping...")
            return True

        # Read document
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            print(f"  Document length: {len(text)} chars")

            if nlu_results:
                print(f"  NLU input: {len(nlu_results)} techniques to review")

            # Pass 1: Extract technique candidates (clean prompt, no review data injected)
            additions, deletions = self.extract_techniques(doc_id, text, nlu_results)

            print(f"  Pass 1: {len(additions)} candidates extracted")
            if deletions:
                print(f"  ✗ Suggested {len(deletions)} deletions")

            # Pass 2: RAG verification — retrieve technique-specific review history
            # and verify each candidate against confirmed/rejected examples
            if additions:
                additions = self._verify_candidates(additions, doc_id)
                print(f"  ✓ Final: {len(additions)} techniques after verification")

            # Display results
            if additions:
                for match in additions:
                    conf = match.get('confidence', 'Unknown')
                    tech_id = match.get('techniqueId', 'unknown')
                    print(f"    [+{conf}] {tech_id}")

            if deletions:
                for d in deletions:
                    tech_id = d.get('techniqueId', 'unknown')
                    print(f"    [-DEL] {tech_id}: {d.get('reasoning', '')[:50]}")

            # Store results + checkpoint under a lock so concurrent workers don't
            # corrupt self.results mid-serialization (parallel LLM pass).
            with self._results_lock:
                self.results[doc_id] = {
                    "additions": additions,
                    "deletions": deletions
                }
                self._save_checkpoint()

            return True

        except Exception as e:
            print(f"  ✗ Error processing document: {e}")
            print(f"  Error type: {type(e).__name__}")

            import traceback
            print(f"\n  Full traceback:")
            traceback.print_exc()

            return False

    def process_all_documents(self, specific_doc_id: Optional[str] = None):
        """Process all documents or a specific one."""

        # Get list of documents
        if specific_doc_id:
            # Find the file for this doc_id
            files = list(FLAT_TEXT_DIR.glob("*.txt"))
            target_file = None
            for f in files:
                if f.stem == specific_doc_id or specific_doc_id in str(f):
                    target_file = f
                    break

            if not target_file:
                print(f"Error: Could not find file for doc_id: {specific_doc_id}")
                return

            files_to_process = [(specific_doc_id, target_file)]
        else:
            # Process all flat text files
            files = sorted(FLAT_TEXT_DIR.glob("*.txt"))
            files_to_process = [(f.stem, f) for f in files]

        print(f"\n{'='*80}")
        print(f"LLM-Assisted Technique Extraction")
        print(f"{'='*80}")
        print(f"Documents to process: {len(files_to_process)}")
        print(f"Model: {self.model}")
        print(f"Resume mode: {self.resume}")
        print(f"Output: {OUTPUT_PATH}")
        print(f"{'='*80}\n")

        # Process each document
        successful = 0
        failed = 0
        skipped = 0

        for i, (doc_id, file_path) in enumerate(files_to_process, 1):
            print(f"\n[{i}/{len(files_to_process)}] ", end="")

            if self.resume and doc_id in self.results:
                print(f"{doc_id} - SKIPPED (already processed)")
                skipped += 1
                continue

            success = self.process_document(doc_id, file_path)

            if success:
                successful += 1
            else:
                failed += 1

        # Save final results
        print(f"\n{'='*80}")
        print("Saving final results...")
        print(f"{'='*80}")

        self._save_results()

        # Summary
        print(f"\n{'='*80}")
        print("EXTRACTION COMPLETE")
        print(f"{'='*80}")
        print(f"Total documents: {len(files_to_process)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Skipped (already processed): {skipped}")
        print(f"\nResults saved to: {OUTPUT_PATH}")
        print(f"Checkpoint saved to: {CHECKPOINT_PATH}")

    def _save_results(self):
        """Save results to model_technique_map.json."""
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Convert internal format to output format
        # When run standalone, output just the additions (deletions are only meaningful in pipeline)
        output = {}
        for doc_id, result in self.results.items():
            if isinstance(result, dict) and 'additions' in result:
                output[doc_id] = result['additions']
            else:
                # Legacy format fallback
                output[doc_id] = result

        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved {len(output)} document analyses to {OUTPUT_PATH}")

    def get_raw_results(self) -> Dict:
        """Get raw results including deletions (for pipeline use)."""
        return self.results


def main():
    parser = argparse.ArgumentParser(
        description="LLM-assisted technique extraction from source documents"
    )
    parser.add_argument(
        '--id',
        type=str,
        help='Process only a specific document ID'
    )
    parser.add_argument(
        '--model',
        type=str,
        choices=['haiku', 'sonnet', 'sonnet-legacy', 'opus', 'opus-5', 'sonnet-5'],
        default='sonnet',
        help='Claude model to use (default: sonnet)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )
    parser.add_argument(
        '--single-call',
        action='store_true',
        help='Use the legacy single monolithic-prompt extraction call per document '
             'instead of one call per technique category (A/B fallback; see T3.2)'
    )

    args = parser.parse_args()

    # Validate environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=your-api-key")
        sys.exit(1)

    # Create extractor and run
    extractor = LLMExtractor(model_name=args.model, resume=args.resume, single_call=args.single_call)
    extractor.process_all_documents(specific_doc_id=args.id)


if __name__ == "__main__":
    main()
