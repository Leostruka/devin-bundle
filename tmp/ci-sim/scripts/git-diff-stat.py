#!/usr/bin/env python3
"""PostToolUse hook: one-line git diff --stat footer after exec calls.

Opt-in footer: only emits when .devin/output-mode.json selects a mode
whose preset sets flags.diff_footer (currently caveman and lean), the cwd
is a git repo, and the diff is non-empty. Format:

    diff-stat: 3 files (+45/-12)

Fail-open everywhere: any exception -> exit 0 silent.
"""
import json
import os
import re
import subprocess
import sys


def _project_dir():
    return os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()


def _footer_enabled(root):
    try:
        with open(os.path.join(root, ".devin", "output-mode.json"),
                  encoding="utf-8-sig") as fh:
            mode = str(json.load(fh).get("mode") or "off").lower()
    except (OSError, ValueError):
        return False
    if mode == "off":
        return False
    try:
        with open(os.path.join(root, "data", "output-modes.json"),
                  encoding="utf-8-sig") as fh:
            presets = json.load(fh)
    except (OSError, ValueError):
        return False
    return any(
        presets.get(p, {}).get("flags", {}).get("diff_footer")
        for p in mode.split("+"))


def _shortstat(root):
    try:
        r = subprocess.run(
            ["git", "diff", "--shortstat", "HEAD"],
            capture_output=True, text=True, timeout=10, cwd=root,
            encoding="utf-8", errors="replace")
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return ""
    if r.returncode != 0:
        return ""
    # " 3 files changed, 45 insertions(+), 12 deletions(-)"
    m = re.search(r"(\d+) files? changed(?:, (\d+) insertion)?"
                  r"(?:, (\d+) deletion)?", r.stdout)
    if not m:
        return ""
    files = m.group(1)
    ins = m.group(2) or "0"
    dele = m.group(3) or "0"
    return "%s files (+%s/-%s)" % (files, ins, dele)


def main():
    try:
        _recfg = getattr(sys.stdin, "reconfigure", None)
        if _recfg:
            try:
                _recfg(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)

    if data.get("tool_name") != "exec":
        sys.exit(0)
    root = _project_dir()
    if not _footer_enabled(root):
        sys.exit(0)
    stat = _shortstat(root)
    if not stat:
        sys.exit(0)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "diff-stat: " + stat,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
