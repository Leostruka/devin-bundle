"""ci.yml contract — path filter exists and classifies correctly (#487)."""
import os
import re

import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..")
WF = os.path.join(ROOT, ".github", "workflows", "ci.yml")

DOC_RE = re.compile(
    r"^docs/|^\.devin/(docs|issues|scratch|research|ledgers|plans|evals"
    r"|goals|metrics|approvals)/|\.md$|^manifest\.json$")


def _doc_only(paths):
    return all(DOC_RE.search(p) for p in paths)


def test_workflow_parses_and_has_changes_job():
    wf = yaml.safe_load(open(WF, encoding="utf-8"))
    assert "changes" in wf["jobs"]
    for job in ("test", "rust", "install"):
        j = wf["jobs"][job]
        assert j.get("needs") == "changes"
        assert "changes.outputs.code" in (j.get("if") or "")


def test_doc_filter_classification():
    assert _doc_only(["docs/a.md", "CHANGELOG.md", "manifest.json",
                      ".devin/scratch/x/t.json"])
    assert _doc_only([".devin/issues/12.md"])
    assert not _doc_only(["scripts/x.py"])
    assert not _doc_only(["docs/a.md", "tests/test_x.py"])
    # the classic trap: leading dot must not be stripped
    assert _doc_only([".devin/docs/STATE.md"])
    assert not _doc_only([".github/workflows/ci.yml"])


def test_ci_aggregator_accepts_skipped():
    s = open(WF, encoding="utf-8").read()
    assert "'skipped'" in s  # docs-only PRs leave needs skipped, not failed
