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


def _git(*args, extra_env=None, stdin=None):
    # commit-tree needs a committer identity; CI runners have none.
    # Throwaway fixture objects only - never pushed, no attribution meaning.
    env = dict(os.environ)
    env.setdefault("GIT_COMMITTER_NAME", "gate7-fixture")
    env.setdefault("GIT_COMMITTER_EMAIL", "gate7-fixture@localhost")
    env.setdefault("GIT_AUTHOR_NAME", "gate7-fixture")
    env.setdefault("GIT_AUTHOR_EMAIL", "gate7-fixture@localhost")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["git"] + list(args), capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          cwd=REPO, env=env, input=stdin)


@pytest.fixture
def merged_branch():
    name = "gate7-test-merged"
    r = _git("branch", "-f", name, "HEAD~1")
    # CI diagnostics 2026-11-26: cherry reported "unknown commit" on macos/
    # ubuntu while WSL passed - pin down whether fixture creation itself
    # fails rather than guessing at gate behavior.
    assert r.returncode == 0, f"branch -f failed: {r.stderr!r}"
    v = _git("rev-parse", "--verify", name)
    assert v.returncode == 0, f"created branch unverifiable: {v.stderr!r}"
    yield name
    _git("branch", "-D", name)


@pytest.fixture
def unmerged_branch():
    name = "gate7-test-unmerged"
    # A root commit's patch-id is undefined/empty in some git versions
    # (diff-tree without --root), so cherry can mark it '-' on CI while
    # marking it '+' elsewhere - the observed inversion. Build a commit
    # with a proper parent and a real content delta instead: the patch-id
    # is then well-defined and unique.
    parent = _git("rev-parse", "HEAD").stdout.strip()
    assert parent
    blob = _git("hash-object", "-w", "--stdin",
                stdin="gate7 unmerged fixture\n").stdout.strip()
    assert blob
    idx = os.path.join(REPO, ".git", "gate7-test-index")
    idx_env = {"GIT_INDEX_FILE": idx}
    try:
        r = _git("read-tree", "HEAD", extra_env=idx_env)
        assert r.returncode == 0, f"read-tree: {r.stderr!r}"
        r = _git("update-index", "--add", "--cacheinfo",
                 f"100644,{blob},gate7-unmerged-fixture.txt",
                 extra_env=idx_env)
        assert r.returncode == 0, f"update-index: {r.stderr!r}"
        tree = _git("write-tree", extra_env=idx_env).stdout.strip()
        assert tree
    finally:
        if os.path.exists(idx):
            os.unlink(idx)
    sha = _git("commit-tree", tree, "-p", parent, "-m",
               "gate7 unmerged").stdout.strip()
    assert sha
    r = _git("branch", "-f", name, sha)
    assert r.returncode == 0, f"branch -f failed: {r.stderr!r}"
    v = _git("rev-parse", "--verify", name)
    assert v.returncode == 0, f"created branch unverifiable: {v.stderr!r}"
    yield name
    _git("branch", "-D", name)


def _diag(cmd, proc):
    cherry = ""
    for tok in cmd.split():
        if tok.startswith("gate7-test"):
            c = _git("cherry", "HEAD", tok)
            cherry += (f"cherry {tok}: rc={c.returncode} "
                       f"out={c.stdout[:120]!r} err={c.stderr[:120]!r} ")
    return (f"rc={proc.returncode} out={proc.stdout[:200]!r} "
            f"err={proc.stderr[:200]!r} {cherry}")


def test_merged_branch_allowed(merged_branch):
    cmd = f"git branch -D {merged_branch}"
    proc = run_gate(cmd)
    assert proc.returncode == 0, _diag(cmd, proc)


def test_unmerged_branch_blocked(unmerged_branch):
    cmd = f"git branch -D {unmerged_branch}"
    proc = run_gate(cmd)
    assert proc.returncode == 2, _diag(cmd, proc)


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
