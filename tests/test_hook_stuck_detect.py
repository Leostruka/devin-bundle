"""stuck-detect.py - PostToolUse hook: advisory on repeated exec failures."""
import importlib.util
import io
import json
import os
import sys
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
spec = importlib.util.spec_from_file_location(
    "stuck_detect", os.path.join(SCRIPTS, "stuck-detect.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _payload(cmd="npm run build", success=False, output="", error=None,
             tool="exec"):
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": tool,
        "tool_input": {"command": cmd},
        "tool_response": {"success": success, "output": output,
                          "error": error},
        "session_id": "t",
    }


def _run(payload):
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out), \
         pytest.raises(SystemExit) as e:
        mod.main()
    return e.value.code, out.getvalue()


@pytest.fixture(autouse=True)
def _state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BUNDLE_MEMORY_DIR", str(tmp_path))
    return tmp_path


def test_three_consecutive_failures_warn():
    for _ in range(2):
        code, out = _run(_payload())
        assert code == 0 and out == ""
    code, out = _run(_payload())
    assert code == 0
    assert "stuck-detect" in out and "npm run build" in out
    assert "additionalContext" in out


def test_warns_only_once_per_signature():
    for _ in range(4):
        _, out = _run(_payload())
    count = 0
    for _ in range(3):
        _, out = _run(_payload())
        count += out.count("stuck-detect")
    assert count == 0


def test_success_resets_streak():
    _run(_payload())
    _run(_payload(success=True))
    _run(_payload())
    _, out = _run(_payload())
    assert "stuck-detect" not in out


def test_different_commands_do_not_stack():
    for cmd in ("cmd-a", "cmd-b", "cmd-c"):
        _run(_payload(cmd=cmd))
    _, out = _run(_payload(cmd="cmd-d"))
    assert "stuck-detect" not in out


def test_alternating_failures_do_not_warn():
    for cmd in ("cmd-a", "cmd-b", "cmd-a", "cmd-b", "cmd-a"):
        _, out = _run(_payload(cmd=cmd))
    assert "stuck-detect" not in out


def test_nonzero_exit_in_output_counts_as_failure():
    for i in range(2):
        _, out = _run(_payload(success=True, output="fail"))
        assert "stuck-detect" not in out
    _, out = _run(_payload(success=True, output="oops\nExit code: 1"))
    _, out = _run(_payload(success=True, output="oops\nExit code: 1"))
    _, out = _run(_payload(success=True, output="oops\nExit code: 1"))
    assert "stuck-detect" in out


def test_ignores_non_exec_tools():
    for _ in range(4):
        _, out = _run(_payload(tool="mcp_call_tool"))
    assert "stuck-detect" not in out


def test_malformed_payload_silent():
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO("{broken")), \
         patch.object(sys, "stdout", out), \
         pytest.raises(SystemExit) as e:
        mod.main()
    assert e.value.code == 0 and out.getvalue() == ""


def test_corrupt_state_recovers(_state_dir):
    state = os.path.join(_state_dir, ".stuck-detect.json")
    with open(state, "w") as f:
        f.write("{not json")
    for _ in range(3):
        _, out = _run(_payload())
    assert "stuck-detect" in out


def test_state_file_capped(_state_dir):
    for i in range(40):
        _run(_payload(cmd=f"unique-cmd-{i}", success=True))
    state = os.path.join(_state_dir, ".stuck-detect.json")
    data = json.load(open(state))
    assert len(data["history"]) <= 12
