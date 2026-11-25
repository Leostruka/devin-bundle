#!/usr/bin/env python3
"""dep-audit-gate — PostToolUse(exec) hook: scan deps after installs.

Cheap pre-filter: exits silently unless the command looks like a package
install AND at least one audit scanner is on PATH. On findings, injects a
[DEP-AUDIT] additionalContext warning. Fail-open on every error path.
"""
import json
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _hookrun

# Segment start: also `(` subshells, backtick / $( ) command substitution
# and shell-wrapper prefixes (cmd /c, powershell -c, bash -c) - each
# previously made the whole install invisible to the gate.
_SEG = r"(?:^|[;&|(`$]\s*)"
_WRAP = (r"(?:(?:cmd(?:\.exe)?\s+/[ckCK]|"
         r"(?:powershell|pwsh|bash|sh)(?:\.exe)?\s+-c)\s+[\"']?)?")
# Global flags may sit between the manager name and the install verb
# (`pip -q install`, `npm -g i`, `npm --prefix app i`). Any flag may take
# a space-separated value (-i URL, --registry URL, -r req.txt): the
# optional \S+ operand keeps `pip -i https://evil install x` inside the
# match instead of skipping the audit entirely; backtracking keeps
# boolean flags working (`-q install` -> -q flag, install verb).
_GAP = (r"(?:(?:-[a-zA-Z][\w-]*|--[\w-]+(?:=\S*)?)(?:\s+\S+)?\s+)*")
_PFX = _SEG + r"(?:sudo\s+)?" + _WRAP

_INSTALL_RE_PATTERN = (
    _PFX +
    # python family: pip/pip3 (incl. `python -m pip`), uv, poetry,
    # pipenv, pipx, conda/mamba (issue #404 coverage gaps)
    r"(?:(?:(?:python3?(?:\.\d+)?|py)\s+-m\s+)?pip3?|uv|poetry|pipenv|"
    r"pipx|conda|mamba)(?:\.exe)?\s+" + _GAP +
    r"(?:pip\s+)?(?:install|add|sync|update|upgrade)\b"
    # node family
    r"|" + _PFX + r"(?:npm|pnpm|yarn|bun)(?:\.exe)?\s+" + _GAP +
    r"(?:install|i|add|ci|update|up|upgrade)\b"
    # rust / go / php
    r"|" + _PFX + r"cargo(?:\.exe)?\s+" + _GAP +
    r"(?:add|install|update)\b"
    r"|" + _PFX + r"go(?:\.exe)?\s+" + _GAP +
    r"(?:get|install|mod\s+tidy)\b"
    r"|" + _PFX + r"composer(?:\.exe)?\s+" + _GAP +
    r"(?:global\s+)?(?:require|install|update)\b"
    # ruby / elixir / dotnet (issue #404: detected ecosystems whose
    # install commands never triggered the gate)
    r"|" + _PFX + r"gem(?:\.exe)?\s+" + _GAP + r"install\b"
    r"|" + _PFX + r"(?:bundle|bundler)(?:\.exe)?\s+" + _GAP + r"install\b"
    r"|" + _PFX + r"mix(?:\.exe)?\s+" + _GAP + r"deps\.(?:get|update)\b"
    r"|" + _PFX + r"dotnet(?:\.exe)?\s+" + _GAP +
    r"(?:add\b|tool\s+install\b|restore\b)"
    # windows package managers (scoop/winget/choco install)
    r"|" + _PFX + r"(?:scoop|winget|choco(?:latey)?)(?:\.exe)?\s+" +
    _GAP + r"(?:install|add|update|upgrade)\b"
)

_INSTALL_HINTS = (
    "python", "pip", "uv", "poetry", "pipenv", "pipx", "conda",
    "mamba", "npm", "pnpm", "yarn", "bun", "cargo", "go", "composer",
    "gem", "bundle", "mix", "dotnet", "scoop", "winget", "choco",
    "py",
)
_INSTALL_RE = None


def _install_re():
    global _INSTALL_RE
    if _INSTALL_RE is None:
        _INSTALL_RE = re.compile(_INSTALL_RE_PATTERN, re.IGNORECASE)
    return _INSTALL_RE


def _has_install_hint(cmd):
    lowered = cmd.lower()
    return any(hint in lowered for hint in _INSTALL_HINTS)


SCANNER_HINTS = ("pip-audit", "osv-scanner", "npm", "cargo-audit",
                 "govulncheck")


def _scanners_present():
    import shutil
    return any(shutil.which(s) for s in SCANNER_HINTS)


def main():
    try:
        _hookrun.pin_stdio_utf8(sys.stdin)
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("payload not a dict")
    except Exception:
        return 0
    if payload.get("tool_name") not in ("exec", "write_to_process"):
        return 0
    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        ti = {}
    cmd = ti.get("command") or ""
    if payload.get("tool_name") == "write_to_process":
        # 'command' on a wtp payload is never trusted (not in its tool
        # schema; injectable by the caller). Extraction is idempotent so
        # always extract the submitted lines ourselves.
        cmd = _hookrun.wtp_submitted_text(payload)
    if not isinstance(cmd, str) or not _has_install_hint(cmd) \
            or not _install_re().search(cmd):
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
        import subprocess
        p = subprocess.run(
            [sys.executable, script, "--root", root,
             "--max-seconds", "28"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=32,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        data = json.loads(p.stdout or "{}")
    except Exception:
        return 0
    if not data.get("ok"):
        return 0
    try:
        scanned = [s for s in data.get("scanned", []) if isinstance(s, dict)]
        total = sum(len(s.get("findings") or [])
                    for s in scanned)
        if total == 0:
            return 0
        ids = []
        for s in scanned:
            for f in (s.get("findings") or [])[:5]:
                if isinstance(f, dict):
                    ids.append(f"{f.get('pkg') or '?'}:{f.get('id') or '?'}")
    except (TypeError, AttributeError):
        return 0
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
