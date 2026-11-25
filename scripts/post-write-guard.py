#!/usr/bin/env python3
"""PostToolUse write|edit consolidated guard - one spawn.

Runs in-process: memory-post-edit, compact-gate, file-size-guard,
design-lint-gate. Same matcher for all four children, so consolidation
is exact: each write/edit previously paid 4 Python interpreter startups
(~350ms measured on Windows) for what is one interpreter's worth of work.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

if __name__ == '__main__':
    _hookrun.main([
        'memory-post-edit.py',
        'compact-gate.py',
        'file-size-guard.py',
        'design-lint-gate.py',
    ], event='PostToolUse')
