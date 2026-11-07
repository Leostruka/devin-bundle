#!/usr/bin/env python3
"""dep-audit-gate — PostToolUse(exec) hook: scan deps after installs.

Cheap pre-filter: exits silently unless the command looks like a package
install AND at least one audit scanner is on PATH. On findings, injects a
[DEP-AUDIT] additionalContext warning. Fail-open on every error path.
"""
import json
import os
import re
import shutil
import subprocess
import sys

try:
    _CF = subprocess.CREATE_NO_WINDOW
except AttributeError:
    _CF = 0

INSTALL_RE = re.compile(
    r"(?:^|[;&|]\s*)(?:sudo\s+)?"
    r"(?:pip3?|uv|poetry|pipenv)\s+(?:install|add|sync|update)\b"
    r"|(?:^|[;&|]\s*)(?:npm|pnpm|yarn|bun)\s+"
    r"(?:install|i|add|ci|update|up)\b"
    r"|(?:^|[;&|]\s*)cargo\s+(?:add|install|update)\b"
    r"|(?:^|[;&|]\s*)go\s+(?:get|install|mod\s+tidy)\b"
    r"|(?:^|[;&|]\s*)composer\s+(?:require|install|update)\b",
    re.IGNORECASE)

SCANNER_HINTS = ("pip-audit", "osv-scanner", "npm", "cargo-audit",
                 "govulncheck")


def _scanners_present():
    return any(shutil.which(s) for s in SCANNER_HINTS)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get("tool_name") != "exec":
        return 0
    cmd = (payload.get("tool_input") or {}).get("command") or ""
    if not INSTALL_RE.search(cmd):
        return 0
    if not _scanners_present():
        return 0
    root = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "dep-audit.py")
    try:
        p = subprocess.run(
            [sys.executable, script, "--root", root],
            capture_output=True, text=True, timeout=300,
            creationflags=_CF)
        data = json.loads(p.stdout or "{}")
    except Exception:
        return 0
    if not data.get("ok"):
        return 0
    total = sum(len(s.get("findings", [])) for s in data.get("scanned", []))
    if total == 0:
        return 0
    ids = []
    for s in data.get("scanned", []):
        for f in s.get("findings", [])[:5]:
            ids.append(f"{f.get('pkg') or '?'}:{f.get('id') or '?'}")
    more = total - len(ids)
    suffix = f" (+{more} more)" if more > 0 else ""
    ctx = (f"[DEP-AUDIT] {total} vulnerable dependenc"
           f"{'y' if total == 1 else 'ies'} found after install: "
           + ", ".join(ids) + suffix
           + ". Run `python scripts/dep-audit.py` for details.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": ctx}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
