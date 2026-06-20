"""Canonical id resolution for techniques and models across taxonomy versions.

REFACTOR.md §3.4 (taxonomy drift) and WORKPLAN B.1.5. Set operations in the
evaluators (TP/FP/FN computation) compare technique ids between a fresh
automated run and a frozen ground truth that may have been authored under an
older taxonomy. If a technique was renamed or two techniques were merged, a raw
set comparison double-counts the same concept as both a false negative (old id
missing) and a false positive (new id unexpected), silently deflating metrics.

This module is the single source of truth for those renames/merges. Every value
(alias *target*) MUST be a currently-defined id; `assert_*_resolve` enforces that
in CI so a stale alias can't point at a deleted technique.

Aliases are intentionally conservative: only documented renames/merges go here,
NOT fuzzy synonyms. Adding an alias changes measured metrics, so each entry
should correspond to a real taxonomy edit recorded in git history.
"""

# --- Technique renames / merges (old id -> current canonical id) ---
# Sourced from the 2026-06-19 taxonomy reconciliation (incidents.json repoints,
# WORKPLAN B.0.5): three synonym pairs were collapsed onto a single canonical id.
TECHNIQUE_ALIASES = {
    "tech-content-watermarking": "tech-watermarking",
    "tech-hallucination-detection": "tech-hallucination-grounding",
    "tech-copyright-compliance": "tech-copyright-ip-violation",
}

# --- Model id renames (old id -> current canonical id) ---
# Fabricated Meta ids removed in WORKPLAN A.1; their evidence refs were repointed
# to the real Scout/Maverick checkpoints.
MODEL_ALIASES = {
    "llama-4-8b": "llama-4-scout",
    "llama-4-17b": "llama-4-maverick",
}


def canonical_technique(tech_id: str) -> str:
    """Resolve a (possibly legacy) technique id to its current canonical id.

    Resolution is single-hop by design — alias chains are disallowed so that the
    map stays auditable. If you rename A->B then later B->C, update the A entry to
    point at C directly rather than relying on transitive resolution.
    """
    return TECHNIQUE_ALIASES.get(tech_id, tech_id)


def canonical_techniques(tech_ids) -> set:
    """Canonicalize an iterable of technique ids into a set (dedupes merges)."""
    return {canonical_technique(t) for t in tech_ids}


def canonical_model(model_id: str) -> str:
    """Resolve a (possibly legacy) model id to its current canonical id."""
    return MODEL_ALIASES.get(model_id, model_id)


def assert_technique_aliases_resolve(valid_technique_ids) -> list:
    """Return alias targets that are NOT a currently-defined technique id.

    A non-empty result means the alias map has drifted from techniques.json and
    must be fixed; CI (check_integrity.py / tests) treats it as a hard failure.
    """
    valid = set(valid_technique_ids)
    return sorted({tgt for tgt in TECHNIQUE_ALIASES.values() if tgt not in valid})


def assert_model_aliases_resolve(valid_model_ids) -> list:
    """Return model alias targets that are NOT a currently-defined model id."""
    valid = set(valid_model_ids)
    return sorted({tgt for tgt in MODEL_ALIASES.values() if tgt not in valid})


def assert_no_alias_cycles() -> list:
    """Return alias *targets* that are themselves alias *keys* (chain detection).

    Single-hop resolution means a key appearing as another entry's target would be
    resolved inconsistently depending on traversal order. Keep the map flat.
    """
    bad = []
    for mapping in (TECHNIQUE_ALIASES, MODEL_ALIASES):
        keys = set(mapping)
        for tgt in mapping.values():
            if tgt in keys:
                bad.append(tgt)
    return sorted(set(bad))
