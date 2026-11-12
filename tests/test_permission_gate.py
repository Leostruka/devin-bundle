"""Tests for scripts/permission-gate.py — approve-only PermissionRequest gate."""
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "permission-gate.py")


def run_gate(payload):
    r = subprocess.run([sys.executable, SCRIPT], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
    return r.stdout.strip()


def gate(cmd, tool="exec"):
    return run_gate({"hook_event_name": "PermissionRequest",
                     "tool_name": tool,
                     "tool_input": {"command": cmd}})


def test_approves_readonly_git():
    for c in ("git status", "git status --porcelain", "git diff HEAD~1",
              "git log --oneline -5", "git show abc1234", "git ls-files",
              "git rev-parse HEAD", "git check-ignore foo.py"):
        out = gate(c)
        assert json.loads(out)["decision"] == "approve", c


def test_approves_readonly_misc():
    for c in ("ls -la", "rg foo -t py", "fd -e md", "cat file.txt",
              "pwd", "wc -l x", "which python", "date", "echo hi"):
        out = gate(c)
        assert json.loads(out)["decision"] == "approve", c


def test_silent_on_writes():
    for c in ("npm install foo", "git push origin main", "git commit -m x",
              "git checkout -b b", "pip install x", "rm -rf y",
              "gh pr create --title t", "git branch -d feat"):
        assert gate(c) == "", c


def test_silent_on_shell_composition():
    for c in ("git status; rm x", "git log | head", "git diff && rm -rf /",
              "cat $(whoami)", "git log `id`", "git status > /tmp/o",
              "git log\nrm -rf /"):
        assert gate(c) == "", c


def test_silent_on_gh_api_write():
    assert gate('gh api repos/x -X POST -f k=v') == ""
    assert gate("gh pr merge 1 --squash") == ""


def test_gh_api_read_approved():
    out = gate("gh api repos/Leostruka/devin-bundle")
    assert json.loads(out)["decision"] == "approve"


def test_silent_on_other_tools():
    assert run_gate({"hook_event_name": "PermissionRequest",
                     "tool_name": "write",
                     "tool_input": {"file_path": "x"}}) == ""


def test_fail_open_on_garbage():
    r = subprocess.run([sys.executable, SCRIPT], input="not json",
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
    assert r.stdout.strip() == ""
