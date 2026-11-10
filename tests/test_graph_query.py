"""Tests for scripts/graph-query.py (graph-before-grep spike)."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "graph-query.py")


def run_gq(args, cwd=None):
    return subprocess.run(
        [sys.executable, SCRIPT] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=cwd or ROOT)


def _build_index(root):
    """Index a temp root with the real code-graph indexer."""
    ext = os.path.join(ROOT, "extensions", "code-graph")
    sys.path.insert(0, ext)
    import code_graph as cg  # noqa: E401
    db_dir = os.path.join(root, ".devin", "code-graph")
    os.makedirs(db_dir, exist_ok=True)
    db = cg.open_db(os.path.join(db_dir, "index.db"))
    for dirpath, _dirs, names in os.walk(root):
        if ".devin" in dirpath:
            continue
        for n in names:
            if n.endswith((".py", ".md")):
                cg.index_file(db, root, os.path.join(dirpath, n))
    db.commit()


def test_envelope_ok_and_ranked_results(tmp_path):
    (tmp_path / "alpha.py").write_text(
        "def token_budget():\n    return 42\n", encoding="utf-8")
    (tmp_path / "beta.py").write_text(
        "def unrelated_thing():\n    pass\n", encoding="utf-8")
    _build_index(str(tmp_path))
    p = run_gq(["token budget", "--root", str(tmp_path)])
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["ok"] is True
    files = [r["file"] for r in out["results"]]
    assert "alpha.py" in files
    assert files.index("alpha.py") < files.index("beta.py") \
        if "beta.py" in files else True
    top = out["results"][0]
    assert top["file"] == "alpha.py"
    assert any("symbol" in r for r in top["rationale"])


def test_degrades_without_index(tmp_path):
    (tmp_path / "only.py").write_text("x = 1\n", encoding="utf-8")
    p = run_gq(["anything", "--root", str(tmp_path)])
    assert p.returncode == 0
    out = json.loads(p.stdout)
    assert out["ok"] is True
    assert out["results"] == []
    assert out["degraded"]


def test_bad_root_exits_nonzero(tmp_path):
    p = run_gq(["q", "--root", str(tmp_path / "nope")])
    assert p.returncode != 0
    out = json.loads(p.stdout)
    assert out["ok"] is False


def test_memory_note_path_cue(tmp_path):
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "hook.py").write_text(
        "def pinned_constraint():\n    pass\n", encoding="utf-8")
    mdir = tmp_path / ".devin" / "memory"
    mdir.mkdir(parents=True)
    (mdir / "note.md").write_text(
        "---\ntitle: t\n- path: \"target/hook.py\"\n---\n"
        "about pinned constraint\n", encoding="utf-8")
    _build_index(str(tmp_path))
    p = run_gq(["pinned constraint", "--root", str(tmp_path)])
    assert p.returncode == 0
    out = json.loads(p.stdout)
    files = [r["file"] for r in out["results"]]
    assert any("hook.py" in f for f in files)
    assert any("note.md" in f for f in files)
