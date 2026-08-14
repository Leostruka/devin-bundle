#!/usr/bin/env python3
"""PreToolUse hook: blocks git push when local checks are failing.

Reads tool input JSON from stdin. Exit 0 = allow, exit 1 = block.
Only triggers on exec commands containing 'git push'.
Runs the project's test/lint check before allowing push.
"""
import sys, json, subprocess, os

def run_check(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0, result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return True, "check timed out or not found — allowing push"

def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool = data.get("tool", "")
    tool_input = data.get("tool_input", {})

    if tool != "exec":
        sys.exit(0)

    command = tool_input.get("command", "")
    if "git push" not in command.lower():
        sys.exit(0)

    cwd = os.getcwd()

    # Try common test commands in priority order
    checks = [
        ("npm test", "npm"),
        ("pnpm test", "pnpm"),
        ("yarn test", "yarn"),
        ("pytest", "pytest"),
        ("cargo test", "cargo"),
        ("go test ./...", "go"),
        ("dotnet test", "dotnet"),
    ]

    # Check if package.json or test config exists
    has_npm = os.path.exists(os.path.join(cwd, "package.json"))
    has_pytest = os.path.exists(os.path.join(cwd, "pytest.ini")) or \
                 os.path.exists(os.path.join(cwd, "pyproject.toml")) or \
                 os.path.exists(os.path.join(cwd, "setup.cfg"))
    has_cargo = os.path.exists(os.path.join(cwd, "Cargo.toml"))
    has_go = os.path.exists(os.path.join(cwd, "go.mod"))

    check_cmd = None
    if has_npm:
        check_cmd = "npm test"
    elif has_pytest:
        check_cmd = "pytest"
    elif has_cargo:
        check_cmd = "cargo test"
    elif has_go:
        check_cmd = "go test ./..."

    if not check_cmd:
        sys.exit(0)  # no test framework detected, allow push

    passed, output = run_check(check_cmd, cwd)
    if not passed:
        print(f"BLOCKED: git push rejected — '{check_cmd}' is failing.", file=sys.stderr)
        print("Fix tests before pushing. (Rule: no push without green)", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
