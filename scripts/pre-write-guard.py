#!/usr/bin/env python3
"""PreToolUse(^(write|edit|notebook_edit)$) consolidated guard — one spawn.

Always runs architecture-gate + validate-tool-args. check-ai-signature and
validate-mermaid run only for write|edit payloads — same coverage as the
previous per-tool bindings (notebook_edit was never bound to them).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

ALWAYS = ['architecture-gate.py', 'validate-tool-args.py',
          'no-em-dash.py']
TEXT_ONLY = ['check-ai-signature.py', 'validate-mermaid.py']

if __name__ == '__main__':
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        payload = {}
    checks = list(ALWAYS)
    if payload.get('tool_name') in ('write', 'edit'):
        checks += TEXT_ONLY
    sys.exit(_hookrun.run(checks, payload))
