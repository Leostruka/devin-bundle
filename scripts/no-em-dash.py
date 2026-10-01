#!/usr/bin/env python3
"""Blocks the em-dash character (U+2014) in prose within prose deliverables.

Two scopes combine: only prose file types are covered (TEXT_EXTS;
code/config/data files are exempt), and inside those files only
prose-position uses count. Structural markdown uses are allowed:
table rows ('| a | - |'), em-dash bullet items ('- item'), quote
attribution ('> - name'), and text inside fenced code blocks. Prose
usage ('a - b' mid-sentence) is what is blocked.

Handles two events, dispatched on `hook_event_name`:
  PreToolUse - exec (git commit message, including -F/--file), write,
             edit, notebook_edit - prose file paths only
  Stop       - scans staged/unstaged changes and untracked files,
             prose file paths only

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

# Prose deliverables only. Source code, configs and data files are exempt:
# the rule guards written text, not characters inside string literals.
TEXT_EXTS = {
    ".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".tex",
    ".ipynb",
}


def is_text_path(path):
    """True when the path is a prose deliverable the rule covers."""
    if not path:
        return True  # unknown target: keep checking
    ext = os.path.splitext(path)[1].lower()
    if not ext:
        return True  # extensionless docs (LICENSE, AUTHORS, NOTICE)
    return ext in TEXT_EXTS


def block(reason):
    """Emit a block decision and exit with code 2 (deny)."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(2)


def prose_em_dash_lines(text):
    """Return lines where U+2014 appears in prose position.

    Allowed structural contexts (markdown): table rows, em-dash bullets,
    quote attribution, and fenced code blocks. Everything else counts
    as prose."""
    hits = []
    in_fence = False
    fence_marker = None
    for line in (text or "").split("\n"):
        s = line.strip()
        if s[:3] in ("```", "~~~"):
            if not in_fence:
                in_fence, fence_marker = True, s[:3]
            elif s.startswith(fence_marker):
                in_fence, fence_marker = False, None
            continue
        if in_fence or EM_DASH not in s:
            continue
        if s.startswith("|"):                    # md table row
            continue
        if s.startswith(EM_DASH):                # '- item' dash bullet
            continue
        if re.match(r"^>\s*" + EM_DASH, s):      # '> - attribution'
            continue
        hits.append(line)
    return hits


def has_prose_em_dash(text):
    return bool(prose_em_dash_lines(text))


def read_text_file(filepath, cwd):
    path = filepath if os.path.isabs(filepath) else os.path.join(cwd, filepath)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, IOError):
        return ""


def extract_flag_file(command, flags, short_f=True):
    """Extract the filepath from '--flag=<file>' args (and -F for git).

    short_f must stay off for gh commands: there '-F' means --fill."""
    patterns = [
        rf"--(?:{flags})=([^\s]+)",
        rf"--(?:{flags})\s+([^\s]+)",
    ]
    if short_f:
        patterns += [
            r"(?:^|\s)-F\s+([^\s]+)",
            r"(?:^|\s)-F([^\s]+)",
        ]
    for pattern in patterns:
        m = re.search(pattern, command)
        if m:
            return m.group(1).strip().strip("\"'")
    return None


DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.*)$")


def added_text_lines(diff_output):
    """Collect added lines from prose files only.

    Tracks the `+++ b/<path>` header per diff section; also drops this
    detector's own file (its source names the rule)."""
    out = []
    current_is_text = False
    for line in diff_output.split("\n"):
        if line.startswith("diff --git"):
            current_is_text = False
            continue
        m = DIFF_FILE_RE.match(line)
        if m:
            path = m.group(1)
            current_is_text = (SELF_FILE not in path) and is_text_path(path)
            continue
        if current_is_text and line.startswith("+") \
                and not line.startswith("+++"):
            out.append(line[1:])
    return "\n".join(out)


def handle_stop(_data):
    """Scan staged and unstaged changes for the em-dash character."""
    cwd = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    for args in (
        ["git", "diff", "--cached", "--unified=0"],
        ["git", "diff", "--unified=0"],
    ):
        try:
            result = subprocess.run(
                args, capture_output=True, timeout=10, cwd=cwd,
                encoding="utf-8", errors="replace",
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return  # no git or no repo: allow
        if result.returncode != 0:
            continue
        added = added_text_lines(result.stdout)
        if has_prose_em_dash(added):
            scope = "staged" if "--cached" in args else "unstaged"
            block(
                f"em-dash (U+2014) detected in {scope} changes. "
                "Rewrite the text naturally before stopping - "
                "do not just swap in a hyphen."
            )
    scan_untracked(cwd)


def scan_untracked(cwd):
    """Scan files git diff never lists: new, unstaged-for-add files."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, timeout=10, cwd=cwd,
            encoding="utf-8", errors="replace",
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return
    if result.returncode != 0:
        return
    for rel in result.stdout.splitlines():
        if not rel or SELF_FILE in rel or not is_text_path(rel):
            continue
        path = os.path.join(cwd, rel)
        try:
            if os.path.getsize(path) > 512 * 1024:
                continue
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        if b"\x00" in raw[:4096]:  # binary
            continue
        if has_prose_em_dash(raw.decode("utf-8", "replace")):
            block(
                f"em-dash (U+2014) detected in untracked file '{rel}'. "
                "Rewrite the text naturally before stopping - "
                "do not just swap in a hyphen."
            )


def handle_pre_tool_use(data):
    tool_name = data.get("tool_name", "") or ""
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return

    if tool_name == "exec":
        command = tool_input.get("command", "") or ""
        low = command.lower()
        cwd = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
        if re.search(r"git\s+(commit|tag|merge|cherry-pick|rebase|stash)\b", low):
            msg_file = extract_flag_file(command, r"file|message")
            if msg_file:
                if has_prose_em_dash(read_text_file(msg_file, cwd)):
                    block(
                        "em-dash (U+2014) detected in the git message "
                        f"file '{msg_file}'. Rewrite the text naturally."
                    )
            elif has_prose_em_dash(command):
                block("em-dash (U+2014) detected in the git message text. "
                      "Rewrite the text naturally.")
            return
        if re.search(
                r"gh\s+(pr|issue|release)\s+"
                r"(create|comment|edit|review|close|reopen)", low):
            body_file = extract_flag_file(
                command, r"body-file|notes-file", short_f=False)
            if body_file:
                if has_prose_em_dash(read_text_file(body_file, cwd)):
                    block(
                        "em-dash (U+2014) detected in the gh body "
                        f"file '{body_file}'. Rewrite the text naturally."
                    )
            elif has_prose_em_dash(command):
                block("em-dash (U+2014) detected in a deliverable text "
                      "command. Rewrite the text naturally.")
        return

    if tool_name in ("write", "edit", "notebook_edit"):
        file_path = tool_input.get("file_path", "") \
            or tool_input.get("notebook_path") or ""
        if SELF_FILE in file_path or not is_text_path(file_path):
            return
        content = tool_input.get("content") \
            or tool_input.get("new_string") \
            or tool_input.get("new_source") or ""
        if has_prose_em_dash(content):
            block(
                f"em-dash (U+2014) detected in {tool_name} content. "
                "Rewrite the sentence naturally - commas, periods or "
                "restructuring work; do not just swap in a hyphen."
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
