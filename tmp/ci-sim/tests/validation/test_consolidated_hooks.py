import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]

# built at runtime so the literal signature never appears in this file
AI_SIG = "# Generated with " + "Devin\n"


def run(script, payload):
    return subprocess.run(
        [sys.executable, f"scripts/{script}"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )


def test_pre_exec_guard_blocks_destructive():
    p = run("pre-exec-guard.py", {"hook_event_name": "PreToolUse", "tool_name": "exec",
                                  "tool_input": {"command": "rm -rf /"}})
    assert p.returncode == 2
    assert json.loads(p.stdout)["decision"] == "block"


def test_pre_exec_guard_allows_benign():
    p = run("pre-exec-guard.py", {"hook_event_name": "PreToolUse", "tool_name": "exec",
                                  "tool_input": {"command": "git status"}})
    assert p.returncode == 0


def test_pre_exec_guard_blocks_ai_commit_identity():
    # AI identity injected via -c user.* is a Rule 2 signature in the commit
    # author metadata, not the message. Built at runtime so the literal value
    # never sits in this file.
    cmd = ("git -c user.name=\"De" + "vin\" -c user.email=\"x[bot]@y.z\" "
           "commit -m \"feat: thing\"")
    p = run("pre-exec-guard.py", {"hook_event_name": "PreToolUse", "tool_name": "exec",
                                  "tool_input": {"command": cmd}})
    assert p.returncode == 2
    assert "identity" in json.loads(p.stdout)["reason"].lower()


def test_pre_exec_guard_allows_human_commit_identity():
    cmd = ('git -c user.name="leandro ostruka" -c user.email="leo@example.com" '
           'commit -m "feat: thing"')
    p = run("pre-exec-guard.py", {"hook_event_name": "PreToolUse", "tool_name": "exec",
                                  "tool_input": {"command": cmd}})
    assert p.returncode == 0, p.stdout


def test_pre_write_guard_blocks_ai_signature():
    p = run("pre-write-guard.py", {"hook_event_name": "PreToolUse", "tool_name": "write",
                                   "tool_input": {"file_path": str(ROOT / "x.py"),
                                                  "content": AI_SIG}})
    assert p.returncode == 2


def test_pre_write_guard_notebook_edit_skips_text_checks():
    # notebook_edit was never bound to signature/mermaid checks — the guard
    # must keep that coverage boundary (arch-gate + tool-args only).
    p = run("pre-write-guard.py", {"hook_event_name": "PreToolUse", "tool_name": "notebook_edit",
                                   "tool_input": {"notebook_path": str(ROOT / "x.ipynb"),
                                                  "cell_number": 0,
                                                  "new_source": AI_SIG}})
    assert p.returncode == 0, p.stdout


def test_user_prompt_merges_contexts():
    p = run("user-prompt.py", {"hook_event_name": "UserPromptSubmit", "prompt": "hi"})
    assert p.returncode == 0
    ctx = json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "Self-check before responding" in ctx


def test_post_exec_passes_clean():
    p = run("post-exec.py", {"hook_event_name": "PostToolUse", "tool_name": "exec",
                             "tool_input": {"command": "git status"},
                             "tool_response": {"success": True, "output": "ok", "error": None}})
    assert p.returncode == 0


def test_stop_guard_passes_clean():
    p = run("stop-guard.py", {"hook_event_name": "Stop", "stop_hook_active": False})
    assert p.returncode == 0


def test_session_start_passes():
    p = run("session-start.py", {"hook_event_name": "SessionStart", "source": "cli"})
    assert p.returncode == 0


def test_file_size_guard_warns_over_threshold(tmp_path, monkeypatch):
    big = tmp_path / "big.py"
    big.write_text("x = 1\n" * 900)
    monkeypatch.setenv("DEVIN_PROJECT_DIR", str(tmp_path))
    p = run("file-size-guard.py", {"hook_event_name": "PostToolUse", "tool_name": "edit",
                                   "tool_input": {"file_path": str(big)}})
    assert p.returncode == 0
    ctx = json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "900 lines" in ctx and "big-file-refactor" in ctx


def test_file_size_guard_silent_below_threshold(tmp_path, monkeypatch):
    small = tmp_path / "small.py"
    small.write_text("x = 1\n" * 10)
    monkeypatch.setenv("DEVIN_PROJECT_DIR", str(tmp_path))
    p = run("file-size-guard.py", {"hook_event_name": "PostToolUse", "tool_name": "edit",
                                   "tool_input": {"file_path": str(small)}})
    assert p.returncode == 0
    assert p.stdout.strip() == ""


def test_file_size_guard_skips_non_code(tmp_path):
    f = tmp_path / "big.txt"
    f.write_text("line\n" * 9000)
    p = run("file-size-guard.py", {"hook_event_name": "PostToolUse", "tool_name": "write",
                                   "tool_input": {"file_path": str(f)}})
    assert p.returncode == 0
    assert p.stdout.strip() == ""


def test_file_size_guard_band_dedup(tmp_path, monkeypatch):
    big = tmp_path / "big.py"
    big.write_text("x = 1\n" * 900)
    monkeypatch.setenv("DEVIN_PROJECT_DIR", str(tmp_path))
    payload = {"hook_event_name": "PostToolUse", "tool_name": "edit",
               "tool_input": {"file_path": str(big)}}
    run("file-size-guard.py", payload)
    p = run("file-size-guard.py", payload)
    assert p.stdout.strip() == ""
