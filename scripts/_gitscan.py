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

_cache = {}


class GitResult:
    __slots__ = ("returncode", "stdout", "stderr")

    def __init__(self, returncode, stdout, stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_git(argv, cwd):
    """Memoized read-only git invocation. Returns GitResult or raises
    the same OSError family subprocess.run would (callers already handle)."""
    key = (tuple(argv), cwd)
    if key in _cache:
        return _cache[key]
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        argv, capture_output=True, timeout=10, cwd=cwd,
        encoding="utf-8", errors="replace", creationflags=flags,
    )
    frozen = GitResult(result.returncode, result.stdout, result.stderr or "")
    _cache[key] = frozen
    return frozen


if __name__ == '__main__':
    sys.exit('usage: import _gitscan from a hook script (see check-ai-signature.py)')
