"""validate-mermaid.py - PreToolUse hook scanning write/edit content for
mermaid fences and validating each via node. Edge tests: event/tool
gating, fence extraction, fail-open when node/mermaid is missing."""
import importlib.util
import io
import json
import os
import sys
from unittest.mock import patch

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "validate-mermaid.py")

spec = importlib.util.spec_from_file_location("validate_mermaid", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _run(payload):
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
         patch.object(sys, "stdout", out), \
         pytest.raises(SystemExit) as e:
        mod.main()
    return e.value.code, out.getvalue()


def _write(content, tool="write", key="content"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": {key: content, "file_path": "f.md"}}


def test_extract_mermaid_blocks():
    content = ("text\n```mermaid\ngraph TD; A-->B\n```\nmore\n"
               "```MERMAID\npie\n```\n```python\nx\n```")
    blocks = mod.extract_mermaid_blocks(content)
    assert len(blocks) == 2
    assert "A-->B" in blocks[0] and "pie" in blocks[1]


def test_no_mermaid_blocks_allowed():
    code, out = _run(_write("# plain markdown"))
    assert code == 0 and out == ""


def test_wrong_event_ignored():
    code, _ = _run({"hook_event_name": "PostToolUse",
                    "tool_name": "write",
                    "tool_input": {"content": "```mermaid\nx\n```"}})
    assert code == 0


def test_wrong_tool_ignored():
    code, _ = _run({"hook_event_name": "PreToolUse",
                    "tool_name": "read",
                    "tool_input": {"file_path": "f.md"}})
    assert code == 0


def test_invalid_json_fails_open():
    with patch.object(sys, "stdin", io.StringIO("{bad")), \
         pytest.raises(SystemExit) as e:
        mod.main()
    assert e.value.code == 0


def test_edit_uses_new_string(monkeypatch):
    # Simulate a working validator: node+mermaid may be absent or partial
    # on the host, so stub the subprocess layer for a deterministic result.
    class _Ok:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(mod, "_run", lambda *a, **kw: _Ok())
    code, _ = _run(_write("```mermaid\ngraph TD\n  A-->B\n```",
                          tool="edit", key="new_string"))
    assert code == 0


def test_node_unavailable_fails_open(monkeypatch):
    def boom(*a, **kw):
        raise FileNotFoundError("node")
    monkeypatch.setattr(mod, "_run", boom)
    code, _ = _run(_write("```mermaid\ngraph TD\n```"))
    assert code == 0


def test_invalid_diagram_blocks(monkeypatch):
    class R:
        returncode = 1
        stderr = "Parse error on line 1"
        stdout = ""
    monkeypatch.setattr(mod, "_run", lambda *a, **kw: R())
    code, out = _run(_write("```mermaid\nnot a diagram\n```"))
    assert code == 2
    assert json.loads(out)["decision"] == "block"
    assert "Parse error" in out
