"""TOOLS-MAP.md hooks table must name every inner module of each consolidated
entry point, and every entry point must appear as a table row.

Companion to test_hooks_pipeline_doc.py — TOOLS-MAP drifted behind the
pipeline doc (git-diff-stat, token-saver, rl-resume-detect, permission-gate
were missing from its rows).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(ROOT, ".devin", "docs", "TOOLS-MAP.md")

AGGREGATORS = (
    "pre-exec-guard.py", "pre-write-guard.py", "post-exec.py",
    "user-prompt.py", "session-start.py", "stop-guard.py",
)


def _inner_modules(entry):
    src = open(os.path.join(ROOT, "scripts", entry), encoding="utf-8").read()
    return {m[:-3] for m in re.findall(r"'([a-z0-9_\-]+\.py)'", src)
            if m != "_hookrun.py"}


def _doc():
    return open(DOC, encoding="utf-8").read()


def test_every_aggregator_inner_module_named():
    doc = _doc()
    for ep in AGGREGATORS:
        missing = {m for m in _inner_modules(ep) if m not in doc}
        assert not missing, f"{ep}: inner modules absent from TOOLS-MAP: {sorted(missing)}"


def test_every_entry_point_is_a_row():
    doc = _doc()
    hooks_src = open(os.path.join(ROOT, "hooks.v1.json"), encoding="utf-8").read()
    entry_points = set(re.findall(r'scripts/([A-Za-z0-9_\-]+\.py)', hooks_src))
    missing = {ep for ep in entry_points if ep not in doc}
    assert not missing, f"entry points absent from TOOLS-MAP: {sorted(missing)}"


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-q"]))
