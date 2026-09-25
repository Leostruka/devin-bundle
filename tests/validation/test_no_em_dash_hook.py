"""no-em-dash.py hook - U+2014 blocked across write/edit/notebook_edit,
git commit messages, and staged/unstaged diffs (Stop event).

The character is built at runtime so this file stays free of it (the
Stop scan would flag the literal in a diff otherwise).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
EM = chr(0x2014)  # em dash; built so no literal enters this file


def run(script, payload, cwd=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd or ROOT,
        timeout=60,
    )


def _pre(tool, tool_input):
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": tool_input}


def test_write_blocked():
    p = run("no-em-dash.py", _pre("write",
            {"file_path": str(ROOT / "x.md"), "content": f"a {EM} b"}))
    assert p.returncode == 2
    assert json.loads(p.stdout)["decision"] == "block"


def test_edit_blocked():
    p = run("no-em-dash.py", _pre("edit",
            {"file_path": str(ROOT / "x.md"), "old_string": "a",
             "new_string": f"a {EM} b"}))
    assert p.returncode == 2


def test_notebook_edit_blocked():
    p = run("no-em-dash.py", _pre("notebook_edit",
            {"notebook_path": str(ROOT / "x.ipynb"), "cell_number": 0,
             "new_source": f"x {EM} y"}))
    assert p.returncode == 2


def test_write_clean_allowed():
    p = run("no-em-dash.py", _pre("write",
            {"file_path": str(ROOT / "x.md"),
             "content": "plain text - hyphen ok"}))
    assert p.returncode == 0


def test_self_file_skipped():
    p = run("no-em-dash.py", _pre("write",
            {"file_path": str(ROOT / "scripts" / "no-em-dash.py"),
             "content": f"detector names {EM}"}))
    assert p.returncode == 0


def test_commit_message_blocked():
    p = run("no-em-dash.py", _pre("exec",
            {"command": f'git commit -m "fix: thing {EM} desc"'}))
    assert p.returncode == 2


def test_commit_file_blocked(tmp_path):
    msg = tmp_path / "msg.txt"
    msg.write_text(f"subject {EM} body\n", encoding="utf-8")
    p = run("no-em-dash.py", _pre("exec",
            {"command": f"git commit -F {msg}"}))
    assert p.returncode == 2


def test_non_commit_command_with_dash_allowed():
    """grep/sed pipelines legitimately carry the character."""
    p = run("no-em-dash.py", _pre("exec",
            {"command": f"grep -rn '{EM}' src/"}))
    assert p.returncode == 0


def test_gh_pr_body_blocked():
    p = run("no-em-dash.py", _pre("exec",
            {"command": f'gh pr create --title t --body "a {EM} b"'}))
    assert p.returncode == 2


def test_gh_read_command_allowed():
    p = run("no-em-dash.py", _pre("exec",
            {"command": "gh pr view 64 --json title"}))
    assert p.returncode == 0


def test_gh_body_file_blocked(tmp_path):
    body = tmp_path / "body.md"
    body.write_text(f"corpo {EM}\n", encoding="utf-8")
    p = run("no-em-dash.py", _pre("exec",
            {"command": f"gh pr create --body-file {body} --title t"}))
    assert p.returncode == 2


def test_gh_body_file_clean_allowed(tmp_path):
    body = tmp_path / "body.md"
    body.write_text("corpo limpo\n", encoding="utf-8")
    p = run("no-em-dash.py", _pre("exec",
            {"command": f"gh pr create --body-file {body} --title t"}))
    assert p.returncode == 0


def test_gh_fill_short_flag_not_a_file():
    """'gh pr create -F' is --fill, not a file path."""
    p = run("no-em-dash.py", _pre("exec",
            {"command": "gh pr create -F --title ok"}))
    assert p.returncode == 0


def test_git_tag_file_blocked(tmp_path):
    msg = tmp_path / "tagmsg.txt"
    msg.write_text(f"release {EM}\n", encoding="utf-8")
    p = run("no-em-dash.py", _pre("exec",
            {"command": f"git tag -a v1 -F {msg}"}))
    assert p.returncode == 2


def test_stop_blocks_untracked_dash(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    (tmp_path / "novo.md").write_text(f"texto {EM}\n", encoding="utf-8")
    p = run("no-em-dash.py", {"hook_event_name": "Stop"}, cwd=tmp_path)
    assert p.returncode == 2
    assert "untracked" in json.loads(p.stdout)["reason"]


def test_stop_untracked_clean_allowed(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    (tmp_path / "novo.md").write_text("limpo\n", encoding="utf-8")
    (tmp_path / "bin.dat").write_bytes(b"\x00\x01" + EM.encode("utf-8"))
    p = run("no-em-dash.py", {"hook_event_name": "Stop"}, cwd=tmp_path)
    assert p.returncode == 0


def test_stop_blocks_staged_dash(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    (tmp_path / "a.md").write_text(f"line {EM}\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.md"], cwd=tmp_path)
    p = run("no-em-dash.py", {"hook_event_name": "Stop"}, cwd=tmp_path)
    assert p.returncode == 2
    assert "staged" in json.loads(p.stdout)["reason"]


def test_stop_blocks_unstaged_dash(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path)
    (tmp_path / "a.md").write_text("clean\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.md"], cwd=tmp_path)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=tmp_path)
    (tmp_path / "a.md").write_text(f"now {EM}\n", encoding="utf-8")
    p = run("no-em-dash.py", {"hook_event_name": "Stop"}, cwd=tmp_path)
    assert p.returncode == 2
    assert "unstaged" in json.loads(p.stdout)["reason"]


def test_stop_clean_allowed(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    (tmp_path / "a.md").write_text("clean\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.md"], cwd=tmp_path)
    p = run("no-em-dash.py", {"hook_event_name": "Stop"}, cwd=tmp_path)
    assert p.returncode == 0


def test_invalid_payload_fails_open():
    p = subprocess.run(
        [sys.executable, "scripts/no-em-dash.py"],
        input="not json", capture_output=True, text=True,
        cwd=ROOT, timeout=30)
    assert p.returncode == 0
