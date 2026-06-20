#!/usr/bin/env python3
"""Umbrella dataset validator (WORKPLAN B.2.1, REFACTOR §4.1/§3.8).

Two layers, run together:

  1. SCHEMA  — validate each data/*.json against its draft-2020-12 schema in
     schema/llm-safety-v1.1.0.json ($defs ending in '_file'). Catches structural
     drift, wrong types, missing required fields, and out-of-vocabulary enums
     (provider/model status, evidence type, relationship, sentiment, severity, and
     the `created_by` provenance enum on technique-map evidence).

  2. REFS    — referential integrity across files (foreign keys), delegated to
     check_integrity.check() so there is exactly one implementation.

Exit code is non-zero if EITHER layer fails, so it is a single CI gate command.
Schema validation needs `jsonschema`; if it is absent, that layer is skipped with
a loud warning and only REFS run (CI installs jsonschema, so it normally runs both).

Usage:
    python scripts/validate.py
    python scripts/validate.py --quiet
    python scripts/validate.py --schema-only
    python scripts/validate.py --refs-only
    python scripts/validate.py --max-errors 5
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMA_PATH = ROOT / "schema" / "llm-safety-v1.1.0.json"

# data file -> the $defs entry describing the whole file
FILE_MAP = {
    "providers.json": "providers_file",
    "models.json": "models_file",
    "categories.json": "categories_file",
    "risk_areas.json": "risk_areas_file",
    "model_lifecycle.json": "model_lifecycle_file",
    "techniques.json": "techniques_file",
    "standards.json": "standards_file",
    "standards_mapping.json": "standards_mapping_file",
    "evidence.json": "evidence_file",
    "commentary.json": "commentary_file",
    "incidents.json": "incidents_file",
    "model_technique_map.json": "model_technique_map_file",
}


def load_bundle():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _fmt_error(e):
    loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
    msg = e.message
    if len(msg) > 200:
        msg = msg[:197] + "..."
    return f"{loc}: {msg}"


def validate_file(bundle, data, defname, max_errors=20):
    """Return a list of formatted schema-error strings for `data` (empty == valid).

    Pure given a loaded bundle + data, so unit tests can exercise it with synthetic
    inputs. Requires jsonschema; raises ImportError if unavailable.
    """
    from jsonschema import Draft202012Validator

    schema = {"$ref": f"#/$defs/{defname}", "$defs": bundle["$defs"]}
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    out = [_fmt_error(e) for e in errors[:max_errors]]
    if len(errors) > max_errors:
        out.append(f"... and {len(errors) - max_errors} more")
    return out


def run_schema(quiet=False, max_errors=20):
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        print("⚠️  jsonschema not installed — SCHEMA layer skipped. "
              "Install with: pip install jsonschema")
        return None  # signal "not run"

    bundle = load_bundle()
    print("=" * 60)
    print("SCHEMA VALIDATION")
    print("=" * 60)
    failures = 0
    for fname, defname in FILE_MAP.items():
        path = DATA / fname
        if not path.exists():
            print(f"  – {fname}: not present (skipped)")
            continue
        try:
            data = json.load(open(path, encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  ✗ {fname}: JSON parse error: {e}")
            failures += 1
            continue
        errors = validate_file(bundle, data, defname, max_errors)
        if errors:
            failures += 1
            print(f"  ✗ {fname}: {len(errors)} issue(s)")
            if not quiet:
                for err in errors:
                    print(f"        {err}")
        else:
            print(f"  ✓ {fname}")
    if failures:
        print(f"\n✗ Schema validation failed for {failures} file(s).")
        return 1
    print("\n✓ All datasets conform to schema.")
    return 0


def run_refs(quiet=False):
    import check_integrity
    print()
    return check_integrity.check(quiet=quiet)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--schema-only", action="store_true")
    ap.add_argument("--refs-only", action="store_true")
    ap.add_argument("--max-errors", type=int, default=20)
    args = ap.parse_args()

    rc = 0
    if not args.refs_only:
        schema_rc = run_schema(args.quiet, args.max_errors)
        if schema_rc == 1:
            rc = 1
    if not args.schema_only:
        if run_refs(args.quiet) != 0:
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
