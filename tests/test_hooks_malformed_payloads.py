"""Every stdin hook must fail open (or block cleanly, exit 0/2) on
malformed JSON payloads — never crash with a traceback.

Regression suite for the non-dict payload / non-str field bug class
(audit sweep 2026-11-16 found 19 hooks crashing on `[1,2]`-shaped
payloads and 7 more on wrong-typed fields).
"""
import glob
import json
import os
import subprocess
import sys

import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
PY = sys.executable

ARGV_CLIS = {"render-user-hooks.py", "_hookrun.py"}  # not stdin hooks


def _stdin_hooks():
    out = []
    for path in sorted(glob.glob(os.path.join(SCRIPTS, "*.py"))):
        name = os.path.basename(path)
        if name in ARGV_CLIS:
            continue
        with open(path, encoding="utf-8") as f:
            if "sys.stdin" in f.read():
                out.append(path)
    return out


HOOKS = _stdin_hooks()

NON_DICT_PAYLOADS = ['[1,2]', '"x"', '42', 'null']

FIELD_PAYLOADS = [
    {"hook_event_name": "PreToolUse", "tool_name": "exec",
     "tool_input": {"command": 123}},
    {"hook_event_name": "PreToolUse", "tool_name": "exec",
     "tool_input": {"command": ["ls"]}},
    {"hook_event_name": "PreToolUse", "tool_name": "write",
     "tool_input": {"file_path": 123}},
    {"hook_event_name": "PreToolUse", "tool_name": "write",
     "tool_input": {"file_path": "/x.md", "content": {"c": 1}}},
    {"hook_event_name": "PreToolUse", "tool_name": "edit",
     "tool_input": {"file_path": "/x", "old_string": 5,
                    "new_string": True}},
    {"hook_event_name": "PreToolUse", "tool_name": "exec",
     "tool_input": [1]},
    {"hook_event_name": "UserPromptSubmit", "prompt": 9},
    {"hook_event_name": "PostToolUse", "tool_name": "exec",
     "tool_input": {"command": "x"}, "tool_response": {"output": [1]}},
]


def _run(path, payload):
    return subprocess.run([PY, path], input=payload, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=20)


@pytest.mark.parametrize("raw", NON_DICT_PAYLOADS)
@pytest.mark.parametrize("hook", HOOKS, ids=lambda p: os.path.basename(p))
def test_non_dict_payload_no_crash(hook, raw):
    r = _run(hook, raw)
    assert 'Traceback' not in r.stderr, \
        f"{os.path.basename(hook)} crashed on {raw}: {r.stderr[-200:]}"
    assert r.returncode in (0, 2)


@pytest.mark.parametrize("payload", FIELD_PAYLOADS,
                         ids=lambda p: p.get("tool_name") or
                         p.get("hook_event_name"))
@pytest.mark.parametrize("hook", HOOKS, ids=lambda p: os.path.basename(p))
def test_wrong_field_types_no_crash(hook, payload):
    r = _run(hook, json.dumps(payload))
    assert 'Traceback' not in r.stderr, \
        f"{os.path.basename(hook)} crashed: {r.stderr[-200:]}"
    assert r.returncode in (0, 2)
