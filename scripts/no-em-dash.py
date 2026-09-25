#!/usr/bin/env python3
"""Blocks the em-dash character (U+2014) in agent output and deliverables.

Handles two events, dispatched on `hook_event_name`:
  PreToolUse - exec (git commit message, including -F/--file), write,
             edit, notebook_edit
  Stop       - scans staged/unstaged changes for the character

Stdin payloads (per /cli/extensibility/hooks/lifecycle-hooks):
  PreToolUse {"hook_event_name": "PreToolUse", "tool_name": "exec",
              "tool_input": {"command": "..."}}
  Stop       {"hook_event_name": "Stop", "stop_hook_active": false}

Exit codes (per /cli/extensibility/hooks/overview#exit-codes):
  0 = allow, 2 = block.

Commands that merely inspect or replace the character (grep, sed, python
one-liners) stay allowed - exec is only checked where the character would
enter a deliverable: the git commit message.
"""
import sys, json, re, os, subprocess

EM_DASH = chr(0x2014)
SELF_FILE = "no-em-dash.py"


def block(reason):
    """Emit a block decision and exit with code 2 (deny)."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def has_em_dash(text):
    return bool(text) and EM_DASH in text


def read_commit_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, IOError):
        return ""


def extract_commit_file(command):
    """Extract the filepath from 'git commit -F <file>' / '--file=<file>'."""
    for pattern in (
        r"--file=([^\s]+)",
        r"--file\s+([^\s]+)",
        r"(?:^|\s)-F\s+([^\s]+)",
        r"(?:^|\s)-F([^\s]+)",
    ):
        m = re.search(pattern, command)
        if m:
            return m.group(1).strip().strip("\"'")
    return None


def filter_self_diffs(diff_output):
    """Drop diff sections of this detector (its source names the rule)."""
    lines = diff_output.split("\n")
    filtered = []
    skip = False
    for line in lines:
        if line.startswith("diff --git"):
            skip = bool(
                re.search(r'[ab]/(?:.*/)?' + re.escape(SELF_FILE)
                          + r'(?:\s|$)', line))
        if not skip:
            filtered.append(line)
    return "\n".join(filtered)


def handle_stop(_data):
    """Scan staged and unstaged changes for the em-dash character."""
    cwd = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    for args in (
        ["git", "diff", "--cached", "--unified=0"],
        ["git", "diff", "--unified=0"],
    ):
        try:
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=10, cwd=cwd
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return  # no git or no repo: allow
        if result.returncode != 0:
            continue
        filtered = filter_self_diffs(result.stdout)
        added = "\n".join(
            line[1:]
            for line in filtered.split("\n")
            if line.startswith("+") and not line.startswith("+++")
        )
        if has_em_dash(added):
            scope = "staged" if "--cached" in args else "unstaged"
            block(
                f"em-dash (U+2014) detected in {scope} changes. "
                "Replace it before stopping."
            )


def handle_pre_tool_use(data):
    tool_name = data.get("tool_name", "") or ""
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return

    if tool_name == "exec":
        command = tool_input.get("command", "") or ""
        low = command.lower()
        if "git commit" in low:
            commit_file = extract_commit_file(command)
            if commit_file:
                if has_em_dash(read_commit_file(commit_file)):
                    block(
                        f"em-dash (U+2014) detected in the commit message "
                        f"file '{commit_file}'."
                    )
            elif has_em_dash(command):
                block("em-dash (U+2014) detected in the git commit message.")
            return
        # Deliverable-bound commands: the character can only be text
        # destined for a PR/issue/release/tag body.
        if has_em_dash(command) and re.search(
                r"gh\s+(pr|issue|release)\s+(create|comment|edit|review)"
                r"|git\s+tag", low):
            block("em-dash (U+2014) detected in a deliverable text command.")
        return

    if tool_name in ("write", "edit", "notebook_edit"):
        file_path = tool_input.get("file_path", "") \
            or tool_input.get("notebook_path", "") or ""
        if SELF_FILE in file_path:
            return
        content = tool_input.get("content") \
            or tool_input.get("new_string") \
            or tool_input.get("new_source") or ""
        if has_em_dash(content):
            block(
                f"em-dash (U+2014) detected in {tool_name} content. "
                "Use a regular hyphen instead."
            )


HANDLERS = {
    "PreToolUse": handle_pre_tool_use,
    "Stop": handle_stop,
}


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError, ValueError):
        sys.exit(0)  # fail-open

    handler = HANDLERS.get(data.get("hook_event_name", ""))
    if handler is not None:
        handler(data)

    sys.exit(0)


if __name__ == "__main__":
    main()
