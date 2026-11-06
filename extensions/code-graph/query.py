#!/usr/bin/env python3
"""query.py - symbols / outline / refs / files over the code-graph."""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code_graph as cg

DB_REL = os.path.join(".devin", "code-graph", "index.db")


def _db(args):
    path = args.db or os.path.join(os.path.abspath(args.root), DB_REL)
    if not os.path.isfile(path):
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
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("symbols"); s.add_argument("q")
    s = sub.add_parser("outline"); s.add_argument("file")
    s = sub.add_parser("refs"); s.add_argument("symbol")
    s = sub.add_parser("files"); s.add_argument("substr")
    for name in ("symbols", "outline", "refs", "files"):
        sub.choices[name].add_argument("--limit", type=int, default=20)
        sub.choices[name].add_argument("--json", action="store_true")
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

    if args.json:
        print(json.dumps(out, indent=1))
    else:
        for r in out:
            print(" ".join(f"{k}={v}" for k, v in r.items()))
        print(f"-- {len(out)} result(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
