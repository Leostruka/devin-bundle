#!/usr/bin/env python3
"""simplify-scan - periodic rot/dead-code sweep over first-party code.

Scans Python files under the repo root for rot signals:

- comment markers: TODO / FIXME / HACK / XXX (file:line)
- oversized files: Python sources over SIZE_LIMIT lines
- unreferenced defs: functions/classes whose name occurs <= 1 time
  across the whole scan (definition site only)
- exception swallows: `except: pass` / `except Exception: pass`

Usage: simplify-scan.py [--root DIR]
JSON to stdout: {"ok": true, "totals": {...}, "items": [...]}
Exit 0 ok, 1 on {"ok": false} (e.g. bad root), 2 on misuse.
"""
import ast
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SIZE_LIMIT = 800
MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
SKIP_DIRS = {".git", ".venv", "node_modules", "target", "__pycache__",
             "dist", "build", ".devin"}


def iter_py_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def scan(root):
    items = []
    sources = {}   # relpath -> source text
    defs = []      # (name, relpath, lineno, kind)
    files_seen = 0
    for path in iter_py_files(root):
        rel = os.path.relpath(path, root)
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        files_seen += 1
        sources[rel] = src
        lines = src.splitlines()
        if len(lines) > SIZE_LIMIT:
            items.append({"type": "oversized_file", "file": rel,
                          "line": 0, "lines": len(lines),
                          "limit": SIZE_LIMIT})
        for i, line in enumerate(lines, 1):
            hashpos = line.find("#")
            for m in MARKER_RE.finditer(line):
                # comments only - docstrings/strings/regex literals
                # produce noise (incl. this scanner's own docstring)
                if hashpos < 0 or m.start() < hashpos:
                    continue
                items.append({"type": "marker", "file": rel,
                              "line": i, "tag": m.group(1),
                              "text": line.strip()[:120]})
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        def _collect_defs(node, top_level):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.ClassDef)):
                    # only module top-level defs are meaningful for the
                    # name-count heuristic; methods are dispatched via
                    # getattr/reflection (http do_*, HTMLParser handle_*,
                    # hook check_*) and can't be resolved textually
                    if top_level:
                        # pytest fixtures resolve by autouse/parameter name,
                        # never by direct call — not dead code
                        fixture = any(
                            (isinstance(d, ast.Attribute)
                             and d.attr == "fixture")
                            or (isinstance(d, ast.Name)
                                and d.id == "fixture")
                            or (isinstance(d, ast.Call)
                                and isinstance(d.func, ast.Attribute)
                                and d.func.attr == "fixture")
                            or (isinstance(d, ast.Call)
                                and isinstance(d.func, ast.Name)
                                and d.func.id == "fixture")
                            for d in getattr(child, "decorator_list", []))
                        if not fixture:
                            kind = "class" if isinstance(child, ast.ClassDef) \
                                else "function"
                            defs.append((child.name, rel, child.lineno, kind))
                    _collect_defs(child, False)
                else:
                    _collect_defs(child, top_level)

        _collect_defs(tree, True)

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # a sibling handler that re-raises (except X: raise) makes
                # an `except Exception/bare: pass` self-documenting intent
                sibling_reraise = any(
                    len(h.body) == 1 and isinstance(h.body[0], ast.Raise)
                    for h in node.handlers)
                for h in node.handlers:
                    bare = h.type is None
                    exc_e = (isinstance(h.type, ast.Name)
                             and h.type.id == "Exception")
                    annotated = (len(h.body) == 1
                                 and isinstance(h.body[0], ast.Pass)
                                 and h.body[0].lineno <= len(lines)
                                 and "#" in lines[h.body[0].lineno - 1])
                    if (bare or exc_e) and len(h.body) == 1 \
                            and isinstance(h.body[0], ast.Pass) \
                            and not annotated and not sibling_reraise:
                        items.append({"type": "except_pass", "file": rel,
                                      "line": h.lineno,
                                      "kind": "bare" if bare else "Exception"})
    counts = {}
    word_re = re.compile(r"\b\w+\b")
    for src in sources.values():
        for m in word_re.finditer(src):
            w = m.group(0)
            counts[w] = counts.get(w, 0) + 1
    for name, rel, lineno, kind in defs:
        if name.startswith("__") and name.endswith("__"):
            continue
        # pytest collects test_*/Test* by name; they are never referenced
        if name.startswith("test_") or name.startswith("Test"):
            continue
        if counts.get(name, 0) <= 1:
            src_lines = sources[rel].splitlines()
            if lineno <= len(src_lines) and "#" in src_lines[lineno - 1]:
                continue  # annotated on the def line, e.g. `# public-api`
            items.append({"type": "unreferenced_def", "file": rel,
                          "line": lineno, "name": name, "kind": kind})
    totals = {"files_scanned": files_seen, "items": len(items)}
    for it in items:
        key = it["type"] + "s"
        totals[key] = totals.get(key, 0) + 1
    return {"ok": True, "totals": totals, "items": items}


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    root = Path(__file__).resolve().parent.parent
    args = argv[1:]
    for i, a in enumerate(args):
        if a == "--root":
            if i + 1 >= len(args):
                print(json.dumps({"ok": False,
                                  "error": "--root <dir>"}))
                return 2
            root = Path(args[i + 1]).resolve()
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
    if not root.is_dir():
        print(json.dumps({"ok": False,
                          "error": "root not a directory: " + str(root)}))
        return 1
    print(json.dumps(scan(str(root)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
