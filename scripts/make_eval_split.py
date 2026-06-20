#!/usr/bin/env python3
"""Freeze a deterministic, stratified blind train/test split (WORKPLAN B.1.1).

The reliability defect Phase 1 fixes: the same ~35 reviewed documents are used to
tune NLU thresholds, to seed the LLM few-shot review index, AND to report
precision/recall. Any number produced that way is optimistic by construction.

This script carves the frozen ground truth (model_technique_map_reviewed.json) into
two disjoint, version-controlled sets:

  * data/eval/dev_split.json   — documents the pipeline MAY learn from
                                 (threshold calibration, few-shot examples).
  * data/eval/test_split.json  — BLIND documents, reported on exactly once.
  * data/eval_holdout_ids.json — the test ids, in the shape the tuners read to
                                 quarantine them (eval_common.load_holdout_ids).
  * data/eval/split_manifest.json — provenance: protocol, fraction, per-family
                                 breakdown, and a sha256 of the gold key set so
                                 corpus drift invalidates the split loudly.

Determinism: selection is by sorted id within each provider family — no RNG, no
timestamp embedded — so re-running reproduces the committed files byte-for-byte.
`--check` verifies the on-disk split still matches (CI guard).

Usage:
    python scripts/make_eval_split.py            # write/refresh the split
    python scripts/make_eval_split.py --fraction 0.3
    python scripts/make_eval_split.py --check    # verify on-disk == regenerated
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
GOLD_PATH = DATA / "model_technique_map_reviewed.json"
EVAL_DIR = DATA / "eval"

# Ordered (prefix-substring -> family) rules. First match wins; a doc id is tested
# against these in order, so put more-specific prefixes before generic ones.
FAMILY_RULES = [
    ("anthropic", "anthropic"), ("claude", "anthropic"),
    ("gpt", "openai"), ("o3", "openai"), ("o4", "openai"), ("openai", "openai"),
    ("gemini", "google"), ("google", "google"),
    ("llama", "meta"), ("meta", "meta"),
    ("phi", "microsoft"), ("microsoft", "microsoft"), ("mai-", "microsoft"),
    ("deepseek", "deepseek"),
    ("mistral", "mistral"), ("pixtral", "mistral"), ("magistral", "mistral"),
    ("ministral", "mistral"),
    ("qwen", "alibaba"),
    ("grok", "xai"), ("xai", "xai"),
    ("cohere", "cohere"), ("command", "cohere"),
    ("nemotron", "nvidia"), ("nvidia", "nvidia"),
    ("hunyuan", "tencent"), ("tencent", "tencent"),
    ("falcon", "tii"),
    ("nova", "amazon"), ("aws", "amazon"), ("amazon", "amazon"),
]


def family_of(doc_id: str) -> str:
    low = doc_id.lower()
    for prefix, fam in FAMILY_RULES:
        if low.startswith(prefix):
            return fam
    return "other"


def gold_doc_ids() -> list:
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold = json.load(f)
    return sorted(gold.keys())


def gold_sha256(doc_ids) -> str:
    h = hashlib.sha256()
    h.update("\n".join(sorted(doc_ids)).encode("utf-8"))
    return h.hexdigest()


def stratified_split(doc_ids, fraction: float):
    """Return (dev_ids, test_ids, per_family) deterministically.

    Within each family (sorted), the first round(fraction*n) docs go to TEST.
    Families of size 1 contribute 0 test docs (kept whole in dev) — acceptable;
    they're too small to stratify. No randomness: stable across reruns.
    """
    by_family = {}
    for d in doc_ids:
        by_family.setdefault(family_of(d), []).append(d)

    dev, test, per_family = [], [], {}
    for fam in sorted(by_family):
        members = sorted(by_family[fam])
        n = len(members)
        k = round(fraction * n)  # banker's rounding; deterministic for fixed input
        fam_test = members[:k]
        fam_dev = members[k:]
        test.extend(fam_test)
        dev.extend(fam_dev)
        per_family[fam] = {"n": n, "test": fam_test, "dev": fam_dev}
    return sorted(dev), sorted(test), per_family


def build_payloads(fraction: float):
    ids = gold_doc_ids()
    dev, test, per_family = stratified_split(ids, fraction)
    sha = gold_sha256(ids)
    manifest = {
        "protocol": (
            "Deterministic stratified holdout over model_technique_map_reviewed.json. "
            "TEST documents are blind: never used for threshold calibration, few-shot "
            "seeding, or the review index. Selection is by sorted id within each "
            "provider family (no RNG); regenerating with the same gold set reproduces "
            "these files exactly. If gold_sha256 changes, the split is stale and must "
            "be re-frozen and re-reviewed."
        ),
        "fraction_test": fraction,
        "gold_sha256": sha,
        "counts": {"gold": len(ids), "dev": len(dev), "test": len(test)},
        "per_family": per_family,
    }
    dev_payload = {"split": "dev", "gold_sha256": sha, "doc_ids": dev}
    test_payload = {"split": "test", "gold_sha256": sha, "doc_ids": test}
    holdout_payload = {
        "description": "Blind test doc ids quarantined from all tuning (WORKPLAN B.1.2).",
        "gold_sha256": sha,
        "holdout_ids": test,
    }
    return manifest, dev_payload, test_payload, holdout_payload


def _dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_split(fraction: float):
    manifest, dev_p, test_p, holdout_p = build_payloads(fraction)
    _dump(EVAL_DIR / "split_manifest.json", manifest)
    _dump(EVAL_DIR / "dev_split.json", dev_p)
    _dump(EVAL_DIR / "test_split.json", test_p)
    _dump(DATA / "eval_holdout_ids.json", holdout_p)
    print("Froze blind split:")
    print(f"  gold={manifest['counts']['gold']} dev={manifest['counts']['dev']} "
          f"test={manifest['counts']['test']} (fraction_test={fraction})")
    print(f"  gold_sha256={manifest['gold_sha256'][:16]}...")
    print("  per-family test/dev:")
    for fam, info in sorted(manifest["per_family"].items()):
        print(f"    {fam:<12} n={info['n']:>2}  test={len(info['test'])} dev={len(info['dev'])}")
    return 0


def check_split(fraction: float) -> int:
    manifest, dev_p, test_p, holdout_p = build_payloads(fraction)
    want = {
        EVAL_DIR / "split_manifest.json": manifest,
        EVAL_DIR / "dev_split.json": dev_p,
        EVAL_DIR / "test_split.json": test_p,
        DATA / "eval_holdout_ids.json": holdout_p,
    }
    problems = []
    for path, expected in want.items():
        if not path.exists():
            problems.append(f"missing: {path}")
            continue
        with open(path, encoding="utf-8") as f:
            on_disk = json.load(f)
        if on_disk != expected:
            problems.append(f"stale (regenerate): {path}")
    # invariants
    test, dev = set(test_p["doc_ids"]), set(dev_p["doc_ids"])
    if test & dev:
        problems.append(f"test/dev overlap: {sorted(test & dev)}")
    if (test | dev) != set(gold_doc_ids()):
        problems.append("test ∪ dev != gold key set")
    if problems:
        print("✗ split check failed:")
        for p in problems:
            print(f"   - {p}")
        return 1
    print(f"✓ split is current and disjoint (dev={len(dev)}, test={len(test)}).")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fraction", type=float, default=0.30,
                    help="target proportion of each family held out as blind test")
    ap.add_argument("--check", action="store_true",
                    help="verify on-disk split matches regeneration (CI guard)")
    args = ap.parse_args()
    if not 0.0 < args.fraction < 1.0:
        ap.error("--fraction must be in (0, 1)")
    return check_split(args.fraction) if args.check else write_split(args.fraction)


if __name__ == "__main__":
    sys.exit(main())
