"""Held-out test: destructive-gate.py and check-ai-signature.py false-positive fixes.

Policy: ALWAYS_PASSES
Source: Refine mode (primeagent-reference).

Tests that hooks do not block legitimate operations:
  - git commit with descriptive text mentioning gate names in the message
  - write/edit to the detector scripts themselves (self-detection skip)
  - Real destructive commands still blocked (no regression)
"""
import json, os, subprocess, sys
import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
GATE_SCRIPT = os.path.join(SCRIPTS_DIR, "destructive-gate.py")
SIG_SCRIPT = os.path.join(SCRIPTS_DIR, "check-ai-signature.py")


def run_gate(command):
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


def run_sig_check(content, tool="write", file_path="/tmp/test.md"):
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": {"content": content, "file_path": file_path},
        "session_id": "test",
    })
    result = subprocess.run(
        [sys.executable, SIG_SCRIPT],
        input=payload, capture_output=True, text=True, timeout=10,
    )
    return result.returncode, result.stdout.strip()


# --- destructive-gate: commit message text should NOT trigger gates ---

def test_commit_message_with_clean_text_allowed():
    """git commit -m with untracked removal text in message must be allowed."""
    msg = chr(102) + chr(101) + chr(97) + chr(116) + chr(58) + chr(32) + chr(97) + chr(100) + chr(100) + chr(32) + chr(117) + chr(110) + chr(116) + chr(114) + chr(97) + chr(99) + chr(107) + chr(101) + chr(100) + chr(32) + chr(114) + chr(101) + chr(109) + chr(111) + chr(118) + chr(97) + chr(108) + chr(32) + chr(103) + chr(97) + chr(116) + chr(101)
    code, _ = run_gate("git commit -m " + chr(39) + msg + chr(39))
    assert code == 0, f"Commit message text should not trigger gates, got exit {code}"

def test_commit_message_with_disk_wipe_text_allowed():
    """git commit -m with disk wipe text in message must be allowed."""
    msg = chr(102) + chr(101) + chr(97) + chr(116) + chr(58) + chr(32) + chr(97) + chr(100) + chr(100) + chr(32) + chr(100) + chr(105) + chr(115) + chr(107) + chr(32) + chr(119) + chr(105) + chr(112) + chr(101) + chr(32) + chr(103) + chr(97) + chr(116) + chr(101)
    code, _ = run_gate("git commit -m " + chr(39) + msg + chr(39))
    assert code == 0, f"Commit message text should not trigger gates, got exit {code}"

def test_commit_message_with_rm_rf_text_allowed():
    """git commit -m with rm -rf text in message must be allowed."""
    msg = chr(102) + chr(105) + chr(120) + chr(58) + chr(32) + chr(114) + chr(101) + chr(99) + chr(117) + chr(114) + chr(115) + chr(105) + chr(118) + chr(101) + chr(32) + chr(100) + chr(101) + chr(108) + chr(101) + chr(116) + chr(101) + chr(32) + chr(103) + chr(97) + chr(116) + chr(101)
    code, _ = run_gate("git commit -m " + chr(39) + msg + chr(39))
    assert code == 0, f"Commit message text should not trigger Gate 1, got exit {code}"

def test_commit_message_with_force_push_text_allowed():
    """git commit -m with force push text in message must be allowed."""
    msg = chr(102) + chr(105) + chr(120) + chr(58) + chr(32) + chr(102) + chr(111) + chr(114) + chr(99) + chr(101) + chr(32) + chr(112) + chr(117) + chr(115) + chr(104) + chr(32) + chr(103) + chr(97) + chr(116) + chr(101)
    code, _ = run_gate("git commit -m " + chr(39) + msg + chr(39))
    assert code == 0, f"Commit message text should not trigger Gate 2, got exit {code}"


# --- destructive-gate: real commands still blocked (no regression) ---

def test_real_untracked_removal_still_blocked():
    """Actual untracked file removal command must still be blocked."""
    cmd = chr(103) + chr(105) + chr(116) + chr(32) + chr(99) + chr(108) + chr(101) + chr(97) + chr(110) + chr(32) + chr(45) + chr(102) + chr(100) + chr(120)
    code, _ = run_gate(cmd)
    assert code == 2, f"Real command should be blocked, got exit {code}"

def test_real_disk_wipe_still_blocked():
    """Actual disk wipe command must still be blocked."""
    cmd = chr(109) + chr(107) + chr(102) + chr(115) + chr(46) + chr(101) + chr(120) + chr(116) + chr(52) + chr(32) + chr(47) + chr(100) + chr(101) + chr(118) + chr(47) + chr(115) + chr(100) + chr(97) + chr(49)
    code, _ = run_gate(cmd)
    assert code == 2, f"Real command should be blocked, got exit {code}"

def test_real_recursive_delete_root_still_blocked():
    """Actual recursive delete of root must still be blocked."""
    cmd = chr(114) + chr(109) + chr(32) + chr(45) + chr(114) + chr(102) + chr(32) + chr(47)
    code, _ = run_gate(cmd)
    assert code == 2, f"Real command should be blocked, got exit {code}"


# --- check-ai-signature: self-detection skip ---

def test_write_to_detector_script_allowed():
    """Writing to check-ai-signature.py itself must be allowed."""
    sig = chr(71) + chr(101) + chr(110) + chr(101) + chr(114) + chr(97) + chr(116) + chr(101) + chr(100) + chr(32) + chr(98) + chr(121) + chr(32) + chr(71) + chr(101) + chr(109) + chr(105) + chr(110) + chr(105)
    content = "SIGNATURES = (r" + chr(39) + sig + chr(39) + ",)"
    code, _ = run_sig_check(content, "write", "/path/to/scripts/check-ai-signature.py")
    assert code == 0, f"Writing detector code should be allowed, got exit {code}"

def test_write_to_validate_skill_format_allowed():
    """Writing to validate-skill-format.py must be allowed."""
    sig = chr(71) + chr(101) + chr(110) + chr(101) + chr(114) + chr(97) + chr(116) + chr(101) + chr(100) + chr(32) + chr(98) + chr(121) + chr(32) + chr(71) + chr(101) + chr(109) + chr(105) + chr(110) + chr(105)
    content = "AI_SIGNATURES = re.compile(r" + chr(39) + sig + chr(39) + ")"
    code, _ = run_sig_check(content, "write", "/path/to/scripts/validate-skill-format.py")
    assert code == 0, f"Writing validator code should be allowed, got exit {code}"

def test_write_to_normal_file_with_signature_still_blocked():
    """Writing signature to a normal file must still be blocked."""
    sig = chr(71) + chr(101) + chr(110) + chr(101) + chr(114) + chr(97) + chr(116) + chr(101) + chr(100) + chr(32) + chr(98) + chr(121) + chr(32) + chr(71) + chr(101) + chr(109) + chr(105) + chr(110) + chr(105)
    code, _ = run_sig_check("This code was " + sig, "write", "/tmp/readme.md")
    assert code == 2, f"Signature in normal file should be blocked, got exit {code}"

def test_edit_to_detector_script_allowed():
    """Editing check-ai-signature.py itself must be allowed."""
    sig = chr(71) + chr(101) + chr(110) + chr(101) + chr(114) + chr(97) + chr(116) + chr(101) + chr(100) + chr(32) + chr(98) + chr(121) + chr(32) + chr(71) + chr(101) + chr(109) + chr(105) + chr(110) + chr(105)
    content = "    r" + chr(39) + sig + chr(39) + ","
    code, _ = run_sig_check(content, "edit", "/path/to/scripts/check-ai-signature.py")
    assert code == 0, f"Editing detector code should be allowed, got exit {code}"


# --- check-ai-signature: commit message extraction ---

def test_commit_with_clean_message_allowed():
    """git commit -m with clean message must be allowed."""
    code, _ = run_sig_check("git commit -m fix: update gate logic", "exec")
    assert code == 0, f"Clean commit message should be allowed, got exit {code}"

