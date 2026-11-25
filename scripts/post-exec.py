#!/usr/bin/env python3
"""PostToolUse(^(exec|mcp_call_tool)$) consolidated post-checks — one spawn.

Runs in-process: silent-error-review, context-pressure, compact-gate,
memory-post-exec, gh-pr-assignee, stuck-detect, git-diff-stat.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

CHILDREN = [
    'silent-error-review.py',
    'context-pressure.py',
    'compact-gate.py',
    'memory-post-exec.py',
    'gh-pr-assignee.py',
    'stuck-detect.py',
    'git-diff-stat.py',
]


def main():
    # In-process entry for post-exec-guard: _run_one fakes stdin with the
    # payload, and the SystemExit from _hookrun.main propagates through its
    # handler, so nesting is exact. wtp normalization is idempotent by design.
    _hookrun.main(CHILDREN, event='PostToolUse')


if __name__ == '__main__':
    main()
