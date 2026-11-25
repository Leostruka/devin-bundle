#!/usr/bin/env python3
"""PostToolUse consolidated guard for command-ish tools - one spawn.

Replaces two separate hook spawns whose matchers overlapped on exec:
  dep-audit-gate  ^(exec|write_to_process)$
  post-exec       ^(exec|mcp_call_tool)$   (itself a consolidated chain)

Routing preserves the previous per-tool bindings exactly:
  exec            -> dep-audit-gate, then post-exec (config order kept)
  write_to_process -> dep-audit-gate only
  mcp_call_tool   -> post-exec only

Measured on Windows: two interpreter startups (~270ms combined) collapse
to one (~150ms) per exec call - exec is the most frequent tool in sessions.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

if __name__ == '__main__':
    try:
        _hookrun.pin_stdio_utf8(sys.stdin)
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    tool = payload.get('tool_name', '')
    checks = []
    if tool in ('exec', 'write_to_process'):
        checks.append('dep-audit-gate.py')
    if tool in ('exec', 'mcp_call_tool'):
        checks.append('post-exec.py')
    sys.exit(_hookrun.run(checks, payload, event='PostToolUse'))
