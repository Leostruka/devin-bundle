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


# --- C88: second-pass reviewer findings ---

@pytest.mark.parametrize("cmd", [
    "git branch -d -D divergent-zz",
    "git branch -v -D divergent-zz",
    "git branch --list -D divergent-zz",
    "git branch -D ok && git branch -D divergent-zz",
    "git branch -D --sort=x divergent-zz",
])
def test_branch_d_flag_position_bypasses_blocked(cmd):
    """Flags before -D or a second -D segment must not drop operands."""
    code, out = run_gate(cmd)
    assert code == 2, f"flag-position -D bypass should block, got {code}: {out}"


def test_branch_d_value_flag_not_collected():
    """`-m`'s operand is a rename target, not a branch to check - a
    `branch -D -m newname` (git itself rejects -D+-m) must not over-block
    on a phantom branch name."""
    code, _ = run_gate("git branch -D -m")
    assert code == 0  # no operands collected, git errors naturally


@pytest.mark.parametrize("cmd", [
    "rm -rf devin/state",
    "rmdir /s devin/state",
    "find devin/state -delete",
    "sed -i s/a/b/ devin/state/subagent-budget.json",
    "mv devin/state/subagent-s.json /tmp/x.json",
    "mv /tmp/x devin/state/subagent-s.json",
    "rsync src/ devin/state/",
    "install x devin/state/subagent-s.json",
    "dd of=devin/state/subagent-s.json",
])
def test_state_dir_wholesale_ops_blocked(cmd):
    """The whole state dir and non-rm mutators are the same self-unlimiting
    class as file deletes."""
    code, out = run_gate(cmd)
    assert code == 2, f"state-dir op should block, got {code}: {out}"


@pytest.mark.parametrize("cmd", [
    "cp /x/state/subagent-s.json /tmp/bak.json",
    "echo tee state/subagent-x.json",
    "rsync devin/state/subagent-s.json /tmp/bak",
])
def test_state_read_from_or_prose_silent(cmd):
    """Copying FROM state is a read; prose verbs are not commands."""
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" not in out.upper(), cmd


@pytest.mark.parametrize("cmd", [
    "docker cp f ctr:/x",
    "cp f s3://bucket",
    "cp f user@host:dir",
    "scp f host:/tmp/x",
])
def test_ads_remote_forms_silent(cmd):
    """container:/scheme:// and user@host: forms are not NTFS ADS."""
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" not in out.upper(), cmd


@pytest.mark.parametrize("cmd", [
    "echo x > file:hidden",
    "touch note:stream",
    "cp a dir/f:hidden",
])
def test_ads_local_forms_still_blocked(cmd):
    code, out = run_gate(cmd)
    assert code == 2, f"local ADS target should block, got {code}: {out}"


@pytest.mark.parametrize("cmd", [
    "curl x | env sh",
    "gsutil -o x rm -r gs://b",
])
def test_second_pass_extended_shapes_warn(cmd):
    code, out = _warn_text(cmd)
    assert code == 0 and "WARNING" in out.upper(), cmd


# --- C89: flag-value prefixes + wrapper verbs ---

@pytest.mark.parametrize("cmd", [
    "git branch --sort x -D divergent-zz",
    "git branch --points-at a -D divergent-zz",
    "git branch -c old -D divergent-zz",
])
def test_branch_d_flag_value_prefixes_blocked(cmd):
    """A space-separated flag value before -D must not break matching."""
    code, out = run_gate(cmd)
    assert code == 2, f"flag-value -D bypass should block, got {code}: {out}"


@pytest.mark.parametrize("cmd", [
    "env rm state/subagent-x.json",
    "env FOO=1 rm state/subagent-x.json",
    "nice rm state/subagent-x.json",
    "nohup rm state/subagent-x.json",
    "timeout 5 rm state/subagent-x.json",
    "eval \"rm state/subagent-x.json\"",
    "xargs rm state/subagent-x.json",
    "sudo -u root rm state/subagent-x.json",
])
def test_state_delete_wrapper_verbs_blocked(cmd):
    """Privilege/env/scheduler wrappers cannot launder a state delete -
    the verb is still what runs."""
    code, out = run_gate(cmd)
    assert code == 2, f"wrapped state delete should block, got {code}: {out}"


# --- C90: write_to_process stdin channel ---

def run_gate_wtp(tool_input: dict, session_id: str = "") -> tuple[int, str]:
    if not session_id:
        # Per-input session so pending-line buffers never leak between
        # parametrized cases that share the same shell_id.
        session_id = "t" + str(abs(hash(json.dumps(
            tool_input, sort_keys=True))))
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "write_to_process",
        "tool_input": tool_input,
        "session_id": session_id,
    })
    env = dict(os.environ)
    env["DEVIN_STATE_DIR"] = _WTP_STATE
    result = subprocess.run(
        [sys.executable, GATE_SCRIPT],
        input=payload, capture_output=True, text=True, encoding="utf-8",
        env=env)
    return result.returncode, result.stdout + result.stderr


@pytest.mark.parametrize("ti", [
    {"shell_id": "s", "text_input": "git push --force\n"},
    {"shell_id": "s", "bytes_input": "git branch -D divergent-zz<CR>"},
    {"shell_id": "s", "bytes_input": "rm state/subagent-x.json<CR>"},
    {"shell_id": "s", "text_input": "ls\nrm -rf /\n"},
    {"shell_id": "s", "bytes_input": "sudo dd if=/dev/zero of=/dev/sda<CR>"},
])
def test_wtp_submitted_dangerous_blocked(ti):
    """write_to_process launders exec: typed text + CR executes in the
    target shell with zero gate coverage unless the gate scans submitted
    lines."""
    code, out = run_gate_wtp(ti)
    assert code == 2, f"submitted dangerous line should block, got {code}: {out}"


@pytest.mark.parametrize("ti", [
    {"shell_id": "s", "text_input": "rm -rf /"},            # no CR: not submitted
    {"shell_id": "s", "bytes_input": "dd<ESC>dd"},         # vim keystrokes
    {"shell_id": "s", "bytes_input": "y<CR>"},             # prompt answer
    {"shell_id": "s", "bytes_input": "<C-c>"},             # control only
    {"shell_id": "s", "text_input": "echo hi\n"},          # benign line
    {"shell_id": "s", "text_input": "ls\nrm -rf /"},       # partial tail
])
def test_wtp_partial_and_benign_silent(ti):
    """Lines without a CR/LF terminator are not yet submitted to the
    process - keystrokes for TUIs/prompts must stay silent."""
    code, out = run_gate_wtp(ti)
    assert code == 0, f"non-submitted/benign input should stay silent: {out}"


# --- C91: split-write bypass + buffer-state guards ---

import tempfile
_WTP_STATE = tempfile.mkdtemp(prefix="wtpbuf")


def test_wtp_split_write_blocked():
    """Dangerous text in call 1 + CR in call 2 executes in the shell;
    the gate must model the pending input line across calls."""
    sid = "split-wtp-1"
    assert run_gate_wtp({"shell_id": "s", "text_input": "rm -rf /"}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "s", "text_input": "\n"}, sid)[0] == 2


def test_wtp_split_across_three_calls():
    sid = "split-wtp-2"
    assert run_gate_wtp({"shell_id": "s", "text_input": "rm -rf"}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "s", "text_input": " /"}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "s", "text_input": "\n"}, sid)[0] == 2


def test_wtp_ctrl_c_clears_pending():
    """C-c discards the input line in a real shell - pending must reset."""
    sid = "split-wtp-3"
    assert run_gate_wtp({"shell_id": "s", "text_input": "rm -rf /"}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "s", "bytes_input": "<C-c>"}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "s", "text_input": "ls\n"}, sid)[0] == 0


def test_wtp_cross_form_accumulation():
    """text_input partial + bytes_input CR: the shell sees one line."""
    sid = "split-wtp-4"
    assert run_gate_wtp(
        {"shell_id": "s", "text_input": "git push --force"}, sid)[0] == 0
    assert run_gate_wtp(
        {"shell_id": "s", "bytes_input": "<CR>"}, sid)[0] == 2


def test_wtp_buffers_are_per_shell():
    """shell_id partitions pending state - a CR on another shell must not
    inherit the first shell's pending text."""
    sid = "split-wtp-5"
    assert run_gate_wtp({"shell_id": "sA", "text_input": "rm -rf /"}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "sB", "text_input": "\n"}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "sA", "text_input": "\n"}, sid)[0] == 2


@pytest.mark.parametrize("cmd", [
    "rm state/wtp-abc123.txt",
    "del state\\wtp-deadbeef.txt",
    "rm -rf devin/state",
])
def test_wtp_buffer_delete_blocked(cmd):
    """Deleting a pending-line buffer before the CR re-opens the
    split-write bypass - buffers are enforcement state."""
    code, out = run_gate(cmd)
    assert code == 2, f"buffer delete should block, got {code}: {out}"


# --- C94: shell-history recall executes uninspectable text ---

@pytest.mark.parametrize("ti", [
    {"shell_id": "s", "bytes_input": "<UP><CR>"},
    {"shell_id": "s", "bytes_input": "<DOWN><CR>"},
    {"shell_id": "s", "bytes_input": "<C-r>ls<CR>"},
    {"shell_id": "s", "bytes_input": "<UP>x<CR>"},
    {"shell_id": "s", "bytes_input": "<C-p><CR>"},
])
def test_wtp_history_recall_blocked(ti):
    """Recall + submit runs a history entry the gate cannot inspect -
    HISTFILE may hold commands from outside the gated session."""
    code, out = run_gate_wtp(ti, session_id="hist-" + str(abs(hash(str(ti)))))
    assert code == 2, f"history recall should block, got {code}: {out}"


def test_wtp_split_recall_blocked():
    """<UP> in one call and <CR> in the next still executes history."""
    sid = "hist-split"
    assert run_gate_wtp({"shell_id": "s", "bytes_input": "<UP>"}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "s", "bytes_input": "<CR>"}, sid)[0] == 2


def test_wtp_recall_nav_only_silent():
    sid = "hist-nav"
    assert run_gate_wtp({"shell_id": "s", "bytes_input": "<UP><DOWN>"}, sid)[0] == 0


def test_wtp_ctrl_c_clears_recall_taint():
    sid = "hist-cc"
    assert run_gate_wtp({"shell_id": "s", "bytes_input": "<UP>"}, sid)[0] == 0
    assert run_gate_wtp(
        {"shell_id": "s", "bytes_input": "<C-c>ls<CR>"}, sid)[0] == 0


def test_wtp_oversized_line_keeps_head():
    """C95: the 4KB buffer cap must keep the line's HEAD - verbs lead the
    command, so padding past the cap must not drop them."""
    sid = "cap-head"
    pad = "rm -rf /" + " " * 5000
    assert run_gate_wtp({"shell_id": "s", "text_input": pad}, sid)[0] == 0
    assert run_gate_wtp({"shell_id": "s", "text_input": "\n"}, sid)[0] == 2
