"""git-diff-stat.py - PostToolUse: one-line diff footer when mode enables it."""
import importlib.util
import io
import json
import os
import subprocess
import sys
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
spec = importlib.util.spec_from_file_location(
    "git_diff_stat", os.path.join(SCRIPTS, "git-diff-stat.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _run(payload, root):
    out = io.StringIO()
    with patch.object(sys, "stdin",
                      io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out), \
         patch.dict(os.environ, {"DEVIN_PROJECT_DIR": str(root)}), \
         pytest.raises(SystemExit) as e:
        mod.main()
    return e.value.code, out.getvalue()


def _repo(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "output-modes.json").write_text(json.dumps({
        "lean": {"context": "x", "flags": {"diff_footer": True}},
        "quiet": {"context": "x", "flags": {"diff_footer": False}},
    }))
    (tmp_path / ".devin").mkdir()
    (tmp_path / "f.txt").write_text("a")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t",
                    "commit", "-m", "init"], cwd=tmp_path,
                   capture_output=True)
    (tmp_path / "f.txt").write_text("a\nb\nc")
    return tmp_path


def _payload(tool="exec"):
    return {"hook_event_name": "PostToolUse", "tool_name": tool,
            "tool_input": {}, "tool_response": {"success": True},
            "session_id": "t"}


def test_footer_when_lean_mode(tmp_path):
    root = _repo(tmp_path)
    (root / ".devin" / "output-mode.json").write_text(
        json.dumps({"mode": "lean"}))
    code, out = _run(_payload(), root)
    assert code == 0 and "diff-stat: 1 files (+" in out


def test_silent_when_mode_off(tmp_path):
    root = _repo(tmp_path)
    code, out = _run(_payload(), root)
    assert code == 0 and out == ""


def test_silent_when_mode_disables_footer(tmp_path):
    root = _repo(tmp_path)
    (root / ".devin" / "output-mode.json").write_text(
        json.dumps({"mode": "quiet"}))
    code, out = _run(_payload(), root)
    assert code == 0 and out == ""


def test_silent_for_non_exec_tool(tmp_path):
    root = _repo(tmp_path)
    (root / ".devin" / "output-mode.json").write_text(
        json.dumps({"mode": "lean"}))
    code, out = _run(_payload(tool="read"), root)
    assert code == 0 and out == ""
