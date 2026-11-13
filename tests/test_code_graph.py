"""extensions/code-graph - index/query/detect_changes fixture tests (M2_10)."""
import json
import os
import subprocess
import sys

import pytest

EXT = os.path.join(os.path.dirname(__file__), "..", "extensions",
                   "code-graph")
PY = sys.executable


def run(script, *argv):
    return subprocess.run([PY, os.path.join(EXT, script), *argv],
                          capture_output=True, text=True)


@pytest.fixture()
def corpus(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "alpha.py").write_text(
        "import beta\n\ndef myCamelFunc():\n    pass\n"
        "class Snake_case:\n    pass\n")
    (src / "beta.py").write_text("def helper():\n    pass\n")
    r = run("index.py", str(tmp_path))
    assert r.returncode == 0, r.stderr
    return tmp_path


def test_symbols_camel_and_snake(corpus):
    r = run("query.py", str(corpus), "symbols", "mycamel")
    assert "myCamelFunc" in r.stdout
    r = run("query.py", str(corpus), "symbols", "snake")
    assert "Snake_case" in r.stdout


def test_outline_and_refs_and_files(corpus):
    r = run("query.py", str(corpus), "outline", "src/alpha.py")
    assert "myCamelFunc" in r.stdout and "Snake_case" in r.stdout
    r = run("query.py", str(corpus), "refs", "beta")
    assert "alpha.py" in r.stdout
    r = run("query.py", str(corpus), "files", "alpha")
    assert "alpha.py" in r.stdout


def test_detect_changes_clean_then_dirty(corpus):
    r = run("detect_changes.py", str(corpus))
    rep = json.loads(r.stdout)
    assert rep["changed"] == [] and rep["new"] == [] and rep["removed"] == []
    assert rep["api_version"] == 2
    (corpus / "src" / "alpha.py").write_text("def v2():\n    pass\n")
    rep = json.loads(run("detect_changes.py", str(corpus)).stdout)
    assert "src/alpha.py" in rep["changed"]
    (corpus / "src" / "new.py").write_text("def n():\n    pass\n")
    rep = json.loads(run("detect_changes.py", str(corpus)).stdout)
    assert "src/new.py" in rep["new"]


def test_incremental_reindex(corpus):
    (corpus / "src" / "alpha.py").write_text("def added():\n    pass\n")
    run("index.py", str(corpus))
    r = run("query.py", str(corpus), "symbols", "added")
    assert "added" in r.stdout


def test_query_without_index_graphdown(tmp_path):
    r = run("query.py", str(tmp_path), "symbols", "x")
    assert r.returncode == 2 and "GRAPH-DOWN" in r.stderr
