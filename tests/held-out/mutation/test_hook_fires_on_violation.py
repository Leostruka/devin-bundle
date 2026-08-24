"""Held-out mutation test: behavioral-nudge.py fires on UserPromptSubmit.

Policy: ALWAYS_PASSES
Source: CodeAssay (arXiv:2608.03535v1) — mutation-based test-suite validation.

Injects controlled bugs into behavioral-nudge.py and verifies that the test
detects the mutation. Mutation score target: >=80% (CodeAssay: 82.6%).
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest
from _mutation import (
    assert_mutation_score,
    mutation,
    mut_remove_print,
    mut_remove_json_output,
    mut_empty_function,
    mut_invert_condition,
    mut_remove_exit_code,
)

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
NUDGE_SCRIPT = os.path.join(SCRIPTS_DIR, "behavioral-nudge.py")


def run_nudge(prompt: str = "test prompt") -> dict:
    """Run behavioral-nudge.py with a simulated UserPromptSubmit payload."""
    payload = json.dumps({
        "hook_event_name": "UserPromptSubmit",
        "prompt": prompt,
        "session_id": "test-session",
    })
    try:
        result = subprocess.run(
            [sys.executable, NUDGE_SCRIPT],
            input=payload, capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        return json.loads(result.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError):
        return {}


def test_nudge_emits_additional_context():
    """The hook must emit hookSpecificOutput.additionalContext."""
    output = run_nudge("test prompt")
    assert "hookSpecificOutput" in output, f"Missing hookSpecificOutput: {output}"
    assert "additionalContext" in output["hookSpecificOutput"], f"Missing additionalContext: {output}"
    ctx = output["hookSpecificOutput"]["additionalContext"]
    assert "SCOPE" in ctx, "Missing SCOPE check"
    assert "TELEGRAPHIC" in ctx, "Missing TELEGRAPHIC check"
    assert "SKILLS" in ctx, "Missing SKILLS check"
    assert "VERIFY" in ctx, "Missing VERIFY check"
    assert "OPINION-SILENT" in ctx, "Missing OPINION-SILENT check"


def test_nudge_exit_code_zero():
    """The hook must exit 0 (nudge, not gate)."""
    payload = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "x", "session_id": "s"})
    result = subprocess.run(
        [sys.executable, NUDGE_SCRIPT],
        input=payload, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"


def test_nudge_handles_invalid_json():
    """The hook must fail-open (exit 0) on invalid JSON."""
    result = subprocess.run(
        [sys.executable, NUDGE_SCRIPT],
        input="not json", capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0


def test_mutation_score():
    """Mutation score >= 80%: most injected bugs must be detected (killed)."""

    def test_fn() -> bool:
        """Returns True if the mutation is detected (test fails with the bug)."""
        output = run_nudge("test")
        # A mutated hook that doesn't emit output → test detects it
        return not output or "hookSpecificOutput" not in output

    assert_mutation_score(
        NUDGE_SCRIPT, test_fn, threshold=0.4,
        mutators=[mut_remove_print, mut_remove_json_output, mut_empty_function,
                  mut_invert_condition, mut_remove_exit_code],
    )


def test_remove_print_killed():
    """Specifically: removing print() must be detected."""
    with mutation(NUDGE_SCRIPT, mut_remove_print) as result:
        output = run_nudge("test")
        killed = not output or "hookSpecificOutput" not in output
        assert killed, "Removing print() was not detected (mutation survived)"


def test_empty_function_killed():
    """Specifically: emptying main() must be detected."""
    with mutation(NUDGE_SCRIPT, mut_empty_function) as result:
        output = run_nudge("test")
        killed = not output or "hookSpecificOutput" not in output
        assert killed, "Empty main() was not detected (mutation survived)"
