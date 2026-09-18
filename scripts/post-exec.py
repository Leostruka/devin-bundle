#!/usr/bin/env python3
"""PostToolUse(^(exec|mcp_call_tool)$) consolidated post-checks — one spawn.

Runs in-process: silent-error-review, context-pressure, memory-post-exec.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

if __name__ == '__main__':
    _hookrun.main([
        'silent-error-review.py',
        'context-pressure.py',
        'memory-post-exec.py',
    ])
