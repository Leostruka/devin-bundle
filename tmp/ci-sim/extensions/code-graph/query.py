#!/usr/bin/env python3
"""query.py - symbols / outline / refs / files over the code-graph."""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code_graph as cg

DB_REL = os.path.join(".devin", "code-graph", "index.db")

_BUNDLE_VERSION = None


def _bundle_version():
    """Bundle version from the nearest manifest.json ancestor, cached.

    manifest.json sits at the install root in both the repo layout
    (extensions/<name>/ -> repo root) and the live install
    (%APPDATA%/devin/extensions/<name>/ -> %APPDATA%/devin). Only a
    JSON object with a "name" key counts as the bundle manifest;
    malformed or unrelated JSON yields "" rather than a guess.
    """
    global _BUNDLE_VERSION
    if _BUNDLE_VERSION is None:
        _BUNDLE_VERSION = ""
        for parent in Path(__file__).absolute().parents:
            mf = parent / "manifest.json"
            if mf.is_file():
                try:
                    data = json.loads(mf.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    break
                if isinstance(data, dict) and data.get("name"):
                    _BUNDLE_VERSION = str(data.get("version") or "")
                break
    return _BUNDLE_VERSION


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "code-graph"}


def _stamp(payload):
    """Assert envelope contract v2 on a response dict (in place)."""
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)


def _emit(payload):
    print(_dumps(payload, indent=1))


def _db(args):
    path = args.db or os.path.join(os.path.abspath(args.root), DB_REL)
    if not os.path.isfile(path):
        if getattr(args, "json", None) or getattr(args, "envelope", None):
            _emit({"ok": False, "status": "missing",
                   "error": "code-graph index missing - "
                            "run index.py first"})
        else:
            print("[GRAPH-DOWN] index not found - run index.py first; "
                  "fall back to rg/glob", file=sys.stderr)
        sys.exit(2)
    return cg.open_db(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--db", default=None)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--envelope", action="store_true",
                    help="wrap --json output in the contract v2 envelope")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("symbols"); s.add_argument("q")
    s = sub.add_parser("outline"); s.add_argument("file")
    s = sub.add_parser("refs"); s.add_argument("symbol")
    s = sub.add_parser("files"); s.add_argument("substr")
    for name in ("symbols", "outline", "refs", "files"):
        sub.choices[name].add_argument("--limit", type=int, default=20)
        sub.choices[name].add_argument("--json", action="store_true")
        sub.choices[name].add_argument(
            "--envelope", action="store_true",
            help="wrap --json output in the contract v2 envelope")
    args = ap.parse_args()
    db = _db(args)
    limit = args.limit

    if args.cmd == "symbols":
        terms = " ".join(t + "*" for t in re.findall(r"\w+", args.q))
        rows = db.execute(
            "SELECT s.name, s.file, s.line FROM fts f "
            "JOIN symbols s ON s.name=f.name AND s.file=f.file "
            "WHERE f.content MATCH ? LIMIT ?", (terms, limit)).fetchall()
        out = [{"name": n, "file": f, "line": l} for n, f, l in rows]
    elif args.cmd == "outline":
        rows = db.execute(
            "SELECT kind, name, line FROM symbols WHERE file=? "
            "ORDER BY line LIMIT ?", (args.file, limit)).fetchall()
        out = [{"kind": k, "name": n, "line": l} for k, n, l in rows]
    elif args.cmd == "refs":
        rows = db.execute(
            "SELECT file, target FROM edges WHERE target LIKE ? "
            "LIMIT ?", ("%" + args.symbol + "%", limit)).fetchall()
        out = [{"file": f, "imports": t} for f, t in rows]
    else:  # files
        rows = db.execute(
            "SELECT path FROM files WHERE path LIKE ? LIMIT ?",
            ("%" + args.substr + "%", limit)).fetchall()
        out = [{"file": r[0]} for r in rows]

    if args.envelope:
        _emit({"ok": True, "result": out})
    elif args.json:
        sys.stdout.write(json.dumps(out, indent=1) + "\n")
    else:
        for r in out:
            print(" ".join(f"{k}={v}" for k, v in r.items()))
        print(f"-- {len(out)} result(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
