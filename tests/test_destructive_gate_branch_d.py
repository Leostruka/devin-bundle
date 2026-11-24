"""destructive-gate.py: gate 7 smart branch -D (cherry-equivalent allow).

Observed friction (2026-11-24): squash-merged lane branches could not be
deleted because `-d` refuses rewritten commits and the gate blocked `-D`.
`git cherry HEAD <branch>` proves patch-equivalence; merged branches are
allowed, unmerged/unknown stay blocked, foreign-repo flags stay blocked.
"""
import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", "scripts",
                    "destructive-gate.py")
PY = sys.executable
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_gate(cmd):
    payload = json.dumps({"hook_event_name": "PreToolUse",
                          "tool_name": "exec",
                          "tool_input": {"command": cmd}})
    return subprocess.run([PY, HOOK], input=payload, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          cwd=REPO)


def _git(*args):
    return subprocess.run(["git"] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          cwd=REPO)


@pytest.fixture
def merged_branch():
    name = "gate7-test-merged"
    _git("branch", "-f", name, "HEAD~1")
    yield name
    _git("branch", "-D", name)


@pytest.fixture
def unmerged_branch():
    name = "gate7-test-unmerged"
    tree = _git("rev-parse", "HEAD^{tree}").stdout.strip()
    sha = _git("commit-tree", tree, "-m", "gate7 unmerged").stdout.strip()
    assert sha
    _git("branch", "-f", name, sha)
    yield name
    _git("branch", "-D", name)


def test_merged_branch_allowed(merged_branch):
    assert run_gate(f"git branch -D {merged_branch}").returncode == 0


def test_unmerged_branch_blocked(unmerged_branch):
    assert run_gate(f"git branch -D {unmerged_branch}").returncode == 2


def test_nonexistent_branch_blocked():
    assert run_gate("git branch -D no-such-branch-xyz").returncode == 2


def test_foreign_repo_blocked(merged_branch):
    # -C <dir> targets another repo: unverifiable, keep blocking even though
    # the named branch is merged in THIS repo.
    assert run_gate(f"git -C {REPO} branch -D {merged_branch}").returncode == 2


def test_git_dir_env_prefix_blocked(merged_branch):
    # GIT_DIR=/GIT_WORK_TREE= env prefixes point at a foreign repo; cherry
    # runs against THIS repo and cannot verify, so stay blocked.
    assert run_gate(f"GIT_DIR=/tmp/x git branch -D {merged_branch}").returncode == 2
    assert run_gate(f"GIT_WORK_TREE=/tmp/x git branch -D {merged_branch}").returncode == 2


def test_multi_branch_mixed_blocked(merged_branch, unmerged_branch):
    cmd = f"git branch -D {merged_branch} {unmerged_branch}"
    assert run_gate(cmd).returncode == 2


def test_multi_branch_all_merged_allowed(merged_branch):
    name2 = "gate7-test-merged2"
    _git("branch", "-f", name2, "HEAD~1")
    try:
        cmd = f"git branch -D {merged_branch} {name2}"
        assert run_gate(cmd).returncode == 0
    finally:
        _git("branch", "-D", name2)


def test_plain_branch_d_still_blocked_without_merge():
    # A branch flag match with a truly unmerged operand stays blocked
    # regardless of the smart path (regression of original gate intent).
    assert run_gate("git branch -D").returncode == 0  # no operands = no-op


def test_other_gates_unaffected():
    assert run_gate("rm -rf /").returncode == 2
    assert run_gate("git branch -d whatever").returncode == 0
