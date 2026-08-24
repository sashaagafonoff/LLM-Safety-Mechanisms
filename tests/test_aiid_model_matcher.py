"""Tests for the AIID incident model matcher (T5.3, Track C).

docs/workplan/2026-08-execution-plan.md: data/incidents.json has 1630
incidents and zero modelIds populated. These tests cover the pure,
dependency-free alias-generation and matching logic in
scripts/aiid_model_matcher.py against a sample of real data/models.json
entries, so the precision-over-recall safety rules (digit-or-two-words,
provider gating, longest-alias-first overlap suppression, blocklist) stay
locked in as the alias table grows.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import aiid_model_matcher as amm


def load_models():
    data = json.load(open(ROOT / "data" / "models.json", encoding="utf-8"))
    return data["models"] if isinstance(data, dict) else data


def find_model(models, model_id):
    return next(m for m in models if m["id"] == model_id)


# --- is_usable_alias: the core precision gate ---

def test_bare_common_words_are_never_usable():
    for word in ("nova", "command", "phi", "grok", "claude", "gemini",
                 "Nova", "COMMAND", "Grok"):
        assert amm.is_usable_alias(word) is False


def test_single_word_with_digit_is_usable():
    assert amm.is_usable_alias("GPT-4o") is True
    assert amm.is_usable_alias("GPT4o") is True


def test_two_word_alias_without_digit_is_usable():
    assert amm.is_usable_alias("Nova Pro") is True
    assert amm.is_usable_alias("Command A") is True


def test_empty_and_blank_alias_unusable():
    assert amm.is_usable_alias("") is False
    assert amm.is_usable_alias("   ") is False


# --- generate_aliases: driven off real models.json entries ---

def test_generate_aliases_from_real_models_json_sample():
    models = load_models()
    m = find_model(models, "claude-opus-4.7")
    aliases = amm.generate_aliases(m)
    assert "Claude Opus 4.7" in aliases
    # every generated alias must independently pass the usability gate
    assert all(amm.is_usable_alias(a) for a in aliases)


def test_generate_aliases_includes_separator_variants():
    models = load_models()
    m = find_model(models, "gpt-4o")
    aliases = amm.generate_aliases(m)
    assert "GPT-4o" in aliases
    assert "GPT 4o" in aliases  # hyphen -> space variant


def test_generate_aliases_includes_tier_version_swap():
    # "Claude Opus 4.7" (family, tier, version) also generates the
    # "Claude 4.7 Opus" (family, version, tier) ordering.
    models = load_models()
    m = find_model(models, "claude-opus-4.7")
    aliases = amm.generate_aliases(m)
    assert "Claude 4.7 Opus" in aliases


def test_generate_aliases_never_emits_a_bare_family_word():
    # Regression: even a family whose real name is a single common word
    # (Nova, Command, Grok, ...) must never produce a bare blocklisted-word
    # alias on its own.
    models = load_models()
    for model_id in ("nova-pro", "command-a", "grok-4", "claude-opus-4.7"):
        m = find_model(models, model_id)
        for alias in amm.generate_aliases(m):
            assert alias.strip().lower() not in amm.BLOCKLIST_STANDALONE, (
                f"{model_id} produced unsafe bare alias {alias!r}"
            )


def test_hand_curated_extras_are_included():
    models = load_models()
    m = find_model(models, "gpt-4o")
    aliases = amm.generate_aliases(m)
    assert "ChatGPT-4o" in aliases


# --- build_alias_table: no blocklisted bare word ever reaches the table ---

def test_alias_table_from_full_models_json_has_no_bare_blocklisted_alias():
    models = load_models()
    table = amm.build_alias_table(models)
    assert len(table) > 0
    for entry in table:
        alias = entry["alias"].strip()
        if " " not in alias and "-" not in alias:
            assert alias.lower() not in amm.BLOCKLIST_STANDALONE


# --- match_models: blocklist enforcement end-to-end ---

def test_bare_nova_description_matches_nothing():
    models = load_models()
    table = amm.build_alias_table(models)
    text = "The system, internally called Nova, malfunctioned during testing."
    assert amm.match_models(text, table, {"amazon"}) == []


def test_bare_command_description_matches_nothing():
    models = load_models()
    table = amm.build_alias_table(models)
    text = "Users could issue any Command to the assistant without restriction."
    assert amm.match_models(text, table, {"cohere"}) == []


# --- match_models: provider gating ---

def test_mention_not_matched_when_provider_not_already_matched():
    models = load_models()
    table = amm.build_alias_table(models)
    text = "A chatbot built on GPT-4o gave harmful medical advice to a user."
    # providerIds does NOT include openai -> no modelId, even though the
    # text clearly names a real, valid alias.
    assert amm.match_models(text, table, {"anthropic"}) == []
    # same text, correct provider gating -> matches
    assert amm.match_models(text, table, {"openai"}) == ["gpt-4o"]


def test_no_provider_ids_matches_nothing():
    models = load_models()
    table = amm.build_alias_table(models)
    text = "Claude Opus 4.7 was involved in the incident."
    assert amm.match_models(text, table, set()) == []
    assert amm.match_models(text, table, []) == []


# --- match_models: the realistic incident-title case from the design brief ---

def test_realistic_claude_opus_title_matches_exact_model_id():
    models = load_models()
    table = amm.build_alias_table(models)
    title = ("Claude Opus 4.7 Reportedly Compromised Real Company's "
             "Production Infrastructure During Cybersecurity Evaluation")
    assert amm.match_models(title, table, {"anthropic"}) == ["claude-opus-4.7"]


# --- match_models: longest-alias-first overlap suppression ---

def test_longest_alias_wins_on_overlapping_mention():
    models = load_models()
    table = amm.build_alias_table(models)
    # "Grok 4" is a valid alias of grok-4; "Grok 4.3" of grok-4.3. A single
    # mention of "Grok 4.3" must not also credit the shorter "Grok 4".
    text = "xAI shipped Grok 4.3 this week with major upgrades."
    assert amm.match_models(text, table, {"xai"}) == ["grok-4.3"]


def test_distinct_mentions_of_both_models_both_match():
    models = load_models()
    table = amm.build_alias_table(models)
    text = "Grok 4 was the flagship before Grok 4.3 replaced it."
    assert amm.match_models(text, table, {"xai"}) == ["grok-4", "grok-4.3"]


# --- find_notable_unmatched: model-shaped mentions with no models.json entry ---

def test_notable_unmatched_flags_unknown_but_not_real_model():
    # NOTE: this originally used "Claude Mythos 5" as the unknown mention;
    # claude-mythos-5 was added to models.json on 2026-08-24 (owner decision),
    # so it now matches as a real model (asserted below) and the unknown-model
    # case uses a mention with no models.json entry instead.
    models = load_models()
    table = amm.build_alias_table(models)
    title = ("Claude Nebula 7 Reportedly Published Malicious PyPI Package "
             "That Compromised Real Security Company During Evaluation")
    notable = amm.find_notable_unmatched(title, {"anthropic"}, table)
    assert "Claude Nebula 7" in notable
    # a real, matched model must not also show up as "notable unmatched"
    real_title = "Claude Opus 4.7 was compromised during evaluation."
    notable_real = amm.find_notable_unmatched(real_title, {"anthropic"}, table)
    assert notable_real == set()


def test_mythos_5_now_matches_as_real_model():
    # The aiid-1628 title that motivated the matcher: with claude-mythos-5 in
    # models.json this must now MATCH rather than surface as notable-unmatched.
    models = load_models()
    table = amm.build_alias_table(models)
    title = ("Claude Mythos 5 Reportedly Published Malicious PyPI Package "
             "That Compromised Real Security Company During Evaluation")
    assert amm.match_models(title, table, {"anthropic"}) == ["claude-mythos-5"]
    assert amm.find_notable_unmatched(title, {"anthropic"}, table) == set()


def test_notable_unmatched_respects_provider_gating():
    models = load_models()
    table = amm.build_alias_table(models)
    title = "Claude Nebula 7 was compromised."
    # provider not matched -> no notable mentions surfaced either
    assert amm.find_notable_unmatched(title, set(), table) == set()
    assert amm.find_notable_unmatched(title, {"openai"}, table) == set()


# --- referential integrity: every alias table entry points at a live model id ---

def test_alias_table_model_ids_all_exist_in_models_json():
    models = load_models()
    valid_ids = {m["id"] for m in models}
    table = amm.build_alias_table(models)
    for entry in table:
        assert entry["model_id"] in valid_ids
        assert entry["provider"] in {m["provider"] for m in models}
