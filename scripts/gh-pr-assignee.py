#!/usr/bin/env python3
"""PostToolUse hook: auto-assign PRs created via `gh pr create`.

Any session, any repo: when an exec call runs `gh pr create` and stdout
carries the new PR URL, runs `gh pr edit <url> --add-assignee <ASSIGNEE>`
in the same workdir. Assignee = $GH_PR_ASSIGNEE or Leostruka.

Skips when the command already passes --assignee. Never blocks: failures
surface as additionalContext so the agent can retry manually.
"""
import json
import os
import re
import subprocess
import sys

_CREATE_RX = re.compile(r"\bgh\s+pr\s+create\b")
_URL_RX = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/pull/\d+")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)
    if data.get("tool_name") != "exec":
        sys.exit(0)
    resp = data.get("tool_response") or {}
    if not resp.get("success", True):
        sys.exit(0)
    ti = data.get("tool_input") or {}
    cmd = ti.get("command") or ""
    if not _CREATE_RX.search(cmd) or "--assignee" in cmd:
        sys.exit(0)
    m = _URL_RX.search(resp.get("output") or "")
    if not m:
        sys.exit(0)  # no PR URL in output — create may have failed anyway

    url = m.group(0)
    who = os.environ.get("GH_PR_ASSIGNEE", "Leostruka")
    gh = os.environ.get("GH_PR_BIN", "gh")
    try:
        r = subprocess.run(
            [gh, "pr", "edit", url, "--add-assignee", who],
            cwd=ti.get("workdir") or None,
            capture_output=True, text=True, timeout=20)
    except Exception as exc:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext":
                f"gh-pr-assignee: could not assign {who} on {url} "
                f"({type(exc).__name__}) — assign manually"}}))
        sys.exit(0)
    if r.returncode != 0:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext":
                f"gh-pr-assignee: --add-assignee {who} failed on {url}: "
                f"{(r.stderr or r.stdout).strip()[:200]}"}}))
        sys.exit(0)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": f"gh-pr-assignee: assigned {who} on {url}"}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
