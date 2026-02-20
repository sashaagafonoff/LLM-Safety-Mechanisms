#!/usr/bin/env python3
"""
LLM-Assisted Technique Extraction (Two-Pass RAG Architecture)

Uses Claude API to analyze source documents and identify safety techniques.
Implements a Retrieval-Augmented Generation (RAG) pattern in two passes:

  Pass 1 — EXTRACTION: Claude classifies the full document against the
           technique taxonomy. The prompt contains generic examples of true
           and false positive patterns, but NO dataset-specific review data,
           keeping the initial classification unbiased.

  Pass 2 — VERIFICATION: For each candidate technique from Pass 1, the
           review index is queried for that technique's confirmed positives
           and rejected negatives from prior human reviews. These are fed
           to Claude as technique-specific context, and it confirms or
           rejects each candidate. Techniques with no review history pass
           through unverified.

The review index is authoritative and cumulative — it reflects all manual
additions, confirmed automated tags, and explicit deletions across the
full review history in model_technique_map.json.

Usage:
    python scripts/llm_assisted_extraction.py                    # Process all documents
    python scripts/llm_assisted_extraction.py --id doc-id        # Process specific document
    python scripts/llm_assisted_extraction.py --model haiku      # Use Haiku (cheaper)
    python scripts/llm_assisted_extraction.py --resume           # Resume from last checkpoint

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - anthropic package installed: pip install anthropic
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import time
from datetime import datetime
from difflib import SequenceMatcher

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
    "sonnet": "claude-sonnet-4-5-20250929",
    "sonnet-legacy": "claude-3-5-sonnet-20241022",
    "opus": "claude-opus-4-6",
}

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
    if best_score > 0.4 and best_match:
        return best_match.strip()

    return None


# Prompt template for technique extraction
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

For each technique you identify, provide:
- `techniqueId`: The technique ID
- `confidence`: High/Medium/Low based on evidence strength
- `evidence`: A VERBATIM quote (1-2 sentences) copied EXACTLY from the document - do not paraphrase or summarize
- `reasoning`: Why you believe this is a true match (1 sentence)

{nlu_context}

## Few-Shot Examples

Below are examples of CORRECT matches and CORRECT rejections from manually reviewed documents.

### TRUE POSITIVES (should be matched):

```json
[
  {{
    "techniqueId": "tech-rlhf",
    "confidence": "High",
    "evidence": "The model underwent reinforcement learning from human feedback, with human raters scoring outputs for helpfulness and harmlessness.",
    "reasoning": "Explicit description of RLHF implementation with human raters and dual objectives."
  }},
  {{
    "techniqueId": "tech-red-teaming",
    "confidence": "High",
    "evidence": "We conducted extensive red teaming with over 100 external experts across domains including cybersecurity, biosecurity, and persuasion.",
    "reasoning": "Direct description of red teaming activity with specific details about team size and domains."
  }},
  {{
    "techniqueId": "tech-output-filtering-systems",
    "confidence": "Medium",
    "evidence": "A separate classifier is applied to model outputs to detect and filter harmful content before it reaches the user.",
    "reasoning": "Describes a post-generation output filtering system with a classifier."
  }},
  {{
    "techniqueId": "tech-safety-benchmarks",
    "confidence": "High",
    "evidence": "We evaluate on ToxiGen, BBQ, and BOLD benchmarks to measure the model's propensity for generating biased or toxic content.",
    "reasoning": "Specific named safety benchmarks used for evaluation."
  }}
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
   → REJECT tech-regulatory-compliance: Vague statement with no specific compliance details.

Return ONLY a JSON array of technique matches. If no techniques are found, return an empty array [].

IMPORTANT:
- Return ONLY the JSON array, no explanatory text before or after
- The `evidence` field MUST be an exact, verbatim quote from the document - copy-paste directly
- Be conservative: It's better to miss a technique than to include false positives
- Focus on clear, unambiguous evidence of implementation
"""

# Context to add when NLU results are available
NLU_CONTEXT_TEMPLATE = """
## Prior Analysis (NLU Pipeline)

A semantic analysis pipeline has already scanned this document and found the following potential techniques.
Note: This pipeline has approximately 60-70% precision - some matches may be false positives.

**Techniques detected by NLU:**
{nlu_techniques}

Your task:
1. **Confirm or reject** each NLU detection - if you cannot find clear implementation evidence, mark it for deletion
2. **Add any techniques** the NLU may have missed
3. For deletions, add entries with `"delete": true` and explain why

Example with deletion:
```json
[
  {{"techniqueId": "rlhf", "confidence": "High", "evidence": "...", "reasoning": "..."}},
  {{"techniqueId": "input-filtering", "delete": true, "reasoning": "Only mentioned in related work, not implemented"}}
]
```
"""


# RAG verification prompt — fed technique-specific review history after initial extraction
VERIFICATION_PROMPT = """You are verifying technique classifications against prior human review decisions.

For each candidate below, I show:
- The proposed technique match and evidence quote
- Previously CONFIRMED matches for this technique (true positives from human review)
- Previously REJECTED matches for this technique (false positives caught by human review)

Use the confirmed/rejected patterns to judge whether each candidate is a genuine implementation match.

## Candidates to Verify

{candidates_section}

## Instructions

For each candidate, return CONFIRM or REJECT:
- CONFIRM: Evidence clearly describes implementation of the technique, consistent with confirmed examples
- REJECT: Evidence matches a false-positive pattern seen in rejected examples (citation-only, future work, glossary, negation, vague mention)
- When uncertain, CONFIRM — it is better for a human reviewer to catch a borderline case than to lose a valid match

Return ONLY a JSON array:
[{{"techniqueId": "...", "verdict": "confirm", "reason": "..."}}]
"""


class LLMExtractor:
    def __init__(self, model_name: str = "sonnet", resume: bool = False):
        """Initialize the LLM-based extractor."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = MODEL_MAP.get(model_name, MODEL_MAP["sonnet"])
        self.resume = resume

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
        print(f"✓ Using model: {self.model}")

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

        index = {}

        for doc_id, entries in technique_map.items():
            # Only include documents that have been manually reviewed
            is_reviewed = False
            for e in entries:
                if not e.get("active", True) and e.get("deleted_by") not in (None, "system"):
                    is_reviewed = True
                for ev in e.get("evidence", []):
                    if isinstance(ev, dict) and ev.get("created_by") in ("manual", "sashaagafonoff"):
                        is_reviewed = True

            if not is_reviewed:
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
                            text = ev["text"][:300].strip()
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
                            evidence_text = ev["text"][:300].strip()
                            break

                    index[tech_id]["negatives"].append({
                        "doc_id": doc_id,
                        "text": evidence_text,
                        "deleted_by": e.get("deleted_by", "unknown"),
                        "reason": e.get("deletion_reason", ""),
                    })

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

    def _format_techniques_list(self) -> str:
        """Format techniques for the prompt."""
        lines = []
        for tech in self.techniques:
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
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text

        # Truncate and add notice
        truncated = text[:max_chars]
        truncated += f"\n\n[DOCUMENT TRUNCATED - Original length: {len(text)} chars, showing first {max_chars} chars]"
        return truncated

    def _parse_json_response(self, content: str) -> Optional[list]:
        """Extract and parse a JSON array from an LLM response.

        Handles markdown code blocks, bare JSON, and embedded arrays.
        Returns parsed list or None on failure.
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

    def _build_verification_sections(self, candidates: List[Dict],
                                      exclude_doc_id: str = "") -> str:
        """Build the candidates section for the verification prompt.

        For each candidate technique, retrieves confirmed/rejected examples
        from the review index (excluding the current document to avoid
        circular reference).
        """
        sections = []

        for i, c in enumerate(candidates, 1):
            tech_id = c.get("techniqueId", "")
            tech_name = self.tech_names.get(tech_id, tech_id)

            # Extract evidence text from the candidate
            evidence_text = ""
            if isinstance(c.get("evidence"), list) and c["evidence"]:
                ev = c["evidence"][0]
                evidence_text = ev.get("text", "") if isinstance(ev, dict) else str(ev)
            evidence_text = evidence_text[:300]

            reasoning = c.get("reasoning", "")

            section = f"### {i}. {tech_id} ({tech_name})\n"
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
                    section += f'- {p["doc_id"]}: "{p["text"][:200]}"\n'

            if negatives:
                section += "\nRejected matches from other documents:\n"
                for n in negatives:
                    text_part = f': "{n["text"][:200]}"' if n.get("text") else ""
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
        examples. Techniques without review data pass through unmodified.

        This implements the "augmented generation" step of the RAG pattern:
        the review index is the retrieval source, technique-specific examples are
        the augmentation, and Claude's verdict is the generation.
        """
        # Split candidates: those with review data get verified, others pass through
        to_verify = []
        pass_through = []

        for c in candidates:
            tech_id = c.get("techniqueId", "")
            review = self.review_index.get(tech_id, {})
            # Only verify if there are examples from OTHER documents
            has_external = any(p["doc_id"] != doc_id for p in review.get("positives", []))
            has_external = has_external or any(
                n["doc_id"] != doc_id for n in review.get("negatives", []))
            if has_external:
                to_verify.append(c)
            else:
                pass_through.append(c)

        if not to_verify:
            return candidates  # Nothing to verify

        print(f"  Verifying {len(to_verify)} candidates against review index "
              f"({len(pass_through)} pass-through)...")

        # Build verification prompt with technique-specific examples
        candidates_section = self._build_verification_sections(to_verify, exclude_doc_id=doc_id)
        prompt = VERIFICATION_PROMPT.format(candidates_section=candidates_section)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            verdicts = self._parse_json_response(content)

            if verdicts is None:
                print(f"  ⚠️ Could not parse verification response, passing all through")
                return candidates

            # Build verdict lookup
            verdict_map = {}
            for v in verdicts:
                tid = v.get("techniqueId", "")
                verdict_map[tid] = v.get("verdict", "confirm").lower()

            # Filter verified candidates
            confirmed = []
            rejected = []
            for c in to_verify:
                tid = c.get("techniqueId", "")
                verdict = verdict_map.get(tid, "confirm")  # Default to confirm if missing
                if verdict == "confirm":
                    confirmed.append(c)
                else:
                    reason = next((v.get("reason", "") for v in verdicts
                                   if v.get("techniqueId") == tid), "")
                    rejected.append((tid, reason))

            if rejected:
                print(f"  Verification rejected {len(rejected)} candidate(s):")
                for tid, reason in rejected:
                    print(f"    [-] {tid}: {reason[:80]}")

            if confirmed:
                print(f"  Verification confirmed {len(confirmed)} candidate(s)")

            return confirmed + pass_through

        except anthropic.APIError as e:
            print(f"  ⚠️ Verification API error: {e}, passing all candidates through")
            return candidates

        except Exception as e:
            print(f"  ⚠️ Verification failed: {e}, passing all candidates through")
            return candidates

    def extract_techniques(self, doc_id: str, text: str, nlu_results: Optional[List[Dict]] = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract techniques from a document using Claude API.

        Args:
            doc_id: Document identifier
            text: Full document text
            nlu_results: Optional list of NLU-detected techniques to review

        Returns:
            Tuple of (additions, deletions) where each is a list of technique dicts
        """

        # Get document metadata
        metadata = self.evidence_metadata.get(doc_id, {})
        doc_purpose = metadata.get('document_purpose', 'unknown')
        signal_strength = metadata.get('signal_strength', 'medium')
        temporal_focus = metadata.get('temporal_focus', 'unknown')
        primary_topics = ', '.join(metadata.get('primary_topics', [])) or 'none specified'
        excluded_topics = ', '.join(metadata.get('excluded_topics', [])) or 'none specified'

        # Format techniques list
        techniques_list = self._format_techniques_list()

        # Truncate document if needed
        document_text = self._truncate_document(text)

        # Build NLU context if results provided
        nlu_context = ""
        if nlu_results:
            nlu_tech_list = "\n".join([
                f"- {r['techniqueId']} ({r.get('confidence', 'Unknown')})"
                for r in nlu_results if r.get('active', True)
            ])
            nlu_context = NLU_CONTEXT_TEMPLATE.format(nlu_techniques=nlu_tech_list)

        # Build prompt
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
        )

        # Call Claude API
        content = None  # Initialize for error handling
        try:
            print(f"  Calling Claude API ({self.model})...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0,  # Deterministic for consistency
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            content = response.content[0].text
            matches = self._parse_json_response(content)

            if matches is None:
                print(f"  ⚠️ Could not parse JSON from response")
                print(f"  Response preview: {content[:500]}")
                return [], []

            # Separate additions from deletions and format output
            additions = []
            deletions = []

            for match in matches:
                tech_id = match.get('techniqueId')
                if not tech_id:
                    continue

                if match.get('delete'):
                    # This is a deletion suggestion
                    deletions.append({
                        "techniqueId": tech_id,
                        "deleted_by": "llm",
                        "reasoning": match.get('reasoning', '')
                    })
                else:
                    # This is an addition - apply fuzzy matching to get exact quote
                    llm_evidence = match.get('evidence', '')
                    exact_quote = find_exact_passage(llm_evidence, text) if llm_evidence else None

                    # Use exact quote if found, otherwise fall back to LLM's version
                    final_evidence = exact_quote if exact_quote else llm_evidence

                    if final_evidence:
                        additions.append({
                            "techniqueId": tech_id,
                            "confidence": match.get('confidence', 'Medium'),
                            "active": True,
                            "deleted_by": None,
                            "evidence": [{
                                "text": final_evidence,
                                "created_by": "llm",
                                "active": True,
                                "deleted_by": None,
                                "llm_original": llm_evidence if exact_quote else None  # Track if we modified
                            }],
                            "reasoning": match.get('reasoning', '')
                        })

                        if exact_quote and exact_quote != llm_evidence:
                            print(f"    ↳ Fuzzy matched quote for {tech_id}")

            return additions, deletions

        except json.JSONDecodeError as e:
            print(f"  ⚠️ Error parsing JSON response: {e}")
            print(f"  Response content: {content[:500] if content else 'None'}")
            return [], []

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
            if content:
                debug_file = Path(f"cache/debug_response_{doc_id}.txt")
                debug_file.parent.mkdir(parents=True, exist_ok=True)
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"Error: {e}\n")
                    f.write(f"Error type: {type(e).__name__}\n")
                    f.write("="*80 + "\n")
                    f.write("Raw Response:\n")
                    f.write("="*80 + "\n")
                    f.write(content)
                print(f"  Debug info saved to: {debug_file}")

            import traceback
            print(f"  Traceback:\n{traceback.format_exc()}")
            return [], []

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

            # Store results with both additions and deletion metadata
            self.results[doc_id] = {
                "additions": additions,
                "deletions": deletions
            }

            # Save checkpoint after each document
            self._save_checkpoint()

            # Small delay to avoid rate limits
            time.sleep(1)

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
        choices=['haiku', 'sonnet', 'sonnet-legacy', 'opus'],
        default='sonnet',
        help='Claude model to use (default: sonnet)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )

    args = parser.parse_args()

    # Validate environment
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=your-api-key")
        sys.exit(1)

    # Create extractor and run
    extractor = LLMExtractor(model_name=args.model, resume=args.resume)
    extractor.process_all_documents(specific_doc_id=args.id)


if __name__ == "__main__":
    main()
