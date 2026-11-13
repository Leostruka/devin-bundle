"""HOOKS-PIPELINE.md must match hooks.v1.json + the entry points' inner lists.

Drift guard: entry points have been added before without updating the doc
(file-size-guard, memory-post-edit) and the README arithmetic went stale.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _entry_points():
    s = open(os.path.join(ROOT, "hooks.v1.json"), encoding="utf-8").read()
    return set(re.findall(r'scripts/([A-Za-z0-9_\-]+\.py)', s))


def _doc_rows():
    doc = open(os.path.join(ROOT, ".devin", "docs", "HOOKS-PIPELINE.md"),
               encoding="utf-8").read()
    return set(re.findall(r'^\|\s*`([a-z0-9_\-]+\.py)`', doc, re.M))


def _inner_lists(entry):
    src = open(os.path.join(ROOT, "scripts", entry), encoding="utf-8").read()
    return set(re.findall(r"'([a-z0-9_\-]+\.py)'", src))


def test_doc_covers_every_entry_point():
    missing = _entry_points() - _doc_rows()
    assert not missing, f"entry points absent from HOOKS-PIPELINE table: {sorted(missing)}"


def test_inner_modules_exist_on_disk():
    for ep in _entry_points():
        for mod in _inner_lists(ep):
            if mod in ("_hookrun.py",):
                continue
            path = os.path.join(ROOT, "scripts", mod)
            assert os.path.exists(path), f"{ep} references missing inner module {mod}"


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-q"]))
