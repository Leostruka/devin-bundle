#!/usr/bin/env python3
"""permission-gate — PermissionRequest hook: auto-approve provably read-only
commands, stay silent on everything else.

Design: approve-only, never deny. Unknown/complex input exits 0 so the human
prompt proceeds untouched (#541). A command is approved only when it matches
a strict single-invocation read-only pattern — no shell composition, no
redirects, no separators. `block` is never emitted: an unexpected payload is
a bug in the gate, not a reason to hide a decision from the user.
"""
import json
import re
import sys

# Composing characters: a safe command is ONE invocation. Any of these means
# the string is a pipeline/script, not a read-only lookup — stay silent.
UNSAFE_CHARS = re.compile(r"[;&|`$<>\\]|\(|\)|\n")

# Binary -> set of read-only subcommands (None = whole binary is read-only).
SAFE_EXEC = {
    "git": {
        "status", "diff", "log", "show", "branch", "remote", "fetch",
        "ls-files", "ls-remote", "ls-tree", "rev-parse", "rev-list",
        "describe", "blame", "shortlog", "check-ignore", "cat-file",
        "grep", "tag", "stash list", "reflog", "whatchanged", "name-only",
        "count-objects", "verify-commit", "verify-tag", "for-each-ref",
    },
    "gh": {
        "status", "view", "list", "checks", "diff", "search",
        "auth status", "api",
    },
    "rg": None,
    "fd": None,
    "ls": None,
    "dir": None,
    "pwd": None,
    "cat": None,
    "head": None,
    "tail": None,
    "wc": None,
    "file": None,
    "which": None,
    "whereis": None,
    "date": None,
    "env": None,
    "printenv": None,
    "uname": None,
    "hostname": None,
    "whoami": None,
    "git-lfs": None,
}

# gh api is read-only only without -X/-f/--method mutating verbs.
GH_API_WRITE = re.compile(
    r"(-X\s*(POST|PUT|PATCH|DELETE)\b|--method\s+(post|put|patch|delete)\b"
    r"|-f\b|--field\b|--raw-field\b|-H\b.*X-HTTP-Method-Override)",
    re.I)

# git flag that turns a read verb into a write (branch -d/-D/-m, tag -d,
# stash drop/pop, remote add/prune, fetch --prune).
GIT_WRITE_FLAGS = re.compile(
    r"(^|\s)(-d\b|-D\b|-m\b|--delete\b|--prune\b|drop\b|pop\b|add\b|"
    r"remove\b|rename\b|set-url\b|prune\b)")


def _exec_verdict(command: str) -> bool:
    """True only when command is a provably read-only single invocation."""
    cmd = command.strip()
    if not cmd or UNSAFE_CHARS.search(cmd):
        return False
    parts = cmd.split()
    exe = parts[0].rsplit("/", 1)[-1].rsplit("\\", 1)[-1].lower()
    exe = re.sub(r"\.(exe|bat|cmd|ps1)$", "", exe)
    if exe == "echo":
        return True
    if exe not in SAFE_EXEC:
        return False
    allowed = SAFE_EXEC[exe]
    if allowed is None:
        return True
    if len(parts) < 2:
        # `git`/`gh` alone just prints help.
        return True
    sub = parts[1].lower()
    if exe == "gh" and sub == "api":
        return not GH_API_WRITE.search(cmd)
    if sub in allowed or f"{sub} {parts[2].lower() if len(parts) > 2 else ''}".rstrip() in allowed:
        if exe == "git":
            return not GIT_WRITE_FLAGS.search(cmd)
        return True
    return False


def main():
    reconfigure = getattr(sys.stdin, "reconfigure", None)
    if reconfigure:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        return  # fail-open: no opinion
    if not isinstance(data, dict):
        return
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    if tool == "exec":
        cmd = inp.get("command", "") if isinstance(inp, dict) else ""
        if cmd and _exec_verdict(cmd):
            print(json.dumps({"decision": "approve",
                              "reason": "permission-gate: read-only command"}))
    # every other tool: no opinion -> user prompt proceeds


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open always
    sys.exit(0)
