"""laya-tools bootstrap.py CLI contract: --help/--dry-run never install."""
import json
import subprocess
import sys
from pathlib import Path

BOOTSTRAP = (Path(__file__).resolve().parents[1]
             / "extensions" / "laya-tools" / "bootstrap.py")


def run(*args):
    return subprocess.run(
        [sys.executable, str(BOOTSTRAP), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120)


def test_help_exits_zero_without_side_effects():
    r = run("--help")
    assert r.returncode == 0
    assert "usage:" in r.stdout


def test_dry_run_emits_plan_json():
    r = run("--dry-run")
    assert r.returncode in (0, 1)
    data = json.loads(r.stdout)
    assert data["dry_run"] is True
    assert "plan" in data and "torch_index" in data["plan"]
    assert {s["step"] for s in data["steps"]} >= {
        "python_version", "vcruntime", "gpu_detect", "create_venv"}
