#!/usr/bin/env python3
"""Referential-integrity checker for the dataset (REFACTOR.md §4.2).

Validates that every cross-reference between the data files resolves to a defined
entity (providers, models, techniques, categories, risk areas, lifecycle stages,
standards frameworks). Exits non-zero if any dangling reference is found, so it
can gate CI before a commit.

Usage:
    python scripts/check_integrity.py
    python scripts/check_integrity.py --quiet
"""
import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from taxonomy_aliases import (  # noqa: E402
    assert_technique_aliases_resolve, assert_model_aliases_resolve, assert_no_alias_cycles,
)

DATA = Path("data")


def load(name):
    p = DATA / name
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def ids_of(obj):
    """Collect 'id' values from a list of dicts, or a dict-of-dicts/lists."""
    out = set()
    if isinstance(obj, list):
        for x in obj:
            if isinstance(x, dict) and "id" in x:
                out.add(x["id"])
    elif isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, dict) and "id" in v:
                out.add(v["id"])
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, dict) and "id" in x:
                        out.add(x["id"])
    return out


def collect_model_refs(evidence):
    refs = set()

    def walk(o):
        if isinstance(o, list):
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            if isinstance(o.get("modelId"), str):
                refs.add(o["modelId"])
            for v in o.values():
                walk(v)

    walk(evidence)
    return refs


def as_list(obj, key=None):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        if key and isinstance(obj.get(key), list):
            return obj[key]
        for v in obj.values():
            if isinstance(v, list):
                return v
    return []


def check(quiet=False):
    """Run all referential-integrity checks. Returns 0 if clean, 1 otherwise.

    Importable so scripts/validate.py can run integrity as part of one umbrella
    validation command without shelling out.
    """
    providers = load("providers.json") or []
    models = load("models.json") or {"models": []}
    techniques = load("techniques.json") or []
    categories = load("categories.json") or []
    risk_areas = load("risk_areas.json") or []
    lifecycle = load("model_lifecycle.json")
    standards = load("standards.json") or []
    standards_mapping = load("standards_mapping.json")
    commentary = load("commentary.json")
    incidents = load("incidents.json")
    mt_map = load("model_technique_map.json") or {}
    evidence = load("evidence.json")

    model_list = as_list(models, "models")
    provider_ids = {p["id"] for p in providers if isinstance(p, dict) and "id" in p}
    model_ids = {m["id"] for m in model_list if isinstance(m, dict) and "id" in m}
    technique_ids = {t["id"] for t in techniques if isinstance(t, dict) and "id" in t}
    category_ids = {c["id"] for c in categories if isinstance(c, dict) and "id" in c}
    risk_ids = ids_of(risk_areas)
    lifecycle_ids = ids_of(lifecycle) if lifecycle is not None else set()
    framework_ids = ids_of(standards)

    v = defaultdict(list)

    for m in model_list:
        if m.get("provider") not in provider_ids:
            v["model.provider"].append(f"{m.get('id')} -> {m.get('provider')}")

    for t in techniques:
        if t.get("categoryId") not in category_ids:
            v["technique.categoryId"].append(f"{t.get('id')} -> {t.get('categoryId')}")
        for r in t.get("riskAreaIds", []) or []:
            if r not in risk_ids:
                v["technique.riskAreaId"].append(f"{t.get('id')} -> {r}")
        for s in t.get("lifecycleStages", []) or []:
            if lifecycle_ids and s not in lifecycle_ids:
                v["technique.lifecycleStage"].append(f"{t.get('id')} -> {s}")

    for e in as_list(standards_mapping):
        if e.get("techniqueId") not in technique_ids:
            v["standards_mapping.techniqueId"].append(e.get("techniqueId"))
        if framework_ids and e.get("frameworkId") not in framework_ids:
            v["standards_mapping.frameworkId"].append(e.get("frameworkId"))

    for c in as_list(commentary):
        for tid in c.get("techniqueIds", []) or []:
            if tid not in technique_ids:
                v["commentary.techniqueId"].append(tid)

    for inc in as_list(incidents):
        for tid in inc.get("techniqueIds", []) or []:
            if tid not in technique_ids:
                v["incident.techniqueId"].append(tid)
        for pid in inc.get("providerIds", []) or []:
            if pid not in provider_ids:
                v["incident.providerId"].append(pid)
        for mid in inc.get("modelIds", []) or []:
            if mid not in model_ids:
                v["incident.modelId"].append(mid)
        for r in inc.get("riskAreaIds", []) or []:
            if r not in risk_ids:
                v["incident.riskAreaId"].append(r)

    if isinstance(mt_map, dict):
        for doc_id, techs in mt_map.items():
            if isinstance(techs, list):
                for t in techs:
                    if isinstance(t, dict) and t.get("techniqueId") not in technique_ids:
                        v["map.techniqueId"].append(f"{doc_id}: {t.get('techniqueId')}")

    if evidence is not None:
        for mid in collect_model_refs(evidence):
            if mid not in model_ids:
                v["evidence.modelId"].append(mid)

    # Alias-map integrity (B.1.5): every alias target must be a live id; no chains.
    for tgt in assert_technique_aliases_resolve(technique_ids):
        v["alias.technique_target"].append(tgt)
    for tgt in assert_model_aliases_resolve(model_ids):
        v["alias.model_target"].append(tgt)
    for tgt in assert_no_alias_cycles():
        v["alias.cycle"].append(tgt)

    # Blind-split freshness (B.1.1): manifest gold_sha256 must match the current
    # gold key set, else the held-out test docs no longer line up with the corpus.
    manifest = load("eval/split_manifest.json")
    if manifest is not None and isinstance(mt_reviewed := load("model_technique_map_reviewed.json"), dict):
        cur = hashlib.sha256("\n".join(sorted(mt_reviewed.keys())).encode("utf-8")).hexdigest()
        if manifest.get("gold_sha256") != cur:
            v["split.stale"].append("split_manifest.gold_sha256 != gold key set (run make_eval_split.py)")

    total = sum(len(items) for items in v.values())
    print("=" * 60)
    print("REFERENTIAL INTEGRITY CHECK")
    print("=" * 60)
    print(f"providers={len(provider_ids)} models={len(model_ids)} techniques={len(technique_ids)} "
          f"categories={len(category_ids)} risk_areas={len(risk_ids)} "
          f"frameworks={len(framework_ids)} lifecycle={len(lifecycle_ids)}")
    if not total:
        print("✓ No dangling references found.")
        return 0
    print(f"✗ {total} dangling reference(s) across {len(v)} check(s):\n")
    for chk, items in sorted(v.items()):
        counts = Counter(items)
        print(f"  [{chk}] {len(items)} ref(s), {len(counts)} distinct:")
        if not quiet:
            for val, n in counts.most_common():
                print(f"      {n:>5}x  {val}")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    return check(quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
