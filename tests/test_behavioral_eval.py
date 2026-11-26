"""behavioral-eval.py: grader logic, schema validation, compare, record.

CI never calls models (protocol rule 8) - every test here is deterministic
plain-logic over synthetic outputs and tmp ledgers.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "behavioral-eval.py"
EXAMPLE_CASE = ROOT / "evals" / "cases" / "example-control-ordinary-work.case.json"


def run_tool(*argv, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + list(argv),
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", cwd=cwd or ROOT, timeout=60)


def test_example_case_validates():
    proc = run_tool("validate", str(EXAMPLE_CASE))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["ok"] is True


def test_validate_rejects_missing_keys(tmp_path):
    bad = tmp_path / "bad.case.json"
    bad.write_text(json.dumps({"id": "x"}), encoding="utf-8")
    proc = run_tool("validate", str(bad))
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["errors"]


def test_validate_rejects_bad_regex(tmp_path):
    case = {
        "id": "bad-regex", "source": "test", "type": "control",
        "scenario": "x", "grader": {"type": "regex", "pattern": "([unclosed"},
    }
    p = tmp_path / "bad.case.json"
    p.write_text(json.dumps(case), encoding="utf-8")
    proc = run_tool("validate", str(p))
    assert proc.returncode == 1
    assert "invalid regex" in json.loads(proc.stdout)["errors"][0]


def test_grade_pass_and_fail(tmp_path):
    good = tmp_path / "good.txt"
    good.write_text("I will edit the file now.", encoding="utf-8")
    proc = run_tool("grade", "--case", str(EXAMPLE_CASE), "--sample", str(good))
    assert proc.returncode == 0, proc.stdout
    assert json.loads(proc.stdout)["passed"] is True

    bad = tmp_path / "bad.txt"
    bad.write_text("Dispatching a multi-provider review council.", encoding="utf-8")
    proc = run_tool("grade", "--case", str(EXAMPLE_CASE), "--sample", str(bad))
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["passed"] is False


def test_import_placeholder_resolves_live_text(tmp_path):
    src = tmp_path / "live_tool_text.txt"
    src.write_text("UNIQUE-LIVE-MARKER", encoding="utf-8")
    case = {
        "id": "import-case", "source": "test", "type": "regression",
        "scenario": "x",
        "grader": {"type": "contains", "text": "${import:tooltext}"},
        "imports": {"tooltext": str(src)},
    }
    cp = tmp_path / "import.case.json"
    cp.write_text(json.dumps(case), encoding="utf-8")
    sample = tmp_path / "s.txt"
    sample.write_text("output mentions UNIQUE-LIVE-MARKER here", encoding="utf-8")
    proc = run_tool("grade", "--case", str(cp), "--sample", str(sample))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # and when the live text changes, grading follows the new content
    src.write_text("REPLACED-MARKER", encoding="utf-8")
    proc = run_tool("grade", "--case", str(cp), "--sample", str(sample))
    assert proc.returncode == 1


def test_record_and_compare(tmp_path):
    ledger_dir = tmp_path / ".devin" / "ledgers"
    ledger_dir.mkdir(parents=True)
    (tmp_path / ".devin" / "ledgers" / "behavioral-eval.jsonl").write_text(
        "", encoding="utf-8")

    def record(run, idx, passed):
        return run_tool("record", "--case", "c1", "--model", "m1",
                        "--run", run, "--idx", str(idx),
                        "--passed", str(passed), "--cost", "100", cwd=tmp_path)

    for i in range(4):
        assert record("base", i, 1).returncode == 0
    for i in range(4):
        assert record("cand", i, 1 if i < 2 else 0).returncode == 0

    proc = run_tool("compare", "--baseline", "base", "--candidate", "cand",
                    cwd=tmp_path)
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    row = payload["cases"][0]
    assert row["baseline"] == 1.0
    assert row["candidate"] == 0.5
    assert payload["verdict"] == "regressed"
    assert proc.returncode == 1  # regression exits non-zero


def test_compare_rejects_cross_model(tmp_path):
    ledger_dir = tmp_path / ".devin" / "ledgers"
    ledger_dir.mkdir(parents=True)
    entries = [
        {"case": "c1", "model": "m1", "run": "base", "idx": 0, "passed": True},
        {"case": "c1", "model": "m2", "run": "cand", "idx": 0, "passed": True},
    ]
    (tmp_path / ".devin" / "ledgers" / "behavioral-eval.jsonl").write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    proc = run_tool("compare", "--baseline", "base", "--candidate", "cand",
                    cwd=tmp_path)
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert "model mismatch" in payload["error"]
    assert proc.returncode == 1


def test_compare_improved_exits_zero(tmp_path):
    ledger_dir = tmp_path / ".devin" / "ledgers"
    ledger_dir.mkdir(parents=True)
    entries = [
        {"case": "c1", "model": "m1", "run": "base", "idx": 0, "passed": False},
        {"case": "c1", "model": "m1", "run": "cand", "idx": 0, "passed": True},
    ]
    (tmp_path / ".devin" / "ledgers" / "behavioral-eval.jsonl").write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    proc = run_tool("compare", "--baseline", "base", "--candidate", "cand",
                    cwd=tmp_path)
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["verdict"] == "improved-or-equal"
    assert proc.returncode == 0
