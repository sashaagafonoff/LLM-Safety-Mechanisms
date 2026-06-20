"""Shared evaluation primitives — the single source of truth for "what counts".

REFACTOR.md §3.2/§3.3 and WORKPLAN B.1.4. Before this module, three evaluators
(compare_taxonomy_runs.py, evaluate_nlu.py, ground_truth_analysis.py) each carried
their own subtly-different copy of "is this document reviewed?" and "what are its
active techniques?". Divergent definitions produced divergent metrics from the same
data. Everything here is imported by all evaluators so the definitions can't drift.

It also owns the blind-split loaders (WORKPLAN B.1.1/B.1.2): the holdout-id set used
to keep test documents out of the review index and the threshold tuners.

Pure stdlib — safe to import in CI without the ML stack.
"""
import json
from pathlib import Path

from taxonomy_aliases import canonical_technique

DATA = Path(__file__).resolve().parent.parent / "data"

MANUAL_CREATORS = ("manual", "sashaagafonoff")


def _load_json(name, default=None):
    p = DATA / name
    if not p.exists():
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# --- taxonomy universe ---

def load_techniques():
    return _load_json("techniques.json", []) or []


def technique_ids():
    return {t["id"] for t in load_techniques() if isinstance(t, dict) and "id" in t}


# --- document-level predicates (single definition, used everywhere) ---

def is_reviewed_document(entries) -> bool:
    """A document is 'reviewed' iff a human touched it: either it carries manual
    evidence, or a reviewer deactivated a technique (deleted_by is a real person,
    not the 'system' auto-merge). This is the union definition REFACTOR §3.2 calls
    for — matches evaluate_nlu/ground_truth_analysis/_build_review_index exactly.
    """
    for e in entries:
        if not e.get("active", True) and e.get("deleted_by") not in (None, "system"):
            return True
        for ev in e.get("evidence", []) or []:
            if isinstance(ev, dict) and ev.get("created_by") in MANUAL_CREATORS:
                return True
    return False


def active_technique_set(entries, canonicalize: bool = True) -> set:
    """The canonical 'active techniques' set for one document's entry list.

    A technique counts as active iff the entry-level `active` flag is true AND it
    has at least one active evidence item (legacy string evidence and empty
    evidence are treated as active). Ids are canonicalized through the alias map
    (B.1.5) by default so renamed/merged techniques don't double-count in set ops.
    """
    active = set()
    for tech in entries:
        if not tech.get("active", True):
            continue
        evidence = tech.get("evidence", []) or []
        has_active_evidence = False
        for ev in evidence:
            if isinstance(ev, dict):
                if ev.get("active", True):
                    has_active_evidence = True
                    break
            else:  # legacy string evidence — assume active
                has_active_evidence = True
                break
        if has_active_evidence or not evidence:
            tid = tech.get("techniqueId")
            if tid:
                active.add(canonical_technique(tid) if canonicalize else tid)
    return active


def grounded_active_set(entries, canonicalize: bool = True) -> set:
    """Active techniques whose detection is backed by a real source quote.

    REFACTOR §3.3 grounded-precision. A technique qualifies only if it is active
    AND carries at least one active evidence item with non-empty `text` that is not
    flagged `grounding_failed` (the B.0.2 hard grounding gate). Legacy string
    evidence is treated as grounded (it is a verbatim source snippet). Entries with
    no evidence do NOT qualify — there is nothing to ground them.
    """
    grounded = set()
    for tech in entries:
        if not tech.get("active", True):
            continue
        ok = False
        for ev in tech.get("evidence", []) or []:
            if isinstance(ev, dict):
                if ev.get("active", True) and ev.get("text") and not ev.get("grounding_failed"):
                    ok = True
                    break
            elif str(ev).strip():
                ok = True
                break
        if ok:
            tid = tech.get("techniqueId")
            if tid:
                grounded.add(canonical_technique(tid) if canonicalize else tid)
    return grounded


def techniques_by_source(entries, canonicalize: bool = True) -> dict:
    """Active technique ids grouped by evidence source (nlu/llm/manual/legacy).

    Used for per-source recall (which source originally found a missed technique).
    """
    by_source = {"nlu": set(), "llm": set(), "manual": set(), "legacy": set()}
    for tech in entries:
        if not tech.get("active", True):
            continue
        tid = tech.get("techniqueId")
        if not tid:
            continue
        if canonicalize:
            tid = canonical_technique(tid)
        evidence = tech.get("evidence", []) or []
        sources = set()
        for ev in evidence:
            if isinstance(ev, dict):
                if ev.get("active", True):
                    sources.add(ev.get("created_by", "legacy"))
            else:
                sources.add("legacy")
        # Mirror active_technique_set EXACTLY: empty evidence counts as active
        # (legacy bucket); evidence that exists but is all-inactive does NOT, so a
        # technique appears here iff it would appear in active_technique_set.
        if not evidence:
            sources = {"legacy"}
        if not sources:
            continue
        for source in sources:
            by_source.setdefault(source, set()).add(tid)
    return by_source


# --- no-safety-content flags (excluded from FP-only precision distortion) ---

def load_no_safety_flags() -> set:
    """Doc ids explicitly flagged no_safety_content in evidence.json."""
    data = _load_json("evidence.json", {}) or {}
    flagged = set()
    for source in data.get("sources", []) or []:
        meta = source.get("content_metadata", {}) or {}
        if meta.get("no_safety_content", False):
            doc_id = source.get("id")
            if doc_id:
                flagged.add(doc_id)
    return flagged


# --- blind split loaders (B.1.1 / B.1.2) ---

def load_split(split: str) -> list:
    """Return the ordered doc-id list for 'test' or 'dev' from data/eval/.

    Returns [] if the split file does not exist yet (split not frozen) — callers
    must treat an empty test split as 'no blind evaluation available', not 'all
    docs'. See make_eval_split.py.
    """
    if split not in ("test", "dev"):
        raise ValueError(f"split must be 'test' or 'dev', got {split!r}")
    payload = _load_json(f"eval/{split}_split.json")
    if not payload:
        return []
    return list(payload.get("doc_ids", []))


def load_holdout_ids() -> set:
    """The frozen blind-test doc ids that MUST be quarantined from any tuning.

    Read by `_build_review_index` (few-shot quarantine) and the threshold
    calibrator. Returns an empty set when the split has not been frozen yet, so
    quarantine is a safe no-op until make_eval_split.py runs.
    """
    payload = _load_json("eval_holdout_ids.json")
    if not payload:
        return set()
    if isinstance(payload, dict):
        return set(payload.get("holdout_ids", []))
    return set(payload)  # tolerate a bare list


# --- metric helpers (one definition, used by every report) ---

def confusion(detected: set, gold: set):
    """(tp, fp, fn) as sets, from a detected set and a gold set."""
    detected, gold = set(detected), set(gold)
    return detected & gold, detected - gold, gold - detected


def prf(tp: int, fp: int, fn: int):
    """(precision, recall, f1). Zero denominators -> 0.0 (not NaN) for stable reports."""
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1
