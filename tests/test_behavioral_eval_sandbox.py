"""Regression tests for the 2026-11-26 independent-review findings on the
behavioral eval harness. These encode exploit shapes verified by the
reviewer; they must stay fixed forever."""
import importlib.util
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "behavioral_eval", os.path.join(ROOT, "scripts", "behavioral-eval.py"))
beval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(beval)


def test_workspace_files_cannot_escape_isolation(tmp_path, monkeypatch):
    """Review critical: workspace_files keys with ../ or absolute paths
    must never be written outside the sample workspace."""
    written = []

    class FakeCompleted:
        stdout = "done"
        stderr = ""

    def fake_run(cmd, **kw):
        return FakeCompleted()

    monkeypatch.setattr(beval.subprocess, "run", fake_run)
    monkeypatch.setattr(beval.tempfile, "mkdtemp",
                        lambda prefix: str(tmp_path))
    escape = tmp_path.parent / "escaped.txt"
    if escape.exists():
        escape.unlink()
    case = {
        "id": "escapetest", "prompt": "x",
        "workspace_files": {
            "../escaped.txt": "PWNED",
            "C:/abs.txt": "PWNED",
            "ok/file.txt": "fine",
        },
    }
    output, meta = beval.run_one_sample(case, 0, None, 10)
    assert not escape.exists(), "parent traversal wrote outside workspace"
    assert not os.path.exists("C:/abs.txt")
    assert os.path.isfile(tmp_path / "ok" / "file.txt")
    assert set(meta["skipped_keys"]) == {"../escaped.txt", "C:/abs.txt"}


def test_digest_excludes_devin_state(tmp_path):
    """Review verified exploit: .devin hook state inside the workspace
    contains the original prompt verbatim; including it in the digest
    false-passes content graders. Digest must skip .devin entirely."""
    devin_dir = tmp_path / ".devin" / "laya"
    devin_dir.mkdir(parents=True)
    (devin_dir / "gate-state.json").write_text(
        json.dumps({"prompt": "SECRET-NEEDLE-12345"}), encoding="utf-8")
    (tmp_path / "work.txt").write_text("ordinary content", encoding="utf-8")
    output = beval.synthesize_output(str(tmp_path), "transcript")
    assert "SECRET-NEEDLE-12345" not in output
    assert "ordinary content" in output


def test_digest_delimits_artifacts(tmp_path):
    """End delimiters prevent a regex anchored on one artifact from
    bleeding into the next."""
    (tmp_path / "a.txt").write_text("content-a", encoding="utf-8")
    output = beval.synthesize_output(str(tmp_path), "t")
    assert "### end a.txt" in output


def test_empty_needle_fails_visibly():
    """'' in output is trivially true; an empty needle (missing import)
    must be a visible failure, never a pass."""
    passed, detail = beval.apply_grader(
        {"type": "contains", "text": "${import:nope}"}, "anything",
        {"nope": ""})
    assert passed is False
    assert "EMPTY" in detail


def test_missing_import_is_unmatchable_sentinel():
    case = {"imports": {"x": "does/not/exist-anywhere.txt"}}
    texts = beval.load_imports(case, ".")
    assert texts["x"] == beval._MISSING_IMPORT
    passed, _ = beval.apply_grader(
        {"type": "contains", "text": "${import:x}"}, "any output", texts)
    assert passed is False


def test_imports_reject_traversal_and_absolute():
    case = {"imports": {
        "up": "../../etc/passwd",
        "win": "C:/Windows/win.ini",
        "abs": "/etc/passwd",
    }}
    texts = beval.load_imports(case, ".")
    for key in ("up", "win", "abs"):
        assert texts[key] == beval._MISSING_IMPORT


def test_safe_relpath_rules():
    assert beval._safe_relpath("a/b/c.txt") == os.path.join("a", "b", "c.txt")
    assert beval._safe_relpath("../x") is None
    assert beval._safe_relpath("/abs/x") is None
    assert beval._safe_relpath("C:/x") is None
    assert beval._safe_relpath("") is None
    assert beval._safe_relpath(None) is None


def test_sample_command_uses_in_process():
    """Daemon mode outlives the CLI child; timeout must be a real cap."""
    src = open(os.path.join(ROOT, "scripts", "behavioral-eval.py"),
               encoding="utf-8").read()
    assert '"--process-model=in-process"' in src


def test_all_committed_cases_validate():
    """Every case file in evals/cases must pass schema validation - a
    malformed case committed silently makes the suite lie by omission."""
    cases_dir = os.path.join(ROOT, "evals", "cases")
    names = sorted(f for f in os.listdir(cases_dir) if f.endswith(".json"))
    assert names, "no cases found - the suite must not be empty"
    for name in names:
        path = os.path.join(cases_dir, name)
        with open(path, encoding="utf-8") as fh:
            case = json.load(fh)
        errors = beval.validate_case(case, name)
        assert errors == [], f"{name}: {errors}"


def test_compare_disjoint_runs_are_incomparable():
    """Two runs sharing no case have nothing being compared; a
    pass-flavored verdict there is a lie by omission."""
    entries = [
        {"run": "r1", "case": "a", "model": "m", "passed": True},
        {"run": "r2", "case": "b", "model": "m", "passed": True},
    ]
    result, err = beval.compare_runs("r1", "r2", entries)
    assert err is None
    assert result["verdict"] == "incomparable-no-overlapping-cases"
    assert result["overlap"] == 0


def test_compare_overlapping_regression_detected():
    entries = [
        {"run": "r1", "case": "a", "model": "m", "passed": True},
        {"run": "r2", "case": "a", "model": "m", "passed": False},
    ]
    result, err = beval.compare_runs("r1", "r2", entries)
    assert result["verdict"] == "regressed"
    assert result["overlap"] == 1


def test_digest_paths_use_forward_slashes(tmp_path):
    """Case regexes must be portable across sampling hosts - digest
    artifact paths are normalized to forward slashes."""
    sub = tmp_path / "docs"
    sub.mkdir()
    (sub / "MAP.md").write_text("x", encoding="utf-8")
    output = beval.synthesize_output(str(tmp_path), "t")
    assert "### docs/MAP.md" in output
    assert "docs\\MAP.md" not in output
