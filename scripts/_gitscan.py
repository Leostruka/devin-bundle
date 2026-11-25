#!/usr/bin/env python3
"""Per-process memoization for read-only git hook scans.

Stop consolidates check-ai-signature + no-em-dash in one process; both scan
the same diffs and untracked listings, paying ~90ms per duplicated git spawn
on Windows. Hook execution is atomic - no tool call can mutate the tree
mid-event - so caching read-only git output per process is exact.

Standalone execution is unaffected: a fresh process means a fresh cache.
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

_cache = {}


class GitResult:
    __slots__ = ("returncode", "stdout", "stderr")

    def __init__(self, returncode, stdout, stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _invoke_git(argv, cwd):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        argv, capture_output=True, timeout=10, cwd=cwd,
        encoding="utf-8", errors="replace", creationflags=flags,
    )
    return GitResult(result.returncode, result.stdout, result.stderr or "")


def run_git(argv, cwd):
    """Memoized read-only git invocation. Returns GitResult or raises
    the same OSError family subprocess.run would (callers already handle)."""
    key = (tuple(argv), cwd)
    if key not in _cache:
        _cache[key] = _invoke_git(argv, cwd)
    return _cache[key]


def run_git_batch(argvs, cwd):
    """Run independent read-only git scans concurrently and memoize successes.

    Returns a list aligned with `argvs`: GitResult for a completed scan, or
    the caught exception instance for a failed spawn/timeout. Exceptions are
    values here because callers have per-scan failure policies (for example,
    a missing upstream must not suppress the untracked-file scan). Duplicate
    invocations within the batch share one subprocess.
    """
    outcomes = [None] * len(argvs)
    pending = []
    pending_keys = set()
    keys = [(tuple(argv), cwd) for argv in argvs]
    for i, key in enumerate(keys):
        if key in _cache:
            outcomes[i] = _cache[key]
        elif key not in pending_keys:
            pending_keys.add(key)
            pending.append((key, list(argvs[i])))

    def invoke(item):
        key, argv = item
        try:
            return key, _invoke_git(argv, cwd)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            return key, exc

    if pending:
        if len(pending) == 1:
            completed = [invoke(pending[0])]
        else:
            with ThreadPoolExecutor(max_workers=len(pending)) as pool:
                completed = list(pool.map(invoke, pending))
        by_key = {}
        for key, outcome in completed:
            if not isinstance(outcome, Exception):
                _cache[key] = outcome
            by_key[key] = outcome
        for i, key in enumerate(keys):
            if outcomes[i] is None:
                outcomes[i] = by_key[key]
    return outcomes


if __name__ == '__main__':
    sys.exit('usage: import _gitscan from a hook script (see check-ai-signature.py)')
