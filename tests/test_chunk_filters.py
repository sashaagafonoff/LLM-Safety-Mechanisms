"""Tests for the chunk-quality gate (WORKPLAN T2.2 / docs/workplan/2026-08-execution-plan.md).

Deliberately imports ONLY chunk_filters — no sentence_transformers / HuggingFace
deps, no NLUAnalyzer instantiation, so this test runs fast in any environment.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import chunk_filters as cf


# --- Must-reject fixtures ---

REAL_TABLE_SOUP_EXAMPLE = (
    "BasicCommandand Discoverallowedcommunicationchannelswhenestablishinganew "
    "PASS PASS PASS | Control(C2) | foothold. | | | | | ----------- | --------- | --- | ---"
)

MARKDOWN_TABLE_ROW = (
    "| Technique | Score | Status |\n"
    "|-----------|-------|--------|\n"
    "| RLHF | 0.92 | PASS |\n"
    "| Constitutional AI | 0.88 | PASS |"
)

NUMBERS_ONLY_BENCHMARK_LINE = (
    "94.2 87.3 91.0 88.5 PASS PASS PASS FAIL N/A 76.3 82.1 79.4 90.2 85.6 PASS"
)

MASHED_WORDS_LINE = (
    "Thisisalongsentencewithoutanyspacesbetweenthewordsatallwhichmakesithardtoreadproperly"
)


def test_rejects_real_published_false_evidence_example():
    assert cf.is_low_quality_chunk(REAL_TABLE_SOUP_EXAMPLE) is True
    reasons = cf.chunk_quality_reasons(REAL_TABLE_SOUP_EXAMPLE)
    assert reasons  # non-empty
    # Should be caught by more than one heuristic (table syntax, mashed word,
    # repeated benchmark tokens all present in this fragment).
    assert "table_syntax_density" in reasons
    assert "mashed_word" in reasons
    assert "repeated_benchmark_tokens" in reasons


def test_rejects_markdown_table_row():
    assert cf.is_low_quality_chunk(MARKDOWN_TABLE_ROW) is True
    assert "table_syntax_density" in cf.chunk_quality_reasons(MARKDOWN_TABLE_ROW)


def test_rejects_numbers_only_benchmark_line():
    assert cf.is_low_quality_chunk(NUMBERS_ONLY_BENCHMARK_LINE) is True
    reasons = cf.chunk_quality_reasons(NUMBERS_ONLY_BENCHMARK_LINE)
    assert "digit_heavy" in reasons or "repeated_benchmark_tokens" in reasons


def test_rejects_mashed_words_line():
    assert cf.is_low_quality_chunk(MASHED_WORDS_LINE) is True
    assert "mashed_word" in cf.chunk_quality_reasons(MASHED_WORDS_LINE)


def test_rejects_empty_text_is_not_flagged_as_noise():
    # Empty/whitespace-only text is "nothing", not "table soup" -- callers
    # should already be filtering empty chunks elsewhere, so this gate stays
    # conservative and doesn't report reasons for it.
    assert cf.chunk_quality_reasons("") == []
    assert cf.chunk_quality_reasons("   \n\t  ") == []


# --- Must-pass fixtures (realistic safety-doc prose) ---

PASS_FIXTURES = [
    (
        "red_teaming",
        "We conducted extensive red teaming with over 100 external experts "
        "across domains including cybersecurity and biosecurity.",
    ),
    (
        "figures_percentage",
        "The model refused 99.2% of harmful requests in our evaluation.",
    ),
    (
        "rlhf_dpo",
        "We fine-tuned the model using RLHF and DPO to align outputs with "
        "human preferences.",
    ),
    (
        "two_sentence_deployment",
        "Before shipping any model update, we run a staged rollout with "
        "automated safety evaluations. Deployment is halted automatically "
        "if refusal rates drop below the configured threshold.",
    ),
    (
        "url_reference",
        "See https://example.com/safety-report for more details on our "
        "deployment safeguards.",
    ),
    (
        "abbreviation_mid_sentence",
        "The system employs multiple safeguards, e.g., rate limiting and "
        "content filtering, before a response is returned to the user.",
    ),
    (
        "long_technical_prose",
        "Constitutional AI trains the model to critique and revise its own "
        "responses against a set of guiding principles, reducing reliance on "
        "large volumes of human preference labels while still steering the "
        "model away from harmful or policy-violating outputs during training.",
    ),
]


def test_accepts_realistic_safety_prose():
    for name, text in PASS_FIXTURES:
        assert cf.is_low_quality_chunk(text) is False, (
            f"fixture '{name}' was incorrectly flagged as low quality: "
            f"{cf.chunk_quality_reasons(text)}"
        )
        assert cf.chunk_quality_reasons(text) == []


def test_pass_fixtures_cover_at_least_six_cases():
    assert len(PASS_FIXTURES) >= 6
