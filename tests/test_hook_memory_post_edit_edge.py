"""memory-post-edit.py - PostToolUse hook: injects memory notes matching
path cues of the edited file. Edge tests: event gating, scoring,
TOP_K cap, fail-open paths."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "memory-post-edit.py")


NOTE = ("---\ntitle: {title}\ncategory: ops\nstatus: {status}\n"
        "  - path: {cue}\n---\n{body}\n")


def _run(payload, mem_dir, cwd=None):
    env = dict(os.environ, BUNDLE_MEMORY_DIR=str(mem_dir))
    return subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(payload),
        capture_output=True, text=True,
        cwd=cwd or ROOT, env=env, timeout=20)


def _edit(file_path, tool="write", event="PostToolUse"):
    return {"hook_event_name": event, "tool_name": tool,
            "tool_input": {"file_path": str(file_path)}}


@pytest.fixture
def mem(tmp_path):
    d = tmp_path / "mem"
    d.mkdir()
    return d


def test_matching_note_injected(mem, tmp_path):
    (mem / "n1.md").write_text(
        NOTE.format(title="N1", status="active",
                    cue="src/auth", body="remember this"))
    p = _run(_edit(tmp_path / "src" / "auth" / "x.py"), mem)
    assert p.returncode == 0
    out = json.loads(p.stdout)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "N1" in ctx and "remember this" in ctx


def test_no_match_prints_nothing(mem, tmp_path):
    (mem / "n1.md").write_text(
        NOTE.format(title="N1", status="active", cue="other/dir",
                    body="x"))
    p = _run(_edit(tmp_path / "src" / "main.py"), mem)
    assert p.returncode == 0 and p.stdout == ""


def test_inactive_note_ignored(mem, tmp_path):
    (mem / "n1.md").write_text(
        NOTE.format(title="N1", status="archived", cue="src",
                    body="x"))
    p = _run(_edit(tmp_path / "src" / "main.py"), mem)
    assert p.returncode == 0 and p.stdout == ""


def test_wrong_event_or_tool_ignored(mem, tmp_path):
    (mem / "n1.md").write_text(
        NOTE.format(title="N1", status="active", cue="", body="x"))
    assert _run(_edit(tmp_path / "a.py", event="PreToolUse"),
                mem).stdout == ""
    assert _run(_edit(tmp_path / "a.py", tool="read"),
                mem).stdout == ""


def test_moc_file_excluded(mem, tmp_path):
    (mem / "MOC.md").write_text(
        NOTE.format(title="MOC", status="active", cue="src", body="x"))
    p = _run(_edit(tmp_path / "src" / "a.py"), mem)
    assert p.returncode == 0 and p.stdout == ""


def test_top_k_cap(mem, tmp_path):
    for i in range(4):
        (mem / f"n{i}.md").write_text(
            NOTE.format(title=f"N{i}", status="active", cue="src",
                        body="b"))
    p = _run(_edit(tmp_path / "src" / "a.py"), mem)
    ctx = json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]
    assert ctx.count("**[[") == 2  # TOP_K = 2


def test_missing_memory_dir_fails_open(tmp_path):
    p = _run(_edit(tmp_path / "a.py"), tmp_path / "nonexistent")
    assert p.returncode == 0 and p.stdout == ""


def test_invalid_json_fails_open(mem):
    env = dict(os.environ, BUNDLE_MEMORY_DIR=str(mem))
    p = subprocess.run([sys.executable, SCRIPT], input="nope",
                       capture_output=True, text=True, env=env,
                       timeout=20)
    assert p.returncode == 0


def test_missing_file_path_fails_open(mem):
    p = _run({"hook_event_name": "PostToolUse", "tool_name": "write",
              "tool_input": {}}, mem)
    assert p.returncode == 0
