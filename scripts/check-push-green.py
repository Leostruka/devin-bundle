#!/usr/bin/env python3
"""PreToolUse hook: blocks git push when local checks are failing.

Stdin payload (per /cli/extensibility/hooks/lifecycle-hooks):
  {"hook_event_name": "PreToolUse", "tool_name": "exec",
   "tool_input": {"command": "git push ..."}}

Exit codes (per /cli/extensibility/hooks/overview#exit-codes):
  0 = allow, 2 = block.

Two gates:
  1. Test suite must pass (AGENTS.md Rule 5, no push without green)
  2. Held-out gap: if tests/validation/ and tests/held-out/ both exist, a
     validation-green / held-out-red split blocks the push (AGENTS.md Rule 16)

Sources:
  SpecBench (arXiv:2605.21384) - held-out gap grows 28pp per 10x code size.
  "Reward Hacking in Self-Improving Code Agents" (ICLR 2026 Workshop) - 73.8%
  Kernel-Bench and 46.8% ALE-Bench optimizations show proxy gains without real
  gains, so agent-chosen tests alone are not evidence of improvement.
"""
import sys, json, subprocess, os, re

_CF = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

def _run(*a, **kw):
    kw.setdefault('creationflags', _CF)
    return subprocess.run(*a, **kw)

TEST_TIMEOUT = 120
# Fail-closed means a timeout blocks the push, so the cap must exceed real
# suite time but stay under the pre-exec-guard hook budget (300s here).
# Repos with bigger suites or tighter budgets tune BUNDLE_PUSH_GATE_TIMEOUT.
MAIN_TIMEOUT = int(os.environ.get("BUNDLE_PUSH_GATE_TIMEOUT", "250"))


def block(reason):
    """Emit a block decision and exit with code 2 (deny)."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def run_check(cmd, cwd, timeout=TEST_TIMEOUT):
    """Run a shell check. Returns (status, output).

    status is one of: "pass", "fail", "timeout", "unavailable".
    The caller decides policy; the main suite treats anything but "pass"
    as a block (fail-closed) so the gate cannot silently degrade to a no-op.

    stdout goes to a temp file, not a pipe: a timed-out `cmd /c` kill
    orphans the grandchild (pytest), which would otherwise hold the pipe
    open and block run() past the timeout while its console window leaks.
    """
    import tempfile
    out_file = tempfile.TemporaryFile(mode="w+t", encoding="utf-8",
                                      errors="replace")
    # Strip hook-injected env: tests that exercise hook scripts in tmp repos
    # expect cwd isolation; DEVIN_PROJECT_DIR would redirect their scans.
    env = dict(os.environ)
    env.pop("DEVIN_PROJECT_DIR", None)
    try:
        proc = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=out_file,
                                stderr=subprocess.STDOUT, creationflags=_CF,
                                env=env)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Kill the whole tree; cmd alone dies leaving pytest orphaned.
            try:
                _run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                     capture_output=True, timeout=15)
            except (FileNotFoundError, OSError, subprocess.SubprocessError):
                proc.kill()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            out_file.seek(0)
            tail = out_file.read() or ""
            return "timeout", tail + "\ncheck timed out after {}s".format(timeout)
        out_file.seek(0)
        return ("pass" if proc.returncode == 0 else "fail"), out_file.read()
    except (FileNotFoundError, OSError) as e:
        return "unavailable", f"check unavailable: {e}"
    finally:
        out_file.close()


def is_git_push(command):
    """True when the command issues a git push.

    Tokenizes shell segments so whitespace variants (`git  push`),
    global flags between verb and subcommand (`git -C repo push`,
    `git -c k=v push`) and command chaining (`x && git push`) are caught.
    """
    import shlex
    # git options that consume the next token as a value.
    git_opts_with_arg = {"-C", "-c", "--git-dir", "--work-tree",
                         "--namespace", "--exec-path"}
    for segment in re.split(r"&&|\|\||;|\|", command):
        try:
            tokens = shlex.split(segment, posix=(os.name != "nt"))
        except ValueError:
            tokens = segment.split()
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            base = os.path.basename(tok).lower()
            if base in ("git", "git.exe") or tok.lower().endswith("\\git.exe"):
                j = i + 1
                while j < len(tokens):
                    t = tokens[j]
                    if t in git_opts_with_arg:
                        j += 2
                        continue
                    if t.startswith("-"):
                        j += 1
                        continue
                    break
                if j < len(tokens) and tokens[j].lower() == "push":
                    return True
                i = j
            i += 1
    return False


def detect_test_command(cwd):
    """Return (command, is_pytest) for the project's test runner, or (None, False)."""
    if os.path.exists(os.path.join(cwd, "package.json")):
        # Prefer pnpm/yarn if lockfiles indicate them, else npm
        if os.path.exists(os.path.join(cwd, "pnpm-lock.yaml")):
            return "pnpm test", False
        if os.path.exists(os.path.join(cwd, "yarn.lock")):
            return "yarn test", False
        return "npm test", False
    for marker in ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"):
        if os.path.exists(os.path.join(cwd, marker)):
            return "pytest", True
    if os.path.exists(os.path.join(cwd, "Cargo.toml")):
        return "cargo test", False
    if os.path.exists(os.path.join(cwd, "go.mod")):
        return "go test ./...", False
    if os.path.exists(os.path.join(cwd, "pom.xml")):
        return "mvn test", False
    if os.path.exists(os.path.join(cwd, "build.gradle")) or os.path.exists(os.path.join(cwd, "build.gradle.kts")):
        return "gradle test", False
    if os.path.exists(os.path.join(cwd, "Rakefile")) or os.path.exists(os.path.join(cwd, "Gemfile")):
        return "rake test", False
    try:
        entries = os.listdir(cwd)
    except OSError:
        entries = []
    if any(f.endswith((".sln", ".csproj")) for f in entries):
        return "dotnet test", False
    return None, False


# secret-shaped-key = "value" pairs in a TOML file (single-line strings only).
TOML_SECRET_RE = re.compile(
    r'(?im)^\s*([\w.\-]*(?:api_?key|token|secret|password|private_?key'
    r'|credential)[\w.\-]*)\s*=\s*"([^"]*)"')
# "secret-shaped-key": "value" pairs in JSON.
JSON_SECRET_RE = re.compile(
    r'"(API_KEY|TOKEN|SECRET|PASSWORD|KEY|api_key|token|secret|password|key'
    r'|apiKey|accessToken|clientSecret|privateKey)"\s*:\s*"([^"]*)"')


def check_unmasked_secrets(cwd):
    """Block if credentials.toml or mcp_config.json contain unmasked secrets.

    Per-entry check: every secret-shaped value must equal MASKED. A single
    MASKED placeholder elsewhere in the file does not clear real secrets.
    """
    creds = os.path.join(cwd, "credentials.toml")
    mcp = os.path.join(cwd, "mcp_config.json")

    if os.path.isfile(creds):
        with open(creds, encoding="utf-8") as f:
            content = f.read()
        for m in TOML_SECRET_RE.finditer(content):
            if m.group(2).strip() and m.group(2).strip().upper() != "MASKED":
                block(
                    "credentials.toml contains unmasked secret values. "
                    "Every secret-shaped value must be MASKED before pushing, "
                    "or exclude the file from the commit."
                )

    if os.path.isfile(mcp):
        with open(mcp, encoding="utf-8") as f:
            content = f.read()
        for m in JSON_SECRET_RE.finditer(content):
            value = m.group(2).strip()
            if len(value) >= 4 and value.upper() != "MASKED":
                block(
                    "mcp_config.json contains unmasked secret values. "
                    "Export with masking before pushing."
                )


def check_held_out_gap(cwd, is_pytest, val_result, held_result):
    """Block when validation tests pass but held-out tests fail (Rule 16)."""
    if val_result is None:
        return  # no held-out split configured / not pytest
    val_passed = val_result[0] == "pass"
    held_passed = held_result[0] == "pass"
    held_output = held_result[1]
    if val_passed and not held_passed:
        block(
            "Validation tests pass but held-out tests fail. This gap indicates "
            "overfitting to the tests you optimized against; 47-74% of "
            "self-improvement gains are illusory (AGENTS.md Rule 16). "
            "Fix the held-out failures before pushing.\n"
            + held_output.strip()[-800:]
        )


APPROVAL_MARKERS = (
    os.path.join(".devin", "test-deletion-approved"),
    os.path.join(".devin", "approvals", "test-deletion.txt"),
)


def check_test_deletions(cwd):
    """Block push when the pending diff deletes tests (AGENTS.md Rule 25).

    Flags deleted files under tests/ (git status porcelain D) and removed
    test-function lines in the HEAD diff. Approved deletions carry a marker:
    the file .devin/test-deletion-approved or env TEST_DELETION_APPROVED=1
    (document the reason in the commit message / ledger).
    """
    if os.environ.get("TEST_DELETION_APPROVED") == "1":
        return
    for rel in APPROVAL_MARKERS:
        if os.path.isfile(os.path.join(cwd, rel)):
            return
    try:
        status = _run(["git", "status", "--porcelain"], capture_output=True,
                      text=True, timeout=15, cwd=cwd,
                      encoding="utf-8", errors="replace")
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return  # no git: cannot check, allow
    if status.returncode == 0:
        for line in status.stdout.splitlines():
            xy = line[:2]
            path = line[3:].strip()
            norm = path.replace("\\", "/")
            if "D" in xy and (norm.startswith("tests/")
                              or norm.startswith("test/")
                              or "/tests/" in norm):
                block(
                    f"git push rejected: test file '{path}' is deleted "
                    "(AGENTS.md Rule 25: no test deletion without approval). "
                    "Restore it or record approval in "
                    ".devin/test-deletion-approved with the reason."
                )
    try:
        diff = _run(["git", "diff", "HEAD", "--unified=0", "--", "tests/", "test/"],
                    capture_output=True, text=True, timeout=15, cwd=cwd,
                    encoding="utf-8", errors="replace")
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return
    if diff.returncode == 0:
        removed_tests = [
            ln for ln in diff.stdout.splitlines()
            if ln.startswith("-") and not ln.startswith("---")
            and re.search(r"def test_|class Test", ln)
        ]
        if removed_tests:
            block(
                "git push rejected: the pending diff removes test functions "
                f"({len(removed_tests)} removed 'def test_'/'class Test' "
                "lines under tests/). AGENTS.md Rule 25 requires explicit "
                "approval for test deletion; record the reason in "
                ".devin/test-deletion-approved before pushing."
            )


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open

    if data.get("hook_event_name", "") != "PreToolUse":
        sys.exit(0)
    if data.get("tool_name", "") != "exec":
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command", "") or ""
    if not is_git_push(command):
        sys.exit(0)
    # A dry run does not publish anything, so let it through.
    if "--dry-run" in command:
        sys.exit(0)

    cwd = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()

    # Defense in depth: block push if secrets are unmasked in bundle files.
    check_unmasked_secrets(cwd)

    # Rule 25: no test deletion without approval.
    check_test_deletions(cwd)

    check_cmd, is_pytest = detect_test_command(cwd)
    if not check_cmd:
        if os.path.isdir(os.path.join(cwd, "tests")):
            block(
                "git push rejected: a tests/ directory exists but no test "
                "framework marker was detected (pytest.ini, package.json, "
                "Cargo.toml, ...). The push gate cannot verify green; add a "
                "framework marker or remove tests/ (AGENTS.md Rule 5)."
            )
        print("check-push-green: no test framework detected; gate skipped",
              file=sys.stderr)
        sys.exit(0)

    validation_dir = os.path.join(cwd, "tests", "validation")
    heldout_dir = os.path.join(cwd, "tests", "held-out")
    gap_active = os.path.isdir(validation_dir) and os.path.isdir(heldout_dir) and is_pytest

    # Rule 15 declares tests/validation + tests/held-out as the push-gate
    # contract; when both exist they ARE the main check (scoped to fit the
    # budget, fail-closed) instead of re-running them plus the full suite.
    # CI still runs the full suite.
    # NOTE: these suites run SEQUENTIALLY, not concurrently. Held-out
    # mutation tests rewrite scripts/*.py in place (mutate -> run -> restore),
    # so a concurrent validation run can read a half-mutated script and fail
    # audit's compile check — exactly the flake this gate kept hitting.
    # Sequential cost is ~20s and fits the budget easily.
    if gap_active:
        val_result = run_check(f'pytest "{validation_dir}" -q', cwd, MAIN_TIMEOUT)
        held_result = run_check(f'pytest "{heldout_dir}" -q', cwd, MAIN_TIMEOUT)
        check_cmd = "validation+held-out"
        if val_result[0] == "pass" and held_result[0] == "pass":
            status, output = "pass", ""
        else:
            status = "fail" if "fail" in (val_result[0], held_result[0]) else \
                ("timeout" if "timeout" in (val_result[0], held_result[0])
                 else val_result[0] if val_result[0] != "pass" else held_result[0])
            output = val_result[1] + "\n" + held_result[1]
    else:
        status, output = run_check(check_cmd, cwd, MAIN_TIMEOUT)
        val_result = held_result = None

    # Fail-closed: any outcome other than a passing run blocks the push, so
    # a timed-out or unrunnable suite cannot silently degrade the gate.
    if status != "pass":
        detail = {
            "fail": f"'{check_cmd}' is failing",
            "timeout": f"'{check_cmd}' did not finish within {MAIN_TIMEOUT}s",
            "unavailable": f"'{check_cmd}' could not be run",
        }.get(status, f"'{check_cmd}' status: {status}")
        try:
            dbg = os.path.join(cwd, ".devin", "scratch",
                               "push-gate-last-failure.log")
            os.makedirs(os.path.dirname(dbg), exist_ok=True)
            with open(dbg, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(f"status={status} cmd={check_cmd}\n" + output)
        except OSError:
            pass
        block(
            f"git push rejected: {detail}. Fix the failures in the "
            "inner loop before pushing (AGENTS.md Rule 5).\n"
            + output.strip()[-800:]
        )

    check_held_out_gap(cwd, is_pytest, val_result, held_result)

    sys.exit(0)


if __name__ == "__main__":
    main()
