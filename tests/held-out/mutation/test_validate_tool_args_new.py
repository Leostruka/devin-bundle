"""Held-out mutation test: validate-tool-args.py new validations.

Policy: ALWAYS_PASSES
Source: CodeAssay (arXiv:2608.03535v1) — mutation-based test-suite validation.

Tests the validations added in the self-improvement loop:
  - ask_user_question: max 4 questions, max 4 options
  - todo_write: at most 1 in_progress item
  - run_subagent: is_background must be boolean
"""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
VALIDATE_SCRIPT = os.path.join(SCRIPTS_DIR, "validate-tool-args.py")


def run_validate(tool_name: str, tool_input: dict) -> tuple[int, str]:
    """Run validate-tool-args.py with a simulated PreToolUse payload."""
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "session_id": "test",
    })
    result = subprocess.run(
        [sys.executable, VALIDATE_SCRIPT],
        input=payload, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
    )
    return result.returncode, result.stdout.strip()


def _run_session(tool_name, tool_input, session_id, state_dir, is_subagent=False):
    """Like run_validate but with a scoped session + isolated state dir."""
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": tool_input,
        "session_id": session_id,
        **({"is_subagent": True} if is_subagent else {}),
    })
    env = dict(os.environ, DEVIN_STATE_DIR=str(state_dir))
    r = subprocess.run(
        [sys.executable, VALIDATE_SCRIPT],
        input=payload, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=10, env=env,
    )
    return r.returncode, r.stdout.strip()


def test_profile_deny_blocks_exec(tmp_path):
    """C82: a researcher-profile dispatch records the profile; the
    subagent's later exec call is denied."""
    sid = "deny-single"
    _run_session("run_subagent", {"task": "research x", "profile": "researcher"}, sid, tmp_path)
    code, out = _run_session("exec", {"command": "ls"}, sid, tmp_path, is_subagent=True)
    assert code == 2, f"researcher exec should be denied, got {code}: {out}"


def test_profile_deny_mixed_session_fails_open(tmp_path):
    """C82: researcher + implementer in one session cannot attribute a call
    to its dispatch - uniform-deny must fail OPEN (no false block), which
    also fixes the old last-recorded-wins scheme that denied whichever
    profile was written last."""
    sid = "deny-mixed"
    _run_session("run_subagent", {"task": "research x", "profile": "researcher"}, sid, tmp_path)
    _run_session("run_subagent", {"task": "build y", "profile": "implementer"}, sid, tmp_path)
    code, _ = _run_session("exec", {"command": "ls"}, sid, tmp_path, is_subagent=True)
    assert code == 0, f"mixed-profile session must not over-block, got {code}"


def test_profile_deny_uniform_set_blocks(tmp_path):
    """C82: researcher + issue-tracker both deny exec - the union still
    blocks (old last-wins scheme allowed it when issue-tracker recorded
    after researcher... and vice versa)."""
    sid = "deny-uniform"
    _run_session("run_subagent", {"task": "research x", "profile": "researcher"}, sid, tmp_path)
    _run_session("run_subagent", {"task": "triage y", "profile": "issue-tracker"}, sid, tmp_path)
    code, out = _run_session("exec", {"command": "ls"}, sid, tmp_path, is_subagent=True)
    assert code == 2, f"uniformly-denied exec should block, got {code}: {out}"


def test_profile_deny_parent_not_blocked(tmp_path):
    """Deny only applies to subagent-marked calls; the parent's own exec
    in a session carrying a denied profile stays allowed."""
    sid = "deny-parent"
    _run_session("run_subagent", {"task": "research x", "profile": "researcher"}, sid, tmp_path)
    code, _ = _run_session("exec", {"command": "ls"}, sid, tmp_path, is_subagent=False)
    assert code == 0, f"parent exec must not be denied, got {code}"


def test_profile_deny_blocked_dispatch_no_unlock(tmp_path):
    """C82: a BLOCKED dispatch must not write profile state. Record-before-
    validate let a bogus-profile dispatch (exit 2) flip the session set
    ambiguous and silently unlock exec for denied subagents."""
    sid = "deny-blocked"
    _run_session("run_subagent", {"task": "research x", "profile": "researcher"}, sid, tmp_path)
    # invalid profile -> dispatch blocked, must NOT record
    code, _ = _run_session("run_subagent", {"task": "evil", "profile": "bogus-profile"}, sid, tmp_path)
    assert code == 2
    code, out = _run_session("exec", {"command": "ls"}, sid, tmp_path, is_subagent=True)
    assert code == 2, f"blocked dispatch must not unlock exec, got {code}: {out}"


def test_state_file_write_blocked(tmp_path):
    """C82: subagent enforcement state is not agent-writable - overwriting
    the dispatch ledger or a profile record resets its own limits."""
    for tool, key in (("write", "file_path"), ("edit", "file_path"),
                      ("notebook_edit", "notebook_path")):
        code, out = _run_session(
            tool, {key: str(tmp_path / "subagent-ledger.jsonl"),
                   "old_string": "x", "new_string": "y"},
            "state-guard", tmp_path)
        assert code == 2, f"{tool} to state file should block, got {code}: {out}"


def test_state_dir_other_files_allowed(tmp_path):
    """Only subagent-* state files are protected; other state writes pass."""
    (tmp_path).mkdir(exist_ok=True)
    code, _ = _run_session(
        "write", {"file_path": str(tmp_path / "notes.txt")},
        "state-ok", tmp_path)
    assert code == 0, f"non-state write should be allowed, got {code}"


def test_profile_deny_legacy_file(tmp_path):
    """Legacy single-profile state files still deny."""
    sid = "deny-legacy"
    os.makedirs(tmp_path, exist_ok=True)
    with open(tmp_path / f"subagent-{sid}.json", "w", encoding="utf-8") as f:
        json.dump({"profile": "researcher", "session_id": sid}, f)
    code, _ = _run_session("exec", {"command": "ls"}, sid, tmp_path, is_subagent=True)
    assert code == 2, "legacy profile file should still deny exec"


def test_ask_user_question_max_4_questions():
    """ask_user_question with 5 questions must be blocked."""
    questions = [{"question": f"Q{i}?", "header": f"H{i}", "options": [{"label": "a"}, {"label": "b"}]} for i in range(5)]
    code, out = run_validate("ask_user_question", {"questions": questions})
    assert code == 2, f"Expected block for 5 questions, got {code}: {out}"


def test_ask_user_question_4_questions_allowed():
    """ask_user_question with 4 questions must be allowed."""
    questions = [{"question": f"Q{i}?", "header": f"H{i}", "options": [{"label": "a"}, {"label": "b"}]} for i in range(4)]
    code, _ = run_validate("ask_user_question", {"questions": questions})
    assert code == 0, f"4 questions should be allowed, got exit {code}"


def test_ask_user_question_max_4_options():
    """ask_user_question with 5 options per question must be blocked."""
    questions = [{"question": "Q?", "header": "H", "options": [{"label": f"o{i}"} for i in range(5)]}]
    code, out = run_validate("ask_user_question", {"questions": questions})
    assert code == 2, f"Expected block for 5 options, got {code}: {out}"


def test_todo_write_multiple_in_progress_blocked():
    """todo_write with 2 in_progress items must be blocked."""
    todos = [
        {"content": "task 1", "status": "in_progress"},
        {"content": "task 2", "status": "in_progress"},
    ]
    code, out = run_validate("todo_write", {"todos": todos})
    assert code == 2, f"Expected block for 2 in_progress, got {code}: {out}"
    assert "in_progress" in out.lower()


def test_todo_write_single_in_progress_allowed():
    """todo_write with 1 in_progress item must be allowed."""
    todos = [
        {"content": "task 1", "status": "in_progress"},
        {"content": "task 2", "status": "pending"},
    ]
    code, _ = run_validate("todo_write", {"todos": todos})
    assert code == 0, f"1 in_progress should be allowed, got exit {code}"


def test_todo_write_zero_in_progress_allowed():
    """todo_write with 0 in_progress items must be allowed."""
    todos = [
        {"content": "task 1", "status": "pending"},
        {"content": "task 2", "status": "completed"},
    ]
    code, _ = run_validate("todo_write", {"todos": todos})
    assert code == 0, f"0 in_progress should be allowed, got exit {code}"


def test_run_subagent_is_background_non_bool_blocked():
    """run_subagent with is_background='yes' (string) must be blocked."""
    code, out = run_validate("run_subagent", {"task": "do something", "profile": "researcher", "is_background": "yes"})
    assert code == 2, f"Expected block for non-bool is_background, got {code}: {out}"


def test_run_subagent_is_background_bool_allowed():
    """run_subagent with is_background=true must be allowed."""
    code, _ = run_validate("run_subagent", {"task": "do something", "profile": "researcher", "is_background": True})
    assert code == 0, f"bool is_background should be allowed, got exit {code}"


def test_run_subagent_is_background_omitted_allowed():
    """run_subagent without is_background must be allowed."""
    code, _ = run_validate("run_subagent", {"task": "do something", "profile": "researcher"})
    assert code == 0, f"Omitted is_background should be allowed, got exit {code}"


def test_run_subagent_max_parallel_string_blocked():
    """run_subagent with max_parallel='3' (string) must be blocked."""
    code, out = run_validate("run_subagent", {"task": "do something", "profile": "researcher", "max_parallel": "3"})
    assert code == 2, f"Expected block for string max_parallel, got {code}: {out}"


def test_run_subagent_max_parallel_float_blocked():
    """run_subagent with max_parallel=3.5 (float) must be blocked."""
    code, out = run_validate("run_subagent", {"task": "do something", "profile": "researcher", "max_parallel": 3.5})
    assert code == 2, f"Expected block for float max_parallel, got {code}: {out}"


def test_run_subagent_max_parallel_too_large_blocked():
    """run_subagent with max_parallel=5 must be blocked."""
    code, out = run_validate("run_subagent", {"task": "do something", "profile": "researcher", "max_parallel": 5})
    assert code == 2, f"Expected block for max_parallel > 3, got {code}: {out}"


def test_run_subagent_max_parallel_int_allowed():
    """run_subagent with max_parallel=3 (int) must be allowed."""
    code, _ = run_validate("run_subagent", {"task": "do something", "profile": "researcher", "max_parallel": 3})
    assert code == 0, f"max_parallel=3 should be allowed, got exit {code}"


def test_fail_open_on_invalid_json():
    """The hook must fail-open (exit 0) on invalid JSON."""
    result = subprocess.run(
        [sys.executable, VALIDATE_SCRIPT],
        input="not json", capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
    )
    assert result.returncode == 0
