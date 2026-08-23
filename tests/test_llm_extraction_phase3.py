"""Tests for docs/workplan/2026-08-execution-plan.md T3.1-T3.4 (LLM-pass recall uplift).

Covers, in scripts/llm_assisted_extraction.py:
  - T3.1  _format_nlu_findings()            — NLU evidence injected into the prompt
  - T3.2  _group_techniques_by_category(),
          _dedupe_candidates(), _dedupe_deletions(),
          doc-block byte-identity across category calls (prompt caching)
  - T3.3  _validate_matches_payload(), _validate_verdicts_payload(),
          RECORD_TECHNIQUES_SCHEMA / RECORD_VERDICTS_SCHEMA,
          _call_structured() strict->non-strict retry + legacy text fallback
  - T3.4  _apply_verdicts() index-keyed verdict mapping (incl. duplicate
          techniqueId disambiguation), 500-char snippet budgets
  - MODEL_MAP additions (opus-5, sonnet-5)

No real Anthropic API calls are made anywhere in this file. Module import
requires no ANTHROPIC_API_KEY (only LLMExtractor.__init__ does — the
`extractor` fixture below sets a dummy one before constructing).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import llm_assisted_extraction as llm_mod  # noqa: E402
import anthropic  # noqa: E402


# ---------------------------------------------------------------------------
# Fakes standing in for anthropic SDK response objects — no network, no SDK
# object construction beyond what's needed to exercise the parsing code.
# ---------------------------------------------------------------------------

class FakeToolUseBlock:
    def __init__(self, name, input_):
        self.type = "tool_use"
        self.name = name
        self.input = input_


class FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class FakeResponse:
    def __init__(self, content):
        self.content = content


@pytest.fixture
def extractor(monkeypatch):
    """A real LLMExtractor over the live repo data, with a dummy API key
    (client construction does no network I/O) so its client can be
    monkeypatched per-test to avoid any real API calls."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-dummy-not-real")
    return llm_mod.LLMExtractor(model_name="haiku", resume=False, single_call=False)


# ---------------------------------------------------------------------------
# T3.1 — _format_nlu_findings
# ---------------------------------------------------------------------------

def test_format_nlu_findings_with_scores():
    nlu_results = [{
        "techniqueId": "tech-rlhf",
        "active": True,
        "evidence": [{"text": "human raters scored outputs", "retrieval_score": 0.812345,
                      "verification_score": 0.9001}],
    }]
    block = llm_mod._format_nlu_findings(nlu_results)
    assert block == '- tech-rlhf (retrieval 0.81, verification 0.90): "human raters scored outputs"'


def test_format_nlu_findings_without_scores_omits_parenthetical():
    # Older NLU entries (pre-T2.4) may lack retrieval_score/verification_score.
    nlu_results = [{
        "techniqueId": "tech-red-teaming",
        "active": True,
        "evidence": [{"text": "red team exercise conducted"}],
    }]
    block = llm_mod._format_nlu_findings(nlu_results)
    assert block == '- tech-red-teaming: "red team exercise conducted"'
    assert "(" not in block


def test_format_nlu_findings_skips_inactive_entries():
    nlu_results = [
        {"techniqueId": "tech-a", "active": False, "evidence": [{"text": "x", "retrieval_score": 0.5, "verification_score": 0.5}]},
        {"techniqueId": "tech-b", "active": True, "evidence": [{"text": "y", "retrieval_score": 0.6, "verification_score": 0.6}]},
    ]
    block = llm_mod._format_nlu_findings(nlu_results)
    assert "tech-a" not in block
    assert "tech-b" in block


def test_format_nlu_findings_filters_by_technique_ids():
    nlu_results = [
        {"techniqueId": "tech-a", "active": True, "evidence": [{"text": "x"}]},
        {"techniqueId": "tech-b", "active": True, "evidence": [{"text": "y"}]},
    ]
    block = llm_mod._format_nlu_findings(nlu_results, technique_ids={"tech-b"})
    assert "tech-a" not in block
    assert "tech-b" in block


def test_format_nlu_findings_truncates_evidence_to_300_chars():
    long_text = "z" * 500
    nlu_results = [{"techniqueId": "tech-a", "active": True, "evidence": [{"text": long_text}]}]
    block = llm_mod._format_nlu_findings(nlu_results)
    # 300 z's plus the surrounding quote/dash/id text
    assert "z" * 300 in block
    assert "z" * 301 not in block


def test_format_nlu_findings_empty_input():
    assert llm_mod._format_nlu_findings([]) == ""
    assert llm_mod._format_nlu_findings(None) == ""


def test_format_nlu_findings_ignores_entries_without_technique_id_or_evidence():
    nlu_results = [
        {"active": True, "evidence": [{"text": "no techniqueId"}]},
        {"techniqueId": "tech-a", "active": True, "evidence": []},  # no evidence -> empty text, still one line
    ]
    block = llm_mod._format_nlu_findings(nlu_results)
    assert '- tech-a: ""' == block


# ---------------------------------------------------------------------------
# T3.2 — category grouping
# ---------------------------------------------------------------------------

def test_group_techniques_by_category_preserves_order_and_drops_empty():
    categories = {"cat-1": {"name": "One"}, "cat-2": {"name": "Two"}, "cat-3": {"name": "Three"}}
    techniques = [
        {"id": "t1", "categoryId": "cat-2"},
        {"id": "t2", "categoryId": "cat-1"},
        {"id": "t3", "categoryId": "cat-1"},
        # cat-3 has no techniques -> must be dropped entirely
    ]
    grouped = llm_mod._group_techniques_by_category(techniques, categories)
    assert list(grouped.keys()) == ["cat-1", "cat-2"]  # categories.json order preserved, cat-3 dropped
    assert [t["id"] for t in grouped["cat-1"]] == ["t2", "t3"]
    assert [t["id"] for t in grouped["cat-2"]] == ["t1"]


def test_group_techniques_by_category_unknown_category_appended():
    categories = {"cat-1": {"name": "One"}}
    techniques = [{"id": "t1", "categoryId": "cat-1"}, {"id": "t2", "categoryId": "cat-unknown"}]
    grouped = llm_mod._group_techniques_by_category(techniques, categories)
    assert "cat-unknown" in grouped
    assert [t["id"] for t in grouped["cat-unknown"]] == ["t2"]


def test_group_techniques_by_category_on_live_taxonomy_covers_all_57():
    # Sanity check against the real dataset: every technique lands in exactly
    # one non-empty group, and nothing is silently dropped.
    import json
    techniques = json.load(open(ROOT / "data" / "techniques.json", encoding="utf-8"))
    categories_list = json.load(open(ROOT / "data" / "categories.json", encoding="utf-8"))
    categories = {c["id"]: c for c in categories_list}

    grouped = llm_mod._group_techniques_by_category(techniques, categories)
    total = sum(len(v) for v in grouped.values())
    assert total == len(techniques)
    assert list(grouped.keys()) == list(categories.keys())  # all 5 categories non-empty today


# ---------------------------------------------------------------------------
# T3.2 — candidate/deletion dedupe
# ---------------------------------------------------------------------------

def test_dedupe_candidates_keeps_higher_confidence():
    additions = [
        {"techniqueId": "tech-a", "confidence": "Low"},
        {"techniqueId": "tech-a", "confidence": "High"},
        {"techniqueId": "tech-b", "confidence": "Medium"},
    ]
    result = llm_mod._dedupe_candidates(additions)
    by_id = {r["techniqueId"]: r for r in result}
    assert len(result) == 2
    assert by_id["tech-a"]["confidence"] == "High"
    assert by_id["tech-b"]["confidence"] == "Medium"


def test_dedupe_candidates_stable_on_tie_first_wins():
    first = {"techniqueId": "tech-a", "confidence": "Medium", "evidence": "first"}
    second = {"techniqueId": "tech-a", "confidence": "Medium", "evidence": "second"}
    result = llm_mod._dedupe_candidates([first, second])
    assert len(result) == 1
    assert result[0]["evidence"] == "first"


def test_dedupe_candidates_skips_entries_without_technique_id():
    result = llm_mod._dedupe_candidates([{"confidence": "High"}, {"techniqueId": "tech-a", "confidence": "Low"}])
    assert len(result) == 1
    assert result[0]["techniqueId"] == "tech-a"


def test_dedupe_deletions_unions_by_technique_id_first_wins():
    deletions = [
        {"techniqueId": "tech-a", "reasoning": "first reason"},
        {"techniqueId": "tech-a", "reasoning": "second reason"},
        {"techniqueId": "tech-b", "reasoning": "other"},
    ]
    result = llm_mod._dedupe_deletions(deletions)
    by_id = {r["techniqueId"]: r for r in result}
    assert len(result) == 2
    assert by_id["tech-a"]["reasoning"] == "first reason"


# ---------------------------------------------------------------------------
# T3.3 — structured-output validation
# ---------------------------------------------------------------------------

def test_validate_matches_payload_happy_path():
    raw = {"matches": [
        {"techniqueId": "tech-a", "confidence": "High", "evidence": "quote", "reasoning": "why"},
        {"techniqueId": "tech-b", "confidence": "Low", "evidence": "", "reasoning": "why not", "delete": True},
    ]}
    result = llm_mod._validate_matches_payload(raw)
    assert result == [
        {"techniqueId": "tech-a", "confidence": "High", "evidence": "quote", "reasoning": "why", "delete": False},
        {"techniqueId": "tech-b", "confidence": "Low", "evidence": "", "reasoning": "why not", "delete": True},
    ]


def test_validate_matches_payload_drops_malformed_items_keeps_valid():
    raw = {"matches": [
        {"techniqueId": "tech-a", "confidence": "High", "evidence": "q", "reasoning": "r"},
        {"confidence": "High"},          # missing techniqueId -> dropped
        "not-a-dict",                    # dropped
        {"techniqueId": "tech-b", "confidence": "Unknown", "evidence": "q2", "reasoning": "r2"},  # bad enum -> coerced
    ]}
    result = llm_mod._validate_matches_payload(raw)
    assert [r["techniqueId"] for r in result] == ["tech-a", "tech-b"]
    assert result[1]["confidence"] == "Medium"  # coerced fallback for invalid enum


def test_validate_matches_payload_rejects_non_dict_or_missing_matches():
    assert llm_mod._validate_matches_payload("not a dict") is None
    assert llm_mod._validate_matches_payload({}) is None
    assert llm_mod._validate_matches_payload({"matches": "not a list"}) is None


def test_validate_verdicts_payload_happy_path():
    raw = {"verdicts": [
        {"index": 1, "techniqueId": "tech-a", "verdict": "Confirm", "reason": "matches example"},
        {"index": 2, "techniqueId": "tech-b", "verdict": "reject", "reason": "citation only"},
    ]}
    result = llm_mod._validate_verdicts_payload(raw)
    assert result == [
        {"index": 1, "techniqueId": "tech-a", "verdict": "confirm", "reason": "matches example"},
        {"index": 2, "techniqueId": "tech-b", "verdict": "reject", "reason": "citation only"},
    ]


def test_validate_verdicts_payload_bool_index_rejected():
    # bool is a subclass of int in Python — must not be accepted as a real index.
    raw = {"verdicts": [{"index": True, "techniqueId": "tech-a", "verdict": "confirm", "reason": "x"}]}
    result = llm_mod._validate_verdicts_payload(raw)
    assert result == []


def test_validate_verdicts_payload_invalid_verdict_coerced_to_abstain():
    raw = {"verdicts": [{"index": 1, "techniqueId": "tech-a", "verdict": "maybe", "reason": "unsure"}]}
    result = llm_mod._validate_verdicts_payload(raw)
    assert result[0]["verdict"] == "abstain"


def test_validate_verdicts_payload_rejects_non_dict_or_missing_verdicts():
    assert llm_mod._validate_verdicts_payload("nope") is None
    assert llm_mod._validate_verdicts_payload({"verdicts": None}) is None


# ---------------------------------------------------------------------------
# T3.4 — index-keyed verdict application (duplicate techniqueId disambiguation)
# ---------------------------------------------------------------------------

def _candidate(tech_id, evidence_text="some evidence"):
    return {
        "techniqueId": tech_id,
        "confidence": "Medium",
        "active": True,
        "evidence": [{"text": evidence_text, "active": True}],
        "reasoning": "",
    }


def test_apply_verdicts_indexed_disambiguates_duplicate_technique_ids():
    # Two candidates share a techniqueId but came from different evidence quotes;
    # the verifier confirms index 1 and rejects index 2 — a techniqueId-keyed
    # lookup could not represent this, which is exactly what T3.4 fixes.
    c1 = _candidate("tech-a", "strong implementation evidence")
    c2 = _candidate("tech-a", "weak/unrelated mention")
    indexed = [(1, c1), (2, c2)]
    verdicts = [
        {"index": 1, "techniqueId": "tech-a", "verdict": "confirm", "reason": "clear match"},
        {"index": 2, "techniqueId": "tech-a", "verdict": "reject", "reason": "citation only"},
    ]

    confirmed, rejected, abstained = llm_mod._apply_verdicts(indexed, verdicts, used_legacy=False)

    assert confirmed == [c1]
    # A "reject" verdict excludes the candidate from every returned bucket
    # (confirmed/abstained) — it's simply dropped, matching pre-T3.4 semantics
    # where rejected candidates were never part of the persisted result.
    assert rejected == [("tech-a", "citation only")]
    assert abstained == []
    assert c1 not in rejected  # (rejected holds tuples, not candidate dicts)
    assert c2 not in confirmed and c2 not in abstained
    assert c1["active"] is True  # confirmed candidate untouched


def test_apply_verdicts_missing_index_abstains():
    c1 = _candidate("tech-a")
    indexed = [(1, c1)]
    verdicts = [{"index": 99, "techniqueId": "tech-a", "verdict": "confirm", "reason": "irrelevant"}]

    confirmed, rejected, abstained = llm_mod._apply_verdicts(indexed, verdicts, used_legacy=False)

    assert confirmed == []
    assert rejected == []
    assert abstained == [c1]
    assert c1["active"] is False
    assert c1["review_reason"] == "verifier_abstained"


def test_apply_verdicts_legacy_mode_keys_by_technique_id():
    c1 = _candidate("tech-a")
    indexed = [(1, c1)]
    # Legacy free-text fallback carries no "index" key.
    verdicts = [{"techniqueId": "tech-a", "verdict": "confirm", "reason": "ok"}]

    confirmed, rejected, abstained = llm_mod._apply_verdicts(indexed, verdicts, used_legacy=True)

    assert confirmed == [c1]


def test_apply_verdicts_legacy_mode_missing_technique_id_abstains():
    c1 = _candidate("tech-a")
    indexed = [(1, c1)]
    verdicts = [{"techniqueId": "tech-other", "verdict": "confirm", "reason": "n/a"}]

    confirmed, rejected, abstained = llm_mod._apply_verdicts(indexed, verdicts, used_legacy=True)

    assert confirmed == []
    assert abstained == [c1]


# ---------------------------------------------------------------------------
# Tool schema validity (T3.3)
# ---------------------------------------------------------------------------

jsonschema = pytest.importorskip("jsonschema")


def test_record_techniques_schema_is_valid_jsonschema():
    from jsonschema import Draft202012Validator
    Draft202012Validator.check_schema(llm_mod.RECORD_TECHNIQUES_SCHEMA)


def test_record_verdicts_schema_is_valid_jsonschema():
    from jsonschema import Draft202012Validator
    Draft202012Validator.check_schema(llm_mod.RECORD_VERDICTS_SCHEMA)


def test_record_techniques_schema_validates_example_payload():
    from jsonschema import Draft202012Validator
    Draft202012Validator(llm_mod.RECORD_TECHNIQUES_SCHEMA).validate({
        "matches": [
            {"techniqueId": "tech-a", "confidence": "High", "evidence": "q", "reasoning": "r"},
            {"techniqueId": "tech-b", "confidence": "Low", "evidence": "", "reasoning": "r2", "delete": True},
        ]
    })


def test_record_techniques_schema_rejects_bad_confidence_enum():
    from jsonschema import Draft202012Validator, ValidationError
    with pytest.raises(ValidationError):
        Draft202012Validator(llm_mod.RECORD_TECHNIQUES_SCHEMA).validate({
            "matches": [{"techniqueId": "tech-a", "confidence": "Certain", "evidence": "q", "reasoning": "r"}]
        })


def test_record_verdicts_schema_validates_example_payload():
    from jsonschema import Draft202012Validator
    Draft202012Validator(llm_mod.RECORD_VERDICTS_SCHEMA).validate({
        "verdicts": [{"index": 1, "techniqueId": "tech-a", "verdict": "confirm", "reason": "ok"}]
    })


# ---------------------------------------------------------------------------
# MODEL_MAP additions
# ---------------------------------------------------------------------------

def test_model_map_has_opus5_and_sonnet5():
    assert llm_mod.MODEL_MAP["opus-5"] == "claude-opus-5"
    assert llm_mod.MODEL_MAP["sonnet-5"] == "claude-sonnet-5"


def test_model_map_existing_entries_unchanged():
    assert llm_mod.MODEL_MAP["sonnet"] == "claude-sonnet-4-6"
    assert llm_mod.MODEL_MAP["haiku"] == "claude-haiku-4-5-20251001"
    assert llm_mod.MODEL_MAP["opus"] == "claude-opus-4-8"


# ---------------------------------------------------------------------------
# _call_structured: strict -> non-strict retry, and the legacy text fallback
# chain (T3.3). These need an LLMExtractor instance (self.client/self.model),
# so they use the `extractor` fixture with a monkeypatched client — no real
# API calls occur.
# ---------------------------------------------------------------------------

def test_call_structured_retries_without_strict_on_bad_request(extractor):
    httpx = pytest.importorskip("httpx")
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = httpx.Response(400, request=req, json={
        "type": "error",
        "error": {"type": "invalid_request_error", "message": "strict is not supported"},
    })
    bad_request = anthropic.BadRequestError("strict is not supported", response=resp, body=None)

    calls = []
    success = FakeResponse([FakeToolUseBlock("record_techniques", {"matches": []})])

    def fake_create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise bad_request
        return success

    extractor.client.messages.create = fake_create

    payload, used_legacy, _response = extractor._call_structured(
        content_blocks=[{"type": "text", "text": "hello"}],
        tool_name="record_techniques",
        tool_schema=llm_mod.RECORD_TECHNIQUES_SCHEMA,
        tool_description="test",
        max_tokens=100,
        validator=llm_mod._validate_matches_payload,
    )

    assert payload == []
    assert used_legacy is False
    assert len(calls) == 2
    assert calls[0]["tools"][0]["strict"] is True
    assert "strict" not in calls[1]["tools"][0]
    # Retry uses the same tool name/schema, just without `strict`.
    assert calls[1]["tools"][0]["name"] == "record_techniques"
    assert calls[1]["tool_choice"] == {"type": "tool", "name": "record_techniques"}


def test_call_structured_falls_back_to_legacy_text_when_tool_use_missing(extractor):
    text_content = ('```json\n[{"techniqueId": "tech-rlhf", "confidence": "High", '
                     '"evidence": "quote", "reasoning": "why"}]\n```')
    fake_resp = FakeResponse([FakeTextBlock(text_content)])
    extractor.client.messages.create = lambda **kwargs: fake_resp

    payload, used_legacy, _response = extractor._call_structured(
        content_blocks=[{"type": "text", "text": "hello"}],
        tool_name="record_techniques",
        tool_schema=llm_mod.RECORD_TECHNIQUES_SCHEMA,
        tool_description="test",
        max_tokens=100,
        validator=llm_mod._validate_matches_payload,
    )

    assert used_legacy is True
    assert payload == [{"techniqueId": "tech-rlhf", "confidence": "High",
                         "evidence": "quote", "reasoning": "why"}]


def test_call_structured_total_failure_returns_none(extractor):
    fake_resp = FakeResponse([FakeTextBlock("not parseable as JSON, sorry")])
    extractor.client.messages.create = lambda **kwargs: fake_resp

    payload, used_legacy, _response = extractor._call_structured(
        content_blocks=[{"type": "text", "text": "hello"}],
        tool_name="record_techniques",
        tool_schema=llm_mod.RECORD_TECHNIQUES_SCHEMA,
        tool_description="test",
        max_tokens=100,
        validator=llm_mod._validate_matches_payload,
    )

    assert payload is None
    assert used_legacy is True


# ---------------------------------------------------------------------------
# End-to-end extract_techniques with a mocked client (T3.2 doc-block
# byte-identity across category calls + T3.3 structured parsing, combined).
# ---------------------------------------------------------------------------

def test_extract_techniques_category_batched_end_to_end(extractor):
    calls = []

    def fake_create(**kwargs):
        calls.append(kwargs)
        category_block_text = kwargs["messages"][0]["content"][1]["text"]
        if "tech-rlhf" in category_block_text:
            payload = {"matches": [{
                "techniqueId": "tech-rlhf",
                "confidence": "High",
                "evidence": "Document body mentioning RLHF training procedure.",
                "reasoning": "test fixture",
            }]}
        else:
            payload = {"matches": []}
        return FakeResponse([FakeToolUseBlock("record_techniques", payload)])

    extractor.client.messages.create = fake_create

    doc_text = "Document body mentioning RLHF training procedure. Nothing else notable."
    additions, deletions = extractor.extract_techniques("doc-test-e2e", doc_text, nlu_results=[])

    # One call per non-empty category (5 in the live taxonomy today).
    assert len(calls) == 5
    for c in calls:
        assert c["max_tokens"] == 8192
        assert c["tool_choice"] == {"type": "tool", "name": "record_techniques"}
        assert c["tools"][0]["strict"] is True

    # Block 1 (document context) must be byte-identical across every call —
    # built once and reused, so calls 2-5 can hit the prompt cache written by call 1.
    block1_texts = [c["messages"][0]["content"][0]["text"] for c in calls]
    assert all(t == block1_texts[0] for t in block1_texts)
    assert all(t is block1_texts[0] for t in block1_texts), "block 1 must be the same string object, not just equal"
    assert all(c["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"} for c in calls)
    # Block 2 (category-specific) must NOT carry cache_control.
    assert all("cache_control" not in c["messages"][0]["content"][1] for c in calls)
    # Block 2 varies by category (different techniques listed) — not identical across calls.
    block2_texts = [c["messages"][0]["content"][1]["text"] for c in calls]
    assert len(set(block2_texts)) == len(block2_texts)

    assert deletions == []
    assert len(additions) == 1
    assert additions[0]["techniqueId"] == "tech-rlhf"


def test_extract_techniques_single_call_mode_uses_one_call(extractor):
    extractor.single_call = True
    calls = []

    def fake_create(**kwargs):
        calls.append(kwargs)
        payload = {"matches": [{
            "techniqueId": "tech-rlhf",
            "confidence": "High",
            "evidence": "RLHF was used to train the model.",
            "reasoning": "test fixture",
        }]}
        return FakeResponse([FakeToolUseBlock("record_techniques", payload)])

    extractor.client.messages.create = fake_create

    doc_text = "RLHF was used to train the model."
    additions, deletions = extractor.extract_techniques("doc-test-single", doc_text, nlu_results=[])

    assert len(calls) == 1  # legacy path: one call for the whole document
    assert calls[0]["max_tokens"] == 4096
    # Single-call path sends one content block (no doc/category split).
    assert len(calls[0]["messages"][0]["content"]) == 1
    assert len(additions) == 1
    assert additions[0]["techniqueId"] == "tech-rlhf"
    assert deletions == []


def test_build_document_block_deterministic(extractor):
    block1 = extractor._build_document_block("doc-x", "some document text")
    block2 = extractor._build_document_block("doc-x", "some document text")
    assert block1 == block2
    assert "doc-x" in block1
    assert "some document text" in block1
