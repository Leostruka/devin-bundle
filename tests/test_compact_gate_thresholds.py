"""Held-out tests for the compaction-threshold policy (ISSUE_08 C6).

Threshold contract being pinned:
  - context-pressure marker accumulates tool output tokens per session and
    resets when the runtime emits PostCompaction (the compactor rewrote the
    live context; cumulative totals describe removed history).
  - compact-gate evaluates only when due: p <= eval_floor -> silent;
    eval_floor < p < compact_at -> shadow entry with action continue;
    p >= compact_at -> shadow entry with action prune (floor heuristic).
  - compact-gate PostCompaction resets its digest/counters epoch but keeps
    the session id.

Subprocess-isolated: APPDATA -> tmp devin home, DEVIN_PROJECT_DIR -> tmp
project with a fake laya install so the gate takes the shadow path without
a daemon (laya_cli.py exists but exits instantly -> daemon_unavailable ->
floor heuristic decides).
"""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


def _env(tmp_path):
    env = dict(os.environ)
    env["APPDATA"] = str(tmp_path / "home")
    env["DEVIN_PROJECT_DIR"] = str(tmp_path / "proj")
    return env


def _make_proj(tmp_path, window=10000):
    proj = tmp_path / "proj"
    (proj / "extensions" / "laya-tools").mkdir(parents=True)
    (proj / "extensions" / "laya-tools" / "laya_cli.py").write_text("", encoding="utf-8")
    (proj / ".devin" / "laya").mkdir(parents=True)
    (proj / ".devin" / "laya" / "profile.json").write_text(json.dumps({
        "version": 1, "mode": "shadow",
        "profiles": ["compact-gate-v1", "compact-boundary-v1"],
        "compact_gate": {"eval_floor": 0.25, "compact_at": 0.7,
                         "compact_to": 0.4, "force_at": 0.8,
                         "k_calls": 8, "cooldown_turns": 10},
    }), encoding="utf-8")
    (proj / "data").mkdir()
    (proj / "data" / "bundle-models.json").write_text(json.dumps({
        "models": [{"id": "test-model", "is_default_parent": True,
                    "context_window": window}],
    }), encoding="utf-8")
    return proj


def _set_marker(tmp_path, tool_output_tokens, calls=0):
    d = tmp_path / "home" / "devin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "context-pressure.json").write_text(json.dumps({
        "tool_output_tokens": tool_output_tokens, "calls": calls,
        "session_start": "2026-11-25T08:00:00", "session_id": "S1",
    }), encoding="utf-8")


def _marker(tmp_path):
    p = tmp_path / "home" / "devin" / "context-pressure.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _run(script, payload, env, cwd):
    return subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script)],
        input=json.dumps(payload), capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env, cwd=cwd, timeout=30)


def _shadow_entries(tmp_path):
    log = tmp_path / "proj" / ".devin" / "laya" / "shadow.jsonl"
    if not log.exists():
        return []
    return [json.loads(l) for l in
            log.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_pressure_marker_resets_on_postcompaction(tmp_path):
    env = _env(tmp_path)
    proj = _make_proj(tmp_path)
    ptu = {"hook_event_name": "PostToolUse", "tool_name": "exec",
           "session_id": "S1",
           "tool_output": {"output": "x" * 4000}}
    r = _run("context-pressure.py", ptu, env, proj)
    assert r.returncode == 0
    assert _marker(tmp_path)["tool_output_tokens"] == 1000

    pc = {"hook_event_name": "PostCompaction", "session_id": "S1"}
    r = _run("context-pressure.py", pc, env, proj)
    assert r.returncode == 0
    assert _marker(tmp_path) is None

    # Post-compaction accumulation restarts from zero for the same session.
    r = _run("context-pressure.py", ptu, env, proj)
    assert r.returncode == 0
    m = _marker(tmp_path)
    assert m["tool_output_tokens"] == 1000 and m["session_id"] == "S1"


def test_compact_gate_action_follows_pressure(tmp_path):
    env = _env(tmp_path)
    proj = _make_proj(tmp_path, window=10000)
    ptu = {"hook_event_name": "PostToolUse", "tool_name": "write",
           "session_id": "S1", "tool_input": {"file_path": "f.txt"},
           "tool_output": {"output": "ok"}}

    # p = 2000/10000 = 0.20 <= eval_floor -> not due -> no shadow entry.
    _set_marker(tmp_path, 2000)
    assert _run("compact-gate.py", dict(ptu, session_id="lo"), env, proj).returncode == 0
    assert _shadow_entries(tmp_path) == []

    # p = 5000/10000 = 0.50 -> due, below compact_at -> action continue.
    _set_marker(tmp_path, 5000)
    assert _run("compact-gate.py", dict(ptu, session_id="mid"), env, proj).returncode == 0
    entries = _shadow_entries(tmp_path)
    assert len(entries) == 1 and entries[0]["action"] == "continue"
    assert entries[0]["p"] == 0.5

    # p = 7500/10000 = 0.75 >= compact_at -> floor prune (daemon absent).
    _set_marker(tmp_path, 7500)
    assert _run("compact-gate.py", dict(ptu, session_id="hi"), env, proj).returncode == 0
    entries = _shadow_entries(tmp_path)
    assert entries[-1]["action"] == "prune" and entries[-1]["p"] == 0.75


def test_compact_gate_state_resets_on_postcompaction(tmp_path):
    env = _env(tmp_path)
    proj = _make_proj(tmp_path)
    laya = proj / ".devin" / "laya"
    (laya / "gate-state.json").write_text(json.dumps({
        "digest": {"first_task": "old", "files": ["a.py"]},
        "calls": 40, "turns": 9, "last_eval_call": 39,
        "cooldown_until_turn": 20, "session_id": "S1",
    }), encoding="utf-8")
    pc = {"hook_event_name": "PostCompaction", "session_id": "S1"}
    assert _run("compact-gate.py", pc, env, proj).returncode == 0
    st = json.loads((laya / "gate-state.json").read_text(encoding="utf-8"))
    assert st["digest"] == {} and st["calls"] == 0 and st["turns"] == 0
    assert st["session_id"] == "S1"
    assert "cooldown_until_turn" not in st
