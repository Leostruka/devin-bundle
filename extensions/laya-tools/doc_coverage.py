"""doc_coverage — JEV-5 doc-to-test coverage check (stdlib only).

For each changed rule/doc/ADR, verify an EXPLICIT declared contract
exists in tests. The mapping is user-authored JSON — heuristics never
prove coverage:

  {"AGENTS.md": ["tests/validation/test_rules.py::test_rule_contract"],
   ".devin/rules/x.md": ["tests/validation/test_x.py"]}

A target is "file.py" or "file.py::test_name". Targets are confined
to `<tests_root>/tests/validation/`: `tests_root` is the PROJECT root,
not the tests directory itself. A valid target must be a real,
non-symlinked `test_*.py` file inside that directory that parses and
declares actual tests — module-level `test_*` functions or `test_*`
methods inside `Test*` classes, found via AST (a `def` inside a
docstring or comment does not count). For `::name` targets the named
test must be declared; bare-file targets require at least one test
declaration in the file.

A changed doc with no mapping entry, a malformed mapping, or a broken
target is an Important finding — a changed rule without an executable
contract is never Minor (Rule 15 evidence standard). Files are parsed
with ast, never imported or executed.

CLI:
  python doc_coverage.py --changed AGENTS.md .devin/rules/x.md \
      --map coverage.json [--tests-root .]
JSON on stdout; exit 0 on success, 2 on usage/IO error.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

VALIDATION_SUBDIR = ("tests", "validation")


def _declared_tests(tree):
    """Real test declarations in an AST: module-level test_*
    functions plus test_* methods of Test* classes."""
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name.startswith("test_"):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef) \
                and node.name.startswith("Test"):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef,
                                    ast.AsyncFunctionDef)) \
                        and sub.name.startswith("test_"):
                    names.add(sub.name)
    return names


def _resolve_confined(rel_path, tests_root):
    """Return (Path, reason). reason None on success: relative,
    non-escaping, inside <tests_root>/tests/validation, existing,
    not a symlink."""
    if not isinstance(rel_path, str) or not rel_path \
            or Path(rel_path).is_absolute():
        return None, "target_invalid"
    base = Path(tests_root).resolve()
    confine = base.joinpath(*VALIDATION_SUBDIR)
    cand = (base / rel_path).resolve()
    try:
        cand.relative_to(confine)
    except ValueError:
        return None, "target_out_of_scope"
    raw = base / rel_path
    if not raw.is_file():
        return None, "missing_test_file"
    if raw.is_symlink():
        return None, "target_is_symlink"
    return raw, None


def _check_target(target, tests_root):
    """One mapping target -> (ok, reason)."""
    if not isinstance(target, str) or not target:
        return False, "target_invalid"
    path, sep, func = target.partition("::")
    f, reason = _resolve_confined(path, tests_root)
    if reason:
        return False, reason
    name = Path(path).name
    if not (name.startswith("test_") and name.endswith(".py")):
        return False, "not_a_test_file"
    try:
        tree = ast.parse(f.read_text(encoding="utf-8",
                                     errors="replace"))
    except (SyntaxError, ValueError, OSError):
        return False, "unparseable_test_file"
    declared = _declared_tests(tree)
    if func:
        if func not in declared:
            return False, "missing_test_function"
    elif not declared:
        return False, "no_test_declarations"
    return True, "contract_present"


def check_coverage(changed_docs, mapping, *, tests_root="."):
    """changed_docs: iterable (materialized once) of doc/rule paths
    that changed. mapping: {doc_path: [test targets]}. Returns covered
    list and Important findings; never raises."""
    docs = list(changed_docs or [])
    if not isinstance(mapping, dict):
        return {"ok": False, "error": "mapping_invalid",
                "covered": [], "findings": [
                    {"doc": d, "severity": "Important",
                     "reason": "mapping_invalid", "target": None}
                    for d in docs],
                "stats": {"changed": len(docs), "covered": 0,
                          "findings": len(docs)}}
    covered, findings = [], []
    for doc in docs:
        targets = mapping.get(doc)
        if not isinstance(targets, list) or not targets:
            reason = "no_contract_mapping" if targets is None \
                else "mapping_entry_invalid"
            findings.append({"doc": doc, "severity": "Important",
                             "reason": reason, "target": None})
            continue
        ok_all = True
        for t in targets:
            ok, reason = _check_target(t, tests_root)
            if not ok:
                ok_all = False
                findings.append({"doc": doc, "severity": "Important",
                                 "reason": reason, "target": t})
        if ok_all:
            covered.append(doc)
    return {"ok": True, "covered": covered, "findings": findings,
            "stats": {"changed": len(docs),
                      "covered": len(covered),
                      "findings": len(findings)}}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="JEV-5 explicit doc-to-test coverage check")
    ap.add_argument("--changed", nargs="+", required=True,
                    help="changed rule/doc/ADR paths")
    ap.add_argument("--map", required=True, dest="map_path",
                    help="JSON file: doc path -> [test targets]")
    ap.add_argument("--tests-root", default=".",
                    help="PROJECT root; targets must live under "
                         "<tests-root>/tests/validation/")
    args = ap.parse_args(argv)
    try:
        mapping = json.loads(Path(args.map_path).read_text(
            encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": f"map_error:{e}"}))
        return 2
    out = check_coverage(args.changed, mapping,
                         tests_root=args.tests_root)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
