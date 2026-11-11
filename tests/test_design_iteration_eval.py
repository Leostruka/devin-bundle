"""Runs the design-iteration-loop contract eval (#516)."""
import json
import os
import subprocess
import sys

EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", ".devin", "evals",
                        "design-iteration-loop")


def test_contract_eval_all_cases(tmp_path):
    report = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, os.path.join(EVAL_DIR, "run_eval.py"),
         "--report", str(report)],
        capture_output=True, text=True, timeout=15,
        encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["passed"] == data["total"] == 10
