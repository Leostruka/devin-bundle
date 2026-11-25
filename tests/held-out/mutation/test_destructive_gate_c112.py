"""Held-out mutation test: destructive-gate.py C112 ADS de-escape regression.

Policy: ALWAYS_PASSES
Source: CodeAssay (arXiv:2608.03535v1) — mutation-based test-suite validation.

C105 fix: _deescape_shell collapsed the backslash after a drive letter
(`C:\\dir` -> `C:dir`), which made the ADS lookahead lose its anchor and
block every absolute Windows path used as a redirect/copy target. The fix
preserves `\\` after `[A-Za-z]:`. These tests pin both sides: absolute
drive-letter targets allowed, bare `name:stream` ADS still blocked.
"""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
GATE_SCRIPT = os.path.join(SCRIPTS_DIR, "destructive-gate.py")


def run_gate(command: str) -> tuple[int, str]:
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "exec",
        "tool_input": {"command": command},
        "session_id": "test",
    })
    result = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        input=payload, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=10,
    )
    return result.returncode, result.stdout.strip()


@pytest.mark.parametrize("cmd", [
    "echo x > C:\\logs\\out.txt",
    "cp src.txt D:\\dst\\out.txt",
    "mkdir C:\\new\\dir",
    "type nul > E:\\tmp\\f.log",
])
def test_drive_letter_abs_targets_allowed(cmd):
    """Absolute drive-letter targets are not NTFS ADS."""
    code, out = run_gate(cmd)
    assert code == 0, f"abs drive path should be allowed, got {code}: {out}"


@pytest.mark.parametrize("cmd", [
    "echo x > file:hidden",
    "cp a note:stream",
    "type x > C:\\dir\\f.txt:hidden",
])
def test_real_ads_forms_still_blocked(cmd):
    code, out = run_gate(cmd)
    assert code == 2, f"real ADS should block, got {code}: {out}"
