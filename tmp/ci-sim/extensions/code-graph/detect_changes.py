#!/usr/bin/env python3
"""detect_changes.py - files whose mtime+sha differ from the index."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code_graph as cg
from pathlib import Path

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "code-graph"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)


DB_REL = os.path.join(".devin", "code-graph", "index.db")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    db_path = args.db or os.path.join(root, DB_REL)
    if not os.path.isfile(db_path):
        print(_dumps({"changed": [], "new": [], "removed": [],
                          "error": "no index"}))
        return 0
    db = cg.open_db(db_path)
    recorded = {r[0]: (r[1], r[2]) for r in db.execute(
        "SELECT path, mtime, sha FROM files")}
    live = {}
    for p in cg.iter_files(root):
        rel = os.path.relpath(p, root).replace("\\", "/")
        live[rel] = p
    changed = [rel for rel, p in live.items()
               if rel in recorded and
               cg.sha1(p) != recorded[rel][1]]
    new = [rel for rel in live if rel not in recorded]
    removed = [rel for rel in recorded if rel not in live]
    print(_dumps({"changed": sorted(changed),
                      "new": sorted(new),
                      "removed": sorted(removed)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
