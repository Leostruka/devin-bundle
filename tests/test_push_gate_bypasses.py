"""Regression: push-gate bypasses found in review.

1. `--dry-run` anywhere in the command skipped the whole gate — a stray
   mention (echo, commit message, another command) must not exempt a real
   push. The flag is only honored inside the push segment itself.
2. The segment splitter missed `&`, `()`, backticks, `$()` — `git push&`,
   `(git push)`, `$(git push)` published with no gate at all.
"""
import importlib.util
import sys

sys.path.insert(0, "scripts")


def _mod():
    spec = importlib.util.spec_from_file_location(
        "check_push_green_bypass", "scripts/check-push-green.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


PUSH_FORMS = [
    "git push",
    "git push origin main --force",
    "git push&",
    "git push &",
    "(git push)",
    "`git push`",
    "$(git push)",
    "echo x && git push",
    "git push; echo done",
    "git -C repo push",
    "git -c protocol.version=2 push",
    "git --git-dir=x push",
]

NOT_PUSH = [
    "git pull",
    "git fetch && git log",
    "git checkout -b x(push)",
    "git status",
    "gh pr merge",
]


def test_push_segment_forms():
    m = _mod()
    for c in PUSH_FORMS:
        assert m.is_git_push(c), c
    for c in NOT_PUSH:
        assert not m.is_git_push(c), c


def test_dry_run_scoped_to_push_segment():
    m = _mod()
    # Stray --dry-run outside the push segment must NOT exempt the push:
    seg = m._push_segment("git commit -m note --dry-run && git push")
    assert seg is not None and "--dry-run" not in seg
    seg = m._push_segment("echo --dry-run; git push origin main")
    assert seg is not None and "--dry-run" not in seg
    # A real dry-run push IS honored:
    seg = m._push_segment("git push --dry-run")
    assert seg is not None and "--dry-run" in seg
    seg = m._push_segment("git push origin main --dry-run")
    assert seg is not None and "--dry-run" in seg
