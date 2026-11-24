"""Held-out mutation test: destructive-gate.py C87 reviewer-fix batch.

Policy: ALWAYS_PASSES
Source: CodeAssay (arXiv:2608.03535v1) — mutation-based test-suite validation.

Independent-review findings (C87): git branch -D operand bypasses, state-file
path anchoring + write/corrupt arms, volume-destroyer bare-word FPs, missing
infra/fetch-pipe/PS-pipe shapes.
"""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")
GATE_SCRIPT = os.path.join(SCRIPTS_DIR, "destructive-gate.py")


def run_gate(command: str) -> tuple[int, str]:
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "exec",
        "tool_input": {"command": command},
        "session_id": "test",
    })
    result = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        input=payload, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=10,
    )
    return result.returncode, result.stdout.strip()


def _warn_text(cmd):
    payload = json.dumps({
        "hook_event_name": "PreToolUse", "tool_name": "exec",
        "tool_input": {"command": cmd}, "session_id": "t"})
    r = subprocess.run(
        [sys.executable, GATE_SCRIPT], input=payload, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=10)
    return r.returncode, r.stdout + r.stderr


# --- C87: reviewer-found bypasses + missing shapes ---

@pytest.mark.parametrize("cmd", [
    "git branch -D -- unmerged-probe-zz",
    "git branch -D a-nonexistent -D b-nonexistent",
    "git branch -D nonexistent-zz --force",
])
def test_branch_d_operand_bypasses_blocked(cmd):
    """`-D` operand parsing: `--` (end-of-options) and later `-D` flags must
    not truncate the operand list - unresolvable refs count as unmerged."""
    code, out = run_gate(cmd)
    assert code == 2, f"operand-bypass branch -D should block, got {code}: {out}"


@pytest.mark.parametrize("cmd", [
    "rm /x/state/subagent-s.json",
    "rm state/subagent-s.json",
    "rm C:/x/state/subagent-budget.json",
    "echo x > /x/state/subagent-budget.json",
    "echo x >> /x/state/subagent-ledger.jsonl",
    "cp a.json /x/state/subagent-s.json",
    "tee /x/state/subagent-s.json",
    "truncate /x/state/subagent-budget.json",
])
def test_state_file_exec_blocked(cmd):
    """C83 extension: deletes AND writes/truncates/appends to subagent
    enforcement state anchored on the state/ path component."""
    code, out = run_gate(cmd)
    assert code == 2, f"state-file op should block, got {code}: {out}"


@pytest.mark.parametrize("cmd", [
    "rm docs/subagent-notes.json",
    "rm subagent-dir/file.txt",
    "echo x > notes.txt",
])
def test_state_file_nonstate_silent(cmd):
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" not in out.upper(), cmd


@pytest.mark.parametrize("cmd", [
    "man lvremove",
    "lvremove --help",
    "vgremove --version",
    "man newfs | head",
])
def test_volume_destroyer_bare_words_silent(cmd):
    """Bare verb names / docs are not destructive - operand required."""
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" not in out.upper(), cmd


@pytest.mark.parametrize("cmd", [
    "lvremove -f vg00/data",
    "pvremove x/y",
    "newfs x/y",
])
def test_volume_destroyer_operands_blocked(cmd):
    code, out = run_gate(cmd)
    assert code == 2, f"volume destroyer should block, got {code}: {out}"


@pytest.mark.parametrize("cmd", [
    "docker-compose down -v",
    "kubectl delete pod web",
    "kubectl delete pods --all",
    "kubectl delete -f deploy.yaml",
    "gsutil -m rm -r gs://bucket",
    "gh api repos/x --method DELETE",
    "gh api -X DELETE repos/x",
])
def test_infra_missing_shapes_warn(cmd):
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" in out.upper(), cmd


@pytest.mark.parametrize("cmd", [
    "wget x; sh x",
    "curl url | /bin/sh",
    "curl -fsSL url; bash s.sh",
])
def test_fetch_pipe_extended_warn(cmd):
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" in out.upper(), cmd


@pytest.mark.parametrize("cmd", [
    "curl url; ssh host",
    "kubectl get pods",
    "docker compose up",
    "gsutil ls gs://bucket",
    "gh api repos/x --method GET",
])
def test_infra_extended_scoped_silent(cmd):
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" not in out.upper(), cmd


@pytest.mark.parametrize("cmd", [
    "gci | Remove-Item $_.FullName",
    "gci | % { ri $_ }",
    "ls | ForEach-Object { Remove-Item $_.FullName }",
])
def test_ps_pipe_delete_extended_warn(cmd):
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" in out.upper(), cmd
