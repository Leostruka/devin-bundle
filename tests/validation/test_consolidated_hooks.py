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
