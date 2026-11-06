#!/usr/bin/env python3
"""index.py - build/refresh the code-graph index (incremental)."""
import argparse
import os
import sys
import time

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
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    t0 = time.time()
    db = cg.open_db(db_path)
    seen, updated = set(), 0
    for path in cg.iter_files(root):
        rel = os.path.relpath(path, root).replace("\\", "/")
        seen.add(rel)
        if cg.index_file(db, root, path):
            updated += 1
    # purge vanished files
    for (rel,) in db.execute("SELECT path FROM files").fetchall():
        if rel not in seen:
            for t in ("symbols", "edges", "fts"):
                db.execute(f"DELETE FROM {t} WHERE file=?", (rel,))
            db.execute("DELETE FROM files WHERE path=?", (rel,))
    db.commit()
    nsyms = db.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
    print({"files": len(seen), "updated": updated,
           "symbols": nsyms,
           "elapsed_s": round(time.time() - t0, 2),
           "db": db_path})
    return 0


if __name__ == "__main__":
    sys.exit(main())
