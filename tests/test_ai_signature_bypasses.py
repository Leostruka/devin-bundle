"""check-ai-signature.py: clustered/attached/long-form -m bypasses +
non-dict payload fail-open (regressions found by fuzzing)."""
import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts",
                    "check-ai-signature.py")
PY = sys.executable
SIG = "C" + "o-Authored-By: Dev" + "in"


def run_commit(cmd):
    payload = json.dumps({"hook_event_name": "PreToolUse",
                          "tool_name": "exec",
                          "tool_input": {"command": cmd}})
    return subprocess.run([PY, HOOK], input=payload, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


@pytest.mark.parametrize("form", [
    'git commit -m "{sig}"',
    'git commit -am "{sig}"',
    'git commit -sm "{sig}"',
    'git commit -asm "{sig}"',
    'git commit -m"{sig}"',
    "git commit -m'{sig}'",
    "git commit -am'{sig}'",
    'git commit --message="{sig}"',
    'git commit --message "{sig}"',
    'git commit -a -m "{sig}" && echo done',
])
def test_signature_blocked_in_all_m_forms(form):
    r = run_commit(form.format(sig=SIG))
    assert r.returncode == 2
    assert "block" in r.stdout


@pytest.mark.parametrize("cmd", [
    'git commit --amend --no-edit',
    'git commit --allow-empty',
    'git commit -m "clean message"',
    'git commit -s',
])
def test_clean_commit_forms_allowed(cmd):
    r = run_commit(cmd)
    assert r.returncode == 0


@pytest.mark.parametrize("raw", ['[1,2]', '"x"', '42', 'null'])
def test_non_dict_payload_fail_open(raw):
    r = subprocess.run([PY, HOOK], input=raw, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and 'Traceback' not in r.stderr
