#!/usr/bin/env python3
"""PreToolUse(^exec$) consolidated guard — one spawn for all pre-exec checks.

Runs in-process: destructive-gate, architecture-gate, check-ai-signature,
check-push-green, validate-tool-args. Semantics identical to running each
script separately; see _hookrun.py for merge rules.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

if __name__ == '__main__':
    _hookrun.main([
        'destructive-gate.py',
        'architecture-gate.py',
        'check-ai-signature.py',
        'check-push-green.py',
        'validate-tool-args.py',
        'no-em-dash.py',
    ])
