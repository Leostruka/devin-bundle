#!/usr/bin/env python3
"""graph-query.py - graph-before-grep retrieval spike.

Expands a natural-language-ish query through existing indexes and returns
ranked file paths with rationale, as a JSON envelope:

  {"ok": true, "query": ..., "results": [{"file", "score", "rationale"}],
   "degraded": [...]}

Sources (all optional, degrades gracefully):
- code-graph FTS index (.devin/code-graph/index.db) via extensions/code-graph
- file path substring matches in the same index
- .devin/memory note cues (keyword/path/symbol frontmatter)

Exit non-zero when ok is false. UTF-8 pinned.
"""
import argparse
import glob
import io
import json
import os
import re
import sys
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
    return {"bundle": _bundle_version(), "wrapper": "graph-query"}


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


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

STOPWORDS = {
    "the", "a", "an", "how", "does", "do", "is", "are", "what", "where",
    "when", "which", "to", "for", "of", "in", "on", "and", "or", "that",
    "this", "it", "i", "we", "can", "should", "would", "with", "from",
    "me", "my", "show", "find", "get", "use", "used", "work", "works",
}


def fail(msg):
    print(_dumps({"ok": False, "error": msg}))
    return 1


def query_terms(q):
    toks = [t.lower() for t in re.findall(r"[A-Za-z_][\w]*", q)]
    return [t for t in toks if t not in STOPWORDS and len(t) > 1]


def load_graph(root, degraded):
    """Open the code-graph DB if present; return (db, ext_dir) or (None, _)."""
    bundle = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ext_dir = os.path.join(bundle, "extensions", "code-graph")
    db_path = os.path.join(root, ".devin", "code-graph", "index.db")
    if not os.path.isfile(db_path):
        degraded.append("code-graph index missing: run "
                        "python extensions/code-graph/index.py")
        return None
    try:
        import sqlite3
        return sqlite3.connect(db_path)
    except Exception as e:  # sqlite failure: degrade, do not die
        degraded.append(f"code-graph open failed: {e}")
        return None


def _add(hits, f, term, rationale):
    h = hits.setdefault(f, {"terms": set(), "rationale": set()})
    h["terms"].add(term)
    h["rationale"].add(rationale)


def graph_hits(db, terms, limit):
    """Return {file: {"terms", "rationale"}} from symbol FTS + path LIKE."""
    hits = {}
    if not terms:
        return hits
    # OR semantics: each term matches symbol tokens independently
    for t in terms:
        try:
            rows = db.execute(
                "SELECT s.name, s.file, s.line FROM fts f "
                "JOIN symbols s ON s.name=f.name AND s.file=f.file "
                "WHERE f.content MATCH ? LIMIT ?", (t + "*", limit)).fetchall()
        except Exception:
            rows = []
        for name, f, line in rows:
            _add(hits, f, t, f"symbol {name}:{line}")
    for t in terms:
        if len(t) < 3:
            continue
        rows = db.execute(
            "SELECT path FROM files WHERE path LIKE ? LIMIT ?",
            ("%" + t + "%", limit)).fetchall()
        for (p,) in rows:
            _add(hits, p, t, f"path contains '{t}'")
    return hits


def memory_hits(root, terms, limit):
    """Return {file: {"terms", "rationale"}} from memory note cue matches."""
    hits = {}
    mdir = os.path.join(root, ".devin", "memory")
    if not os.path.isdir(mdir):
        return hits
    joined = " ".join(terms)
    for p in glob.glob(os.path.join(mdir, "**", "*.md"), recursive=True):
        if p.endswith("MOC.md"):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read().lower()
        except OSError:
            continue
        matched = [t for t in terms if t in text]
        if not matched:
            continue
        rel = os.path.relpath(p, root).replace("\\", "/")
        for t in matched:
            _add(hits, rel, t, "memory note mentions terms")
        # cues of kind path: promote referenced paths
        for m in re.finditer(r'-\s*path:\s*"?([^"\n]+)"?', text):
            tgt = m.group(1).strip()
            if (tgt and any(t in tgt for t in terms)) or joined in tgt:
                for t in matched:
                    _add(hits, tgt, t, f"memory cue path from {rel}")
    return hits


def main():
    ap = argparse.ArgumentParser(description="graph-before-grep retrieval")
    ap.add_argument("query", help="natural-language-ish query")
    ap.add_argument("--root", default=None,
                    help="repo root (default: parent of scripts/)")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    root = os.path.abspath(args.root) if args.root else os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isdir(root):
        return fail(f"root not found: {root}")

    terms = query_terms(args.query)
    degraded = []
    db = load_graph(root, degraded)

    file_hits = {}
    if db is not None:
        file_hits = graph_hits(db, terms, args.limit)
    for f, h in memory_hits(root, terms, args.limit).items():
        e = file_hits.setdefault(f, {"terms": set(), "rationale": set()})
        e["terms"] |= h["terms"]
        e["rationale"] |= h["rationale"]

    results = []
    for f, h in file_hits.items():
        rationale = sorted(h["rationale"])
        nsym = sum(1 for r in rationale if r.startswith("symbol"))
        # term coverage dominates; symbol hits break ties
        score = 10 * len(h["terms"]) + min(nsym, 5)
        results.append({"file": f, "score": score,
                        "matched_terms": sorted(h["terms"]),
                        "rationale": rationale[:8]})
    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[: args.limit]

    out = {"ok": True, "query": args.query, "terms": terms,
           "results": results}
    if degraded:
        out["degraded"] = degraded
    print(_dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
