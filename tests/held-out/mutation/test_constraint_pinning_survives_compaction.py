"""Held-out mutation test: constraint-pinning.py survives compaction.

Policy: ALWAYS_PASSES
Source: Rule 14 + CodeAssay (arXiv:2608.03535v1).

Verifies that constraint-pinning.py:
  1. Writes a marker on PostCompaction when constraints are dropped.
  2. Re-injects on UserPromptSubmit when marker exists.
  3. Clears marker after re-injection.
  4. Clears all markers on SessionStart.
"""
import json
import os
import subprocess
import sys
import tempfile
import glob

import pytest
from _mutation import mutation, mut_empty_function, mut_remove_print

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
PINNING_SCRIPT = os.path.join(SCRIPTS_DIR, "constraint-pinning.py")

MARKER_PREFIX = "devin-constraint-reinject"


def run_pinning(event: str, payload: dict = None) -> tuple:
    """Run constraint-pinning.py with a simulated event. Returns (exit_code, stdout, stderr)."""
    data = {"hook_event_name": event}
    if payload:
        data.update(payload)
    result = subprocess.run(
        [sys.executable, PINNING_SCRIPT],
        input=json.dumps(data), capture_output=True, text=True, timeout=10,
    )
    return result.returncode, result.stdout, result.stderr


def get_markers():
    """Find all constraint-pinning markers in temp dir."""
    pattern = os.path.join(tempfile.gettempdir(), f"{MARKER_PREFIX}*")
    return glob.glob(pattern)


def clear_all_markers():
    for f in get_markers():
        try:
            os.remove(f)
        except OSError:
            pass


def test_post_compaction_dropped_constraints():
    """PostCompaction with empty summary should write a marker."""
    clear_all_markers()
    code, out, err = run_pinning("PostCompaction", {"summary": "", "session_id": "test-sess"})
    assert code == 0
    markers = get_markers()
    assert len(markers) > 0, "No marker written after compaction with dropped constraints"
    clear_all_markers()


def test_post_compaction_retained_constraints():
    """PostCompaction with constraints in summary should NOT write a marker."""
    clear_all_markers()
    summary = "Pinned governance constraints: no AI signatures, no push without green, execute-first, maximum precision, security sandbox, constraint pinning, context window lean, never read secrets."
    code, out, err = run_pinning("PostCompaction", {"summary": summary, "session_id": "test-sess2"})
    assert code == 0
    # Marker should not exist for this session
    markers = [m for m in get_markers() if "test-sess2" in m]
    assert len(markers) == 0, "Marker written despite constraints surviving"
    clear_all_markers()


def test_user_prompt_submit_reinjects():
    """UserPromptSubmit with existing marker should re-inject constraints."""
    clear_all_markers()
    # First, create a marker via PostCompaction
    run_pinning("PostCompaction", {"summary": "", "session_id": "test-reinject"})
    # Then, trigger UserPromptSubmit
    code, out, err = run_pinning("UserPromptSubmit", {"prompt": "test", "session_id": "test-reinject"})
    assert code == 0
    assert "hookSpecificOutput" in out, f"Re-injection did not emit hookSpecificOutput: {out}"
    assert "additionalContext" in out, "Re-injection missing additionalContext"
    # Marker should be cleared after re-injection
    markers = [m for m in get_markers() if "test-reinject" in m]
    assert len(markers) == 0, "Marker not cleared after re-injection"
    clear_all_markers()


def test_session_start_clears_markers():
    """SessionStart should clear all stale markers."""
    clear_all_markers()
    # Create a marker
    run_pinning("PostCompaction", {"summary": "", "session_id": "stale-sess"})
    assert len(get_markers()) > 0, "Pre-condition: marker should exist"
    # Trigger SessionStart
    code, out, err = run_pinning("SessionStart", {"source": "test"})
    assert code == 0
    assert len(get_markers()) == 0, "SessionStart did not clear markers"
    clear_all_markers()


def test_invalid_json_fail_open():
    """Invalid JSON must fail-open (exit 0)."""
    result = subprocess.run(
        [sys.executable, PINNING_SCRIPT],
        input="not json", capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0


def test_unknown_event_fail_open():
    """Unknown event must fail-open (exit 0)."""
    code, _, _ = run_pinning("UnknownEvent")
    assert code == 0


def test_mutation_empty_function():
    """Emptying main() must be detected: pinning stops working."""
    with mutation(PINNING_SCRIPT, mut_empty_function) as result:
        clear_all_markers()
        code, out, err = run_pinning("PostCompaction", {"summary": "", "session_id": "mut-test"})
        # With empty main(), no marker is written
        markers = [m for m in get_markers() if "mut-test" in m]
        killed = len(markers) == 0  # empty function → no marker → detected
        assert killed, "mut_empty_function survived: marker still written"
        clear_all_markers()


def test_mutation_remove_print():
    """Removing print() must be detected: no re-injection output."""
    with mutation(PINNING_SCRIPT, mut_remove_print) as result:
        clear_all_markers()
        # Create marker
        run_pinning("PostCompaction", {"summary": "", "session_id": "mut-print"})
        # Try re-injection
        code, out, err = run_pinning("UserPromptSubmit", {"prompt": "x", "session_id": "mut-print"})
        killed = "hookSpecificOutput" not in out  # no output → detected
        assert killed, "mut_remove_print survived: re-injection still emitted"
        clear_all_markers()
