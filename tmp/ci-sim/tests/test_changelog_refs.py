"""changelog-refs — missing-ref detection + docs(changelog) exclusion (#488)."""
import importlib.util
import os
import sys
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "changelog_refs",
    os.path.join(os.path.dirname(__file__), "..", "scripts",
                 "changelog-refs.py"))
mod = importlib.util.module_from_spec(spec)
sys.modules["changelog_refs"] = mod
spec.loader.exec_module(mod)

CHLOG = "## [Unreleased]\n- covered thing (#1)\n\n## [1.0]\n"


def test_missing_detected_and_covered_skipped():
    subs = ["feat: covered thing (#1)", "feat: new thing (#42)"]
    with patch.object(mod, "_subjects", return_value=subs):
        got = mod.missing_refs(CHLOG)
    assert got == [("42", "feat: new thing (#42)")]


def test_docs_changelog_prs_excluded():
    subs = ["docs(changelog): refs (#9)", "feat: x (#10)"]
    with patch.object(mod, "_subjects", return_value=subs):
        got = mod.missing_refs(CHLOG)
    assert [n for n, _s in got] == ["10"]


def test_empty_when_all_covered():
    subs = ["feat: covered thing (#1)"]
    with patch.object(mod, "_subjects", return_value=subs):
        assert mod.missing_refs(CHLOG) == []
