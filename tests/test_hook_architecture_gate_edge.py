"""architecture-gate.py - PreToolUse hook: blocks source edits in a
.devin-managed project that lacks ARCHITECTURE_MANIFEST.md. Edge tests:
exit codes, .devin exemption, read-only pass-through, fail-open."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "architecture-gate.py")
MANIFEST = os.path.join(".devin", "ARCHITECTURE_MANIFEST.md")


def _run(payload, cwd=None):
    return subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(payload),
        capture_output=True, text=True,
        cwd=cwd or ROOT, timeout=20)


def _write(path):
    return {"hook_event_name": "PreToolUse", "tool_name": "write",
            "tool_input": {"file_path": str(path)}}


@pytest.fixture
def managed(tmp_path):
    (tmp_path / ".devin").mkdir()
    return tmp_path


def test_write_blocked_without_manifest(managed):
    target = managed / "src" / "main.py"
    p = _run(_write(target))
    assert p.returncode == 2
    out = json.loads(p.stdout)
    assert out["decision"] == "block"
    assert "ARCHITECTURE_MANIFEST" in out["reason"]


def test_write_allowed_with_manifest(managed):
    (managed / ".devin" / "ARCHITECTURE_MANIFEST.md").write_text("# m")
    p = _run(_write(managed / "src" / "main.py"))
    assert p.returncode == 0


def test_write_inside_devin_always_allowed(managed):
    p = _run(_write(managed / ".devin" / "notes" / "x.md"))
    assert p.returncode == 0


def test_creating_manifest_itself_allowed(managed):
    p = _run(_write(managed / ".devin" / "ARCHITECTURE_MANIFEST.md"))
    assert p.returncode == 0


def test_unmanaged_project_not_gated():
    # A path whose ancestors contain no .devin/ is outside the gate's
    # scope. Use a synthetic path directly under the filesystem root so
    # no user-home .devin (e.g. ~/.devin) can capture it.
    root = os.path.abspath(os.sep)
    if os.path.isdir(os.path.join(root, ".devin")):
        pytest.skip("filesystem root itself is .devin-managed")
    target = os.path.join(root, "ag-unmanaged-xyz", "x.py")
    p = _run(_write(target))
    assert p.returncode == 0


def test_mutating_exec_blocked(managed):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "exec",
               "tool_input": {"command": "mkdir src",
                              "workdir": str(managed)}}
    p = _run(payload)
    assert p.returncode == 2
    assert json.loads(p.stdout)["decision"] == "block"


def test_readonly_exec_allowed(managed):
    for cmd in ("ls", "git status", "pytest -q",
                "grep -rn foo .", "cat f.md"):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "exec",
                   "tool_input": {"command": cmd,
                                  "workdir": str(managed)}}
        assert _run(payload).returncode == 0, cmd


def test_redirect_in_quotes_not_false_positive(managed):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "exec",
               "tool_input": {"command": 'git commit -m "a > b"',
                              "workdir": str(managed)}}
    assert _run(payload).returncode == 0


def test_manifest_escape_hatch_exec(managed):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "exec",
               "tool_input": {"command":
                              "cp template ARCHITECTURE_MANIFEST.md",
                              "workdir": str(managed)}}
    assert _run(payload).returncode == 0


def test_invalid_json_fails_open():
    p = subprocess.run([sys.executable, SCRIPT], input="{bad",
                       capture_output=True, text=True, timeout=20)
    assert p.returncode == 0


def test_other_tool_ignored(managed):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "read",
               "tool_input": {"file_path": str(managed / "x.py")}}
    assert _run(payload).returncode == 0


def test_non_dict_tool_input_fails_open():
    p = subprocess.run([sys.executable, SCRIPT],
                       input=json.dumps({"tool_name": "write",
                                         "tool_input": "x"}),
                       capture_output=True, text=True, timeout=20)
    assert p.returncode == 0
