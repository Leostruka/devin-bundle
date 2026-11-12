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
    # python family: pip/pip3 (incl. `python -m pip`), uv, poetry,
    # pipenv, pipx, conda/mamba (issue #404 coverage gaps)
    r"(?:(?:python3?(?:\.\d+)?|py)\s+-m\s+)?pip3?\s+"
    r"(?:install|add|sync|update|upgrade)\b"
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?"
    r"uv\s+(?:pip\s+)?(?:install|add|sync|update|upgrade)\b"
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?"
    r"(?:poetry|pipenv|pipx|conda|mamba)\s+"
    r"(?:install|add|sync|update|upgrade)\b"
    # node family
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?"
    r"(?:npm|pnpm|yarn|bun)\s+"
    r"(?:install|i|add|ci|update|up|upgrade)\b"
    # rust / go / php
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?cargo\s+(?:add|install|update)\b"
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?go\s+(?:get|install|mod\s+tidy)\b"
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?composer\s+"
    r"(?:global\s+)?(?:require|install|update)\b"
    # ruby / elixir / dotnet (issue #404: detected ecosystems whose
    # install commands never triggered the gate)
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?gem\s+install\b"
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?(?:bundle|bundler)\s+install\b"
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?mix\s+deps\.(?:get|update)\b"
    r"|(?:^|[;&|]\s*)(?:sudo\s+)?dotnet\s+"
    r"(?:add\b|tool\s+install\b|restore\b)",
    re.IGNORECASE)

SCANNER_HINTS = ("pip-audit", "osv-scanner", "npm", "cargo-audit",
                 "govulncheck")


def _scanners_present():
    return any(shutil.which(s) for s in SCANNER_HINTS)


def main():
    try:
        _recfg = getattr(sys.stdin, "reconfigure", None)
        if _recfg:
            try:
                _recfg(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
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
        # hook budget is 35s (hooks.v1.json): keep the child scan under
        # it - dep-audit self-limits via --max-seconds, this is the
        # hard kill (issue #404: 300s timeout could never finish).
        p = subprocess.run(
            [sys.executable, script, "--root", root,
             "--max-seconds", "28"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=32,
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
