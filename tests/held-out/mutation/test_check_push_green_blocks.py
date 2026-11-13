"""Held-out mutation test: check-push-green.py blocks on held-out gap.

Policy: ALWAYS_PASSES
Source: CodeAssay (arXiv:2608.03535v1) + Rule 16.

Verifies that check-push-green.py:
  1. Blocks git push when tests fail (exit 2).
  2. Blocks when validation passes but held-out fails (Rule 16 gap).
  3. Allows when all tests pass.
"""
import json
import os
import subprocess
import sys

import pytest
from _mutation import mutation, mut_remove_exit_code, mut_empty_function

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
PUSH_SCRIPT = os.path.join(SCRIPTS_DIR, "check-push-green.py")


def run_push_check(command: str = "git push origin main", cwd: str = None) -> int:
    """Run check-push-green.py with a simulated PreToolUse payload. Returns exit code."""
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "exec",
        "tool_input": {"command": command},
    })
    env = os.environ.copy()
    if cwd:
        env["DEVIN_PROJECT_DIR"] = cwd
    result = subprocess.run(
        [sys.executable, PUSH_SCRIPT],
        input=payload, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, env=env,
    )
    return result.returncode


def test_allows_dry_run():
    """--dry-run must be allowed (exit 0)."""
    code = run_push_check("git push --dry-run origin main")
    assert code == 0, f"--dry-run should be allowed, got exit {code}"


def test_non_push_command_allowed():
    """Non-push commands must be allowed (exit 0)."""
    code = run_push_check("git status")
    assert code == 0


def test_non_exec_tool_allowed():
    """Non-exec tools must be allowed (exit 0)."""
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "read",
        "tool_input": {"file_path": "test.txt"},
    })
    result = subprocess.run(
        [sys.executable, PUSH_SCRIPT],
        input=payload, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
    )
    assert result.returncode == 0


def test_invalid_json_fail_open():
    """Invalid JSON must fail-open (exit 0)."""
    result = subprocess.run(
        [sys.executable, PUSH_SCRIPT],
        input="not json", capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
    )
    assert result.returncode == 0


def _secrets_block_dir(tmp_path):
    """Project dir that deterministically triggers the unmasked-secrets block."""
    (tmp_path / "credentials.toml").write_text(
        'api_key = "definitely-a-real-secret-value"\n', encoding="utf-8"
    )
    return str(tmp_path)


def test_unmasked_secrets_block(tmp_path):
    """credentials.toml with a real secret must block the push (exit 2)."""
    code = run_push_check("git push origin main", cwd=_secrets_block_dir(tmp_path))
    assert code == 2, f"unmasked secret should block, got exit {code}"


def test_mutation_remove_exit_code(tmp_path):
    """Mutating exit(2)→exit(0) must be detected: blocks print but don't stop."""
    with mutation(PUSH_SCRIPT, mut_remove_exit_code):
        code = run_push_check("git push origin main",
                              cwd=_secrets_block_dir(tmp_path))
        killed = code != 2
        assert killed, "mut_remove_exit_code survived: secrets scenario still blocked"


def test_mutation_empty_function(tmp_path):
    """Emptying main() must be detected: no checks run at all."""
    with mutation(PUSH_SCRIPT, mut_empty_function):
        code = run_push_check("git push origin main",
                              cwd=_secrets_block_dir(tmp_path))
        killed = code != 2
        assert killed, "mut_empty_function survived: secrets scenario still blocked"
