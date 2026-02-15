"""
clean_flat_text.py - Post-ingestion cleanup of flat text files.

Removes structural noise that causes false positives in NLU analysis:
  1. Tables of Contents (TOC) - section listings with dot leaders/page numbers
  2. Reference/Bibliography sections - academic citations at end of documents
  3. Tabular data - benchmark score tables, performance comparison matrices
  4. ArXiv metadata stamps - character-by-character arXiv IDs at start of PDFs
  5. Contributor/author lists - long name lists with no safety technique content

Each removal is replaced with a transparent placeholder:
  [PIPELINE INGESTION WORKFLOW - REMOVED TOC]
  [PIPELINE INGESTION WORKFLOW - REMOVED REFERENCES]
  [PIPELINE INGESTION WORKFLOW - REMOVED TABULAR DATA]
  [PIPELINE INGESTION WORKFLOW - REMOVED ARXIV METADATA]
  [PIPELINE INGESTION WORKFLOW - REMOVED CONTRIBUTOR LIST]

Usage:
  python scripts/clean_flat_text.py                    # Clean all files
  python scripts/clean_flat_text.py --id doc-id        # Clean specific file
  python scripts/clean_flat_text.py --dry-run          # Preview without changes
"""

import argparse
import re
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("CleanFlatText")

FLAT_TEXT_DIR = Path("data/flat_text")
LOG_DIR = Path("data/flat_text/clean_up_logs")
EVIDENCE_PATH = Path("data/evidence.json")

PLACEHOLDER_TOC = "[PIPELINE INGESTION WORKFLOW - REMOVED TOC]"
PLACEHOLDER_REF = "[PIPELINE INGESTION WORKFLOW - REMOVED REFERENCES]"
PLACEHOLDER_TABLE = "[PIPELINE INGESTION WORKFLOW - REMOVED TABULAR DATA]"
PLACEHOLDER_ARXIV = "[PIPELINE INGESTION WORKFLOW - REMOVED ARXIV METADATA]"
PLACEHOLDER_CONTRIBUTORS = "[PIPELINE INGESTION WORKFLOW - REMOVED CONTRIBUTOR LIST]"


def detect_header_block(lines):
    """Find the metadata header (SOURCE_ID/TITLE/URI + separator)."""
    for i, line in enumerate(lines):
        if line.strip().startswith("----"):
            return i + 1  # Content starts after separator
    return 0


def remove_arxiv_metadata(lines, start_idx):
    """Remove character-by-character arXiv ID stamps at start of PDF-extracted text.

    These appear as single characters on separate lines, e.g.:
        2
        3
        0
        2
        (blank)
        v
        o
        N
        ...
        a
        r
        X
        i
        v
    """
    if start_idx >= len(lines):
        return lines, []

    # Check if the content starts with single-character lines (arXiv stamp)
    single_char_count = 0
    end_idx = start_idx
    for i in range(start_idx, min(start_idx + 80, len(lines))):
        stripped = lines[i].strip()
        if len(stripped) <= 1:  # Single char or empty
            single_char_count += 1
            end_idx = i + 1
        elif len(stripped) <= 3 and (stripped.isdigit() or stripped in (':', '[', ']', '.')):
            single_char_count += 1
            end_idx = i + 1
        else:
            # Allow a few non-single-char lines in the stamp
            # but break if we hit substantial content
            if single_char_count > 10:
                break
            elif single_char_count > 0:
                # Might still be in stamp region, check next lines
                next_singles = 0
                for j in range(i, min(i + 5, len(lines))):
                    if len(lines[j].strip()) <= 1:
                        next_singles += 1
                if next_singles >= 2:
                    end_idx = i + 1
                    continue
            break

    if single_char_count >= 15:  # Confident this is an arXiv stamp
        removed = lines[start_idx:end_idx]
        new_lines = lines[:start_idx] + [PLACEHOLDER_ARXIV + "\n", "\n"] + lines[end_idx:]
        return new_lines, [("arxiv_metadata", start_idx + 1, end_idx + 1,
                           f"Removed {len(removed)} lines of arXiv metadata")]
    return lines, []


def remove_toc(lines, start_idx):
    """Remove Table of Contents sections.

    Detects two patterns:
    1. Dot-leader TOC: lines with ". . . ." patterns (common in arXiv PDFs)
    2. Explicit "Contents" / "Table of Contents" heading followed by numbered sections
    """
    removals = []

    # Pattern 1: Find contiguous TOC blocks with dot leaders
    dot_leader_re = re.compile(r'\. \. \.|\.{4,}')
    i = start_idx
    while i < len(lines):
        if dot_leader_re.search(lines[i]):
            # Found a dot leader line - scan backwards and forwards for the TOC block
            block_start = i
            block_end = i

            # Scan backwards to find start (look for section number or heading)
            for j in range(i - 1, max(start_idx, i - 5) - 1, -1):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                # Section headings like "4.2.1 Web data alone..."
                if re.match(r'^\d+\.?[\d.]*\s+\S', stripped):
                    block_start = j
                    break
                # Standalone page numbers
                if stripped.isdigit():
                    block_start = j
                    break

            # Scan forward through connected TOC lines
            for j in range(i + 1, len(lines)):
                stripped = lines[j].strip()
                if dot_leader_re.search(stripped):
                    block_end = j
                elif not stripped:
                    block_end = j
                elif stripped.isdigit() and len(stripped) <= 3:
                    block_end = j  # Page number
                elif re.match(r'^\d+\.?[\d.]*\s+\S', stripped):
                    # Another section heading - part of TOC
                    block_end = j
                else:
                    break

            # Only remove if we found a substantial block (3+ dot-leader lines nearby)
            dot_lines_in_block = sum(1 for k in range(block_start, block_end + 1)
                                    if dot_leader_re.search(lines[k]))
            if dot_lines_in_block >= 3:
                removals.append((block_start, block_end + 1))
                i = block_end + 1
            else:
                i += 1
        else:
            i += 1

    # Pattern 2: Explicit "Contents" heading
    for i in range(start_idx, len(lines)):
        stripped = lines[i].strip()
        if stripped.lower() in ('contents', 'table of contents'):
            block_start = i
            block_end = i
            # Scan forward through numbered section entries
            for j in range(i + 1, min(i + 200, len(lines))):
                stripped_j = lines[j].strip()
                if not stripped_j:
                    block_end = j
                    continue
                if re.match(r'^\d+\.?[\d.]*\s+\S', stripped_j):
                    block_end = j
                elif stripped_j.isdigit() and len(stripped_j) <= 3:
                    block_end = j  # Page number
                elif dot_leader_re.search(stripped_j):
                    block_end = j
                elif len(stripped_j) < 5:
                    block_end = j  # Short fragments
                else:
                    # Check if this is a substantial content line
                    if len(stripped_j) > 30:
                        break
                    block_end = j
            if block_end - block_start >= 5:
                removals.append((block_start, block_end + 1))

    # Merge overlapping removals
    if not removals:
        return lines, []

    removals.sort()
    merged = [removals[0]]
    for start, end in removals[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Apply removals (reverse order to preserve indices)
    log_entries = []
    for start, end in reversed(merged):
        removed_text = ''.join(lines[start:end])
        line_count = end - start
        preview = lines[start].strip()[:80]
        log_entries.insert(0, ("toc", start + 1, end + 1,
                              f"Removed {line_count} TOC lines starting with: {preview}"))
        lines = lines[:start] + [PLACEHOLDER_TOC + "\n", "\n"] + lines[end:]

    return lines, log_entries


def remove_references(lines, start_idx):
    """Remove reference/bibliography sections at the end of documents.

    Detects the start of reference sections by heading patterns,
    then removes everything from that point until the next major section
    or end of file.
    """
    removals = []

    # Find reference section headings
    ref_heading_re = re.compile(
        r'^(?:#{0,3}\s*)?(?:\d+\.?\s+)?'
        r'(?:References?|Bibliography|REFERENCES|BIBLIOGRAPHY|Works Cited)\s*$',
        re.IGNORECASE
    )

    for i in range(start_idx, len(lines)):
        if ref_heading_re.match(lines[i].strip()):
            ref_start = i

            # Verify this is a real references section by checking the next 20 lines
            # for citation patterns
            citation_signals = 0
            for j in range(i + 1, min(i + 30, len(lines))):
                stripped = lines[j].strip()
                # Author-year: "Name, A. (2023)"
                if re.search(r'\(\d{4}[a-z]?\)', stripped):
                    citation_signals += 1
                # Numbered: "[1]", "[23]"
                if re.match(r'^\[\d+\]', stripped):
                    citation_signals += 1
                # arXiv references
                if 'arXiv' in stripped or 'arxiv.org' in stripped:
                    citation_signals += 1
                # Publication venues
                if re.search(r'(?:proceedings|conference|journal|workshop|preprint)',
                            stripped, re.IGNORECASE):
                    citation_signals += 1

            if citation_signals < 2:
                continue  # Not a real references section

            # Find the end of the references section
            # References end at: next major heading, appendix, or end of file
            ref_end = len(lines)
            for j in range(i + 5, len(lines)):
                stripped = lines[j].strip()
                # Major section heading (not a reference)
                if re.match(r'^(?:#{1,3}\s+)?(?:\d+\.?\s+)?(?:Appendix|Appendices)\b',
                           stripped, re.IGNORECASE):
                    ref_end = j
                    break
                # "A " or "B " style appendix headings (common in academic papers)
                if re.match(r'^[A-Z]\s+[A-Z]', stripped) and len(stripped) > 5:
                    # Check if this looks like an appendix heading
                    if not re.search(r'\(\d{4}\)', stripped):  # Not a citation
                        ref_end = j
                        break

            removals.append((ref_start, ref_end))

    if not removals:
        return lines, []

    # Merge overlapping
    removals.sort()
    merged = [removals[0]]
    for start, end in removals[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    log_entries = []
    for start, end in reversed(merged):
        line_count = end - start
        log_entries.insert(0, ("references", start + 1, end + 1,
                              f"Removed {line_count} reference lines"))
        lines = lines[:start] + [PLACEHOLDER_REF + "\n", "\n"] + lines[end:]

    return lines, log_entries


def is_table_line(line):
    """Heuristic: does this line look like part of a data table?"""
    stripped = line.strip()
    if not stripped:
        return False

    # Lines that are mostly numbers, percentages, or short tokens
    tokens = stripped.split()
    if len(tokens) < 2:
        return False

    numeric_tokens = 0
    for t in tokens:
        # Remove common formatting
        cleaned = t.strip('%,()±—–-')
        try:
            float(cleaned)
            numeric_tokens += 1
        except ValueError:
            pass

    # If more than 40% of tokens are numeric and there are at least 3
    if len(tokens) >= 3 and numeric_tokens / len(tokens) >= 0.4:
        return True

    return False


def remove_tables(lines, start_idx):
    """Remove tabular benchmark data.

    Detects tables by:
    1. "Table N:" captions followed by data rows
    2. Dense blocks of numeric data (benchmark scores)
    """
    removals = []

    # Pattern 1: Explicit "Table N:" captions
    table_caption_re = re.compile(r'^(?:Table|TABLE)\s+\d+[.:|\s]', re.IGNORECASE)

    i = start_idx
    while i < len(lines):
        stripped = lines[i].strip()

        if table_caption_re.match(stripped):
            table_start = i
            table_end = i

            # Caption can span multiple lines
            for j in range(i + 1, min(i + 10, len(lines))):
                s = lines[j].strip()
                if not s:
                    table_end = j
                    break
                # Still caption text (no numbers-heavy content yet)
                if not is_table_line(lines[j]):
                    table_end = j
                else:
                    table_end = j
                    break

            # Now scan through table data
            for j in range(table_end + 1, len(lines)):
                stripped_j = lines[j].strip()
                if not stripped_j:
                    # Allow blank lines within tables
                    # But if we see 3+ blanks, table is probably over
                    blank_run = 0
                    for k in range(j, min(j + 4, len(lines))):
                        if not lines[k].strip():
                            blank_run += 1
                        else:
                            break
                    if blank_run >= 3:
                        table_end = j
                        break
                    table_end = j
                    continue

                # Page numbers (standalone digits)
                if stripped_j.isdigit() and len(stripped_j) <= 4:
                    table_end = j
                    continue

                # Check if this looks like table content
                if is_table_line(lines[j]):
                    table_end = j
                elif len(stripped_j) < 60 and not stripped_j.endswith('.'):
                    # Short lines without periods are likely column headers or row labels
                    table_end = j
                elif table_caption_re.match(stripped_j):
                    # Another table starts - include it
                    table_end = j
                else:
                    # Substantial text = end of table
                    break

            if table_end - table_start >= 3:  # Need at least 3 lines
                removals.append((table_start, table_end + 1))
            i = table_end + 1
        else:
            i += 1

    # Pattern 2: Dense numeric blocks (benchmark scores without "Table N:" prefix)
    i = start_idx
    while i < len(lines):
        if is_table_line(lines[i]):
            block_start = i
            block_end = i
            table_lines = 1

            for j in range(i + 1, len(lines)):
                stripped_j = lines[j].strip()
                if not stripped_j:
                    block_end = j
                    continue
                if is_table_line(lines[j]):
                    block_end = j
                    table_lines += 1
                elif stripped_j.isdigit() and len(stripped_j) <= 4:
                    block_end = j  # Page number
                elif len(stripped_j) < 40 and not stripped_j.endswith('.'):
                    block_end = j  # Short label
                else:
                    break

            # Only remove substantial numeric blocks (5+ data lines)
            if table_lines >= 5:
                # Check we're not already covering this
                already_covered = any(
                    s <= block_start and block_end < e
                    for s, e in removals
                )
                if not already_covered:
                    removals.append((block_start, block_end + 1))
            i = block_end + 1
        else:
            i += 1

    if not removals:
        return lines, []

    # Merge overlapping/adjacent removals
    removals.sort()
    merged = [removals[0]]
    for start, end in removals[1:]:
        if start <= merged[-1][1] + 2:  # Allow 2-line gap
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    log_entries = []
    for start, end in reversed(merged):
        line_count = end - start
        preview = lines[start].strip()[:80]
        log_entries.insert(0, ("table", start + 1, end + 1,
                              f"Removed {line_count} table lines starting with: {preview}"))
        lines = lines[:start] + [PLACEHOLDER_TABLE + "\n", "\n"] + lines[end:]

    return lines, log_entries


def remove_contributor_lists(lines, start_idx):
    """Remove long contributor/author name lists.

    These are blocks of comma-separated names that add no analytical value.
    Only removes lists of 20+ names to avoid false positives.
    """
    removals = []

    contrib_heading_re = re.compile(
        r'^(?:#{0,3}\s*)?(?:Core\s+)?(?:Contributors?|Acknowledgements?|'
        r'Author\s+Contributions?|Contributors?\s+and\s+Acknowledgements?)\s*$',
        re.IGNORECASE
    )

    for i in range(start_idx, len(lines)):
        if contrib_heading_re.match(lines[i].strip()):
            block_start = i
            block_end = i
            name_count = 0

            for j in range(i + 1, len(lines)):
                stripped = lines[j].strip()
                if not stripped:
                    block_end = j
                    continue

                # Count comma-separated name-like tokens
                if ',' in stripped:
                    parts = stripped.split(',')
                    name_like = sum(1 for p in parts
                                  if re.match(r'\s*[A-Z][a-z]+\s', p.strip()))
                    name_count += name_like

                # If we hit a new major section, stop
                if re.match(r'^(?:#{1,3}\s+)?\d+\.?\s+[A-Z]', stripped):
                    break
                if re.match(r'^(?:#{1,3}\s+)?(?:References?|Appendix)', stripped, re.IGNORECASE):
                    break

                block_end = j

            if name_count >= 20:
                removals.append((block_start, block_end + 1))

    if not removals:
        return lines, []

    log_entries = []
    for start, end in reversed(removals):
        line_count = end - start
        log_entries.insert(0, ("contributors", start + 1, end + 1,
                              f"Removed {line_count} contributor list lines"))
        lines = lines[:start] + [PLACEHOLDER_CONTRIBUTORS + "\n", "\n"] + lines[end:]

    return lines, log_entries


def clean_file(file_path, dry_run=False):
    """Clean a single flat text file. Returns (was_modified, log_entries)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    original_line_count = len(lines)
    header_end = detect_header_block(lines)
    all_logs = []

    # Skip files that have already been cleaned
    content = ''.join(lines)
    if PLACEHOLDER_TOC in content or PLACEHOLDER_REF in content or PLACEHOLDER_TABLE in content:
        # Already cleaned - run cleanup again from scratch would require
        # the original file. Just skip.
        return False, [("skip", 0, 0, "File already contains cleanup placeholders - skipping")]

    # Apply cleanups in order (each adjusts line numbers for subsequent passes)
    # 1. ArXiv metadata
    lines, logs = remove_arxiv_metadata(lines, header_end)
    all_logs.extend(logs)

    # Recalculate header end since lines may have shifted
    header_end = detect_header_block(lines)

    # 2. TOC
    lines, logs = remove_toc(lines, header_end)
    all_logs.extend(logs)

    # 3. Tables
    lines, logs = remove_tables(lines, header_end)
    all_logs.extend(logs)

    # 4. References
    lines, logs = remove_references(lines, header_end)
    all_logs.extend(logs)

    # 5. Contributor lists
    lines, logs = remove_contributor_lists(lines, header_end)
    all_logs.extend(logs)

    new_line_count = len(lines)
    was_modified = new_line_count != original_line_count

    if was_modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return was_modified, all_logs


def write_log(doc_id, log_entries, stats):
    """Write cleanup log for a document."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{doc_id}.log"

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"Cleanup Log: {doc_id}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Original lines: {stats['original_lines']}\n")
        f.write(f"Final lines: {stats['final_lines']}\n")
        f.write(f"Lines removed: {stats['lines_removed']}\n")
        f.write("=" * 60 + "\n\n")

        if not log_entries:
            f.write("No changes made.\n")
            return

        for entry_type, start_line, end_line, description in log_entries:
            f.write(f"[{entry_type.upper()}] Lines {start_line}-{end_line}: {description}\n")

    return log_path


def main():
    parser = argparse.ArgumentParser(
        description="Clean flat text files by removing TOCs, references, and tabular data."
    )
    parser.add_argument("--id", help="Clean a specific document by ID", default=None)
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without modifying files")
    args = parser.parse_args()

    if args.id:
        files = [FLAT_TEXT_DIR / f"{args.id}.txt"]
        if not files[0].exists():
            logger.error(f"File not found: {files[0]}")
            return
    else:
        files = sorted(FLAT_TEXT_DIR.glob("*.txt"))
        files = [f for f in files if not f.name.startswith("temp_")]

    total_files = len(files)
    modified_count = 0
    total_lines_removed = 0

    print(f"\n{'=' * 60}")
    print(f"FLAT TEXT CLEANUP {'(DRY RUN)' if args.dry_run else ''}")
    print(f"{'=' * 60}")
    print(f"Processing {total_files} files...\n")

    for i, file_path in enumerate(files, 1):
        doc_id = file_path.stem

        with open(file_path, 'r', encoding='utf-8') as f:
            original_lines = len(f.readlines())

        was_modified, log_entries = clean_file(file_path, dry_run=args.dry_run)

        if log_entries and log_entries[0][0] == "skip":
            print(f"[{i}/{total_files}] {doc_id}: SKIPPED (already cleaned)")
            continue

        with open(file_path, 'r', encoding='utf-8') as f:
            final_lines = len(f.readlines())

        lines_removed = original_lines - final_lines if was_modified else 0
        total_lines_removed += lines_removed

        if was_modified:
            modified_count += 1
            removal_types = set(e[0] for e in log_entries)
            print(f"[{i}/{total_files}] {doc_id}: {lines_removed} lines removed "
                  f"({', '.join(sorted(removal_types))})")
        else:
            print(f"[{i}/{total_files}] {doc_id}: no changes")

        # Write log
        stats = {
            'original_lines': original_lines,
            'final_lines': final_lines if was_modified else original_lines,
            'lines_removed': lines_removed
        }
        write_log(doc_id, log_entries, stats)

    print(f"\n{'=' * 60}")
    print(f"CLEANUP COMPLETE")
    print(f"{'=' * 60}")
    print(f"Files processed: {total_files}")
    print(f"Files modified: {modified_count}")
    print(f"Total lines removed: {total_lines_removed}")
    if args.dry_run:
        print("(DRY RUN - no files were actually modified)")
    print(f"Logs written to: {LOG_DIR}/")


if __name__ == "__main__":
    main()
