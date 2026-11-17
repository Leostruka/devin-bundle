"""validate-tool-args.py: ripgrep-unsupported syntax gate + non-dict
payload fail-open (regressions)."""
import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts",
                    "validate-tool-args.py")
PY = sys.executable


def run_grep(pattern, path="."):
    payload = json.dumps({"hook_event_name": "PreToolUse",
                          "tool_name": "grep",
                          "tool_input": {"pattern": pattern, "path": path}})
    return subprocess.run([PY, HOOK], input=payload, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


@pytest.mark.parametrize("pat", [
    "foo(?=bar)", "foo(?!bar)", "(?<=x)y", "(?<!x)y",
    "(a)" + chr(92) + "1", "(?>a)b",
])
def test_ripgrep_unsupported_blocked(pat):
    r = run_grep(pat)
    assert r.returncode == 2 and "ripgrep" in r.stdout


@pytest.mark.parametrize("pat", ["a\\G", "x(?(<n>)y|z)"])
def test_python_invalid_also_blocked(pat):
    # Not rg-specific: rejected earlier by the Python compile check.
    assert run_grep(pat).returncode == 2


@pytest.mark.parametrize("pat", [
    "foo" + chr(92) + "([^)]", "a{1,9}", "(a|b)c", "x+",
    "(?P<name>foo)", "[a-z]+\\b\\d+",
])
def test_rg_supported_allowed(pat):
    assert run_grep(pat).returncode == 0


@pytest.mark.parametrize("raw", ['[1,2]', '"x"', '42', 'null'])
def test_non_dict_payload_fail_open(raw):
    r = subprocess.run([PY, HOOK], input=raw, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and 'Traceback' not in r.stderr
