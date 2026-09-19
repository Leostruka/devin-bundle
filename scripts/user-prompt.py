#!/usr/bin/env python3
"""UserPromptSubmit consolidated hook — one spawn.

Runs in-process: constraint-pinning, behavioral-nudge, memory-retrieval.
additionalContext outputs merge in order (pinned rules, self-check, memories).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

if __name__ == '__main__':
    _hookrun.main([
        'constraint-pinning.py',
        'behavioral-nudge.py',
        'memory-retrieval.py',
    ])
