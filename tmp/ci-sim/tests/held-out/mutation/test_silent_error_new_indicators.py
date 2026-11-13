"""Held-out mutation test: silent-error-review.py expanded error indicators.

Policy: ALWAYS_PASSES
Source: CodeAssay (arXiv:2608.03535v1) — mutation-based test-suite validation.

Tests the error indicators added in the self-improvement loop:
  - Exit codes (exit code 1, exited with code 255)
  - Errno names (EACCES, ECONNREFUSED, ECONNRESET, ETIMEDOUT, ENOENT)
  - Python exception types (ValueError, TypeError, KeyError, etc.)
  - npm ERR!, cargo error, BUILD FAILED, Go FAIL
"""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
SILENT_SCRIPT = os.path.join(SCRIPTS_DIR, "silent-error-review.py")


def run_silent_check(output: str, tool: str = "exec", success: bool = True) -> tuple[int, str]:
    """Run silent-error-review.py with a simulated PostToolUse payload."""
    payload = json.dumps({
        "hook_event_name": "PostToolUse",
        "tool_name": tool,
        "tool_input": {"command": "test"},
        "tool_response": {"success": success, "output": output, "error": None},
        "session_id": "test",
    })
    result = subprocess.run(
        [sys.executable, SILENT_SCRIPT],
        input=payload, capture_output=True, text=True, timeout=10,
    )
    return result.returncode, result.stdout.strip()


def test_exit_code_detected():
    """Output with 'exit code 1' must be flagged."""
    code, out = run_silent_check("Program completed\nexit code 1")
    assert code == 0  # never blocks
    assert "hookSpecificOutput" in out or "additionalContext" in out, f"Should flag exit code: {out}"


def test_exited_with_code_detected():
    """Output with 'exited with code 255' must be flagged."""
    code, out = run_silent_check("Process exited with code 255")
    assert "hookSpecificOutput" in out or "additionalContext" in out, f"Should flag exited with code: {out}"


def test_eacces_detected():
    """Output with EACCES must be flagged."""
    code, out = run_silent_check("PermissionError: [Errno 13] EACCES: '/root/file'")
    assert "hookSpecificOutput" in out or "additionalContext" in out, f"Should flag EACCES: {out}"


def test_econnrefused_detected():
    """Output with ECONNREFUSED must be flagged."""
    code, out = run_silent_check("ConnectionRefusedError: [Errno 111] ECONNREFUSED")
    assert "hookSpecificOutput" in out or "additionalContext" in out, f"Should flag ECONNREFUSED: {out}"


def test_value_error_detected():
    """Output with ValueError must be flagged."""
    code, out = run_silent_check("ValueError: invalid literal for int() with base 10: 'abc'")
    assert "hookSpecificOutput" in out or "additionalContext" in out, f"Should flag ValueError: {out}"


def test_key_error_detected():
    """Output with KeyError must be flagged."""
    code, out = run_silent_check("KeyError: 'missing_key'")
    assert "hookSpecificOutput" in out or "additionalContext" in out, f"Should flag KeyError: {out}"


def test_npm_err_detected():
    """Output with npm ERR! must be flagged."""
    code, out = run_silent_check("npm ERR! code ELIFECYCLE\nnpm ERR! errno 1")
    assert "hookSpecificObject" in out or "hookSpecificOutput" in out or "additionalContext" in out, f"Should flag npm ERR!: {out}"


def test_build_failed_detected():
    """Output with BUILD FAILED must be flagged."""
    code, out = run_silent_check("BUILD FAILED in 2s")
    assert "hookSpecificOutput" in out or "additionalContext" in out, f"Should flag BUILD FAILED: {out}"


def test_clean_output_not_flagged():
    """Clean output without errors must NOT be flagged."""
    code, out = run_silent_check("All tests passed\n0 failures")
    assert "hookSpecificOutput" not in out, f"Clean output should not be flagged: {out}"


def test_fail_open_on_invalid_json():
    """The hook must fail-open (exit 0) on invalid JSON."""
    result = subprocess.run(
        [sys.executable, SILENT_SCRIPT],
        input="not json", capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
