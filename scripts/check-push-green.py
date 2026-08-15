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
import sys, json, subprocess, os

TEST_TIMEOUT = 60


def block(reason):
    """Emit a block decision and exit with code 2 (deny)."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def run_check(cmd, cwd):
    """Run a shell check. Returns (passed, output). Fails open on timeout."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=TEST_TIMEOUT,
        )
        return result.returncode == 0, (result.stdout or "") + (result.stderr or "")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return True, "check timed out or was not found - allowing push"


def detect_test_command(cwd):
    """Return (command, is_pytest) for the project's test runner, or (None, False)."""
    if os.path.exists(os.path.join(cwd, "package.json")):
        return "npm test", False
    for marker in ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"):
        if os.path.exists(os.path.join(cwd, marker)):
            return "pytest", True
    if os.path.exists(os.path.join(cwd, "Cargo.toml")):
        return "cargo test", False
    if os.path.exists(os.path.join(cwd, "go.mod")):
        return "go test ./...", False
    try:
        entries = os.listdir(cwd)
    except OSError:
        entries = []
    if any(f.endswith((".sln", ".csproj")) for f in entries):
        return "dotnet test", False
    return None, False


def check_held_out_gap(cwd, is_pytest):
    """Block when validation tests pass but held-out tests fail (Rule 16)."""
    validation_dir = os.path.join(cwd, "tests", "validation")
    heldout_dir = os.path.join(cwd, "tests", "held-out")
    if not (os.path.isdir(validation_dir) and os.path.isdir(heldout_dir)):
        return  # no held-out split configured: nothing to compare
    if not is_pytest:
        return  # gap measurement currently implemented for pytest only

    val_passed, _ = run_check(f'pytest "{validation_dir}" -q', cwd)
    held_passed, held_output = run_check(f'pytest "{heldout_dir}" -q', cwd)

    if val_passed and not held_passed:
        block(
            "Validation tests pass but held-out tests fail. This gap indicates "
            "overfitting to the tests you optimized against; 47-74% of "
            "self-improvement gains are illusory (AGENTS.md Rule 16). "
            "Fix the held-out failures before pushing.\n"
            + held_output.strip()[-800:]
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
    if "git push" not in command.lower():
        sys.exit(0)
    # A dry run does not publish anything, so let it through.
    if "--dry-run" in command:
        sys.exit(0)

    cwd = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    check_cmd, is_pytest = detect_test_command(cwd)
    if not check_cmd:
        sys.exit(0)  # no test framework detected: allow

    passed, output = run_check(check_cmd, cwd)
    if not passed:
        block(
            f"git push rejected: '{check_cmd}' is failing. Fix the failures in the "
            "inner loop before pushing (AGENTS.md Rule 5).\n"
            + output.strip()[-800:]
        )

    check_held_out_gap(cwd, is_pytest)

    sys.exit(0)


if __name__ == "__main__":
    main()
