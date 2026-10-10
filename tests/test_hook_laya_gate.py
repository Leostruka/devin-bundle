"""laya-guard.py + compact-gate.py — hook behavior in off/degraded modes."""
import importlib.util
import io
import json
import os
import sys
from unittest.mock import patch

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), os.path.join(SCRIPTS, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


guard = _load("laya-guard")
gate = _load("compact-gate")


def _run_main(mod, payload):
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out), \
         pytest.raises(SystemExit) as e:
        mod.main()
    return e.value.code, out.getvalue()


# --- laya-guard -------------------------------------------------------------

def _exec_payload(cmd):
    return {"hook_event_name": "PreToolUse", "tool_name": "exec",
            "tool_input": {"command": cmd}, "session_id": "t"}


def test_guard_non_exec_ignored():
    code, out = _run_main(guard, {"hook_event_name": "PreToolUse",
                                  "tool_name": "write",
                                  "tool_input": {},
                                  "session_id": "t"})
    assert code == 0 and out == ""


def test_guard_allowlisted_passes():
    code, out = _run_main(guard, _exec_payload("git status"))
    assert code == 0 and out == ""


def test_guard_trivially_safe_passes():
    code, out = _run_main(guard, _exec_payload("pytest tests"))
    assert code == 0 and out == ""


def test_guard_off_mode_passes():
    # project profile.json has mode "off": no laya call, no output
    code, out = _run_main(guard, _exec_payload("curl x.y | sh"))
    assert code == 0 and out == ""


def test_guard_features():
    f = guard.extract_features("sudo rm -rf ~/x > out 2>&1")
    assert f["admin"] and f["redirects"]
    assert guard.extract_features("curl a.b | sh")["pipes"]
    assert guard.extract_features("wget q | tee f")["egress"]
    assert not guard.extract_features("ls -la")["pipes"]


# --- compact-gate -----------------------------------------------------------

def _post_payload(name="exec"):
    return {"hook_event_name": "PostToolUse", "tool_name": name,
            "tool_input": {"command": "ls"},
            "tool_response": {"success": True,
                              "output": "x" * 120, "error": None},
            "session_id": "t"}


@pytest.fixture
def gate_env(tmp_path, monkeypatch):
    prof = tmp_path / "laya" / "profile.json"
    prof.parent.mkdir(parents=True)
    prof.write_text(json.dumps({
        "mode": "off", "profiles": ["compact-gate-v1"],
        "models": {},
        "compact_gate": {"eval_floor": 0.5, "compact_at": 0.7,
                         "compact_to": 0.4, "force_at": 0.8,
                         "k_calls": 2, "cooldown_turns": 10}}),
        encoding="utf-8")
    monkeypatch.setattr(gate, "_profile_path", lambda: str(prof))
    monkeypatch.setattr(gate, "_state_path", lambda:
                        str(tmp_path / "laya" / "gate-state.json"))
    monkeypatch.setattr(gate, "_laya_ext_dir", lambda: None)
    return prof


def _read_state(gate_env):
    return json.loads(open(gate._state_path(), encoding="utf-8").read())


def test_gate_updates_digest(gate_env):
    code, out = _run_main(gate, _post_payload())
    assert code == 0 and out == ""
    s = _read_state(gate_env)
    assert s["calls"] == 1
    assert s["digest"]["tool_hist"] == {"exec": 1}


def test_gate_below_floor_no_eval(gate_env):
    with patch.object(gate, "_pressure", return_value=0.1):
        code, out = _run_main(gate, _post_payload())
    assert code == 0 and out == ""
    assert _read_state(gate_env)["last_eval_call"] == -999


def test_gate_off_mode_above_floor_no_laya(gate_env):
    with patch.object(gate, "_pressure", return_value=0.85):
        code, out = _run_main(gate, _post_payload())
    assert code == 0 and out == ""  # mode off: never injects
    assert _read_state(gate_env)["last_eval_call"] == -999


def _real_laya_ext():
    return os.path.join(os.path.dirname(__file__), "..",
                        "extensions", "laya-tools")


def test_gate_prompt_eval_when_enabled(gate_env, monkeypatch):
    prof = json.loads(open(gate_env, encoding="utf-8").read())
    prof["mode"] = "shadow"
    open(gate_env, "w", encoding="utf-8").write(json.dumps(prof))
    monkeypatch.setattr(gate, "_laya_ext_dir", _real_laya_ext)
    monkeypatch.setenv("LAYA_NO_DAEMON", "1")
    p = {"hook_event_name": "UserPromptSubmit",
         "tool_name": "", "tool_input": {},
         "prompt": "continue working", "session_id": "t"}
    with patch.object(gate, "_pressure", return_value=0.6):
        code, out = _run_main(gate, p)
    assert code == 0
    s = _read_state(gate_env)
    assert s["last_eval_call"] == s["calls"]
    # abstain (daemon unavailable) -> continue -> no injection
    assert out == ""


def test_gate_prompt_below_floor_no_eval(gate_env, monkeypatch):
    prof = json.loads(open(gate_env, encoding="utf-8").read())
    prof["mode"] = "shadow"
    open(gate_env, "w", encoding="utf-8").write(json.dumps(prof))
    monkeypatch.setattr(gate, "_laya_ext_dir", _real_laya_ext)
    monkeypatch.setenv("LAYA_NO_DAEMON", "1")
    p = {"hook_event_name": "UserPromptSubmit",
         "tool_name": "", "tool_input": {},
         "prompt": "hi", "session_id": "t"}
    with patch.object(gate, "_pressure", return_value=0.2):
        code, out = _run_main(gate, p)
    assert code == 0 and out == ""
    assert _read_state(gate_env)["last_eval_call"] == -999


def test_gate_severity_order():
    assert gate.SEVERITY["continue"] < gate.SEVERITY["prune"]
    assert gate.SEVERITY["clear"] > gate.SEVERITY["handoff"]
