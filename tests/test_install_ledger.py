"""install-ledger.py - 5-state reconcile truth table + record commands."""
import importlib.util
import io
import json
import os
import sys
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
spec = importlib.util.spec_from_file_location(
    "install_ledger", os.path.join(SCRIPTS, "install-ledger.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Bundle root + fake DEVIN_HOME with managed dirs."""
    root = tmp_path / "bundle"
    live = tmp_path / "live"
    for d in ("scripts", "skills", "docs"):
        (live / d).mkdir(parents=True)
    (root / ".devin" / "install-ledger").mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"version": "1.0.0", "scripts": [], "skills": []}))
    monkeypatch.setenv("DEVIN_PROJECT_DIR", str(root))
    monkeypatch.setenv("DEVIN_HOME", str(live))
    return root, live


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_reconcile_five_states(env):
    root, live = env
    ledger = {"version": 1, "files": {}}
    h = mod._sha256

    # Current: live == bundle
    _write(root / "scripts" / "cur.py", "cur")
    _write(live / "scripts" / "cur.py", "cur")
    ledger["files"]["scripts/cur.py"] = {
        "dest": "", "source_hash": None,
        "rendered_hash": h(live / "scripts" / "cur.py"),
        "installed_at": "t", "corpus_version": "1.0.0"}

    # Outdated: live == recorded, bundle moved on
    _write(root / "scripts" / "out.py", "new")
    _write(live / "scripts" / "out.py", "old")
    ledger["files"]["scripts/out.py"] = {
        "dest": "", "source_hash": None,
        "rendered_hash": h(live / "scripts" / "out.py"),
        "installed_at": "t", "corpus_version": "1.0.0"}

    # Modified: live != recorded rendered_hash AND live != bundle (local edit)
    _write(root / "scripts" / "mod.py", "bundle-v2")
    _write(live / "scripts" / "mod.py", "same")
    ledger["files"]["scripts/mod.py"] = {
        "dest": "", "source_hash": None, "rendered_hash": "deadbeef",
        "installed_at": "t", "corpus_version": "1.0.0"}

    # Removed: recorded but missing
    ledger["files"]["scripts/gone.py"] = {
        "dest": "", "source_hash": None, "rendered_hash": "x",
        "installed_at": "t", "corpus_version": "1.0.0"}

    # Foreign: on disk, not in ledger, no bundle source
    _write(live / "scripts" / "foreign.py", "foreign")

    (root / ".devin" / "install-ledger" / "installs.json").write_text(
        json.dumps(ledger))

    rep = mod.reconcile()
    assert rep["Current"] == ["scripts/cur.py"]
    assert rep["Outdated"] == ["scripts/out.py"]
    assert rep["Modified"] == ["scripts/mod.py"]
    assert rep["Removed"] == ["scripts/gone.py"]
    assert rep["Foreign"] == ["scripts/foreign.py"]


def test_record_all_then_current(env):
    root, live = env
    _write(root / "scripts" / "a.py", "a")
    _write(live / "scripts" / "a.py", "a")
    rc = mod.main_for(["record-all"]) if hasattr(mod, "main_for") else \
        _cli(["record-all"], env)
    assert rc == 0
    rep = mod.reconcile()
    assert rep["Current"] == ["scripts/a.py"]
    assert rep["Foreign"] == []


def _cli(argv, env):
    with patch.object(sys, "argv", ["install-ledger.py"] + argv), \
         patch.object(sys, "stdout", io.StringIO()):
        return mod.main()


def test_backup_if_differs_writes_copy(env, tmp_path):
    dst = tmp_path / "file.py"
    dst.write_text("old bytes")
    bak = mod.backup_if_differs(str(dst), str(tmp_path / "backups"))
    assert bak and open(bak).read() == "old bytes"


def test_backup_if_differs_missing_returns_none(tmp_path):
    assert mod.backup_if_differs(
        str(tmp_path / "nope"), str(tmp_path / "b")) is None


def test_backup_failure_aborts_write(env, tmp_path):
    """Simulated backup failure -> caller must abort; dst untouched."""
    dst = tmp_path / "f.py"
    dst.write_text("keep")
    ro_dir = tmp_path / "ro"
    ro_dir.mkdir()
    with patch.object(mod.shutil, "copyfile",
                      side_effect=OSError("disk full")):
        try:
            mod.backup_if_differs(str(dst), str(ro_dir))
            aborted = False
        except OSError:
            aborted = True
    assert aborted and dst.read_text() == "keep"


def test_corpus_index_written(env):
    root, live = env
    _write(root / "scripts" / "a.py", "a")
    _cli(["record-all"], env)
    idx = json.loads(
        (root / ".devin" / "install-ledger" / "corpus-index.json")
        .read_text())
    assert idx["files"]["scripts/a.py"] == mod._sha256(
        root / "scripts" / "a.py")


def test_empty_dirs_clean(env):
    rep = mod.reconcile()
    assert rep == {"Current": [], "Outdated": [], "Modified": [],
                   "Removed": [], "Foreign": []}


def test_docs_remap_to_devin_dir(env):
    """live docs/* resolves to bundle .devin/docs/* (install.ps1 §7b)."""
    root, live = env
    _write(root / ".devin" / "docs" / "guide.md", "guide")
    _write(root / ".devin" / "plans" / "p.md", "plan")
    _write(live / "docs" / "guide.md", "guide")
    _write(live / "docs" / "plans" / "p.md", "plan")
    rep = mod.reconcile()
    assert "docs/guide.md" in rep["Current"]
    assert "docs/plans/p.md" in rep["Current"]
    # drift on the bundle source shows as Outdated once recorded
    _cli(["record-all"], env)
    _write(root / ".devin" / "docs" / "guide.md", "guide v2")
    rep = mod.reconcile()
    assert "docs/guide.md" in rep["Outdated"]


def test_corpus_index_covers_remapped_docs(env):
    root, live = env
    _write(root / ".devin" / "docs" / "guide.md", "guide")
    _write(root / ".devin" / "plans" / "p.md", "plan")
    _cli(["record-all"], env)
    idx = json.loads(
        (root / ".devin" / "install-ledger" / "corpus-index.json")
        .read_text())
    assert idx["files"]["docs/guide.md"] == mod._sha256(
        root / ".devin" / "docs" / "guide.md")
    assert idx["files"]["docs/plans/p.md"] == mod._sha256(
        root / ".devin" / "plans" / "p.md")


def test_rendered_file_current_when_source_recorded(env):
    """Rendered managed files (config.json) can never equal their raw
    bundle source — currency must compare rec.source_hash, not live bytes."""
    root, live = env
    h = mod._sha256
    _write(root / "config.json", "src")
    _write(live / "config.json", "rendered-abs-paths")
    ledger = {"version": 1, "files": {"config.json": {
        "dest": "", "source_hash": h(root / "config.json"),
        "rendered_hash": h(live / "config.json"),
        "installed_at": "t", "corpus_version": "1.0.0"}}}
    (root / ".devin" / "install-ledger" / "installs.json").write_text(
        json.dumps(ledger))
    rep = mod.reconcile()
    assert rep["Current"] == ["config.json"]
    # source moves -> same live bytes become Outdated
    _write(root / "config.json", "src v2")
    rep = mod.reconcile()
    assert rep["Outdated"] == ["config.json"]


def test_build_artifacts_never_drift(env):
    """Install-time artifacts (.pyd/.so/.dll/.pyc) aren't shipped sources."""
    root, live = env
    _write(live / "extensions" / "rust-core" / "fast_math.pyd", "bin")
    ledger = {"version": 1, "files": {
        "extensions/rust-core/fast_math.pyd": {
            "dest": "", "source_hash": None, "rendered_hash": "stale",
            "installed_at": "t", "corpus_version": "1.0.0"}}}
    (root / ".devin" / "install-ledger" / "installs.json").write_text(
        json.dumps(ledger))
    rep = mod.reconcile()
    assert all("fast_math.pyd" not in v for v in rep.values())


def test_corpus_index_excludes_noise_dirs_and_artifacts(env):
    """site-packages/.venv/build artifacts never enter the corpus index."""
    root, live = env
    _write(root / "extensions" / "x" / ".venv" / "Lib" / "junk.py", "j")
    _write(root / "extensions" / "x" / "fast.pyd", "bin")
    _write(root / "extensions" / "x" / "real.py", "r")
    _cli(["record-all"], env)
    idx = json.loads(
        (root / ".devin" / "install-ledger" / "corpus-index.json")
        .read_text())
    keys = idx["files"]
    assert "extensions/x/real.py" in keys
    assert not any(".venv" in k or k.endswith(".pyd") for k in keys)


def test_record_all_prune_refuses_degenerate_scan(env, capsys):
    """A missing/empty live must not wipe recorded files (review finding)."""
    root, live = env
    # seed 60 records so >25% threshold trips on a wipe
    files = {f"scripts/f{i}.py": {"source_hash": "x", "rendered_hash": "x"}
             for i in range(60)}
    data = {"version": 1, "files": files}
    mod._save_ledger(data)
    # live has no files on disk -> live_set empty -> prune would drop all
    rc = mod.cmd_record_all(None)
    assert rc == 1
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["ok"] is False and "prune refused" in out["error"]
    assert len(mod._load_ledger()["files"]) == 60


def test_record_all_prunes_absent_records(env, capsys):
    root, live = env
    _write(live / "scripts" / "a.py", "a")
    _write(live / "scripts" / "b.py", "b")
    _write(live / "scripts" / "c.py", "c")
    _write(live / "docs" / "d.md", "d")
    files = {r: {"source_hash": "x"} for r in
             ("scripts/a.py", "scripts/b.py", "scripts/c.py", "docs/d.md")}
    files["scripts/gone.py"] = {"source_hash": "x"}
    mod._save_ledger({"version": 1, "files": files})
    rc = mod.cmd_record_all(None)
    assert rc == 0
    ledger = mod._load_ledger()["files"]
    assert "scripts/gone.py" not in ledger
    assert "scripts/a.py" in ledger
