#!/usr/bin/env python3
"""SessionStart consolidated hook — one spawn.

Runs in-process: constraint-pinning, context-budget.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

if __name__ == '__main__':
    _hookrun.main([
        'constraint-pinning.py',
        'context-budget.py',
    ])
