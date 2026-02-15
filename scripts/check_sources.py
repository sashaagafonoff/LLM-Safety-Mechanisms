"""
check_sources.py - Detect changes in source documents and trigger re-processing.

Checks source URIs for updates using HTTP HEAD requests (Last-Modified, ETag,
Content-Length). When changes are detected, can optionally re-ingest and
re-analyse the affected documents.

Designed to be run as a weekly cron/scheduled task.

Usage:
  python scripts/check_sources.py                     # Check all, report only
  python scripts/check_sources.py --update             # Check all, re-ingest changed docs
  python scripts/check_sources.py --update --analyse   # Also run NLU+LLM on changed docs
  python scripts/check_sources.py --id doc-id          # Check a specific document

Cache file: cache/source_checksums.json
Log file:   cache/update_log.json
"""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("CheckSources")

EVIDENCE_PATH = Path("data/evidence.json")
FLAT_TEXT_DIR = Path("data/flat_text")
CACHE_DIR = Path("cache")
CHECKSUM_PATH = CACHE_DIR / "source_checksums.json"
UPDATE_LOG_PATH = CACHE_DIR / "update_log.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}


def load_sources():
    """Load source documents from evidence.json."""
    with open(EVIDENCE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    sources = data.get("sources", data if isinstance(data, list) else [])
    return [s for s in sources if isinstance(s, dict) and s.get("status") != "inactive"]


def load_checksums():
    """Load cached checksums from previous runs."""
    if CHECKSUM_PATH.exists():
        with open(CHECKSUM_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_checksums(checksums):
    """Save checksums to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_PATH, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)


def get_source_fingerprint(url):
    """Get a fingerprint for a source URL using HEAD request metadata.

    Returns a dict with available metadata, or None on failure.
    """
    try:
        resp = requests.head(url, headers=HEADERS, timeout=15, allow_redirects=True)
        resp.raise_for_status()

        fingerprint = {}
        if 'Last-Modified' in resp.headers:
            fingerprint['last_modified'] = resp.headers['Last-Modified']
        if 'ETag' in resp.headers:
            fingerprint['etag'] = resp.headers['ETag']
        if 'Content-Length' in resp.headers:
            fingerprint['content_length'] = resp.headers['Content-Length']

        # If no useful headers, fall back to content hash of first 8KB
        if not fingerprint:
            resp2 = requests.get(url, headers=HEADERS, timeout=15, stream=True)
            chunk = resp2.raw.read(8192)
            resp2.close()
            fingerprint['content_hash'] = hashlib.sha256(chunk).hexdigest()

        return fingerprint

    except Exception as e:
        logger.warning(f"  Could not check: {e}")
        return None


def has_changed(doc_id, new_fingerprint, checksums):
    """Compare new fingerprint against cached version."""
    if doc_id not in checksums:
        return True  # New document, not seen before

    old = checksums[doc_id].get('fingerprint', {})

    # Compare ETag first (most reliable)
    if 'etag' in new_fingerprint and 'etag' in old:
        return new_fingerprint['etag'] != old['etag']

    # Then Last-Modified
    if 'last_modified' in new_fingerprint and 'last_modified' in old:
        return new_fingerprint['last_modified'] != old['last_modified']

    # Then Content-Length
    if 'content_length' in new_fingerprint and 'content_length' in old:
        return new_fingerprint['content_length'] != old['content_length']

    # Then content hash
    if 'content_hash' in new_fingerprint and 'content_hash' in old:
        return new_fingerprint['content_hash'] != old['content_hash']

    # If fingerprint structure changed entirely, assume changed
    return True


def append_update_log(entries):
    """Append to the persistent update log."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    log = []
    if UPDATE_LOG_PATH.exists():
        with open(UPDATE_LOG_PATH, 'r', encoding='utf-8') as f:
            log = json.load(f)

    log.extend(entries)

    # Keep last 500 entries
    if len(log) > 500:
        log = log[-500:]

    with open(UPDATE_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)


def reingest_document(doc_id):
    """Re-ingest a specific document by removing flat text and re-running ingestion."""
    flat_text_path = FLAT_TEXT_DIR / f"{doc_id}.txt"
    if flat_text_path.exists():
        flat_text_path.unlink()
        logger.info(f"  Removed existing flat text: {flat_text_path.name}")

    # Run ingestion (uses conda env for markitdown)
    # Try system python first, fall back to conda
    python_paths = [
        sys.executable,
        r"C:\Users\sasha\anaconda3\envs\llm-safety\python.exe",
        "python",
    ]
    for python in python_paths:
        try:
            result = subprocess.run(
                [python, "scripts/ingest_universal.py", "--id", doc_id],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                logger.info(f"  Re-ingested successfully")
                return True
            else:
                logger.debug(f"  Ingestion attempt with {python} failed: {result.stderr[:200]}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    logger.error(f"  Failed to re-ingest {doc_id}")
    return False


def run_analysis_for_document(doc_id):
    """Run NLU + LLM extraction pipeline for a specific document."""
    logger.info(f"  Running NLU + LLM analysis for {doc_id}...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/run_extraction_pipeline.py", "--id", doc_id],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode == 0:
            logger.info(f"  Analysis complete")
            return True
        else:
            logger.error(f"  Analysis failed: {result.stderr[:300]}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"  Analysis timed out")
        return False


def regenerate_reports():
    """Regenerate dashboard and reports."""
    logger.info("Regenerating reports and dashboard...")
    try:
        subprocess.run(
            [sys.executable, "scripts/generate_report.py"],
            capture_output=True, text=True, timeout=60
        )
        subprocess.run(
            [sys.executable, "scripts/generate_dashboard.py"],
            capture_output=True, text=True, timeout=60
        )
        subprocess.run(
            [sys.executable, "scripts/compare_taxonomy_runs.py", "--detailed"],
            capture_output=True, text=True, timeout=60
        )
        logger.info("Reports regenerated")
        return True
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Check source documents for updates"
    )
    parser.add_argument("--id", help="Check a specific document ID")
    parser.add_argument("--update", action="store_true",
                       help="Re-ingest documents that have changed")
    parser.add_argument("--analyse", action="store_true",
                       help="Run NLU+LLM analysis on changed documents (requires --update)")
    parser.add_argument("--regenerate", action="store_true",
                       help="Regenerate reports/dashboard after processing")
    args = parser.parse_args()

    sources = load_sources()
    checksums = load_checksums()
    now = datetime.now().isoformat()

    if args.id:
        sources = [s for s in sources if s.get("id") == args.id]
        if not sources:
            logger.error(f"Document '{args.id}' not found in evidence sources")
            return

    print(f"\n{'=' * 60}")
    print(f"SOURCE CHANGE DETECTION")
    print(f"{'=' * 60}")
    print(f"Checking {len(sources)} sources at {now}\n")

    changed = []
    unchanged = []
    errors = []
    new_docs = []

    for source in sources:
        doc_id = source.get("id")
        url = source.get("url", source.get("uri"))
        if not doc_id or not url or url == "<missing>":
            continue

        print(f"  [{doc_id}] ", end="", flush=True)

        fingerprint = get_source_fingerprint(url)
        if fingerprint is None:
            print("ERROR (could not reach)")
            errors.append(doc_id)
            continue

        is_new = doc_id not in checksums
        is_changed = has_changed(doc_id, fingerprint, checksums)

        # Update checksum cache
        checksums[doc_id] = {
            'url': url,
            'fingerprint': fingerprint,
            'last_checked': now,
        }

        if is_new:
            print("NEW (first check)")
            new_docs.append(doc_id)
        elif is_changed:
            print("CHANGED")
            changed.append(doc_id)
        else:
            print("unchanged")
            unchanged.append(doc_id)

    save_checksums(checksums)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")
    print(f"  Unchanged: {len(unchanged)}")
    print(f"  Changed:   {len(changed)}")
    print(f"  New:       {len(new_docs)}")
    print(f"  Errors:    {len(errors)}")

    if changed:
        print(f"\n  Changed documents: {', '.join(changed)}")
    if new_docs:
        print(f"  New documents: {', '.join(new_docs)}")
    if errors:
        print(f"  Unreachable: {', '.join(errors)}")

    # Process updates if requested
    update_targets = changed  # Only re-process actually changed docs (not new first-checks)
    log_entries = []

    if args.update and update_targets:
        print(f"\n{'=' * 60}")
        print(f"RE-INGESTING {len(update_targets)} CHANGED DOCUMENTS")
        print(f"{'=' * 60}")

        for doc_id in update_targets:
            print(f"\n  [{doc_id}]")
            success = reingest_document(doc_id)

            entry = {
                'timestamp': now,
                'doc_id': doc_id,
                'action': 'reingest',
                'success': success,
            }

            if success and args.analyse:
                analysis_success = run_analysis_for_document(doc_id)
                entry['analysis'] = analysis_success

            log_entries.append(entry)

        if args.regenerate or args.analyse:
            regenerate_reports()

    if log_entries:
        append_update_log(log_entries)

    # Return exit code based on whether changes were found
    if changed:
        return 1  # Changes detected
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
