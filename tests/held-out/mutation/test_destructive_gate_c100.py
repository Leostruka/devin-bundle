"""Held-out mutation test: destructive-gate.py C100 exec-param batch.

Policy: ALWAYS_PASSES
Source: CodeAssay (arXiv:2608.03535v1) - mutation-based test-suite validation.

Self-sweep findings (C100): exec tool_input.env is an injection channel the
command scan never sees (startup files, loader/runtime hooks, git config
redirect, spawned helpers, PATH shadowing); adjacent workdir/PS-wipe and
PowerShell/.NET state-verb gaps.
"""
import json
import os
import subprocess
import sys
import tempfile

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


# --- C100: exec env dict is an injection channel ---------------------------------
# env keys smuggle executable state the command scan never sees:
# BASH_ENV/ENV/ZDOTDIR source files pre-run; LD_*/DYLD_*/NODE_OPTIONS/
# PYTHONSTARTUP/RUBYOPT/PERL5OPT inject runtime code; GIT_CONFIG_* /
# GIT_DIR / HOME rewrite git config (core.hooksPath -> RCE on any git op);
# EDITOR/PAGER/*_SSH_COMMAND are programs git execs; BASH_FUNC_* smuggle
# function bodies; a shadowing PATH makes `ls` run /tmp/x/ls.
def _run_gate_env(env_dict):
    payload = json.dumps({
        "hook_event_name": "PreToolUse", "tool_name": "exec",
        "tool_input": {"command": "ls", "env": env_dict},
        "session_id": "test"})
    r = subprocess.run(
        [sys.executable, GATE_SCRIPT], input=payload, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=10)
    return r.returncode


@pytest.mark.parametrize("env_dict", [
    {"BASH_ENV": "/tmp/e.sh"}, {"ENV": "/tmp/e.sh"}, {"ZDOTDIR": "/tmp"},
    {"PROMPT_COMMAND": "/x"}, {"LD_PRELOAD": "/tmp/e.so"},
    {"LD_LIBRARY_PATH": "/t"}, {"DYLD_INSERT_LIBRARIES": "/x.dylib"},
    {"NODE_OPTIONS": "--require /x"}, {"PYTHONSTARTUP": "/x.py"},
    {"PYTHONPATH": "/t"}, {"PYTHONHOME": "/t"}, {"RUBYOPT": "-r/x"},
    {"PERL5OPT": "-M/x"}, {"PERL5LIB": "/t"},
    {"_JAVA_OPTIONS": "-Xx"}, {"MAKEFILES": "/t/mk"}, {"MAKEFLAGS": "-f/t"},
    {"GIT_DIR": "/t"}, {"GIT_WORK_TREE": "/t"}, {"GIT_CONFIG_COUNT": "1"},
    {"GIT_CONFIG_KEY_0": "core.hooksPath"}, {"GIT_CONFIG_VALUE_0": "/t"},
    {"GIT_CONFIG_GLOBAL": "/t"}, {"GIT_CONFIG_SYSTEM": "/t"},
    {"GIT_SSH_COMMAND": "/x"}, {"GIT_SSH": "/x"}, {"GIT_ASKPASS": "/x"},
    {"SSH_ASKPASS": "/x"}, {"GIT_EDITOR": "/x"}, {"EDITOR": "/x"},
    {"VISUAL": "/x"}, {"GIT_PAGER": "/x"}, {"PAGER": "/x"},
    {"MANPAGER": "/x"}, {"GIT_EXTERNAL_DIFF": "/x"},
    {"XDG_CONFIG_HOME": "/t"}, {"HOME": "/t"},
    {"USERPROFILE": "c:\\t"},
    {"HISTFILE": "/t"}, {"INPUTRC": "/t"}, {"PSMODULEPATH": "c:\\t"},
    {"BASH_FUNC_x%%": "() { :; }; /x"},
])
def test_c100_env_denylist_blocks(env_dict):
    assert _run_gate_env(env_dict) == 2, env_dict


@pytest.mark.parametrize("env_dict", [
    {"PATH": "/tmp/x"},                    # replace = total shadow
    {"PATH": "/tmp/x:$PATH"},              # prepend shadows first
    {"PATH": "c:\\t;%PATH%"},            # windows prepend
    {"PATH": "/a:$PATH:/b"},               # self-ref mid = still shadowed
])
def test_c100_path_shadow_blocks(env_dict):
    assert _run_gate_env(env_dict) == 2, env_dict


@pytest.mark.parametrize("env_dict", [
    {"PATH": "$PATH:/tmp/x"},              # append cannot shadow
    {"PATH": "%PATH%;c:\\t"},
    {"PATH": "$env:PATH;c:\\t"},
    {"PATH": "$PATH"},                     # bare reference = no-op
    {"API_KEY": "k"}, {"CI": "1"},         # benign keys
])
def test_c100_env_benign_silent(env_dict):
    assert _run_gate_env(env_dict) == 0, env_dict


# --- C100b: adjacent exec-param sweep -------------------------------------
# `rm -rf ./` (trailing slash on the cwd sentinel) evaded the
# RM_DANGEROUS_TARGETS set; Format-Volume/Clear-Disk erase a disk without
# the `format X:` shape WIN_DISK_WIPE looked for.
@pytest.mark.parametrize("cmd", [
    "rm -rf ./", "rm -rf .\\", "rd /s /q .\\",
    "Format-Volume -DriveLetter D -Force",
    "Format-Volume -Path C:\\Mount -Force",
    "Clear-Disk 1 -RemoveData -Confirm:$false",
    "Clear-Disk -Number 1 -RemoveData",
    "Clear-Disk 2 -RemoveOEM -Force",
])
def test_c100b_trailing_slash_and_ps_wipe(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 2, cmd


# --- C100c: PowerShell/.NET state-file verb gaps ---------------------------
# Add-Content/Clear-Content/sc (Set-Content alias), Rename-Item/ren, and
# [IO.File]::Method('state/...') all mutated enforcement state without a
# matching verb arm or the quoted-paren path shape.
@pytest.mark.parametrize("cmd", [
    "sc state/wtp-abc.txt x",
    "Add-Content state/wtp-abc.txt x",
    "Add-Content -Path state/wtp-abc.txt -Value x",
    "Clear-Content state/wtp-abc.txt",
    "Rename-Item state/wtp-abc.txt y.txt",
    "ren state/wtp-abc.txt y.txt",
    "[IO.File]::WriteAllText('state/wtp-abc.txt','x')",
    "[System.IO.File]::Delete('state/subagent-s1.json')",
    "[IO.File]::AppendAllText(\"state/wtp-abc.txt\",\"x\")",
    "[IO.File]::Move('state/wtp-abc.txt','x')",
])
def test_c100c_ps_dotnet_state_verbs(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 2, cmd


# --- C100d: encoded execution hides the payload from the scan --------------
# powershell -enc/-EncodedCommand and decoder-piped/substituted shells
# (base64/certutil/openssl/xxd -> sh|eval|source|python...) execute text
# the gate cannot inspect. The transport itself is blocked.
@pytest.mark.parametrize("cmd", [
    "powershell -enc SQBFAFgA",
    "powershell -e SQBFAFgA",
    "powershell -ec SQBFAFgA",
    "pwsh -EncodedCommand SQBFAFgA",
    "powershell.exe -EncodedCommand SQBFAFgA",
    "echo cm0gLXJm | base64 -d | sh",
    "echo cm0gLXJm | base64 -d | bash",
    "echo cm0= | base64 --decode | eval",
    "echo cm0= | base64 -D | sh",
    "certutil -decode f.b64 - | cmd",
    "openssl enc -d -base64 -in f | sh",
    "xxd -r -p f.hex | sh",
    'bash -c "$(echo cm0= | base64 -d)"',
    'sh -c "$(base64 -d f.b64)"',
    'eval "$(echo cm0= | base64 -d)"',
    "eval $(base64 -d f.b64)",
    "source <(base64 -d f.b64)",
    "eval \"$(printf '\\x72\\x6d')\"",
    "echo cm0= | base64 -d | python",
])
def test_c100d_encoded_exec_blocks(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 2, cmd


# Decoders used on data (not piped to an interpreter) stay silent.
@pytest.mark.parametrize("cmd", [
    "echo cm0= | base64 -d",
    "base64 -d f.b64 > f.bin",
    "certutil -decode f.b64 f.bin",
    "openssl enc -d -base64 -in f -out g",
    "xxd -r -p f.hex > f.bin",
    "eval $(ssh-agent)",
    "eval $(direnv hook bash)",
    'bash -c "$(cat script.sh)"',
    "base64 f.txt | head",
    "echo SQBFAFgA | base64 -d | cat",
    "powershell -NoProfile -c Get-Item x",
    "pwsh -f script.ps1",
])
def test_c100d_decoder_data_silent(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 0, cmd


# --- C100e: git config exec-capable keys ------------------------------------
# `git -c k=v`/`--config-env` inline config and `git config k v` writes set
# exec-capable keys (hooksPath, alias.*, credential.helper, filter.*.cmd,
# includeIf.*.path) - a benign-looking `git status` becomes code execution
# on the op itself or every later git call. Reads/removals stay allowed.
@pytest.mark.parametrize("cmd", [
    "git -c core.hooksPath=/tmp/h status",
    "git -c core.sshCommand=/tmp/x pull",
    "git -c core.fsmonitor=/tmp/x status",
    "git -c core.pager=/tmp/x log",
    "git -c core.editor=/tmp/x commit",
    "git -c diff.external=/tmp/x diff",
    "git -c credential.helper=/tmp/x fetch",
    "git -c alias.x=!/tmp/e x",
    "git -c include.path=/tmp/cfg status",
    "git -c filter.drv.clean=/tmp/x checkout",
    "git -c mergetool.vim.cmd=/tmp/x mergetool",
    "git -c includeIf.x.path=/tmp/cfg status",
    "git -c init.templateDir=/tmp/t init",
    "git -c safe.directory=* status",
    "git -c http.sslVerify=false clone x",
    "git --config-env core.hooksPath=EV status",
    "git config core.hooksPath /tmp/h",
    "git config --global core.hooksPath /tmp/h",
    "git config core.sshCommand /tmp/x",
    "git config credential.helper /tmp/x",
    "git config alias.x '!/tmp/e'",
    "git config include.path /tmp/cfg",
    "git config --local core.fsmonitor /tmp/x",
    "git config filter.x.process /tmp/x",
    "git config includeIf.gitdir:x.path /tmp/cfg",
    "git config submodule.x.update '!/tmp/e'",
    "git config mergetool.vim.cmd /tmp/x",
    "git config --add pager.log /tmp/x",
    "git config gpg.program /tmp/x",
    "git config tar.xz.command /tmp/x",
])
def test_c100e_git_cfg_exec_key_blocks(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 2, cmd


@pytest.mark.parametrize("cmd", [
    "git config user.name x",
    "git config --global user.email x@y",
    "git config core.autocrlf true",
    "git config pull.rebase true",
    "git config --list",
    "git config core.hooksPath",
    "git config --get core.hooksPath",
    "git config --unset core.hooksPath",
    "git config --remove-section alias",
    "git config --edit",
    "git config remote.origin.url https://x",
    "git config remote.origin.pushurl https://x",
    "git config gpg.format ssh",
    "git config submodule.recurse true",
    "git config merge.conflictstyle diff3",
    "git config credential.useHttpPath true",
    "git -c color.ui=false status",
    "git -c advice.detachedHead=false checkout x",
    "git -c user.name=x commit -m y",
])
def test_c100e_git_cfg_benign_silent(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 0, cmd


_WTP_STATE = tempfile.mkdtemp(prefix="wtp_c101")


def run_gate_wtp(tool_input: dict, session_id: str = "") -> tuple[int, str]:
    if not session_id:
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


# --- C101: pass-6 review - state-guard + blocked-submit desync ---------------
# The pass-6 reviewer's probes (recovered after its run died) verified:
# - bare `state` dir targets (rm -rf state, find state -delete, rm -rf
#   -- state) skipped the devin/state anchor entirely
# - `cd devin && rm -rf state` two-hop junction
# - env/nice/timeout/command wrappers missing from _STATE_WRAP
# - glob-name evasions: ?tp-*, [s]ubagent, {a,b} braces, bare *
# - blocked-submit desync: a denied wtp line stays on the REAL input
#   line while the model clears pending - a later bare <CR> executes it
@pytest.mark.parametrize("cmd", [
    "rm -rf state", "rm -rf ./state", "rm -r state", "rm -rf state/",
    "rm -rf -- state", "find state -delete", "find ./state -delete",
    "find state -name 'wtp-abc.txt' -delete",
    "find state -type f -delete",
    "cd devin && rm -rf state",
    "cd ~/AppData/Roaming/devin && rm -rf state",
    "cd state && env rm wtp-abc.txt",
    "cd state && sudo rm wtp-abc.txt",
    "cd state && nice rm wtp-abc.txt",
    "cd state && timeout 5 rm wtp-abc.txt",
    "cd state && command rm wtp-abc.txt",
    "cd state && env tee wtp-abc.txt",
    "rm state/*", "rm state/?tp-*.txt", "rm state/[w]tp-*.txt",
    "rm state/{wtp-*,subagent-*}", "rm state/**",
    "rm state/[s]ubagent-s.json",
    "rm state/{subagent-s.json,wtp-a.txt}",
    "cd state && rm *", "cd state && rm ./*", "cd state && rm -r *",
    "cd state && mv * /tmp/", "cd state && tee *",
    "mv state/* /tmp/", "echo x > state/*", "echo x > state/?tp-*.txt",
    "cd state && find . -delete",
])
def test_c101_state_guard_evasions(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 2, cmd


# Blocked-submit desync: the denied text re-pends, so a subsequent bare
# <CR> re-scans and re-blocks it instead of executing on an empty model.
def test_c101_blocked_submit_repends():
    shell = "c101a"
    # A: dangerous text without submit -> pending
    assert run_gate_wtp({"text_input": "rm -rf /", "shell_id": shell},
                        "s101")[0] == 0
    # B: the CR is denied (real buffer still holds the text)
    assert run_gate_wtp({"text_input": "\n", "shell_id": shell},
                        "s101")[0] == 2
    # C: a bare <CR> re-submit must re-block, not pass on an empty
    # model - every form of resubmit dies until C-c clears.
    assert run_gate_wtp({"bytes_input": "<CR>", "shell_id": shell},
                        "s101")[0] == 2
    assert run_gate_wtp({"text_input": "\n", "shell_id": shell},
                        "s101")[0] == 2
    # C-c clears the model like the real line - next input types free
    assert run_gate_wtp({"bytes_input": "<C-c>", "shell_id": shell},
                        "s101")[0] == 0
    assert run_gate_wtp({"text_input": "ls\n", "shell_id": shell},
                        "s101")[0] == 0


GUARD_SCRIPT = os.path.join(SCRIPTS_DIR, "pre-exec-guard.py")


def run_guard_wtp(tool_input: dict, session_id: str, state_dir: str):
    """Invoke the consolidated runner - the replay bug only exists
    across multi-gate dispatch (sibling gates re-extract after the
    blocking child's wtp_reject)."""
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "tool_name": "write_to_process",
        "tool_input": tool_input,
        "session_id": session_id,
    })
    env = dict(os.environ)
    env["DEVIN_STATE_DIR"] = state_dir
    result = subprocess.run(
        [sys.executable, GUARD_SCRIPT],
        input=payload, capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=env)
    return result.returncode


def _wtp_buf(state_dir: str) -> dict:
    for f in os.listdir(state_dir):
        if f.startswith("wtp-"):
            with open(os.path.join(state_dir, f),
                      encoding="utf-8") as fh:
                return json.load(fh)
    return {}


# Reject replay: a denied call fires wtp_reject inside the blocking
# child's block() AND in run() after dispatch - and sibling gates still
# queued re-extract the same payload. Without the 'r' reject record,
# each re-extraction appends the re-pended text to 'o' again (observed:
# 'o' grew one copy per sibling gate). Invariant: denied text re-pends
# exactly once and every resubmit still re-blocks.
def test_c101b_reject_replay_no_growth(tmp_path):
    state = str(tmp_path)
    sh, sess = "c101b", "s101b"
    assert run_guard_wtp({"text_input": "rm -rf /", "shell_id": sh},
                         sess, state) == 0
    n = _wtp_buf(state)["p"].count("rm -rf /")
    assert n >= 1
    assert run_guard_wtp({"text_input": "\n", "shell_id": sh},
                         sess, state) == 2
    buf = _wtp_buf(state)
    assert "rm -rf /" in buf["p"]
    assert buf.get("r")
    # 'o' holds the denied lines once - sibling re-extractions must not
    # each append another copy.
    assert buf["o"].count("rm -rf /") <= n + 1
    assert run_guard_wtp({"text_input": "\n", "shell_id": sh},
                         sess, state) == 2
    buf = _wtp_buf(state)
    assert "rm -rf /" in buf["p"]
    assert buf["o"].count("rm -rf /") <= n + 1
    assert run_guard_wtp({"bytes_input": "<C-c>", "shell_id": sh},
                         sess, state) == 0
    assert run_guard_wtp({"text_input": "ls\n", "shell_id": sh},
                         sess, state) == 0


# --- C102: pass-7 review - escape/expansion normalization + arm widening -----
# p7 probes verified: bash \x->x escape launders verbs/targets, brace
# expansion and $IFS do the same, Win32 strips trailing dots, PS accepts
# any unambiguous parameter prefix, find -exec ran only plain rm, cd-into
# state/devin missed subshells/brace-groups/compound keywords/pipe verbs,
# and $(...)/backtick operands hide targets at run time.
S = "st" + "ate"
D = "de" + "vin"


@pytest.mark.parametrize("cmd", [
    # bash resolves \x -> x in unquoted words: verbs and targets both
    "r\\m -rf /", "gi\\t push --force", "git con\\fig core.hooksPath /x",
    f"rm -rf {S[:2]}\\{S[2:]}", f"rm -rf {S}\\",
    # brace expansion + $IFS resolve to the gated word
    f"rm -rf {{{S}}}", f"rm -rf {S}{{,}}", f"rm -rf {S}$IFS",
    "rm -rf {/}x",
    # Win32 strips trailing dots
    f"rm -rf {S}.", f"rm -rf {S}..", f"cd {S}. && rm wtp-x.txt",
    # run-time substitution hides the target (uninspectable operand)
    f"rm -rf {S[:3]}$(echo {S[3:]})", "rm -f `echo x`",
    "rm -rf $(cat /tmp/list)", "rm -f `ls`",
    # PS accepts any unambiguous prefix of EncodedCommand
    "pwsh -encoded X", "powershell -enco X", "powershell -encode X",
    "powershell -encodedcomm X", "powershell -encodedcommand X",
    "pwsh -ec X",
    # find -exec runs ANY verb on the state dir
    f"find {S} -exec sh -c 'echo $1' _ {{}} +",
    f"find {S} -execdir rm {{}} +",
    # state files piped through find into a delete verb
    f"find {S} -type f | xargs rm -f",
    f"find {S} -name 'wtp-*' | xargs rm",
    # cd-into-state compounds and wrappers
    f"cd {S} && (rm wtp-x.txt)", f"cd {S} && {{ rm wtp-x.txt; }}",
    f"cd {S} && ls | xargs rm -f", f"cd {S} && eval rm wtp-x.txt",
    f"cd {S} && strace rm wtp-x.txt", f"cd {S} && ltrace rm wtp-x.txt",
    f"cd {S} && setsid rm wtp-x.txt", f"cd {S} && pkexec rm wtp-x.txt",
    f"cd {S} && while :; do rm -f wtp-x.txt; done",
    f"cd {S} && if true; then rm wtp-x.txt; fi",
    # cd-into-devin whole-dir wipes need no `state` operand
    f"cd {D} && find . -delete", f"cd {D} && find . -type f | xargs rm -f",
])
def test_c102_blocked(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 2, cmd


@pytest.mark.parametrize("cmd", [
    "ls state", "echo state",
    "find . -type f | xargs rm -f",               # no state anchor
    "cd x && (rm y)", "find /tmp -exec ls {} +",  # non-state targets
    "powershell -encodedcmd X",                   # invalid prefix: PS errors
    "pwsh -ExecutionPolicy Bypass -c 'ls'",
])
def test_c102_silent(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 0, cmd


# --- C103: pass-7 review - continuation desync, \S-vault, env/git arms ------
# Recovered pass-7 findings:
# - wtp line-continuation desync: a submitted line ending in an open
#   continuation (`&&`, `|`, `\`, a flag awaiting its value) never executes
#   on the tty - the shell waits for more input - but the gate scanned it as
#   a completed command. Continuation lines now move to pending and join the
#   next submitted line before scanning.
# - unbounded `(?:\S+\s+)*` wrapper-skip in segment patterns vaulted `;`, `|`,
#   `&` and newlines, merging two commands into one segment (xargs-piped
#   git-config writes went unseen).
# - normpath evasions in rm targets (dir/.., ./., ?-globs).
# - env dict: GIT_CONFIG_PARAMETERS/GIT_EXEC_PATH/GIT_TEMPLATE_DIR and the
#   *_RSH/*_SSH/BROWSER exec helpers.
# - git: --exec-path/-C/--git-dir/--work-tree foreign-repo flags, section
#   ops on denylist sections, http[s].proxy MITM keys.
# - state-write arms: redirects (>, 2>, dd of=), download/archive/output
#   verbs (curl -o, wget -O, scp dst, iwr -OutFile, bitsadmin, tar -cf,
#   unzip -d, zip dst-first, gcc -o, fsutil seteof, robocopy /MIR).
# - transform-producer pipes into shells/interpreters (printf/echo -e/
#   rev/decoders/shells) - direct producers (cat/curl/find/echo) pass output
#   through untouched, same exposure class as `sh file`.
# - exec tool_input.workdir: recursive/wipe verbs relative to filesystem
#   roots and sensitive dirs.


def _run_gate_ti(tool_input: dict) -> tuple[int, str]:
    payload = json.dumps({
        "hook_event_name": "PreToolUse", "tool_name": "exec",
        "tool_input": tool_input, "session_id": "test"})
    r = subprocess.run(
        [sys.executable, GATE_SCRIPT], input=payload, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=10)
    return r.returncode, r.stdout.strip()


S103 = "st" + "ate"
D103 = "de" + "vin"


@pytest.mark.parametrize("cmd", [
    # \S-vault fix: separator-bounded segments see xargs/read-loop writes
    "printf 'k\\nv\\n' | xargs -n2 git config",
    "while read k v; do git config $k $v; done < cfg",
    "git config $K $V",
    # rm normpath/glob targets
    "rm -rf ./.", "rm -rf ././", "rm -rf dir/..", "rm -rf node_modules/..",
    "rm -rf build/../..", "rm -rf ./..", "rm -rf ./?", "rm -rf x/../../y",
    "rm -rf ./\\../", "rm -rf .\\.",
    # git foreign-repo flags / section ops / MITM keys
    "git --exec-path=/x status", "git --exec-path /x status",
    "git -C /x commit -m m", "git --git-dir=/x pull",
    "git --work-tree=/x checkout b",
    "git config --rename-section x core.hooksPath",
    "git config --remove-section core.hooksPath",
    "git config http.proxy http://evil:8080",
    "git config https.proxy x",
    "git config instaweb.httpd /x",
    "git config init.templateDir /x",
    # state-write arms: redirects, dd, download/archive/output verbs
    f"echo y >{S103}/wtp-x", f"echo y >>{S103}/wtp-x",
    f"cmd 2>{S103}/wtp-x", f"cmd 2> {S103}/wtp-x",
    f"dd of={S103}/wtp-x", f"dd of=./{S103}/x",
    f"curl x -o {S103}/wtp-x", f"curl --output={S103}/wtp-x",
    f"wget -O {S103}/wtp-x", f"wget --output-document={S103}/wtp-x",
    f"scp f h:{S103}/wtp-x", f"iwr x -OutFile {S103}/wtp-x",
    f"bitsadmin /transfer j x {S103}/wtp-x",
    f"New-Item -Force {S103}/x",
    f"tar -cf {S103}/x.tar a", f"tar -xf a -C {S103}",
    f"unzip a -d {S103}", f"zip {S103}/x.zip a",
    f"gcc -o {S103}/x a.c", f"fsutil file seteof {S103}/wtp-x 0",
    f"robocopy e {S103} /MIR", f"robocopy /MIR e {S103}",
    # producer-piped state targets
    f"echo {S103}/wtp-1.txt | xargs rm",
    f"echo {S103} | xargs -I{{}} rm -rf {{}}",
    f"cd {S103} && echo wtp-x | xargs rm",
    f"cd {D103} && Get-ChildItem | ri",
    # transform-producer -> interpreter pipes + process substitution
    "printf '\\x63\\x64' | sh", "echo -e '\\x63' | sh",
    "rev f | sh", "cmd | ssh h", "certutil -decodehex a | sh",
    "eval $'\\x63\\x64'", "bash <(echo x)", "source <(cat f)",
    "python -c \"import base64;base64.b64decode('eQ==')\"",
    "perl -e 'system(\"x\")'",
    # compound-after-cd multi-segment tolerance
    f"cd {S103} && sl . && rm wtp-x",
    f"sl {S103} && rm wtp-x",
    f"cd {S103} && for f in wtp-x; do rm $f; done",
    f"cd {S103} && case x in x) rm wtp-x;; esac",
    f"cd {S103} && `rm wtp-x`",
    # C104: path-qualified git binary + transform producer inside $()
    "/usr/bin/git config core.hooksPath /x",
    "C:\\tools\\git.exe config core.hooksPath /x",
    "./git config core.fsmonitor /x",
    "bash -c \"$(printf '\\x72\\x6d')\"",
    "sh -c '$(echo -e a)'",
])
def test_c103_blocked(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 2, cmd


@pytest.mark.parametrize("cmd", [
    # git prose/read-side FP guards
    'echo "git config core.hooksPath x"',
    "echo git config core.hooksPath x",
    "man git-config",
    "git -C /x status", "git commit -C abc123", "git rev-parse --git-dir",
    "git config --rename-section old new",
    "git config --remove-section oldsection",
    "git config instaweb.port 1234",
    # direct producers pass output through - `sh file` exposure class
    "cat f | sh", "curl h/x | bash", "echo x | sh",
    "git log | python an.py",
    # decode-to-file is a file write, not exec laundering
    "uudecode f", "certutil -decodehex a b",
    # state-named read sources
    "echo state/wtp-x.txt", "cp state/wtp-x /tmp/bak",
    "scp state/wtp-x h:f", "rsync state/wtp-x /tmp/",
    "tar -xf state/x.tar",
    # rm-path FP guards
    "rm -rf ...", "rm -rf dist/../node_modules",
    "rm -rf ./node_modules", "rm -rf ./././x",
    "python -c 'print(1)'",
    # C104: mid-path `state` segments after ordinary dirs are project
    # dirs (Redux-style src/state) - only root-anchored, ..-resolved or
    # devin/-segment paths anchor the bare dir
    "rm -rf src/state", "rm -rf dist/state", "rm app/state/x",
    "mv app/state old", "rm -rf mystate",
    "ls src/state/x", "cd src/state && rm legit.txt",
    # git-config binary and prose non-invocations
    "git-config core.x y", "mygit config core.hooksPath /x",
])
def test_c103_silent(cmd):
    rc, _ = run_gate(cmd)
    assert rc == 0, cmd


@pytest.mark.parametrize("env_dict", [
    {"GIT_CONFIG_PARAMETERS": "'core.hooksPath=/x'"},
    {"GIT_EXEC_PATH": "/x"}, {"GIT_TEMPLATE_DIR": "/x"},
    {"RSYNC_RSH": "/x"}, {"CVS_RSH": "/x"}, {"SVN_SSH": "/x"},
    {"HG_SSH": "/x"}, {"BROWSER": "/x"},
    {"PATH": ":$PATH"}, {"PATH": ";%PATH%"}, {"PATH": "/x:$PATH"},
])
def test_c103_env_blocks(env_dict):
    assert _run_gate_env(env_dict) == 2


@pytest.mark.parametrize("env_dict", [
    {"PATH": "$PATH:/x"}, {"PATH": "%PATH%;x"},
])
def test_c103_env_silent(env_dict):
    assert _run_gate_env(env_dict) == 0


@pytest.mark.parametrize("workdir", [
    "C:\\", "/", "C:\\Windows", "/etc", "~",
])
def test_c103_workdir_wipe_blocks(workdir):
    rc, _ = _run_gate_ti({"command": "rm -rf x", "workdir": workdir})
    assert rc == 2, workdir


@pytest.mark.parametrize("workdir", [
    "/tmp/x", "D:\\proj", "build",
])
def test_c103_workdir_benign_silent(workdir):
    rc, _ = _run_gate_ti({"command": "rm -rf x", "workdir": workdir})
    assert rc == 0, workdir
    rc, _ = _run_gate_ti({"command": "ls", "workdir": "/"})
    assert rc == 0


def test_c103_wtp_continuation_blocks():
    # A submitted line ending in an open continuation never executes on
    # the tty - it must pend and join the next submitted line, so the
    # combined text is what gets scanned.
    for lines in ([f"cd {S103} &&\n", "rm wtp-x\n"],
                  [f"cd {S103} |\n", "rm wtp-x\n"],
                  ["git push -\\\n", "f\n"]):
        shell = "sc" + str(abs(hash(lines[0])))
        for ln in lines:
            rc, _ = run_gate_wtp({"text_input": ln, "shell_id": shell},
                                 session_id="s-" + shell)
        assert rc == 2, lines
