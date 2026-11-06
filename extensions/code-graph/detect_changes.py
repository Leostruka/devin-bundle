#!/usr/bin/env python3
"""detect_changes.py - files whose mtime+sha differ from the index."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import code_graph as cg

DB_REL = os.path.join(".devin", "code-graph", "index.db")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    db_path = args.db or os.path.join(root, DB_REL)
    if not os.path.isfile(db_path):
        print(json.dumps({"changed": [], "new": [], "removed": [],
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
    print(json.dumps({"changed": sorted(changed),
                      "new": sorted(new),
                      "removed": sorted(removed)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
