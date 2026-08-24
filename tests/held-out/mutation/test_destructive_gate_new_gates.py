"""Held-out mutation test: destructive-gate.py new gates (6, 7, 8) + Windows rm.

Policy: ALWAYS_PASSES
Source: CodeAssay (arXiv:2608.03535v1) — mutation-based test-suite validation.

Tests the gates added in the self-improvement loop:
  - Gate 6: git clean -fdx (irreversible untracked/ignored file removal)
  - Gate 7: git branch -D (force delete, loses unmerged work)
  - Gate 8: mkfs / dd to disk devices (filesystem wipe)
  - Windows rm: Remove-Item -Recurse -Force, rd /s, del /s with dangerous paths
"""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
GATE_SCRIPT = os.path.join(SCRIPTS_DIR, "destructive-gate.py")


def run_gate(command: str) -> tuple[int, str]:
    """Run destructive-gate.py with a simulated exec payload. Returns (exit_code, stdout)."""
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "exec",
        "tool_input": {"command": command},
        "session_id": "test",
    })
    result = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        input=payload, capture_output=True, text=True, timeout=10,
    )
    return result.returncode, result.stdout.strip()


def test_git_clean_fdx_blocked():
    """Gate 6: git clean -fdx must be blocked."""
    code, out = run_gate("git clean -fdx")
    assert code == 2, f"Expected block (exit 2), got {code}: {out}"
    assert "git clean" in out.lower(), f"Block reason should mention git clean: {out}"


def test_git_clean_dry_run_allowed():
    """Gate 6: git clean -n (dry-run) must be allowed."""
    code, _ = run_gate("git clean -nfdx")
    assert code == 0, f"Dry-run clean should be allowed, got exit {code}"


def test_git_branch_D_blocked():
    """Gate 7: git branch -D must be blocked."""
    code, out = run_gate("git branch -D feature-branch")
    assert code == 2, f"Expected block (exit 2), got {code}: {out}"
    assert "branch" in out.lower(), f"Block reason should mention branch: {out}"


def test_git_branch_d_allowed():
    """Gate 7: git branch -d (safe delete) must be allowed."""
    code, _ = run_gate("git branch -d merged-branch")
    assert code == 0, f"Safe branch delete should be allowed, got exit {code}"


def test_mkfs_blocked():
    """Gate 8: mkfs must be blocked."""
    code, out = run_gate("mkfs.ext4 /dev/sda1")
    assert code == 2, f"Expected block (exit 2), got {code}: {out}"


def test_dd_to_disk_blocked():
    """Gate 8: dd to /dev/sd* must be blocked."""
    code, out = run_gate("dd if=/dev/zero of=/dev/sda bs=1M")
    assert code == 2, f"Expected block (exit 2), got {code}: {out}"


def test_windows_remove_item_recurse_force_root_blocked():
    r"""Windows rm: Remove-Item -Recurse -Force on C:\ must be blocked."""
    code, out = run_gate('Remove-Item -Recurse -Force "C:\\"')
    assert code == 2, f"Expected block for Windows rm on C:\\, got {code}: {out}"


def test_windows_rd_s_q_blocked():
    """Windows rm: rd /s /q on drive root must be blocked."""
    code, out = run_gate("rd /s /q C:\\")
    assert code == 2, f"Expected block for rd /s /q, got {code}: {out}"


def test_windows_remove_item_safe_allowed():
    """Windows rm: Remove-Item on a safe relative path must be allowed."""
    code, _ = run_gate("Remove-Item -Recurse -Force node_modules")
    assert code == 0, f"Safe Windows rm should be allowed, got exit {code}"


def test_rm_rf_drive_root_blocked():
    """rm -rf C:\\ must be blocked (Windows drive root in RM_DANGEROUS_TARGETS)."""
    code, _ = run_gate("rm -rf C:\\")
    assert code == 2, f"Expected block for rm -rf C:\\, got exit {code}"


def test_fail_open_on_invalid_json():
    """The hook must fail-open (exit 0) on invalid JSON."""
    result = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        input="not json", capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
