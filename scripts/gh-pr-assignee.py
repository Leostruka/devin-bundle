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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

_CF = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

def _run(*a, **kw):
    kw.setdefault('creationflags', _CF)
    if kw.get('text') or kw.get('universal_newlines'):
        kw.setdefault('encoding', 'utf-8')
        kw.setdefault('errors', 'replace')
    return subprocess.run(*a, **kw)

_CREATE_RX = re.compile(
    r"\bgh\b(?:\s+(?:-[a-zA-Z](?:\s+\S+)??|--[\w-]+(?:=\S+|\s+\S+)??))*"
    r"\s+pr\s+create\b")
_URL_RX = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/pull/\d+")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        _hookrun.pin_stdio_utf8(sys.stdin)
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("payload not a dict")
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)
    if data.get("tool_name") != "exec":
        sys.exit(0)
    resp = data.get("tool_response") or {}
    if not isinstance(resp, dict):
        resp = {}
    if not resp.get("success", True):
        sys.exit(0)
    ti = data.get("tool_input") or {}
    if not isinstance(ti, dict):
        ti = {}
    cmd = ti.get("command") or ""
    if not isinstance(cmd, str):
        sys.exit(0)
    if not _CREATE_RX.search(cmd) or "--assignee" in cmd:
        sys.exit(0)
    out = resp.get("output")
    if not isinstance(out, str):
        sys.exit(0)
    m = _URL_RX.search(out)
    if not m:
        sys.exit(0)  # no PR URL in output — create may have failed anyway

    url = m.group(0)
    who = os.environ.get("GH_PR_ASSIGNEE", "Leostruka")
    gh = os.environ.get("GH_PR_BIN", "gh")
    try:
        r = _run(
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
