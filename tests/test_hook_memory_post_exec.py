"""memory-post-exec hook -- unreadable note must not kill retrieval."""
import importlib.util
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "memory-post-exec.py"
spec = importlib.util.spec_from_file_location("memory_post_exec", SCRIPT)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

PAYLOAD = {"hookEventName": "PostToolUse", "tool_name": "exec",
           "tool_input": {"command": "echo hi"},
           "tool_response": {"output": "hi"}}


def _run(tmp_path, monkeypatch, files):
    mem = tmp_path / "mem"
    mem.mkdir()
    for name, data in files.items():
        if isinstance(data, bytes):
            (mem / name).write_bytes(data)
        else:
            (mem / name).write_text(data, encoding="utf-8")
    monkeypatch.setattr(hook, "BASE", str(mem))
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(PAYLOAD))), \
         patch.object(sys, "stdout", out), pytest.raises(SystemExit) as e:
        hook.main()
    return e.value.code, out.getvalue()


def test_unreadable_note_skipped(tmp_path, monkeypatch):
    code, _ = _run(tmp_path, monkeypatch,
                   {"bad.md": b"\x96\x97\x98 latin1 \x80",
                    "good.md": "---\ntitle: t\nstatus: active\n---\nbody"})
    assert code == 0


def test_valid_note_still_scores(tmp_path, monkeypatch):
    note = ("---\ntitle: \"t\"\nstatus: active\ncues:\n"
            "  - keyword: \"hi\"\n---\nmatched body")
    code, out = _run(tmp_path, monkeypatch,
                     {"bad.md": b"\x96\x97",
                      "good.md": note})
    assert code == 0
    assert "additionalContext" in out


def test_no_match_silent(tmp_path, monkeypatch):
    code, out = _run(tmp_path, monkeypatch,
                     {"good.md": "---\nstatus: active\n---\nnothing"})
    assert code == 0
    assert out == ""
