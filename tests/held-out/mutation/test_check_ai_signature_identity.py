"""Held-out mutation test: check-ai-signature.py git identity injection.

Policy: ALWAYS_PASSES

Covers the incident where `git -c user.name="Devin" -c user.email=<bot>`
injected an AI signature into the commit author/committer identity while the
message stayed clean. The old guard exited early: "git commit" is not an
adjacent substring of that command, and only the message text was checked.
"""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
SIG_SCRIPT = os.path.join(SCRIPTS_DIR, "check-ai-signature.py")

# The exact command shape from the incident (author identity injection).
INCIDENT = (
    'git -c user.name="Devin" '
    '-c user.email="158243242+devin-ai-integration[bot]'
    '@users.noreply.github.com" commit -m "feat: add thing"'
)


def run_exec(command: str) -> tuple[int, str]:
    """Run check-ai-signature.py with a simulated exec payload."""
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "exec",
        "tool_input": {"command": command},
        "session_id": "test",
    })
    result = subprocess.run(
        [sys.executable, SIG_SCRIPT],
        input=payload, capture_output=True, text=True, timeout=10,
    )
    return result.returncode, result.stdout.strip()


# --- blocked: AI identity via -c user.* ---

def test_incident_command_blocked():
    code, out = run_exec(INCIDENT)
    assert code == 2, f"Incident command must be blocked, got {code}: {out}"


def test_c_user_name_ai_blocked():
    code, _ = run_exec('git -c user.name="Devin" commit -m "x"')
    assert code == 2


def test_c_user_email_bot_blocked():
    code, _ = run_exec(
        'git -c user.email="devin-ai-integration[bot]'
        '@users.noreply.github.com" commit -m "x"'
    )
    assert code == 2


def test_c_quoted_whole_arg_blocked():
    code, _ = run_exec('git -c "user.name=Claude" commit -m "x"')
    assert code == 2


def test_c_unquoted_ai_blocked():
    code, _ = run_exec("git -c user.name=Copilot commit -m x")
    assert code == 2


# --- blocked: AI identity via --author ---

def test_author_equals_blocked():
    code, _ = run_exec(
        'git commit --author="Claude <noreply@anthropic.com>" -m "x"'
    )
    assert code == 2


def test_author_space_blocked():
    code, _ = run_exec("git commit --author 'Devin <d@x.io>' -m x")
    assert code == 2


# --- blocked: AI identity via env vars and git config ---

def test_git_author_env_blocked():
    code, _ = run_exec("GIT_AUTHOR_NAME=Devin git commit -m x")
    assert code == 2


def test_git_committer_email_env_blocked():
    code, _ = run_exec("GIT_COMMITTER_EMAIL=copilot@github.com git commit -m x")
    assert code == 2


def test_git_config_user_name_blocked():
    code, _ = run_exec('git config user.name "Devin"')
    assert code == 2


def test_git_config_global_email_blocked():
    code, _ = run_exec('git config --global user.email "aider@x.io"')
    assert code == 2


# --- allowed: human identity and non-identity -c flags ---

def test_human_identity_override_allowed():
    code, out = run_exec(
        'git -c user.name="leandro ostruka" -c user.email="leo@example.com" '
        'commit -m "feat: add thing"'
    )
    assert code == 0, f"Human identity override should be allowed: {out}"


def test_non_identity_c_flag_allowed():
    code, _ = run_exec('git -c core.editor=true commit -m "x"')
    assert code == 0


def test_plain_commit_allowed():
    code, _ = run_exec('git commit -m "fix: parser"')
    assert code == 0


def test_non_commit_git_allowed():
    code, _ = run_exec("git -c protocol.version=2 fetch origin")
    assert code == 0


# --- widened commit gate: message sig through flag-separated git commit ---

def test_message_sig_via_flag_separated_commit_blocked():
    sig = "Co-" + "Authored-By: Devin <x@y>"
    code, _ = run_exec(f'git -c core.editor=true commit -m "{sig}"')
    assert code == 2, "Message signature must be caught behind -c flags"


def test_message_sig_via_git_C_dir_blocked():
    sig = "Generated" + " with Devin"
    code, _ = run_exec(f'git -C /tmp/repo commit -m "{sig}"')
    assert code == 2
