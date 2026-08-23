"""
Model-mention matcher for AIID incident ingestion (T5.3, Track C,
docs/workplan/2026-08-execution-plan.md).

Builds a conservative alias table from data/models.json and matches those
aliases against incident title+description text, producing `modelIds` for
data/incidents.json. Precision is prioritized over recall throughout:

- An alias is only usable if it contains a digit OR has >= 2 words -- a bare
  single common word ("Nova", "Grok", "Claude", "Command", ...) is never a
  usable alias by itself, even for models whose real name is that short
  (see ``is_usable_alias`` / ``BLOCKLIST_STANDALONE``).
- A model is only assigned to an incident if the model's provider is already
  present in the incident's matched ``providerIds``. This keeps the model
  link referentially *and* semantically consistent with the provider match
  rather than running an independent (weaker) text matcher.
- Matching is case-insensitive with regex word boundaries. When multiple
  candidate aliases overlap the same text span, the longest alias wins (e.g.
  "Grok 4.3" beats "Grok 4" for the text "...announced Grok 4.3 today...",
  since "Grok 4" would otherwise also satisfy \\b...\\b inside "Grok 4.3").

Also exposes a lightweight "notable unmatched" detector: model-shaped
mentions (a known provider brand word + optional capitalized word + a
version-looking number, e.g. "Claude Mythos 5", "Claude Opus 4.1") that do
NOT fall inside a span already explained by a real model alias. These are
reported for human review -- never auto-added to models.json.
"""
import re

# --- Safety / blocklist ---

# Standalone alias values that are never usable on their own, even though a
# few of them could theoretically pass the digit-or-two-words rule via some
# future version string. Defensive belt-and-suspenders on top of that rule,
# and explicit for the family/tier words called out in the design brief.
BLOCKLIST_STANDALONE = {
    "nova", "command", "phi", "grok", "claude", "gemini", "gpt", "llama",
    "mistral", "qwen", "falcon", "nemotron", "hunyuan", "deepseek",
    "pixtral", "ministral", "magistral", "codestral", "qwq",
    "opus", "sonnet", "haiku", "pro", "plus", "max", "mini", "flash",
    "lite", "large", "medium", "small", "turbo", "thinking", "instruct",
    "chat", "coder", "reasoning", "vision", "translate", "fast", "next",
    "preview", "omni", "nano",
}

# Hand-curated extra aliases beyond what's mechanically derived from the
# `version` field -- known alternate spellings / historical naming that
# don't fall out of the generic separator/order rules below.
MODEL_ALIAS_EXTRAS = {
    "gpt-4o": ["ChatGPT-4o", "GPT4o"],
    "claude-3-5-sonnet": ["Claude Sonnet 3.5"],
    "claude-3-opus": ["Claude Opus 3"],
    "gemini-1-5-pro": ["Gemini-1.5-Pro"],
    "command-r-plus-08-2024": ["Command R+"],
    "command-r-08-2024": ["Command R"],
}

# Brand words used only for the "notable unmatched" heuristic below -- never
# used to assign a modelId by themselves (they're exactly the words
# BLOCKLIST_STANDALONE exists to keep out of the real alias table).
PROVIDER_BRAND_WORDS = {
    "anthropic": ["Claude"],
    "openai": ["GPT", "ChatGPT"],
    "google": ["Gemini"],
    "meta": ["Llama"],
    "amazon": ["Nova"],
    "microsoft": ["Phi", "MAI"],
    "nvidia": ["Nemotron"],
    "xai": ["Grok"],
    "alibaba": ["Qwen"],
    "tencent": ["Hunyuan"],
    "deepseek": ["DeepSeek"],
    "cohere": ["Command"],
    "mistral": ["Mistral", "Magistral", "Ministral", "Pixtral", "Codestral"],
    "tii": ["Falcon"],
}


def is_usable_alias(alias: str) -> bool:
    """Precision gate: digit OR >=2 words, and never a bare blocklisted word."""
    a = alias.strip()
    if not a:
        return False
    words = a.split()
    has_digit = any(ch.isdigit() for ch in a)
    if not has_digit and len(words) < 2:
        return False
    if len(words) == 1 and a.lower() in BLOCKLIST_STANDALONE:
        return False
    return True


def _hyphen_space_variants(s: str) -> set:
    variants = {s}
    if "-" in s:
        variants.add(s.replace("-", " "))
    if " " in s:
        variants.add(s.replace(" ", "-"))
    return variants


def _dot_hyphen_variants(s: str) -> set:
    """'4.7' <-> '4-7' within a token (e.g. mistral-medium-3-5-26-04 style ids)."""
    variants = {s}
    swapped = re.sub(r"(?<=\d)\.(?=\d)", "-", s)
    if swapped != s:
        variants.add(swapped)
    return variants


def _tier_version_swap(s: str) -> set:
    """'Claude Opus 4.7' <-> 'Claude 4.7 Opus' (old- vs new-style Claude naming).

    Only fires on a clean 3-token '<family> <tier> <version>' shape where
    exactly one of the last two tokens carries a digit -- e.g. it will not
    mis-fire on 'Amazon Nova 2 Lite' (4 tokens) or 'Nova Pro' (neither token
    has a digit).
    """
    tokens = s.split()
    variants = set()
    if len(tokens) == 3:
        fam, a, b = tokens
        a_digit = any(ch.isdigit() for ch in a)
        b_digit = any(ch.isdigit() for ch in b)
        if a_digit != b_digit:
            variants.add(f"{fam} {b} {a}")
    return variants


def generate_aliases(model: dict) -> set:
    """Generate candidate alias strings for one models.json entry.

    Pure function: given a model dict (needs 'id', 'version'; 'provider' is
    read by callers, not here), returns the set of alias strings usable for
    matching (already filtered through is_usable_alias). Combines the
    version field with separator variants (dot/hyphen/space) and, where the
    shape allows it, a tier/version-order swap, plus any hand-curated
    MODEL_ALIAS_EXTRAS for this id.
    """
    version = (model.get("version") or "").strip()
    seeds = {version} if version else set()
    seeds |= _tier_version_swap(version)

    aliases = set()
    for seed in seeds:
        for v1 in _hyphen_space_variants(seed):
            aliases.update(_dot_hyphen_variants(v1))

    for extra in MODEL_ALIAS_EXTRAS.get(model.get("id", ""), []):
        aliases.add(extra)

    return {a for a in aliases if is_usable_alias(a)}


def build_alias_table(models: list) -> list:
    """Build match entries for every usable alias of every model.

    `models` is the raw list from models.json (each dict has at least
    id/provider/version). Returns a list of dicts:
    {"pattern": compiled regex, "alias": str, "model_id": str, "provider": str}
    """
    table = []
    for m in models:
        mid = m.get("id")
        provider = m.get("provider")
        if not mid or not provider:
            continue
        for alias in generate_aliases(m):
            table.append({
                "pattern": re.compile(r"\b" + re.escape(alias) + r"\b", re.IGNORECASE),
                "alias": alias,
                "model_id": mid,
                "provider": provider,
            })
    return table


def _scan_alias_matches(text: str, alias_table: list, provider_ids) -> list:
    """Longest-alias-first scan; returns accepted (start, end, model_id) hits.

    Candidates are restricted to models whose provider is in `provider_ids`
    (the incident's already-matched providerIds). Overlapping shorter
    aliases are suppressed once a longer alias has claimed a span, so e.g.
    'Grok 4' does not also fire inside an already-matched 'Grok 4.3'.
    """
    provider_ids = set(provider_ids or ())
    if not provider_ids:
        return []
    candidates = [e for e in alias_table if e["provider"] in provider_ids]
    candidates.sort(key=lambda e: len(e["alias"]), reverse=True)

    claimed = []  # accepted (start, end) spans, longest-first order
    accepted = []
    for entry in candidates:
        for m in entry["pattern"].finditer(text):
            start, end = m.span()
            if any(start < c_end and end > c_start for c_start, c_end in claimed):
                continue
            claimed.append((start, end))
            accepted.append((start, end, entry["model_id"]))
    return accepted


def match_models(text: str, alias_table: list, provider_ids) -> list:
    """Match model aliases in `text`, gated to models whose provider is
    already in `provider_ids`. Returns a sorted, deduped list of model ids.
    """
    hits = _scan_alias_matches(text, alias_table, provider_ids)
    return sorted({model_id for _, _, model_id in hits})


def find_notable_unmatched(text: str, provider_ids, alias_table: list) -> set:
    """Model-shaped mentions for an already-matched provider that don't
    correspond to any models.json alias -- reported, never auto-added.

    Looks for '<brand word> [CapitalizedWord] <version number>' shapes
    (e.g. "Claude Mythos 5", "Claude Opus 4.1") using the small hand-curated
    PROVIDER_BRAND_WORDS table, then discards any hit whose span overlaps a
    span already explained by a real, matched model alias.
    """
    provider_ids = set(provider_ids or ())
    if not provider_ids:
        return set()

    known_spans = [(s, e) for s, e, _ in _scan_alias_matches(text, alias_table, provider_ids)]

    hits = set()
    for provider in provider_ids:
        for brand in PROVIDER_BRAND_WORDS.get(provider, []):
            pattern = re.compile(
                rf"\b{re.escape(brand)}(?:\s+[A-Z][a-zA-Z]+)?\s+\d+(?:\.\d+)*\b"
            )
            for m in pattern.finditer(text):
                span = m.span()
                if any(span[0] < c_end and span[1] > c_start for c_start, c_end in known_spans):
                    continue
                hits.add(m.group().strip())
    return hits
