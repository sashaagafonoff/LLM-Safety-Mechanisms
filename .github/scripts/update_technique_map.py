#!/usr/bin/env python3
"""Apply an approved data-review submission to model_technique_map.json."""

import json
import os
import sys
from datetime import datetime, timezone


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_output(key: str, value: str) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            delimiter = "EOF_DELIM"
            f.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
    else:
        print(f"{key}={value}")


def validate_references(submission: dict, evidence: dict, techniques: list) -> None:
    source_ids = {s["id"] for s in evidence.get("sources", evidence if isinstance(evidence, list) else [])}
    if submission["source_id"] not in source_ids:
        raise ValueError(f"Source ID not found: {submission['source_id']}")

    technique_ids = {t["id"] for t in techniques}
    if submission["technique_id"] not in technique_ids:
        raise ValueError(f"Technique ID not found: {submission['technique_id']}")


def make_evidence_entry(submission: dict, review_type: str = None, created_by: str = None, **extra) -> dict:
    entry = {
        "text": submission["evidence_text"],
        "created_by": created_by or "community",
        "active": True,
        "deleted_by": None,
    }
    if review_type:
        entry["review_type"] = review_type
    entry.update(extra)
    return entry


def apply_submission(technique_map: dict, submission: dict) -> dict:
    version = submission.get("version", 1)
    if version == 2:
        return apply_v2(technique_map, submission)
    return apply_v1(technique_map, submission)


def apply_v2(technique_map: dict, submission: dict) -> dict:
    """Handle version 2 payloads from the two-panel annotation tool."""
    source_id = submission["source_id"]
    technique_id = submission["technique_id"]
    action = submission["action"]
    username = submission.get("github_username", "community")

    if source_id not in technique_map:
        technique_map[source_id] = []

    entries = technique_map[source_id]

    # Find existing entry for this technique
    existing = None
    existing_idx = None
    for idx, e in enumerate(entries):
        if e["techniqueId"] == technique_id:
            existing = e
            existing_idx = idx
            break

    if action == "delete_tag":
        if existing is None:
            raise ValueError(f"Cannot delete non-existent mapping: {technique_id} in {source_id}")
        existing["active"] = False
        existing["deleted_by"] = username
        return {"action": "deleted", "source_id": source_id, "technique_id": technique_id}

    elif action == "link_evidence":
        if existing is None:
            # Create new entry when linking evidence to a new technique
            new_entry = {
                "techniqueId": technique_id,
                "confidence": "Medium",
                "active": True,
                "deleted_by": None,
                "evidence": [make_evidence_entry(submission, created_by=username)],
            }
            entries.append(new_entry)
            return {"action": "linked_new", "source_id": source_id, "technique_id": technique_id}
        else:
            existing.setdefault("evidence", []).append(
                make_evidence_entry(submission, created_by=username)
            )
            return {"action": "linked", "source_id": source_id, "technique_id": technique_id}

    elif action == "add_new_tag":
        if existing and existing.get("active", True):
            # Technique already mapped — append evidence rather than skip
            existing.setdefault("evidence", []).append(
                make_evidence_entry(submission, created_by=username)
            )
            return {"action": "added_evidence", "source_id": source_id, "technique_id": technique_id}

        new_entry = {
            "techniqueId": technique_id,
            "confidence": "Medium",
            "active": True,
            "deleted_by": None,
            "evidence": [make_evidence_entry(submission, created_by=username)],
        }

        if existing_idx is not None:
            entries[existing_idx] = new_entry
            return {"action": "reactivated", "source_id": source_id, "technique_id": technique_id}
        else:
            entries.append(new_entry)
            return {"action": "added", "source_id": source_id, "technique_id": technique_id}

    else:
        raise ValueError(f"Unknown v2 action: {action}")


def apply_v1(technique_map: dict, submission: dict) -> dict:
    """Handle version 1 payloads (legacy form-based tool)."""
    source_id = submission["source_id"]
    technique_id = submission["technique_id"]
    submission_type = submission["submission_type"]

    if source_id not in technique_map:
        technique_map[source_id] = []

    entries = technique_map[source_id]

    # Find existing entry for this technique
    existing = None
    existing_idx = None
    for idx, e in enumerate(entries):
        if e["techniqueId"] == technique_id:
            existing = e
            existing_idx = idx
            break

    if submission_type == "add_new_tag":
        if existing and existing.get("active", True):
            return {"action": "skip", "reason": "Technique already mapped (active)"}

        new_entry = {
            "techniqueId": technique_id,
            "confidence": submission.get("new_confidence", "Medium"),
            "active": True,
            "deleted_by": None,
            "evidence": [make_evidence_entry(submission, review_type="community_add")],
        }

        if existing_idx is not None:
            entries[existing_idx] = new_entry
            return {"action": "reactivated", "source_id": source_id, "technique_id": technique_id}
        else:
            entries.append(new_entry)
            return {"action": "added", "source_id": source_id, "technique_id": technique_id}

    elif submission_type == "review_existing":
        if existing is None:
            raise ValueError(f"Cannot review non-existent mapping: {technique_id} in {source_id}")

        action = submission.get("action", "confirm")

        if action == "confirm":
            existing.setdefault("evidence", []).append(
                make_evidence_entry(submission, review_type="confirmation")
            )
            return {"action": "confirmed", "source_id": source_id, "technique_id": technique_id}

        elif action == "adjust_confidence":
            old_conf = existing.get("confidence", "Unknown")
            new_conf = submission["new_confidence"]
            existing["confidence"] = new_conf
            existing.setdefault("evidence", []).append(
                make_evidence_entry(
                    submission,
                    review_type="confidence_adjustment",
                    old_confidence=old_conf,
                    new_confidence=new_conf,
                )
            )
            return {
                "action": "adjusted",
                "source_id": source_id,
                "technique_id": technique_id,
                "old_confidence": old_conf,
                "new_confidence": new_conf,
            }

        elif action == "dispute":
            existing["active"] = False
            existing["deleted_by"] = "community"
            existing.setdefault("evidence", []).append(
                make_evidence_entry(submission, review_type="dispute")
            )
            return {"action": "disputed", "source_id": source_id, "technique_id": technique_id}

        else:
            raise ValueError(f"Unknown action: {action}")
    else:
        raise ValueError(f"Unknown submission_type: {submission_type}")


def main() -> int:
    submission_json = os.environ.get("SUBMISSION_DATA")
    if not submission_json:
        print("::error::SUBMISSION_DATA environment variable not set", file=sys.stderr)
        return 1

    try:
        submission = json.loads(submission_json)
    except json.JSONDecodeError as e:
        write_output("error", f"Invalid JSON: {e}")
        print(f"::error::Invalid submission JSON: {e}", file=sys.stderr)
        return 1

    try:
        technique_map = load_json("data/model_technique_map.json")
        evidence = load_json("data/evidence.json")
        techniques = load_json("data/techniques.json")

        validate_references(submission, evidence, techniques)
        result = apply_submission(technique_map, submission)

        if result.get("action") == "skip":
            reason = result.get("reason", "duplicate")
            print(f"::warning::No changes: {reason}")
            # Don't write changes_summary so the workflow skips the commit step
            return 0

        save_json("data/model_technique_map.json", technique_map)

        summary = f"{result['action'].title()} technique {result['technique_id']} for source {result['source_id']}"
        if "old_confidence" in result:
            summary += f" ({result['old_confidence']} -> {result['new_confidence']})"

        write_output("changes_summary", summary)
        print(f"Success: {summary}")
        return 0

    except Exception as e:
        write_output("error", str(e))
        print(f"::error::Failed to apply submission: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
