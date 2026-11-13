"""context-budget.py - SessionStart hook / CLI reporter. Edge tests:
JSON mode, missing file, human output to stderr only, simulate flag."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "context-budget.py")


def _run(args, stdin_payload=None, cwd=None):
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        input=json.dumps(stdin_payload) if stdin_payload else "",
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=cwd or ROOT, timeout=20)


def test_json_report_on_real_agents_md():
    p = _run(["--json",
              os.path.join(ROOT, "AGENTS.md")])
    assert p.returncode == 0
    out = json.loads(p.stdout)
    assert out["estimated_tokens"] > 0
    assert out["chars"] > 0 and out["lines"] > 0


def test_human_output_goes_to_stderr_only(tmp_path):
    f = tmp_path / "AGENTS.md"
    f.write_text("# rules\n" + "x" * 400, encoding="utf-8")
    p = _run([str(f)])
    assert p.returncode == 0
    assert p.stdout == ""  # never injects into context (Rule 18)
    assert "tokens" in p.stderr


def test_missing_file_reports_error(tmp_path):
    p = _run([str(tmp_path / "nope.md")])
    assert p.returncode == 1
    assert "cannot read" in p.stderr


def test_no_agents_md_found_fails_open(tmp_path, monkeypatch):
    env = dict(os.environ, DEVIN_PROJECT_DIR=str(tmp_path),
               APPDATA=str(tmp_path / "appdata"))
    p = subprocess.run([sys.executable, SCRIPT],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=str(tmp_path), env=env, timeout=20)
    assert p.returncode == 0
    assert "no AGENTS.md" in p.stderr


def test_hook_stdin_payload_drained():
    p = _run(["--json", os.path.join(ROOT, "AGENTS.md")],
             stdin_payload={"hook_event_name": "SessionStart"})
    assert p.returncode == 0
    json.loads(p.stdout)


def test_simulate_smart_zone_nudge():
    p = _run(["--simulate", "200000"])
    assert p.returncode == 0
    assert "SMART ZONE NUDGE" in p.stderr


def test_simulate_json():
    p = _run(["--json", "--simulate", "4000"])
    out = json.loads(p.stdout)
    assert out["estimated_tokens"] == 4000
