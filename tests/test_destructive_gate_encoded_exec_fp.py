"""False-positive regression pins: destructive-gate ENCODED_EXEC -c payload.

Reproduced 3x in the 2026-11-25 self-improvement session: legitimate heredoc/
probe content containing `python -c X` plus the common words exec/eval/decode/
subprocess in LATER text blocked as encoded execution. Root cause: the keyword
scan after `-[ce]` was unbounded (`[^|;&]*?` matches newlines), so keywords
outside the -c payload argument still matched. The payload is a single shell
word (quoted or bare); keywords beyond its end are not part of the payload.
"""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
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
    # Repro 2 shape: heredoc body with an embedded python -c payload string
    # on one line and the word exec (inside JSON prose) on a later line.
    "python - <<'PYEOF'\n"
    "payload = {\"command\": \"python -c \\\"print(1)\\\"\",\n"
    "           \"tool_name\": \"exec\"}\n"
    "print(payload)\n"
    "PYEOF",
    # Same-line prose: keyword outside the bare -c payload token.
    "echo \"use python -c pass then exec runs the job\"",
    # Keyword in a later command segment after the -c payload closes.
    "python -c 'print(1)'\necho exec is a common word",
    # decode/subprocess/eval are ordinary words outside the payload.
    "python -c 'print(1)' && echo decode eval subprocess",
    "python -c \"print(2)\" ; echo subprocess",
])
def test_encoded_exec_fp_allowed(cmd):
    rc, out = run_gate(cmd)
    assert rc == 0, f"false positive blocked: {cmd!r} -> {out}"


@pytest.mark.parametrize("cmd", [
    # Positive controls: keyword inside the actual -c payload must block.
    "python -c \"import base64;base64.b64decode('eQ==')\"",
    "perl -e 'system(\"x\")'",
    "python -c 'import subprocess'",
    "python3 -c \"exec('x')\"",
    "node -e 'eval(process)'",
])
def test_encoded_exec_payload_still_blocked(cmd):
    rc, out = run_gate(cmd)
    assert rc == 2, f"bypass allowed: {cmd!r}"
