#!/usr/bin/env python3
"""
Local review server for the human-review tagging tool (tools/tagging_tool.html).

The tagging tool fetches data/*.json to let you review and correct the automated
technique detections. On its own it can only *download* a copy of the corrected
model_technique_map.json (which you then have to move into data/ by hand). This
server closes that gap: it serves the repo so the tool loads, and accepts the
tool's "Save" as POST /api/save-map, writing data/model_technique_map.json in
place (after backing up the previous version). Corrections persist immediately;
then a normal commit + push flows them to the live dashboard.

Usage:
    py scripts/review_server.py                 # http://127.0.0.1:8000
    py scripts/review_server.py --port 8123

Then open:
    http://127.0.0.1:8000/tools/tagging_tool.html

Backups of every save land in cache/tagging_backups/. Bind is localhost-only.
"""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent           # repo root
MAP_PATH = ROOT / "data" / "model_technique_map.json"
BACKUP_DIR = ROOT / "cache" / "tagging_backups"
SAVE_ROUTE = "/api/save-map"


def _validate_shape(obj):
    """Light structural check so a malformed POST can't corrupt the dataset.

    Returns an error string, or None if the shape is acceptable.
    """
    if not isinstance(obj, dict):
        return "top level must be an object keyed by document id"
    if not obj:
        return "refusing to save an empty map"
    for key, techs in obj.items():
        if not isinstance(key, str):
            return f"document key {key!r} is not a string"
        if not isinstance(techs, list):
            return f"value for {key!r} must be an array of technique entries"
        for t in techs:
            if not isinstance(t, dict) or "techniqueId" not in t:
                return f"an entry under {key!r} is missing techniqueId"
    return None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # Never cache data files — the tool must see the latest save on reload.
        if self.path.endswith(".json"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path.rstrip("/") != SAVE_ROUTE:
            self._send_json(404, {"ok": False, "error": "unknown endpoint"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            obj = json.loads(raw.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - report any parse failure to the tool
            self._send_json(400, {"ok": False, "error": f"bad JSON: {exc}"})
            return

        err = _validate_shape(obj)
        if err:
            self._send_json(422, {"ok": False, "error": err})
            return

        # Back up the current file before overwriting.
        backup_name = None
        if MAP_PATH.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = BACKUP_DIR / f"model_technique_map.{stamp}.json"
            shutil.copy2(MAP_PATH, backup)
            backup_name = backup.name

        MAP_PATH.write_text(
            json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        links = sum(len(v) for v in obj.values())
        active = sum(1 for v in obj.values() for t in v if t.get("active", True))
        print(
            f"  [save] {len(obj)} docs / {links} links / {active} active"
            + (f"  (backup {backup_name})" if backup_name else "")
        )
        self._send_json(
            200,
            {
                "ok": True,
                "docs": len(obj),
                "links": links,
                "active": active,
                "backup": backup_name,
            },
        )

    def log_message(self, fmt, *args):  # quieter, indented logging
        sys.stderr.write("  " + (fmt % args) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Local review server for the tagging tool")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/tools/tagging_tool.html"
    print("=" * 64)
    print("LLM-Safety review server")
    print(f"  serving repo : {ROOT}")
    print(f"  open tool    : {url}")
    print(f"  save endpoint: POST {SAVE_ROUTE} -> data/model_technique_map.json")
    print(f"  backups      : {BACKUP_DIR}")
    print("  Ctrl+C to stop")
    print("=" * 64)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
