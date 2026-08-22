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
        input=payload, capture_output=True, text=True, timeout=10,
    )
    return result.returncode, result.stdout.strip()


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


def test_fail_open_on_invalid_json():
    """The hook must fail-open (exit 0) on invalid JSON."""
    result = subprocess.run(
        [sys.executable, VALIDATE_SCRIPT],
        input="not json", capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
