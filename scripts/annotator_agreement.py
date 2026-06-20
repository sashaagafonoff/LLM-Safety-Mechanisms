#!/usr/bin/env python3
"""Inter-annotator agreement (Cohen's / Fleiss' kappa) for the gold labels.

WORKPLAN B.1.1 / REFACTOR §3.1. A blind gold set is only trustworthy if its
labels are reliable, which requires >=2 independent annotators and a measured
kappa. This corpus currently has a single annotator, so kappa is undefined — but
the capability lives here and activates the moment a second annotation file is
added, with NO fabricated number in the meantime.

Inputs: one JSON file per annotator at `data/eval/annotations/<name>.json`, each
mapping `{doc_id: [techniqueId, ...]}` (the techniques that annotator marks active
for that document). Only documents labelled by *every* annotator are scored.

Item universe (documented choice): the set of (doc, technique) pairs that **any**
annotator marked for the scored documents. Each annotator's rating on an item is
present(1)/absent(0). This measures agreement over the *proposed* label space
rather than the full doc x technique grid (which would be dominated by trivially-
agreed absent cells and inflate kappa).

Technique ids are canonicalized through the alias map before comparison.

Usage:
    python scripts/annotator_agreement.py
    python scripts/annotator_agreement.py --docs test   # restrict to blind test split
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from taxonomy_aliases import canonical_technique  # noqa: E402
from eval_common import load_split  # noqa: E402

ANNO_DIR = Path(__file__).resolve().parent.parent / "data" / "eval" / "annotations"


def load_annotations():
    if not ANNO_DIR.exists():
        return {}
    out = {}
    for p in sorted(ANNO_DIR.glob("*.json")):
        with open(p, encoding="utf-8") as f:
            raw = json.load(f)
        out[p.stem] = {
            doc: {canonical_technique(t) for t in techs}
            for doc, techs in raw.items()
        }
    return out


def cohen_kappa(items, r1, r2):
    """Binary Cohen's kappa over present/absent labels for two annotators."""
    a = b = c = d = 0
    for it in items:
        x, y = it in r1, it in r2
        if x and y:
            a += 1
        elif x and not y:
            b += 1
        elif not x and y:
            c += 1
        else:
            d += 1
    n = a + b + c + d
    if n == 0:
        return None, 0.0, 0.0, 0
    po = (a + d) / n
    pe = ((a + b) / n) * ((a + c) / n) + ((c + d) / n) * ((b + d) / n)
    kappa = (po - pe) / (1 - pe) if (1 - pe) else 1.0
    return kappa, po, pe, n


def fleiss_kappa(items, raters):
    """Binary Fleiss' kappa over present/absent labels for >=2 annotators."""
    n = len(raters)
    if n < 2 or not items:
        return None, 0.0, 0.0, 0
    N = len(items)
    sum_Pi = 0.0
    total_present = 0
    for it in items:
        present = sum(1 for r in raters if it in r)
        absent = n - present
        total_present += present
        sum_Pi += (present * present + absent * absent - n) / (n * (n - 1))
    Pbar = sum_Pi / N
    p_present = total_present / (N * n)
    Pe = p_present ** 2 + (1 - p_present) ** 2
    kappa = (Pbar - Pe) / (1 - Pe) if (1 - Pe) else 1.0
    return kappa, Pbar, Pe, N


def interpret(k):
    if k is None:
        return "n/a"
    if k < 0:
        return "worse than chance"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    return "almost perfect"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--docs", choices=["all", "test", "dev"], default="all",
                    help="restrict scoring to a split (default: all co-labelled docs)")
    args = ap.parse_args()

    annos = load_annotations()
    print("=" * 64)
    print("INTER-ANNOTATOR AGREEMENT (kappa)")
    print("=" * 64)
    print(f"Annotation files found: {len(annos)}  ({', '.join(annos) or 'none'})")

    if len(annos) < 2:
        print("\nkappa is UNDEFINED with fewer than 2 annotators.")
        print(f"Add a second file under {ANNO_DIR} as <name>.json")
        print('mapping {"doc_id": ["techniqueId", ...]} to activate this metric.')
        print("Until then, treat all reported precision/recall as single-rater.")
        return 0

    # documents every annotator labelled
    common_docs = set.intersection(*[set(a.keys()) for a in annos.values()])
    if args.docs in ("test", "dev"):
        common_docs &= set(load_split(args.docs))
    common_docs = sorted(common_docs)
    if not common_docs:
        print("\nNo documents are labelled by all annotators for this scope.")
        return 0

    # item universe: (doc, tech) any annotator marked, on the common docs
    items = set()
    for a in annos.values():
        for doc in common_docs:
            for t in a.get(doc, set()):
                items.add((doc, t))
    items = sorted(items)

    rater_sets = []
    for a in annos.values():
        s = set()
        for doc in common_docs:
            for t in a.get(doc, set()):
                s.add((doc, t))
        rater_sets.append(s)

    print(f"Scored documents: {len(common_docs)} ({args.docs})")
    print(f"Label items (proposed (doc,technique) pairs): {len(items)}")

    if len(annos) == 2:
        k, po, pe, n = cohen_kappa(items, rater_sets[0], rater_sets[1])
        print(f"\nCohen's kappa = {k:.3f}  ({interpret(k)})")
        print(f"  observed agreement={po:.3f}  expected={pe:.3f}  items={n}")
    else:
        k, pbar, pe, n = fleiss_kappa(items, rater_sets)
        print(f"\nFleiss' kappa = {k:.3f}  ({interpret(k)})  raters={len(annos)}")
        print(f"  mean agreement={pbar:.3f}  expected={pe:.3f}  items={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
