"""Declared-scope contract tests (ISSUE_08 C11).

`data/hook-scope.json` lists hook check arms whose lesson only applies in
a specific context (today: os). Absence = universal = always run. The file
is metadata, not a runtime filter: these tests pin that (a) every declared
os-scoped arm actually carries its guard in code (a removed guard would
fire on every platform and cannot be caught by tests on this host), and
(b) the one functional consequence we can test here, MSYS drive
translation, happens on nt and is skipped when os.name is patched off.
"""
import importlib.util
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "data", "hook-scope.json")


def _load_registry():
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def test_registry_sanity():
    reg = _load_registry()
    arms = reg["scoped_arms"]
    ids = [a["id"] for a in arms]
    assert len(ids) == len(set(ids)), "duplicate scope ids"
    for a in arms:
        path = os.path.join(ROOT, a["file"])
        assert os.path.isfile(path), a["file"]
        assert a["os"], f"{a['id']}: empty os list would mean universal"
        assert a["guard"], f"{a['id']}: guard text required"


def test_scoped_arms_keep_their_guard():
    reg = _load_registry()
    for a in reg["scoped_arms"]:
        with open(os.path.join(ROOT, a["file"]), encoding="utf-8") as f:
            src = f.read()
        assert a["guard"] in src, (
            f"{a['id']}: guard {a['guard']!r} missing in {a['file']} - "
            "an os-scoped arm without its guard fires on every platform "
            "and host tests cannot catch it (os.name is constant here)")


def _load_module(name):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, "scripts", name.replace("_", "-") + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_msys_drive_translation_is_nt_scoped():
    mod = _load_module("architecture_gate")
    cmd = "touch /d/work/x.py"
    nt_targets = list(mod._abs_targets(cmd))
    assert any(t.startswith("D:") or t.startswith("d:")
               for t in nt_targets), nt_targets
    saved = os.name
    try:
        os.name = "posix"
        posix_targets = list(mod._abs_targets(cmd))
        # Guard skipped: /d/... must pass through unconverted (on a real
        # POSIX host os.path is posixpath and the path survives intact;
        # ntpath still roots it on the current drive, which is fine - the
        # point is no MSYS drive-letter rewrite happened).
        assert posix_targets == [os.path.abspath("/d/work/x.py")], (
            posix_targets)
    finally:
        os.name = saved
