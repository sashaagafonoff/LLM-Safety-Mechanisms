#!/usr/bin/env python3
"""
Snapshot — Temporal versioning for model_technique_map.json

Archives dated copies of the technique map and generates diff summaries,
enabling researchers to track how safety technique coverage evolves over time.

Usage:
    python scripts/snapshot.py                    # Create snapshot of current state
    python scripts/snapshot.py --diff             # Show diff vs last snapshot
    python scripts/snapshot.py --diff 2026-01-15  # Diff vs specific date
    python scripts/snapshot.py --list             # List all snapshots
"""

import json
import argparse
import shutil
from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAP_PATH = DATA_DIR / "model_technique_map.json"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
INDEX_PATH = SNAPSHOTS_DIR / "snapshot_index.json"


def load_map(path: Path) -> dict:
    """Load a model_technique_map.json file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_stats(data: dict) -> dict:
    """Compute summary statistics for a technique map."""
    total_sources = len(data)
    total_detections = 0
    active_techniques = set()
    all_techniques = set()
    sources_by_origin = {}

    for source_id, entries in data.items():
        if isinstance(entries, list):
            for entry in entries:
                total_detections += 1
                tid = entry.get("techniqueId", "")
                all_techniques.add(tid)
                if entry.get("active", True):
                    active_techniques.add(tid)
                origin = entry.get("origin", "unknown")
                sources_by_origin[origin] = sources_by_origin.get(origin, 0) + 1

    return {
        "totalSources": total_sources,
        "totalTechniqueDetections": total_detections,
        "uniqueTechniques": len(all_techniques),
        "activeTechniques": len(active_techniques),
    }


def compute_diff(old_data: dict, new_data: dict) -> dict:
    """Compute differences between two technique maps."""

    def get_techniques(data: dict, active_only: bool = False) -> Dict[str, set]:
        """Return {sourceId: set(techniqueIds)}."""
        result = {}
        for source_id, entries in data.items():
            techs = set()
            if isinstance(entries, list):
                for entry in entries:
                    if not active_only or entry.get("active", True):
                        techs.add(entry.get("techniqueId", ""))
            result[source_id] = techs
        return result

    old_techs = get_techniques(old_data, active_only=True)
    new_techs = get_techniques(new_data, active_only=True)

    old_sources = set(old_techs.keys())
    new_sources = set(new_techs.keys())

    added_sources = sorted(new_sources - old_sources)
    removed_sources = sorted(old_sources - new_sources)
    common_sources = old_sources & new_sources

    # Per-source technique changes
    technique_changes = {}
    for source_id in common_sources:
        added = sorted(new_techs[source_id] - old_techs[source_id])
        removed = sorted(old_techs[source_id] - new_techs[source_id])
        if added or removed:
            technique_changes[source_id] = {
                "added": added,
                "removed": removed,
            }

    # Global technique counts
    all_old = set()
    all_new = set()
    for techs in old_techs.values():
        all_old.update(techs)
    for techs in new_techs.values():
        all_new.update(techs)

    return {
        "addedSources": added_sources,
        "removedSources": removed_sources,
        "techniqueChanges": technique_changes,
        "newTechniquesGlobal": sorted(all_new - all_old),
        "removedTechniquesGlobal": sorted(all_old - all_new),
        "stats": {
            "sourcesAdded": len(added_sources),
            "sourcesRemoved": len(removed_sources),
            "sourcesWithChanges": len(technique_changes),
            "totalTechniqueAdditions": sum(
                len(v["added"]) for v in technique_changes.values()
            ),
            "totalTechniqueRemovals": sum(
                len(v["removed"]) for v in technique_changes.values()
            ),
        },
    }


def load_index() -> dict:
    """Load or initialize the snapshot index."""
    if INDEX_PATH.exists():
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"snapshots": []}


def save_index(index: dict):
    """Save the snapshot index."""
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")


def find_snapshot(target_date: str) -> Optional[Path]:
    """Find a snapshot file by date string."""
    index = load_index()
    for snap in index["snapshots"]:
        if snap["date"] == target_date:
            return SNAPSHOTS_DIR / snap["file"]
    # Also try direct file match
    candidate = SNAPSHOTS_DIR / f"model_technique_map_{target_date}.json"
    if candidate.exists():
        return candidate
    return None


def get_latest_snapshot() -> Optional[Tuple[str, Path]]:
    """Get the most recent snapshot date and path."""
    index = load_index()
    if not index["snapshots"]:
        return None
    latest = index["snapshots"][-1]
    path = SNAPSHOTS_DIR / latest["file"]
    if path.exists():
        return latest["date"], path
    return None


def create_snapshot():
    """Create a dated snapshot of the current model_technique_map.json."""
    if not MAP_PATH.exists():
        print(f"Error: {MAP_PATH} not found.")
        return

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    snapshot_filename = f"model_technique_map_{today}.json"
    snapshot_path = SNAPSHOTS_DIR / snapshot_filename

    # Check if snapshot already exists for today
    if snapshot_path.exists():
        print(f"Snapshot for {today} already exists. Overwriting.")

    # Copy the file
    shutil.copy2(MAP_PATH, snapshot_path)

    # Compute stats
    data = load_map(MAP_PATH)
    stats = compute_stats(data)

    # Update index
    index = load_index()

    # Remove existing entry for today if present
    index["snapshots"] = [s for s in index["snapshots"] if s["date"] != today]

    index["snapshots"].append(
        {"date": today, "file": snapshot_filename, "stats": stats}
    )

    # Sort by date
    index["snapshots"].sort(key=lambda s: s["date"])

    save_index(index)

    print(f"Snapshot created: {snapshot_path.name}")
    print(f"  Sources: {stats['totalSources']}")
    print(f"  Technique detections: {stats['totalTechniqueDetections']}")
    print(f"  Unique techniques: {stats['uniqueTechniques']}")
    print(f"  Active techniques: {stats['activeTechniques']}")

    # Auto-diff against previous snapshot
    prev = None
    for i, snap in enumerate(index["snapshots"]):
        if snap["date"] == today and i > 0:
            prev_snap = index["snapshots"][i - 1]
            prev_path = SNAPSHOTS_DIR / prev_snap["file"]
            if prev_path.exists():
                prev = (prev_snap["date"], prev_path)
            break

    if prev:
        print(f"\nChanges since {prev[0]}:")
        show_diff(prev[1], MAP_PATH)
    else:
        print("\nNo previous snapshot for comparison.")


def show_diff(old_path: Path, new_path: Path):
    """Display a human-readable diff between two technique maps."""
    old_data = load_map(old_path)
    new_data = load_map(new_path)
    diff = compute_diff(old_data, new_data)

    stats = diff["stats"]

    if (
        stats["sourcesAdded"] == 0
        and stats["sourcesRemoved"] == 0
        and stats["sourcesWithChanges"] == 0
    ):
        print("  No changes detected.")
        return

    if diff["addedSources"]:
        print(f"  + {stats['sourcesAdded']} new source(s):")
        for s in diff["addedSources"]:
            print(f"    + {s}")

    if diff["removedSources"]:
        print(f"  - {stats['sourcesRemoved']} removed source(s):")
        for s in diff["removedSources"]:
            print(f"    - {s}")

    if diff["techniqueChanges"]:
        print(
            f"  ~ {stats['sourcesWithChanges']} source(s) with technique changes"
            f" (+{stats['totalTechniqueAdditions']}/-{stats['totalTechniqueRemovals']}):"
        )
        for source_id, changes in sorted(diff["techniqueChanges"].items()):
            parts = []
            if changes["added"]:
                parts.append(f"+{', '.join(changes['added'])}")
            if changes["removed"]:
                parts.append(f"-{', '.join(changes['removed'])}")
            print(f"    {source_id}: {'; '.join(parts)}")

    if diff["newTechniquesGlobal"]:
        print(f"  New technique IDs in dataset: {', '.join(diff['newTechniquesGlobal'])}")

    if diff["removedTechniquesGlobal"]:
        print(
            f"  Removed technique IDs from dataset: {', '.join(diff['removedTechniquesGlobal'])}"
        )


def list_snapshots():
    """List all available snapshots."""
    index = load_index()
    if not index["snapshots"]:
        print("No snapshots found.")
        return

    print(f"{'Date':<14} {'Sources':>8} {'Detections':>11} {'Techniques':>11} {'File'}")
    print("-" * 70)
    for snap in index["snapshots"]:
        stats = snap.get("stats", {})
        print(
            f"{snap['date']:<14} "
            f"{stats.get('totalSources', '?'):>8} "
            f"{stats.get('totalTechniqueDetections', '?'):>11} "
            f"{stats.get('activeTechniques', '?'):>11} "
            f"{snap['file']}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Snapshot model_technique_map.json for temporal versioning"
    )
    parser.add_argument(
        "--diff",
        nargs="?",
        const="latest",
        metavar="DATE",
        help="Show diff vs a specific snapshot date (default: latest)",
    )
    parser.add_argument(
        "--list", action="store_true", help="List all available snapshots"
    )

    args = parser.parse_args()

    if args.list:
        list_snapshots()
        return

    if args.diff:
        if not MAP_PATH.exists():
            print(f"Error: {MAP_PATH} not found.")
            return

        if args.diff == "latest":
            latest = get_latest_snapshot()
            if not latest:
                print("No snapshots found. Run without --diff to create one.")
                return
            snap_date, snap_path = latest
            print(f"Diff: {snap_date} → current")
            show_diff(snap_path, MAP_PATH)
        else:
            snap_path = find_snapshot(args.diff)
            if not snap_path:
                print(f"No snapshot found for date: {args.diff}")
                return
            print(f"Diff: {args.diff} → current")
            show_diff(snap_path, MAP_PATH)
        return

    # Default: create a new snapshot
    create_snapshot()


if __name__ == "__main__":
    main()
