"""
chunk_filters.py - Chunk-quality gate for the NLU retrieval stage.

`clean_flat_text.py` strips known structural noise (TOCs, reference lists,
explicit "Table N:" blocks, arXiv stamps, contributor lists) at *ingest*
time, keyed on document-level patterns (headings, blank-line runs, etc.).
But PDF extraction still leaves table fragments and mashed-together text
that don't match those document-level patterns and only become obviously
bad once the text has been windowed into a retrieval chunk. This module is
that retrieval-side backstop: a pure, dependency-free heuristic classifier
applied to each chunk right before it is embedded/scored, so table-soup
never reaches the bi-encoder/cross-encoder (and therefore can never be
tagged as evidence for a safety technique).

Real example currently in the published dataset that motivated this gate
(see docs/workplan/2026-08-execution-plan.md T2.2):

    "BasicCommandand Discoverallowedcommunicationchannelswhenestablishinganew
    PASS PASS PASS | Control(C2) | foothold. | | | | | ----------- | --------- |
    --- | ---"

That fragment is a markdown-table row (pipe/dash syntax) mixed with
mashed-together words (PDF layout extraction lost the spaces between
"Basic Command and Discover allowed communication channels...") and
repeated benchmark tokens ("PASS PASS PASS"). No single heuristic below
catches every variant reliably, so they are combined; a chunk is rejected
if *any* heuristic fires.

Usage:
    from chunk_filters import is_low_quality_chunk, chunk_quality_reasons

    if is_low_quality_chunk(chunk_text):
        continue  # drop before embedding

    reasons = chunk_quality_reasons(chunk_text)  # [] if the chunk is fine
"""

import re
from typing import List

# --- Thresholds (module constants; tune here, not inline) ---

# 1. Alphabetic-character ratio (letters / non-whitespace chars). Normal prose
#    sits well above 0.7; table soup and digit/symbol-heavy fragments drop
#    below this. Kept a bit under 0.6 so numerals in ordinary sentences
#    ("100 external experts", "99.2%") don't trip it.
MIN_ALPHA_RATIO = 0.60

# 2. Table-syntax density: count of pipe/dash-rule/equals-rule/tab-run
#    markers per chunk. Two or more is a strong markdown/plaintext-table
#    signal; a single stray "|" or "--" in prose (em-dash-ish usage) should
#    not be enough on its own.
MIN_TABLE_MARKERS = 2

# 3. Mashed-word detection: PDF column extraction often drops spaces between
#    words ("Discoverallowedcommunicationchannels"). A real English/technical
#    token this long essentially never occurs in safety-doc prose (longest
#    plausible: "counter-multi-agent-coordination" style hyphenated compounds
#    are split by hyphens already). 25 chars comfortably clears real long
#    words (e.g. "interpretability", "unlearning") while catching mashed runs.
MAX_ALPHA_TOKEN_LEN = 25

# 4. Repeated benchmark tokens (PASS/FAIL/N/A/TRUE/FALSE/OK). Benchmark and
#    checklist tables repeat these; normal prose uses them at most once or
#    twice per chunk.
BENCHMARK_TOKEN_MIN_REPEATS = 3
_BENCHMARK_TOKEN_RE = re.compile(r'\b(PASS|FAIL|N/?A|TRUE|FALSE|OK)\b', re.IGNORECASE)

# 5. Digit-heavy content: digit chars / non-whitespace chars. Ordinary prose
#    with the occasional statistic (e.g. "99.2%") stays well under this;
#    dense numeric tables (scores, version grids) exceed it.
MAX_DIGIT_RATIO = 0.30

# 6. Long chunk with no sentence punctuation at all. Real prose chunks this
#    long always contain at least one '.', '?', or '!'; a long run without
#    any is characteristic of table cells/labels concatenated together.
MIN_LENGTH_FOR_PUNCTUATION_CHECK = 200

# Characters counted as "table syntax" markers.
_TABLE_MARKER_RE = re.compile(r'\|{1}|-{3,}|={3,}|\t{1,}')

_ALPHA_TOKEN_RE = re.compile(r'[A-Za-z]+')
_SENTENCE_PUNCT_RE = re.compile(r'[.!?]')


def _alpha_ratio(non_ws: str) -> float:
    if not non_ws:
        return 1.0
    alpha = sum(1 for c in non_ws if c.isalpha())
    return alpha / len(non_ws)


def _digit_ratio(non_ws: str) -> float:
    if not non_ws:
        return 0.0
    digits = sum(1 for c in non_ws if c.isdigit())
    return digits / len(non_ws)


def chunk_quality_reasons(text: str) -> List[str]:
    """Return the list of heuristics that fired for `text` (empty = high quality).

    Each entry is a short machine-readable tag, useful for debugging/logging
    which rule(s) rejected a given chunk.
    """
    reasons: List[str] = []
    if not text or not text.strip():
        return reasons  # empty text isn't "low quality noise", just nothing

    stripped = text.strip()
    non_ws = re.sub(r'\s+', '', stripped)

    if not non_ws:
        return reasons

    # 1. Alphabetic ratio
    if _alpha_ratio(non_ws) < MIN_ALPHA_RATIO:
        reasons.append("low_alpha_ratio")

    # 2. Table-syntax density
    table_markers = len(_TABLE_MARKER_RE.findall(stripped))
    if table_markers >= MIN_TABLE_MARKERS:
        reasons.append("table_syntax_density")

    # 3. Mashed-word detection
    for tok in _ALPHA_TOKEN_RE.findall(stripped):
        if len(tok) > MAX_ALPHA_TOKEN_LEN:
            reasons.append("mashed_word")
            break

    # 4. Repeated benchmark tokens
    benchmark_hits = _BENCHMARK_TOKEN_RE.findall(stripped)
    if len(benchmark_hits) >= BENCHMARK_TOKEN_MIN_REPEATS:
        reasons.append("repeated_benchmark_tokens")

    # 5. Digit-heavy content
    if _digit_ratio(non_ws) > MAX_DIGIT_RATIO:
        reasons.append("digit_heavy")

    # 6. Long chunk, no sentence punctuation
    if len(stripped) > MIN_LENGTH_FOR_PUNCTUATION_CHECK and not _SENTENCE_PUNCT_RE.search(stripped):
        reasons.append("no_sentence_punctuation")

    return reasons


def is_low_quality_chunk(text: str) -> bool:
    """True if `text` looks like structural noise (table soup, mashed PDF
    extraction artifacts, benchmark grids) rather than prose worth retrieving.

    A chunk is rejected if *any* heuristic in `chunk_quality_reasons` fires.
    """
    return len(chunk_quality_reasons(text)) > 0
