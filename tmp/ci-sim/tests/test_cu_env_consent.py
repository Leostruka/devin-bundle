"""Gate for C04 consent: mutating verbs require an interactive human
confirmation bound to the plan digest — non-TTY is refused, and an agent
typing into its own PTY is not consent.
"""
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cu_load import load  # noqa: E402

cu_env = load("cu_env")


def test_consent_refused_without_tty():
    """stdin is a pipe (agent/non-interactive): no consent is possible."""
    fake_in = io.StringIO("yes\n")
    fake_in.isatty = lambda: False
    out = io.StringIO()
    ok = cu_env.interactive_consent(
        {"digest": "abc123", "op": "create"},
        stdin=fake_in, stderr=out)
    assert ok is False


def test_consent_accepted_with_tty_and_digest():
    fake_in = io.StringIO()
    fake_in.isatty = lambda: True
    fake_in.write = lambda s: None  # input() writes prompt to stdout —
    # simulate typed answer by patching readline instead
    answers = iter(["yes"])
    fake_in.readline = lambda: next(answers)
    out = io.StringIO()
    ok = cu_env.interactive_consent(
        {"digest": "abc123", "op": "create"},
        stdin=fake_in, stderr=out)
    assert ok is True
    assert "abc123" in out.getvalue()


def test_consent_rejected_answer_is_denied():
    fake_in = io.StringIO()
    fake_in.isatty = lambda: True
    answers = iter(["no"])
    fake_in.readline = lambda: next(answers)
    ok = cu_env.interactive_consent(
        {"digest": "abc123", "op": "reset"}, stdin=fake_in,
        stderr=io.StringIO())
    assert ok is False
