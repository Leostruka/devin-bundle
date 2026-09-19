#!/usr/bin/env python3
"""Stop consolidated guard — one spawn.

Runs in-process: check-ai-signature, refine-review-prompt, memory-stop.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

if __name__ == '__main__':
    _hookrun.main([
        'check-ai-signature.py',
        'refine-review-prompt.py',
        'memory-stop.py',
    ])
