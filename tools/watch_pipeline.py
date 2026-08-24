#!/usr/bin/env python3
"""Live progress monitor for extraction-pipeline runs.

Tails a pipeline log (the console output of run_extraction_pipeline.py /
analyze_nlu.py, however it was captured) and renders a clean one-line
progress display: current document, percent complete, average pace, and a
rough ETA. Useful because the raw log is dominated by tqdm batch spam.

Usage:
    py tools/watch_pipeline.py <path-to-log> [--interval 5] [--once]

Examples:
    # Live view, refreshes every 5s (Ctrl+C to stop; the pipeline is unaffected):
    py tools/watch_pipeline.py "C:\\...\\tasks\\bon9pn772.output"

    # Single snapshot (for scripting):
    py tools/watch_pipeline.py "C:\\...\\tasks\\bon9pn772.output" --once

The parser looks for the pipeline's own markers, so it works for any run of
the NLU stage regardless of how the log was captured:
    [N/M] doc-id                      -> progress
    'PIPELINE COMPLETE'               -> done
    'chunk-quality gate dropped ...'  -> shown as a supplementary stat
ETA is based on average pace over observed progress and is honest about its
limits: sleep/suspend gaps inflate wall-clock averages, so a 'recent pace'
figure (last 3 documents seen by this watcher) is shown once available.
"""

import argparse
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PROGRESS_RE = re.compile(r"^\[(\d+)/(\d+)\]\s+(\S+)", re.MULTILINE)
TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", re.MULTILINE)
GATE_RE = re.compile(r"chunk-quality gate dropped (\d+) of (\d+) chunks")
COMPLETE_RE = re.compile(r"PIPELINE COMPLETE|GATE COMPLETE|Analysis Complete", re.IGNORECASE)


def read_log(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        sys.exit(f"Cannot read log file: {e}")


def snapshot(path: Path):
    """Parse one snapshot of the log; returns a dict of display fields."""
    text = read_log(path)
    progress = PROGRESS_RE.findall(text)
    stamps = TIMESTAMP_RE.findall(text)
    gates = GATE_RE.findall(text)
    mtime = datetime.fromtimestamp(path.stat().st_mtime)

    out = {
        # Only trust a completion marker near the END of the log: a file that
        # contains an older finished run followed by a new one must not report
        # the new run as complete (learned the hard way).
        "complete": bool(COMPLETE_RE.search(text[-4096:])),
        "mtime": mtime,
        "stale_s": (datetime.now() - mtime).total_seconds(),
        "dropped_chunks": sum(int(d) for d, _ in gates),
        "total_chunks": sum(int(t) for _, t in gates),
    }
    if progress:
        n, m, doc = progress[-1]
        out.update(current=int(n), total=int(m), doc=doc)
    if stamps:
        out["started"] = datetime.strptime(stamps[0], "%Y-%m-%d %H:%M:%S")
    return out


def fmt_td(seconds: float) -> str:
    if seconds < 0:
        return "?"
    td = timedelta(seconds=int(seconds))
    h, rem = divmod(td.seconds + td.days * 86400, 3600)
    m = rem // 60
    return f"{h}h{m:02d}m" if h else f"{m}m"


def render(snap: dict, recent: list) -> str:
    if "current" not in snap:
        return f"waiting for first progress marker... (log updated {fmt_td(snap['stale_s'])} ago)"

    n, m, doc = snap["current"], snap["total"], snap["doc"]
    pct = 100.0 * n / m
    parts = [f"[{n}/{m}] {pct:4.1f}%  {doc}"]

    if "started" in snap and n > 1:
        elapsed = (datetime.now() - snap["started"]).total_seconds()
        per_doc = elapsed / max(n - 1, 1)  # doc in progress isn't done yet
        parts.append(f"avg {fmt_td(per_doc)}/doc (incl. any sleep gaps)")
        parts.append(f"ETA ~{fmt_td(per_doc * (m - n + 1))}")

    # Recent pace from this watcher's own observations (immune to old gaps)
    if len(recent) >= 2:
        (t0, n0), (t1, n1) = recent[0], recent[-1]
        if n1 > n0:
            per_doc = (t1 - t0) / (n1 - n0)
            parts.append(f"recent {fmt_td(per_doc)}/doc -> ETA ~{fmt_td(per_doc * (m - n + 1))}")

    if snap["total_chunks"]:
        parts.append(f"gate dropped {snap['dropped_chunks']}/{snap['total_chunks']} chunks")

    stale = snap["stale_s"]
    parts.append("ACTIVE" if stale < 120 else f"STALLED? last write {fmt_td(stale)} ago")
    return "  |  ".join(parts)


def main():
    ap = argparse.ArgumentParser(description="Live monitor for extraction-pipeline logs")
    ap.add_argument("logfile", nargs="?", help="Path to the pipeline console log to watch, "
                    "or a directory (watches its most recently modified *.output/*.log file)")
    ap.add_argument("--latest", metavar="DIR",
                    help="Watch the most recently modified *.output/*.log file under DIR")
    ap.add_argument("--interval", type=float, default=5.0, help="Refresh seconds (default 5)")
    ap.add_argument("--once", action="store_true", help="Print one snapshot and exit")
    args = ap.parse_args()

    target = args.latest or args.logfile
    if not target:
        ap.error("give a log file, a directory, or --latest DIR")
    path = Path(target)
    if path.is_dir():
        candidates = sorted(
            [p for pat in ("*.output", "*.log") for p in path.glob(pat)],
            key=lambda p: p.stat().st_mtime,
        )
        if not candidates:
            sys.exit(f"No *.output or *.log files found in: {path}")
        path = candidates[-1]
        print(f"watching newest log: {path}")
    if not path.exists():
        sys.exit(f"Log file not found: {path}")

    recent = []  # (monotonic_time, doc_number) pairs observed by this watcher
    try:
        while True:
            snap = snapshot(path)
            if "current" in snap:
                if not recent or recent[-1][1] != snap["current"]:
                    recent.append((time.monotonic(), snap["current"]))
                    recent = recent[-4:]  # last 3 doc transitions
            line = render(snap, recent)
            if args.once:
                print(line)
                return
            print("\r" + line[:200].ljust(200), end="", flush=True)
            if snap["complete"]:
                print("\nRun complete.")
                return
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n(watcher stopped; the pipeline keeps running)")


if __name__ == "__main__":
    main()
