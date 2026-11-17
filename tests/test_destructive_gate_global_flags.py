"""destructive-gate.py: git global-flags bypass, Windows disk wipe,
non-dict payload fail-open, clean -n detection (regressions)."""
import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts",
                    "destructive-gate.py")
PY = sys.executable


def run_gate(cmd):
    payload = json.dumps({"hook_event_name": "PreToolUse",
                          "tool_name": "exec",
                          "tool_input": {"command": cmd}})
    return subprocess.run([PY, HOOK], input=payload, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


@pytest.mark.parametrize("cmd", [
    'git -C repo push -f',
    'git -C repo push --force',
    'git -c user.name=x push -f',
    'git --git-dir=.git push -f',
    'git -P push -f',
    'git -C repo clean -fdx',
    'git -C repo branch -D old',
    'git push -f',
    'git push --force',
    'format c:',
    'format d: /q',
    'diskpart',
    'chmod --recursive 777 /',
    'rm -rf /',
    'Remove-Item -Recurse -Force C:\\',
])
def test_destructive_blocked(cmd):
    assert run_gate(cmd).returncode == 2


@pytest.mark.parametrize("cmd", [
    'git push',
    'git push --force-with-lease',
    'git push --dry-run -f',
    'git -C repo status',
    'git status',
    'Format-Table x',
    'git commit -am "added rm -rf / gate"',
    'git commit --message="push -f docs"',
    'rm -rf node_modules',
    'rm -rf src',
    'git clean -fdx -n',
    'git clean -fdx --dry-run',
])
def test_safe_allowed(cmd):
    assert run_gate(cmd).returncode == 0


@pytest.mark.parametrize("raw", [
    '[1,2]', '"x"', '42', 'null',
    '{"tool_name":"exec","tool_input":"x"}',
    '{"tool_name":"exec","tool_input":42}',
])
def test_fail_open_non_dict(raw):
    r = subprocess.run([PY, HOOK], input=raw, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and 'Traceback' not in r.stderr
